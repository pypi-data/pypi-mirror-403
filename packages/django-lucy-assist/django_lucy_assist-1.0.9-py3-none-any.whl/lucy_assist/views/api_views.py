import json

from django.conf import settings
from django.db.models import Count
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin

from lucy_assist.utils.log_utils import LogUtils
from lucy_assist.utils.message_utils import MessageUtils
from lucy_assist.models import Conversation, Message, ConfigurationLucyAssist
from lucy_assist.constantes import LucyAssistConstantes
from lucy_assist.services.claude_service import ClaudeService
from lucy_assist.services.context_service import ContextService
from lucy_assist.services.tool_executor_service import create_tool_executor

class LucyAssistAPIView(LoginRequiredMixin, View):
    """Classe de base pour les vues API Lucy Assist."""

    def dispatch(self, request, *args, **kwargs):
        # Vérifier que Lucy Assist est activé
        config = ConfigurationLucyAssist.get_config()
        if not config.actif:
            return JsonResponse({
                'error': 'Lucy est temporairement désactivé'
            }, status=503)
        return super().dispatch(request, *args, **kwargs)

    def json_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def error_response(self, message, status=400):
        return JsonResponse({'error': message}, status=status)


class ConversationListCreateView(LucyAssistAPIView):
    """Liste et création de conversations."""

    def get(self, request):
        """Liste les conversations de l'utilisateur."""
        conversations = Conversation.objects.filter(
            utilisateur=request.user,
            is_active=True
        ).order_by('-created_date')[:50]

        data = [{
            'id': conv.id,
            'titre': conv.titre or f"Conversation #{conv.id}",
            'created_date': conv.created_date.isoformat(),
            'total_tokens': conv.total_tokens,
            'dernier_message': conv.dernier_message.contenu[:100] if conv.dernier_message else None
        } for conv in conversations]

        return self.json_response({'conversations': data})

    def post(self, request):
        """Crée une nouvelle conversation."""
        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}

        page_contexte = body.get('page_contexte', '')

        conversation = Conversation.objects.create(
            utilisateur=request.user,
            page_contexte=page_contexte
        )

        return self.json_response({
            'id': conversation.id,
            'titre': conversation.titre,
            'created_date': conversation.created_date.isoformat()
        }, status=201)


class ConversationDetailView(LucyAssistAPIView):
    """Détail, mise à jour et suppression d'une conversation."""

    def get(self, request, pk):
        """Récupère une conversation avec ses messages."""
        try:
            conversation = Conversation.objects.get(
                pk=pk,
                utilisateur=request.user
            )
        except Conversation.DoesNotExist:
            return self.error_response('Conversation non trouvée', 404)

        messages = [{
            'id': msg.id,
            'repondant': msg.repondant,
            'contenu': msg.contenu,
            'tokens_utilises': msg.tokens_utilises,
            'type_action': msg.type_action,
            'created_date': msg.created_date.isoformat()
        } for msg in conversation.messages.all()]

        return self.json_response({
            'id': conversation.id,
            'titre': conversation.titre,
            'page_contexte': conversation.page_contexte,
            'created_date': conversation.created_date.isoformat(),
            'total_tokens': conversation.total_tokens,
            'messages': messages
        })

    def delete(self, request, pk):
        """Supprime une conversation."""
        try:
            conversation = Conversation.objects.get(
                pk=pk,
                utilisateur=request.user
            )
        except Conversation.DoesNotExist:
            return self.error_response('Conversation non trouvée', 404)

        conversation.delete()
        return self.json_response({'success': True})


class MessageCreateView(LucyAssistAPIView):
    """Création d'un message utilisateur."""

    def post(self, request, conversation_id):
        """Ajoute un message utilisateur à une conversation."""
        try:
            conversation = Conversation.objects.get(
                pk=conversation_id,
                utilisateur=request.user
            )
        except Conversation.DoesNotExist:
            return self.error_response('Conversation non trouvée', 404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return self.error_response('JSON invalide', 400)

        contenu = body.get('contenu', '').strip()
        if not contenu:
            return self.error_response('Le message ne peut pas être vide', 400)

        message = Message.objects.create(
            conversation=conversation,
            repondant=LucyAssistConstantes.Repondant.UTILISATEUR,
            contenu=MessageUtils.remove_emojis(contenu)
        )

        # Générer le titre si c'est le premier message
        if conversation.messages.count() == 1:
            conversation.generer_titre()

        return self.json_response({
            'id': message.id,
            'contenu': message.contenu,
            'created_date': message.created_date.isoformat()
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class ChatCompletionView(LucyAssistAPIView):
    """Génération de réponse via Claude API avec streaming."""

    def post(self, request, conversation_id):
        """Génère une réponse Claude pour la conversation."""
        try:
            conversation = Conversation.objects.get(
                pk=conversation_id,
                utilisateur=request.user
            )
        except Conversation.DoesNotExist:
            return self.error_response('Conversation non trouvée', 404)

        # Vérifier les tokens disponibles
        config = ConfigurationLucyAssist.get_config()
        if not config.a_suffisamment_tokens():
            return self.json_response({
                'error': 'tokens_insuffisants',
                'message': 'Vous n\'avez plus assez de crédits. Veuillez acheter un nouveau pack.',
                'tokens_disponibles': config.tokens_disponibles
            }, status=402)

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}

        page_contexte = body.get('page_contexte', conversation.page_contexte)

        # Construire le contexte de la conversation
        messages_historique = list(conversation.messages.all().order_by('created_date'))

        # Obtenir le contexte de la page
        context_service = ContextService(request.user)
        contexte_page = context_service.get_page_context(page_contexte)

        # Appeler Claude avec le tool executor
        claude_service = ClaudeService()
        tool_executor = create_tool_executor(request.user)

        try:
            # Stream la réponse
            def generate():
                full_response = ""
                total_tokens = 0
                tool_actions = []  # Pour tracker les actions effectuées

                for chunk in claude_service.chat_completion_stream(
                    messages=messages_historique,
                    page_context=contexte_page,
                    user=request.user,
                    tool_executor=tool_executor
                ):
                    chunk_type = chunk.get('type')

                    if chunk_type == 'content':
                        full_response += chunk['content']
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk['content']})}\n\n"

                    elif chunk_type == 'tool_use':
                        # Informer le client qu'un tool est appelé
                        yield f"data: {json.dumps({'type': 'tool_use', 'tool_name': chunk['tool_name']})}\n\n"

                    elif chunk_type == 'tool_result':
                        # Envoyer le résultat du tool au client
                        tool_actions.append({
                            'tool': chunk['tool_name'],
                            'result': chunk['result']
                        })
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool_name': chunk['tool_name'], 'result': chunk['result']})}\n\n"

                    elif chunk_type == 'tool_error':
                        yield f"data: {json.dumps({'type': 'tool_error', 'tool_name': chunk['tool_name'], 'error': chunk['error']})}\n\n"

                    elif chunk_type == 'usage':
                        total_tokens = chunk.get('total_tokens', 0)

                    elif chunk_type == 'error':
                        yield f"data: {json.dumps({'type': 'error', 'error': chunk['error']})}\n\n"
                        return

                # Sauvegarder la réponse complète
                if full_response:
                    # Inclure les actions effectuées dans les métadonnées si nécessaire
                    type_action = None
                    if tool_actions:
                        # Déterminer le type d'action principal
                        for action in tool_actions:
                            if 'create' in action['tool']:
                                type_action = LucyAssistConstantes.TypeAction.CRUD
                                break
                            elif 'update' in action['tool'] or 'delete' in action['tool']:
                                type_action = LucyAssistConstantes.TypeAction.CRUD
                                break
                            elif 'search' in action['tool']:
                                type_action = LucyAssistConstantes.TypeAction.RECHERCHE
                                break

                    message = Message.objects.create(
                        conversation=conversation,
                        repondant=LucyAssistConstantes.Repondant.CHATBOT,
                        contenu=MessageUtils.remove_emojis(full_response),
                        tokens_utilises=total_tokens,
                        type_action=type_action
                    )

                    response_data = {
                        'type': 'done',
                        'message_id': message.id,
                        'tokens_utilises': total_tokens
                    }

                    # Ajouter les actions effectuées
                    if tool_actions:
                        response_data['actions'] = tool_actions

                    yield f"data: {json.dumps(response_data)}\n\n"

            response = StreamingHttpResponse(
                generate(),
                content_type='text/event-stream'
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response

        except Exception as e:
            LogUtils.error("Erreur lors de l'appel à Claude")
            return self.error_response(f'Erreur lors de la génération: {str(e)}', 500)


class TokenStatusView(LucyAssistAPIView):
    """Statut des tokens disponibles."""

    def get(self, request):
        """Retourne le statut des tokens."""
        config = ConfigurationLucyAssist.get_config()

        return self.json_response({
            'tokens_disponibles': config.tokens_disponibles,
            'tokens_en_euros': round(config.tokens_restants_en_euros, 2),
            'conversations_estimees': config.conversations_estimees,
            'prix_par_million': float(config.prix_par_million_tokens),
            'actif': config.actif
        })


class AcheterTokensView(LucyAssistAPIView):
    """Achat de tokens via Lucy CRM."""

    def post(self, request):
        """Génère un lien d'achat de tokens."""
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return self.error_response('JSON invalide', 400)

        montant_ht = body.get('montant_ht')
        if not montant_ht or montant_ht < 10:
            return self.error_response('Le montant minimum est de 10 EUR', 400)

        # Récupérer le SIREN client depuis les settings
        siren_client = getattr(settings, 'SIREN_CLIENT', None)
        if not siren_client:
            return self.error_response('Configuration SIREN manquante', 500)

        # Générer l'URL de souscription Lucy
        url_souscription = f"https://app.lucy-crm.fr/sav/souscription-token-lucy-assist/{siren_client}/{montant_ht}"

        # Calculer les tokens qui seront ajoutés
        config = ConfigurationLucyAssist.get_config()
        tokens_a_ajouter = int((montant_ht / float(config.prix_par_million_tokens)) * 1_000_000)

        return self.json_response({
            'url_souscription': url_souscription,
            'montant_ht': montant_ht,
            'tokens_a_ajouter': tokens_a_ajouter,
            'conversations_estimees': int(tokens_a_ajouter / LucyAssistConstantes.TOKENS_MOYENS_PAR_CONVERSATION)
        })


class SuggestionsView(LucyAssistAPIView):
    """Suggestions de questions fréquentes."""

    def get(self, request):
        """Retourne les suggestions de questions."""
        # Récupérer les questions les plus fréquentes des conversations précédentes
        questions_frequentes = Message.objects.filter(
            conversation__utilisateur=request.user,
            repondant=LucyAssistConstantes.Repondant.UTILISATEUR
        ).values('contenu').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        suggestions = [q['contenu'][:100] for q in questions_frequentes]

        # Compléter avec les suggestions configurées si nécessaire
        if len(suggestions) < 5:
            config = ConfigurationLucyAssist.get_config()
            for question in config.get_questions_frequentes():
                if question not in suggestions:
                    suggestions.append(question)
                if len(suggestions) >= 5:
                    break

        return self.json_response({'suggestions': suggestions})


class PageContextView(LucyAssistAPIView):
    """Récupération du contexte de la page courante."""

    def get(self, request):
        """Retourne le contexte de la page."""
        page_url = request.GET.get('url', '')

        context_service = ContextService(request.user)
        contexte = context_service.get_page_context(page_url)

        return self.json_response(contexte)


class CacheStatsView(LucyAssistAPIView):
    """Statistiques du cache de contexte projet."""

    def get(self, request):
        """Retourne les statistiques du cache."""
        from lucy_assist.services.project_context_service import ProjectContextService

        # Vérifier que l'utilisateur est staff
        if not request.user.is_staff:
            return self.error_response('Permission refusée', 403)

        service = ProjectContextService()
        stats = service.get_cache_stats()

        # Calculer les économies en euros
        config = ConfigurationLucyAssist.get_config()
        tokens_saved = stats.get('total_tokens_saved', 0)
        euros_saved = (tokens_saved / 1_000_000) * float(config.prix_par_million_tokens)

        return self.json_response({
            'cache_stats': stats,
            'tokens_economises': tokens_saved,
            'euros_economises': round(euros_saved, 2),
            'message': f"Le cache a permis d'économiser ~{tokens_saved:,} tokens ({euros_saved:.2f}€)"
        })


class CacheInvalidateView(LucyAssistAPIView):
    """Invalidation du cache de contexte projet."""

    def post(self, request):
        """Invalide le cache (tout ou une clé spécifique)."""
        from lucy_assist.services.project_context_service import ProjectContextService

        # Vérifier que l'utilisateur est staff
        if not request.user.is_staff:
            return self.error_response('Permission refusée', 403)

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}

        cache_key = body.get('cache_key')

        from lucy_assist.models import ProjectContextCache

        if cache_key:
            ProjectContextCache.invalidate_cache(cache_key)
            return self.json_response({
                'success': True,
                'message': f"Cache '{cache_key}' invalidé"
            })
        else:
            ProjectContextCache.invalidate_all()
            return self.json_response({
                'success': True,
                'message': "Tous les caches ont été invalidés"
            })


class FeedbackCreateView(LucyAssistAPIView):
    """Envoi d'un feedback utilisateur pour signaler un problème avec Lucy Assist."""

    # Email par défaut si aucun collaborateur associé
    EMAIL_FALLBACK = 'maxence@revolucy.fr'

    def post(self, request):
        """Envoie un email avec la conversation à l'équipe Revolucy."""
        import requests
        from django.core.mail import send_mail
        from django.utils import timezone

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return self.error_response('JSON invalide', 400)

        # Récupérer les données
        conversation_id = body.get('conversation_id')
        description = body.get('description', '').strip()
        page_url = body.get('page_url', '')

        # Récupérer la conversation avec tous ses messages
        conversation = None
        messages_conversation = []

        if conversation_id:
            try:
                conversation = Conversation.objects.get(pk=conversation_id, utilisateur=request.user)
                messages_conversation = list(conversation.messages.all().order_by('created_date'))
            except Conversation.DoesNotExist:
                return self.error_response('Conversation non trouvée', 404)
        else:
            return self.error_response('ID de conversation requis', 400)

        # Construire le contenu de la conversation
        conversation_content = self._formater_conversation(messages_conversation)

        # Envoyer l'email
        try:
            # Récupérer l'email du collaborateur associé via l'API Lucy CRM
            destinataire = self._get_collaborateur_email()

            user_name = request.user.get_full_name() if hasattr(request.user, 'get_full_name') else str(request.user)
            user_email = request.user.email if hasattr(request.user, 'email') else 'Non disponible'

            sujet = f"[Lucy Assist] Feedback - {user_name}"

            message_email = f"""
Un utilisateur a signalé un problème avec Lucy Assist.

================================================================================
INFORMATIONS UTILISATEUR
================================================================================
Utilisateur : {user_name}
Email       : {user_email}
Date        : {timezone.now().strftime('%d/%m/%Y à %H:%M')}
Page        : {page_url or 'Non spécifiée'}

================================================================================
DESCRIPTION DU PROBLÈME
================================================================================
{description or 'Aucune description fournie'}

================================================================================
CONVERSATION COMPLÈTE
================================================================================
{conversation_content}

================================================================================
INFORMATIONS TECHNIQUES
================================================================================
Conversation ID : {conversation.id}
Titre           : {conversation.titre or 'Sans titre'}
Total tokens    : {conversation.total_tokens}
Créée le        : {conversation.created_date.strftime('%d/%m/%Y à %H:%M')}
"""

            # Récupérer l'email expéditeur avec fallback
            from_email = getattr(settings, 'EMAIL_EXPEDITEUR', None) \
                or getattr(settings, 'DEFAULT_FROM_EMAIL', None) \
                or 'noreply@revolucy.fr'

            send_mail(
                subject=sujet,
                message=message_email,
                from_email=from_email,
                recipient_list=[destinataire],
                fail_silently=False
            )

            LogUtils.info(f"Feedback Lucy Assist envoyé par {user_email} à {destinataire} - Conversation #{conversation.id}")

            return self.json_response({
                'success': True,
                'message': 'Merci pour votre retour ! Notre équipe va analyser le problème.'
            }, status=201)

        except Exception as e:
            LogUtils.error(f"Erreur envoi feedback Lucy Assist: {str(e)}")
            return self.error_response('Erreur lors de l\'envoi du feedback', 500)

    def _get_collaborateur_email(self):
        """
        Récupère l'email du collaborateur associé via l'API Lucy CRM.
        Utilise le SIREN du client configuré dans les settings.
        Retourne l'email par défaut si non trouvé.
        """
        import requests

        try:
            # Récupérer le SIREN depuis les settings
            siren_client = getattr(settings, 'SIREN_CLIENT', None)
            if not siren_client:
                LogUtils.warning("SIREN_CLIENT non configuré, utilisation de l'email par défaut")
                return self.EMAIL_FALLBACK

            # Appel à l'API Lucy CRM
            url = f"https://app.lucy-crm.fr/api/credit-client/{siren_client}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                collaborateur_email = data.get('collaborateur_associe')

                if collaborateur_email:
                    LogUtils.info(f"Collaborateur associé trouvé: {collaborateur_email}")
                    return collaborateur_email
                else:
                    LogUtils.info("Aucun collaborateur associé, utilisation de l'email par défaut")
                    return self.EMAIL_FALLBACK
            else:
                LogUtils.warning(f"API Lucy CRM a retourné le status {response.status_code}")
                return self.EMAIL_FALLBACK

        except requests.RequestException as e:
            LogUtils.error(f"Erreur appel API Lucy CRM: {str(e)}")
            return self.EMAIL_FALLBACK
        except Exception as e:
            LogUtils.error(f"Erreur récupération collaborateur: {str(e)}")
            return self.EMAIL_FALLBACK

    def _formater_conversation(self, messages):
        """Formate la liste des messages en texte lisible."""
        if not messages:
            return "Aucun message dans la conversation"

        lignes = []
        for msg in messages:
            repondant = "👤 UTILISATEUR" if msg.repondant == 'UTILISATEUR' else "🤖 LUCY"
            date_str = msg.created_date.strftime('%H:%M:%S')
            lignes.append(f"[{date_str}] {repondant}:")
            lignes.append(f"{msg.contenu}")
            lignes.append("-" * 40)

        return "\n".join(lignes)
