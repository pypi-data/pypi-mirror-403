from django.apps import AppConfig


class LucyAssistConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lucy_assist"
    verbose_name = "Lucy Assist - Chatbot IA"

    def ready(self):
        import lucy_assist.signals  # noqa
