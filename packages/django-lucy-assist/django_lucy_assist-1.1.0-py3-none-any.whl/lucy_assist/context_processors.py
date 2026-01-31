"""
Context Processors pour Lucy Assist.

Ces fonctions injectent automatiquement les données Lucy Assist
dans le contexte de tous les templates Django.
"""
from django.conf import settings

from lucy_assist.models import ConfigurationLucyAssist


def lucy_assist_context(request):
    """
    Context processor pour injecter Lucy Assist dans toutes les pages.

    Ajoute au contexte:
    - lucy_assist_enabled: bool indiquant si Lucy Assist est activé
    - lucy_assist_config: configuration de Lucy Assist
    - lucy_assist_user_has_conversations: bool si l'utilisateur a des conversations

    Usage dans template:
        {% if lucy_assist_enabled %}
            {% include "chatbot_sidebar.html" %}
        {% endif %}
    """
    context = {
        'lucy_assist_enabled': False,
        'lucy_assist_config': None,
        'lucy_assist_user_has_conversations': False,
    }

    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        return context

    try:
        # Récupérer la configuration
        config = ConfigurationLucyAssist.get_config()

        # Vérifier si Lucy Assist est configuré (clé API présente)
        api_key_configured = bool(getattr(settings, 'CLAUDE_LUCY_ASSIST_API_KEY', ''))

        if config and config.actif:
            context['lucy_assist_enabled'] = True
            context['lucy_assist_config'] = {
                'tokens_disponibles': config.tokens_disponibles,
                'tokens_en_euros': round(config.tokens_restants_en_euros, 2),
                'conversations_estimees': config.conversations_estimees,
                'actif': config.actif,
                'api_configured': api_key_configured,
                'avatar_url': config.avatar.url if config.avatar else None,
            }

            # Vérifier si l'utilisateur a des conversations
            from lucy_assist.models import Conversation
            context['lucy_assist_user_has_conversations'] = Conversation.objects.filter(
                utilisateur=request.user,
                is_active=True
            ).exists()

    except Exception:
        # En cas d'erreur, Lucy Assist reste désactivé
        pass

    return context
