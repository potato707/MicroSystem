from django.apps import AppConfig


class HrManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hr_management'

    def ready(self):
        import hr_management.signals
        import hr_management.tenant_signals  # Auto-create tenant modules

        # Auto-initialize module definitions when app starts
        # This ensures modules are available after fresh migrations
        self._initialize_modules()

    def _initialize_modules(self):
        """
        Initialize default module definitions automatically.
        This runs after migrations, ensuring modules are always available.
        Safe to call multiple times (uses get_or_create).
        """
        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError

        try:
            # Check if tables exist before trying to create modules
            # This prevents errors during initial migrations
            with connection.cursor() as cursor:
                # Check if ModuleDefinition table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='hr_management_moduledefinition';
                """)
                table_exists = cursor.fetchone()

                if not table_exists:
                    # Tables don't exist yet, skip initialization
                    return

            # Import here to avoid circular imports
            from .tenant_service import TenantService

            # Initialize module definitions
            created_count = TenantService.initialize_module_definitions()

            if created_count > 0:
                print(f"✅ Auto-initialized {created_count} module definitions")

        except (OperationalError, ProgrammingError) as e:
            # Database not ready yet (during migrations), skip silently
            pass
        except Exception as e:
            # Log other errors but don't crash the app
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not auto-initialize modules: {e}")
