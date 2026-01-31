"""
Service de notification automatique des bugs détectés.

Ce service est appelé quand Lucy détecte un bug lors de l'analyse du code
via GitLab. Il envoie automatiquement un email au gestionnaire de projet.
"""
import requests
from typing import Dict, Any, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from lucy_assist.utils.log_utils import LogUtils


class BugNotificationService:
    """Service pour notifier automatiquement quand un bug est détecté."""

    # Email par défaut si aucun collaborateur associé
    EMAIL_FALLBACK = 'maxence@revolucy.fr'

    def __init__(self, user=None):
        self.user = user

    def get_collaborateur_email(self) -> str:
        """
        Récupère l'email du collaborateur associé via l'API Lucy CRM.
        Utilise le SIREN du client configuré dans les settings.
        Retourne l'email par défaut si non trouvé.
        """
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

    def notify_bug_detected(
        self,
        bug_analysis: Dict[str, Any],
        user_description: str,
        error_message: str = "",
        code_context: str = "",
        file_path: str = "",
        page_url: str = ""
    ) -> Dict[str, Any]:
        """
        Envoie une notification email quand un bug est détecté.

        Args:
            bug_analysis: Résultat de l'analyse du bug (is_bug, analysis, recommendation, severity)
            user_description: Description du problème par l'utilisateur
            error_message: Message d'erreur signalé (optionnel)
            code_context: Code source analysé (optionnel)
            file_path: Chemin du fichier contenant le bug (optionnel)
            page_url: URL de la page où le bug a été signalé (optionnel)

        Returns:
            Dict avec 'success' et 'message'
        """
        # Vérifier si c'est bien un bug
        if not bug_analysis.get('is_bug', False):
            return {
                'success': False,
                'message': "Ce n'est pas un bug, notification non envoyée.",
                'notified': False
            }

        try:
            destinataire = self.get_collaborateur_email()

            # Informations utilisateur
            user_name = "Utilisateur"
            user_email = "Non disponible"
            if self.user:
                user_name = self.user.get_full_name() if hasattr(self.user, 'get_full_name') else str(self.user)
                user_email = self.user.email if hasattr(self.user, 'email') else 'Non disponible'

            # Déterminer la sévérité
            severity = bug_analysis.get('severity', 'medium')
            severity_label = {
                'low': '🟡 Faible',
                'medium': '🟠 Moyenne',
                'high': '🔴 Élevée'
            }.get(severity, '🟠 Moyenne')

            sujet = f"[Lucy Assist] Bug détecté - Sévérité {severity_label}"

            message_email = f"""
Lucy Assist a détecté un bug dans le code.

================================================================================
📊 ANALYSE DU BUG
================================================================================
Sévérité        : {severity_label}
Fichier         : {file_path or 'Non identifié'}
Page            : {page_url or 'Non spécifiée'}

📋 Analyse      :
{bug_analysis.get('analysis', 'Non disponible')}

💡 Recommandation :
{bug_analysis.get('recommendation', 'Non disponible')}

================================================================================
👤 INFORMATIONS UTILISATEUR
================================================================================
Utilisateur     : {user_name}
Email           : {user_email}
Date            : {timezone.now().strftime('%d/%m/%Y à %H:%M')}

📝 Description du problème par l'utilisateur :
{user_description or 'Non fournie'}

⚠️ Message d'erreur signalé :
{error_message or 'Aucun'}

================================================================================
💻 CODE SOURCE ANALYSÉ
================================================================================
{code_context[:2000] if code_context else 'Non disponible'}
{('...[tronqué]' if code_context and len(code_context) > 2000 else '')}

================================================================================
Cette notification a été envoyée automatiquement par Lucy Assist
suite à la détection d'un bug lors de l'analyse du code via GitLab.
================================================================================
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

            LogUtils.info(
                f"Notification bug envoyée à {destinataire} - "
                f"Sévérité: {severity}, Fichier: {file_path or 'inconnu'}"
            )

            return {
                'success': True,
                'message': f"Bug détecté et signalé à Revolucy ({destinataire})",
                'notified': True,
                'recipient': destinataire,
                'severity': severity
            }

        except Exception as e:
            LogUtils.error(f"Erreur envoi notification bug: {str(e)}")
            return {
                'success': False,
                'message': f"Erreur lors de l'envoi de la notification: {str(e)}",
                'notified': False
            }
