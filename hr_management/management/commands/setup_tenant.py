"""
Management command to setup a tenant with its own database
"""
from django.core.management.base import BaseCommand
from hr_management.tenant_models import Tenant
from hr_management.tenant_service import TenantService


class Command(BaseCommand):
    help = 'Setup complete tenant with dedicated database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'subdomain',
            type=str,
            help='Tenant subdomain'
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='admin123',
            help='Password for admin user (default: admin123)'
        )
    
    def handle(self, *args, **options):
        subdomain = options['subdomain']
        admin_password = options['admin_password']
        
        self.stdout.write(self.style.WARNING(f'\nSetting up tenant: {subdomain}'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        try:
            # Get tenant
            tenant = Tenant.objects.get(subdomain=subdomain)
            self.stdout.write(self.style.SUCCESS(f'✓ Found tenant: {tenant.name}'))
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ Tenant not found: {subdomain}'))
            self.stdout.write(self.style.WARNING('\nCreate tenant first using Django admin or:'))
            self.stdout.write(self.style.WARNING('  python manage.py shell'))
            self.stdout.write(self.style.WARNING('  >>> from hr_management.tenant_models import Tenant'))
            self.stdout.write(self.style.WARNING(f'  >>> Tenant.objects.create(name="Company", subdomain="{subdomain}")'))
            return
        
        # Setup tenant
        results = TenantService.setup_complete_tenant(tenant, admin_password)
        
        # Print results
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.WARNING('SETUP RESULTS:'))
        self.stdout.write('=' * 60)
        
        steps = [
            ('Database Created', results['database_created']),
            ('Migrations Run', results['migrations_run']),
            ('Superuser Created', results['superuser_created']),
            ('Modules Initialized', results['modules_initialized']),
            ('Folder Created', results['folder_created']),
            ('Config Generated', results['config_generated']),
        ]
        
        for step_name, success in steps:
            if success:
                self.stdout.write(self.style.SUCCESS(f'✓ {step_name}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ {step_name}'))
        
        if results['errors']:
            self.stdout.write('\n' + self.style.ERROR('ERRORS:'))
            for error in results['errors']:
                self.stdout.write(self.style.ERROR(f'  - {error}'))
        
        # Print access info
        if results['superuser_created']:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS('TENANT ACCESS INFORMATION:'))
            self.stdout.write('=' * 60)
            self.stdout.write(f'  Subdomain:  {subdomain}')
            self.stdout.write(f'  Database:   {results.get("db_alias", "N/A")}')
            self.stdout.write(f'  Admin User: admin')
            self.stdout.write(f'  Password:   {admin_password}')
            self.stdout.write(f'  Modules:    {results.get("modules_count", 0)}')
            self.stdout.write('=' * 60)
            self.stdout.write(self.style.SUCCESS('\n✓ Tenant setup complete!\n'))
        else:
            self.stdout.write('\n' + self.style.ERROR('✗ Tenant setup incomplete!'))
