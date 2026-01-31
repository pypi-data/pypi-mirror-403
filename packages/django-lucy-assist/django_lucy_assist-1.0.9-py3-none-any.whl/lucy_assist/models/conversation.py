from django.conf import settings
from django.db import models

from lucy_assist.models.base import LucyAssistBaseModel


class Conversation(LucyAssistBaseModel):
    """
    Modèle représentant une conversation entre un utilisateur et Lucy Assist.
    """
    titre = models.CharField(max_length=255, blank=True, null=True)
    page_contexte = models.CharField(max_length=500, blank=True, null=True)

    # ForeignKey
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lucy_assist_conversations'
    )

    class Meta:
        verbose_name = "Conversation Lucy Assist"
        verbose_name_plural = "Conversations Lucy Assist"
        ordering = ['-created_date']

    def __str__(self):
        user_str = getattr(self.utilisateur, 'email', str(self.utilisateur))
        return f"Conversation #{self.pk} - {user_str}"

    @property
    def total_tokens(self):
        """Retourne le nombre total de tokens utilisés dans cette conversation."""
        return self.messages.aggregate(
            total=models.Sum('tokens_utilises')
        )['total'] or 0

    @property
    def dernier_message(self):
        """Retourne le dernier message de la conversation."""
        return self.messages.order_by('-created_date').first()

    def generer_titre(self):
        """Génère un titre automatique basé sur le premier message utilisateur."""
        premier_message = self.messages.filter(
            repondant='UTILISATEUR'
        ).order_by('created_date').first()

        if premier_message:
            # Tronquer le message pour créer un titre
            contenu = premier_message.contenu[:50]
            if len(premier_message.contenu) > 50:
                contenu += "..."
            self.titre = contenu
            self.save(update_fields=['titre'])
