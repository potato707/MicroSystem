"""
Initialize default ticket delay thresholds
Run this once during setup
"""
from django.core.management.base import BaseCommand
from hr_management.models import TicketDelayThreshold


class Command(BaseCommand):
    help = 'Initialize default ticket delay thresholds for all priority levels'

    def handle(self, *args, **options):
        self.stdout.write('Initializing default ticket delay thresholds...')
        
        # Global default
        global_threshold, created = TicketDelayThreshold.objects.get_or_create(
            threshold_type='global',
            defaults={
                'system_response_hours': 24,
                'client_response_hours': 48,
                'auto_close_hours': 48,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Created global default thresholds'))
        else:
            self.stdout.write('  Global thresholds already exist')
        
        # Priority-specific thresholds
        priority_configs = {
            'urgent': {'system': 4, 'client': 8, 'auto_close': 12, 'label': 'Urgent'},
            'high': {'system': 12, 'client': 24, 'auto_close': 24, 'label': 'High'},
            'normal': {'system': 24, 'client': 48, 'auto_close': 48, 'label': 'Normal'},
            'low': {'system': 48, 'client': 72, 'auto_close': 72, 'label': 'Low'},
        }
        
        for priority, config in priority_configs.items():
            threshold, created = TicketDelayThreshold.objects.get_or_create(
                threshold_type='priority',
                priority=priority,
                defaults={
                    'system_response_hours': config['system'],
                    'client_response_hours': config['client'],
                    'auto_close_hours': config['auto_close'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created {config["label"]} priority thresholds'))
            else:
                self.stdout.write(f'  {config["label"]} priority thresholds already exist')
        
        self.stdout.write(self.style.SUCCESS('\n✓ All thresholds initialized!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('  1. View thresholds in Django admin')
        self.stdout.write('  2. Customize them via API or admin interface')
        self.stdout.write('  3. Run: python manage.py check_ticket_delays --dry-run')
