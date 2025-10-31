from django.core.management.base import BaseCommand
from django.db import connections
from hr_management.models import ComplaintCategory

class Command(BaseCommand):
    help = 'Create popular complaint categories for a specific tenant database file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--db',
            type=str,
            help='Path to tenant database file (e.g. tenant_adam.sqlite3)',
            required=True
        )

    def handle(self, *args, **options):
        db_path = options['db']
        db_alias = 'custom_tenant_db'

        # إعداد الاتصال الديناميكي
        connections.databases[db_alias] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_path,
            'TIME_ZONE': 'Asia/Riyadh',
            'CONN_HEALTH_CHECKS': False,
            'CONN_MAX_AGE': 0,
            'OPTIONS': {},
            'AUTOCOMMIT': True,
        }

        categories = [
            {
                'name': 'Technical Issues',
                'description': 'Software bugs, system errors, performance problems, and technical malfunctions',
                'color': '#dc2626'
            },
            {
                'name': 'Billing & Payment',
                'description': 'Incorrect charges, payment failures, billing disputes, and invoice issues',
                'color': '#ea580c'
            },
            {
                'name': 'Service Quality',
                'description': 'Poor service delivery, unmet expectations, and quality concerns',
                'color': '#ca8a04'
            },
            {
                'name': 'Delivery Problems',
                'description': 'Late delivery, damaged goods, missing items, and shipping issues',
                'color': '#16a34a'
            },
            {
                'name': 'Product Defects',
                'description': 'Manufacturing defects, broken items, and product quality issues',
                'color': '#2563eb'
            },
            {
                'name': 'Customer Support',
                'description': 'Unresponsive support, poor communication, and service attitude issues',
                'color': '#7c3aed'
            },
            {
                'name': 'Account Issues',
                'description': 'Login problems, account access, password reset, and profile issues',
                'color': '#db2777'
            },
            {
                'name': 'Privacy & Security',
                'description': 'Data privacy concerns, security breaches, and unauthorized access',
                'color': '#059669'
            },
            {
                'name': 'Website/App Issues',
                'description': 'Navigation problems, broken links, mobile app crashes, and UI issues',
                'color': '#0891b2'
            },
            {
                'name': 'Refund Requests',
                'description': 'Product returns, refund processing, and cancellation requests',
                'color': '#65a30d'
            },
            {
                'name': 'Communication',
                'description': 'Missing notifications, spam messages, and communication preferences',
                'color': '#dc2626'
            },
            {
                'name': 'Policy Violations',
                'description': 'Terms of service violations, policy concerns, and compliance issues',
                'color': '#991b1b'
            }
        ]

        created_count = 0
        for category_data in categories:
            category, created = ComplaintCategory.objects.using(db_alias).get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'color': category_data['color']
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories in {db_path}')
        )
