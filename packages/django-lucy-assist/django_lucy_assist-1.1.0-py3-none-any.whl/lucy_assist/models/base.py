"""
Modèle de base pour Lucy Assist.
Utilise le modèle de base configuré dans les settings ou un modèle par défaut.
"""
from django.db import models

from lucy_assist.conf import lucy_assist_settings


def get_base_model():
    """
    Retourne le modèle de base à utiliser pour les modèles Lucy Assist.
    Permet de personnaliser le modèle de base via les settings Django.
    """
    base_model = lucy_assist_settings.BASE_MODEL

    if base_model is None:
        # Utiliser un modèle par défaut simple
        return LucyAssistBaseModel

    if isinstance(base_model, str):
        # Importer le modèle depuis le chemin string
        from django.utils.module_loading import import_string
        return import_string(base_model)

    return base_model


class LucyAssistBaseModel(models.Model):
    """
    Modèle de base par défaut pour Lucy Assist.
    Fournit les champs minimaux nécessaires pour le tracking.
    """
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ["-created_date"]


# Cache pour le modèle de base résolu
_resolved_base_model = None


def get_lucy_assist_model_base():
    """
    Retourne le modèle de base résolu (avec cache).
    """
    global _resolved_base_model
    if _resolved_base_model is None:
        _resolved_base_model = get_base_model()
    return _resolved_base_model
