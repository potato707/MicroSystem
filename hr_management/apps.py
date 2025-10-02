from django.apps import AppConfig


class HrManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hr_management'

    def ready(self):
        import hr_management.signals
