"""
Configuration de Lucy Assist.
Permet de personnaliser le comportement via les settings Django.
"""
from django.conf import settings


class LucyAssistSettings:
    """
    Classe de configuration pour Lucy Assist.
    Lit les settings depuis LUCY_ASSIST dans settings.py.
    """

    # Valeurs par défaut
    DEFAULTS = {
        # Modèle de base pour les modèles Lucy Assist (None = utilise le modèle par défaut)
        # Peut être une string "mon_app.models.MonModele" ou une classe directement
        'BASE_MODEL': None,

        # Clé API Claude (peut aussi être définie via CLAUDE_LUCY_ASSIST_API_KEY)
        'CLAUDE_LUCY_ASSIST_API_KEY': None,

        # Modèle Claude à utiliser
        'CLAUDE_MODEL': 'claude-sonnet-4-20250514',

        # Configuration GitLab pour l'analyse de bugs
        'GITLAB_URL': None,
        'GITLAB_TOKEN': None,
        'GITLAB_PROJECT_ID': None,

        # SIREN du client pour l'API Lucy CRM
        'SIREN_CLIENT': None,

        # Email de fallback pour les feedbacks
        'FEEDBACK_EMAIL': 'support@revolucy.fr',

        # Préfixe des apps du projet pour le mapping modèle -> app
        # Ex: 'apps.' pour filtrer les apps commençant par 'apps.'
        'PROJECT_APPS_PREFIX': None,

        # URL de base de l'API Lucy CRM
        'LUCY_CRM_API_URL': 'https://app.lucy-crm.fr',

        # Prix par million de tokens (en euros)
        'PRIX_PAR_MILLION_TOKENS': 50.0,

        # Nombre moyen de tokens par conversation
        'TOKENS_MOYENS_PAR_CONVERSATION': 2000,

        # Questions fréquentes par défaut (génériques)
        'QUESTIONS_FREQUENTES_DEFAULT': [
            "Comment créer un nouveau client ?",
            "Comment effectuer une recherche ?",
            "Comment exporter des données ?",
            "Comment modifier mon profil ?",
            "Où trouver la liste des réservations ?",
        ],

        # Chemin vers le module contenant set_current_user pour le ThreadLocal
        # Ex: 'alyse.middleware.middleware' pour le projet Alyse
        'THREAD_LOCAL_MODULE': None,

        # Attributs de l'utilisateur à copier vers la requête
        # Ex: ['franchise', 'tenant', 'organization']
        'REQUEST_USER_ATTRS': [],
    }

    def __init__(self):
        self._settings = getattr(settings, 'LUCY_ASSIST', {})

    def __getattr__(self, name):
        if name in self.DEFAULTS:
            # Vérifier d'abord dans LUCY_ASSIST settings
            if name in self._settings:
                return self._settings[name]

            # Cas spéciaux pour les settings qui peuvent être définis au niveau global
            if name == 'CLAUDE_LUCY_ASSIST_API_KEY':
                # Chercher dans plusieurs variables possibles
                return (
                    getattr(settings, 'CLAUDE_LUCY_ASSIST_API_KEY', None) or
                    self.DEFAULTS[name]
                )

            if name == 'SIREN_CLIENT':
                return getattr(settings, 'SIREN_CLIENT', None) or self.DEFAULTS[name]

            if name == 'GITLAB_URL':
                return getattr(settings, 'GITLAB_URL', None) or self.DEFAULTS[name]

            if name == 'GITLAB_TOKEN':
                return getattr(settings, 'GITLAB_TOKEN', None) or self.DEFAULTS[name]

            if name == 'GITLAB_PROJECT_ID':
                return getattr(settings, 'GITLAB_PROJECT_ID', None) or self.DEFAULTS[name]

            return self.DEFAULTS[name]

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def get(self, name, default=None):
        """Récupère une valeur de configuration avec une valeur par défaut."""
        try:
            return getattr(self, name)
        except AttributeError:
            return default


# Instance singleton des settings
lucy_assist_settings = LucyAssistSettings()
