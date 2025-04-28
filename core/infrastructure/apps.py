from django.apps import AppConfig


class InfrastructureConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.infrastructure"

    def ready(self):
        # Import your models here
        from core.infrastructure.models import sql_models
