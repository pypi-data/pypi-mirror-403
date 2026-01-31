"""
Signaux pour Lucy Assist
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from lucy_assist.models import Message, ConfigurationLucyAssist


@receiver(post_save, sender=Message)
def message_post_save(sender, instance, created, **kwargs):
    """
    Signal déclenché après sauvegarde d'un message.
    Décompte les tokens utilisés de la configuration.
    """
    if getattr(instance, '_skip_signals', False):
        return

    if created and instance.tokens_utilises > 0:
        # Déduire les tokens de la configuration
        config = ConfigurationLucyAssist.get_config()
        if config:
            config.tokens_disponibles = max(0, config.tokens_disponibles - instance.tokens_utilises)
            config._skip_signals = True
            config.save(update_fields=['tokens_disponibles'])
