"""
Management command to initialize tenant module definitions
"""
from django.core.management.base import BaseCommand
from hr_management.tenant_service import TenantService


class Command(BaseCommand):
    help = 'Initialize default module definitions for the tenant system'
    
    def handle(self, *args, **options):
        self.stdout.write('Initializing module definitions...')
        
        count = TenantService.initialize_module_definitions()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully initialized {count} module definitions'
            )
        )
