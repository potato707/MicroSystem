from django.apps import AppConfig


class PosManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pos_management'
    verbose_name = 'نقاط البيع'
    
    def ready(self):
        import pos_management.signals
