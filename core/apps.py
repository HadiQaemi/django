from django.apps import AppConfig
from django.conf import settings

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        if getattr(settings, 'USE_WEAVIATE', False):
            import core.infrastructure.signals.weaviate_signals