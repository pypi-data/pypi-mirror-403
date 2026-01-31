from django.db import models

from lucy_assist.models.base import LucyAssistBaseModel
from lucy_assist.constantes import LucyAssistConstantes


class Message(LucyAssistBaseModel):
    """
    Modèle représentant un message dans une conversation Lucy Assist.
    """
    repondant = models.CharField(max_length=20, choices=LucyAssistConstantes.Repondant.tuples)
    contenu = models.TextField()
    tokens_utilises = models.IntegerField(default=0)
    type_action = models.CharField(
        max_length=50,
        choices=LucyAssistConstantes.TypeAction.tuples,
        blank=True,
        null=True
    )
    metadata = models.JSONField(default=dict, blank=True)  # Données supplémentaires (contexte, erreurs, etc.)

    # ForeignKey
    conversation = models.ForeignKey(
        'lucy_assist.Conversation',
        on_delete=models.CASCADE,
        related_name='messages'
    )

    class Meta:
        verbose_name = "Message Lucy Assist"
        verbose_name_plural = "Messages Lucy Assist"
        ordering = ['created_date']

    def __str__(self):
        return f"Message #{self.pk} - {self.get_repondant_display()}"

    @property
    def est_chatbot(self):
        """Retourne True si le message vient du chatbot."""
        return self.repondant == LucyAssistConstantes.Repondant.CHATBOT

    @property
    def est_utilisateur(self):
        """Retourne True si le message vient de l'utilisateur."""
        return self.repondant == LucyAssistConstantes.Repondant.UTILISATEUR
