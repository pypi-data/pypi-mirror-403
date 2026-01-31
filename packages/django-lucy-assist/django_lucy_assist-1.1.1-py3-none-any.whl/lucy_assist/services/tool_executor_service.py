"""
Service d'exécution des tools pour Lucy Assist.

Ce service fait le lien entre les appels de tools de Claude
et les services CRUD/Context de l'application.
"""
from typing import Dict, Any

from django.urls import reverse

from lucy_assist.utils.log_utils import LogUtils
from lucy_assist.services.crud_service import CRUDService
from lucy_assist.services.context_service import ContextService
from lucy_assist.services.tools_definition import get_app_for_model
from lucy_assist.services.gitlab_service import GitLabService
from lucy_assist.services.bug_notification_service import BugNotificationService


class ToolExecutorService:
    """Service pour exécuter les tools appelés par Claude."""

    def __init__(self, user):
        self.user = user
        self.crud_service = CRUDService(user)
        self.context_service = ContextService(user)
        self.gitlab_service = GitLabService()
        self.bug_notification_service = BugNotificationService(user)

    def execute(self, tool_name: str, tool_input: Dict[str, Any], user=None) -> Dict[str, Any]:
        """
        Exécute un tool et retourne le résultat.

        Args:
            tool_name: Nom du tool à exécuter
            tool_input: Paramètres du tool
            user: Utilisateur (optionnel, utilise self.user si non fourni)

        Returns:
            Dict avec le résultat de l'exécution
        """
        if user:
            self.user = user
            self.crud_service = CRUDService(user)
            self.context_service = ContextService(user)

        # Dispatcher vers la méthode appropriée
        handlers = {
            'create_object': self._handle_create_object,
            'update_object': self._handle_update_object,
            'get_deletion_impact': self._handle_get_deletion_impact,
            'delete_object': self._handle_delete_object,
            'search_objects': self._handle_search_objects,
            'get_object_details': self._handle_get_object_details,
            'get_form_fields': self._handle_get_form_fields,
            'navigate_to_page': self._handle_navigate_to_page,
            'analyze_bug': self._handle_analyze_bug,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return {'error': f'Tool inconnu: {tool_name}'}

        try:
            return handler(tool_input)
        except Exception as e:
            LogUtils.error(f"Erreur lors de l'exécution du tool {tool_name}")
            return {'error': str(e)}

    def _handle_create_object(self, params: Dict) -> Dict:
        """Crée un nouvel objet."""
        app_name = params.get('app_name') or get_app_for_model(params.get('model_name', ''))
        model_name = params.get('model_name', '')
        data = params.get('data', {})

        if not model_name:
            return {'error': 'model_name est requis'}

        if not data:
            return {'error': 'data est requis pour créer un objet'}

        result = self.crud_service.create_object(app_name, model_name, data)

        if result.get('success'):
            # Ajouter l'URL de l'objet créé
            try:
                url = reverse(
                    f'{app_name}:{model_name.lower()}-form',
                    kwargs={'pk': result['object_id']}
                )
                result['url'] = url
            except Exception:
                pass

        return result

    def _handle_update_object(self, params: Dict) -> Dict:
        """Met à jour un objet existant."""
        app_name = params.get('app_name') or get_app_for_model(params.get('model_name', ''))
        model_name = params.get('model_name', '')
        object_id = params.get('object_id')
        data = params.get('data', {})

        if not model_name:
            return {'error': 'model_name est requis'}

        if not object_id:
            return {'error': 'object_id est requis'}

        if not data:
            return {'error': 'data est requis pour modifier un objet'}

        return self.crud_service.update_object(app_name, model_name, object_id, data)

    def _handle_get_deletion_impact(self, params: Dict) -> Dict:
        """
        Analyse l'impact d'une suppression avant de l'exécuter.
        Retourne la liste de toutes les conséquences (cascade, SET_NULL, etc.)
        """
        app_name = params.get('app_name') or get_app_for_model(params.get('model_name', ''))
        model_name = params.get('model_name', '')
        object_id = params.get('object_id')

        if not model_name:
            return {'error': 'model_name est requis'}

        if not object_id:
            return {'error': 'object_id est requis'}

        # Analyser l'impact
        impact = self.crud_service.get_deletion_impact(app_name, model_name, object_id)

        # Formater le message pour l'utilisateur
        impact['formatted_message'] = self.crud_service.format_deletion_impact_message(impact)

        return {
            'success': True,
            'impact': impact
        }

    def _handle_delete_object(self, params: Dict) -> Dict:
        """
        Supprime un objet.
        Requiert que l'utilisateur ait explicitement confirmé après avoir vu l'impact.
        """
        app_name = params.get('app_name') or get_app_for_model(params.get('model_name', ''))
        model_name = params.get('model_name', '')
        object_id = params.get('object_id')
        confirmed = params.get('confirmed', False)

        if not model_name:
            return {'error': 'model_name est requis'}

        if not object_id:
            return {'error': 'object_id est requis'}

        # Vérifier que la confirmation a été donnée
        if not confirmed:
            return {
                'error': 'Confirmation requise. Utilisez d\'abord get_deletion_impact pour voir les conséquences, '
                         'puis demandez confirmation à l\'utilisateur avant de supprimer.',
                'requires_confirmation': True
            }

        # Exécuter la suppression
        return self.crud_service.delete_object(app_name, model_name, object_id)

    def _handle_search_objects(self, params: Dict) -> Dict:
        """Recherche des objets."""
        query = params.get('query', '')
        model_name = params.get('model_name')
        limit = params.get('limit', 10)

        if not query:
            return {'error': 'query est requis'}

        results = self.context_service.search_objects(query, model_name, limit)

        return {
            'success': True,
            'count': len(results),
            'results': results
        }

    def _handle_get_object_details(self, params: Dict) -> Dict:
        """Récupère les détails d'un objet."""
        app_name = params.get('app_name') or get_app_for_model(params.get('model_name', ''))
        model_name = params.get('model_name', '')
        object_id = params.get('object_id')

        if not model_name:
            return {'error': 'model_name est requis'}

        if not object_id:
            return {'error': 'object_id est requis'}

        result = self.crud_service.get_object(app_name, model_name, object_id)

        if result:
            return {'success': True, 'data': result}
        else:
            return {'error': f'{model_name} #{object_id} non trouvé ou accès refusé'}

    def _handle_get_form_fields(self, params: Dict) -> Dict:
        """Récupère les champs d'un formulaire."""
        app_name = params.get('app_name') or get_app_for_model(params.get('model_name', ''))
        model_name = params.get('model_name', '')

        if not model_name:
            return {'error': 'model_name est requis'}

        required_fields = self.crud_service.get_required_fields(
            self.crud_service.get_model(app_name, model_name)
        )
        optional_fields = self.crud_service.get_optional_fields(
            self.crud_service.get_model(app_name, model_name)
        )

        return {
            'success': True,
            'model_name': model_name,
            'required_fields': required_fields,
            'optional_fields': optional_fields
        }

    def _handle_navigate_to_page(self, params: Dict) -> Dict:
        """Génère une URL de navigation."""
        page_type = params.get('page_type', 'list')
        app_name = params.get('app_name') or get_app_for_model(params.get('model_name', ''))
        model_name = params.get('model_name', '')
        object_id = params.get('object_id')

        if not model_name:
            return {'error': 'model_name est requis'}

        model_lower = model_name.lower()

        try:
            if page_type == 'list':
                url = reverse(f'{app_name}:{model_lower}-list')
            elif page_type == 'create':
                url = reverse(f'{app_name}:{model_lower}-form')
            elif page_type in ['detail', 'edit']:
                if not object_id:
                    return {'error': 'object_id est requis pour detail/edit'}
                url = reverse(f'{app_name}:{model_lower}-form', kwargs={'pk': object_id})
            else:
                return {'error': f'Type de page inconnu: {page_type}'}

            return {
                'success': True,
                'url': url,
                'message': f'Naviguez vers: {url}'
            }

        except Exception as e:
            LogUtils.info(f"Erreur génération URL: {e}")
            # Fallback: générer une URL probable
            if page_type == 'list':
                url = f'/{app_name}/{model_lower}/list/'
            elif page_type == 'create':
                url = f'/{app_name}/{model_lower}/add/'
            else:
                url = f'/{app_name}/{model_lower}/{object_id}/'

            return {
                'success': True,
                'url': url,
                'message': f'URL probable: {url} (vérifiez la disponibilité)'
            }

    def _handle_analyze_bug(self, params: Dict) -> Dict:
        """
        Analyse un bug potentiel en utilisant GitLab et Claude.
        Si un bug est détecté, envoie automatiquement une notification à Revolucy.
        """
        from lucy_assist.services.claude_service import ClaudeService

        user_description = params.get('user_description', '')
        error_message = params.get('error_message', '')
        page_url = params.get('page_url', '')
        model_name = params.get('model_name', '')
        action_type = params.get('action_type', 'other')

        if not user_description:
            return {'error': 'user_description est requis'}

        # Récupérer le contexte du code via GitLab
        code_context = ""
        file_path = ""

        try:
            # Rechercher le code pertinent basé sur le modèle ou l'URL
            if model_name:
                # Chercher le modèle et ses fichiers associés
                model_info = self.gitlab_service.find_model_and_form(model_name)
                if model_info.get('model_code'):
                    code_context += f"=== MODÈLE {model_name} ===\n"
                    code_context += f"Fichier: {model_info.get('model_file', 'inconnu')}\n"
                    code_context += model_info['model_code'][:3000] + "\n\n"
                    file_path = model_info.get('model_file', '')

                if model_info.get('form_code'):
                    code_context += f"=== FORMULAIRE {model_name}Form ===\n"
                    code_context += f"Fichier: {model_info.get('form_file', 'inconnu')}\n"
                    code_context += model_info['form_code'][:2000] + "\n\n"

            if page_url:
                # Chercher la vue correspondant à l'URL
                view_info = self.gitlab_service.find_view_for_url(page_url)
                if view_info and view_info.get('code'):
                    code_context += f"=== VUE {view_info.get('view_name', 'inconnue')} ===\n"
                    code_context += f"Fichier: {view_info.get('file_path', 'inconnu')}\n"
                    code_context += view_info['code'][:3000] + "\n"
                    if not file_path:
                        file_path = view_info.get('file_path', '')

            # Si pas de code trouvé via les méthodes précédentes, chercher par mots-clés
            if not code_context and error_message:
                # Extraire des mots-clés de l'erreur pour rechercher dans le code
                search_results = self.gitlab_service.search_code(error_message[:100])
                if search_results:
                    for result in search_results[:2]:
                        file_content = self.gitlab_service.get_file_content(result.get('filename', ''))
                        if file_content:
                            code_context += f"=== {result.get('filename', 'fichier')} ===\n"
                            code_context += file_content[:2000] + "\n\n"
                            if not file_path:
                                file_path = result.get('filename', '')

        except Exception as e:
            LogUtils.error(f"Erreur lors de la récupération du code GitLab: {e}")
            code_context = f"Impossible de récupérer le code source: {str(e)}"

        # Analyser le bug avec Claude
        try:
            claude_service = ClaudeService()
            bug_analysis = claude_service.analyze_code_for_bug(
                error_message=error_message,
                code_context=code_context,
                user_description=user_description
            )
        except Exception as e:
            LogUtils.error(f"Erreur lors de l'analyse Claude: {e}")
            bug_analysis = {
                'is_bug': False,
                'analysis': f'Impossible d\'analyser: {str(e)}',
                'recommendation': 'Veuillez contacter le support technique.'
            }

        # Si c'est un bug, envoyer la notification automatiquement
        notification_result = {'notified': False}
        if bug_analysis.get('is_bug', False):
            notification_result = self.bug_notification_service.notify_bug_detected(
                bug_analysis=bug_analysis,
                user_description=user_description,
                error_message=error_message,
                code_context=code_context,
                file_path=file_path,
                page_url=page_url
            )

        return {
            'success': True,
            'is_bug': bug_analysis.get('is_bug', False),
            'analysis': bug_analysis.get('analysis', ''),
            'recommendation': bug_analysis.get('recommendation', ''),
            'severity': bug_analysis.get('severity', 'medium') if bug_analysis.get('is_bug') else None,
            'file_path': file_path,
            'revolucy_notified': notification_result.get('notified', False),
            'notification_message': notification_result.get('message', '')
        }


def create_tool_executor(user):
    """
    Factory function pour créer un callable d'exécution de tools.

    Usage:
        executor = create_tool_executor(request.user)
        result = executor('create_object', {...}, user)
    """
    service = ToolExecutorService(user)
    return service.execute
