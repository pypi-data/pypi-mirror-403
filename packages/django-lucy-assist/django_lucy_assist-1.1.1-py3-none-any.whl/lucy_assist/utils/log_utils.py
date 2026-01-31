"""
Utilitaire de logging pour Lucy Assist.
Version simplifiée et autonome.
"""
import inspect
import logging
import os

from django.conf import settings

logger = logging.getLogger("lucy_assist")


class LogUtils:
    """
    Classe générique de gestion des logs pour Lucy Assist.
    Format: lucy_assist [$className.$methodName] - $message
    """

    @staticmethod
    def _get_caller_info():
        """Récupère les informations sur l'appelant."""
        try:
            frame = inspect.stack()[2]
            class_name = frame[0].f_locals.get("self", None)
            if class_name:
                class_name = class_name.__class__.__name__
            else:
                # Méthode statique ou fonction
                class_name = frame[0].f_globals.get('__name__', 'unknown').split('.')[-1]

            method_name = frame[3]
            return f"{class_name}.{method_name}"
        except Exception:
            return "unknown"

    @staticmethod
    def info(msg=None):
        """Log un message de niveau INFO."""
        caller = LogUtils._get_caller_info()
        logger.info(f"lucy_assist [{caller}] - {msg}")

    @staticmethod
    def warning(msg=None):
        """Log un message de niveau WARNING."""
        caller = LogUtils._get_caller_info()
        logger.warning(f"lucy_assist [{caller}] - {msg}")

    @staticmethod
    def debug(msg=None):
        """Log un message de niveau DEBUG."""
        caller = LogUtils._get_caller_info()
        logger.debug(f"lucy_assist [{caller}] - {msg}")

    @staticmethod
    def error(msg=None):
        """Log un message de niveau ERROR."""
        caller = LogUtils._get_caller_info()
        logger.error(f"lucy_assist [{caller}] - {msg}")
