from django.core.management.base import BaseCommand
from hr_management.models import ComplaintCategory


class Command(BaseCommand):
    help = 'Create popular complaint categories'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Technical Issues',
                'description': 'Software bugs, system errors, performance problems, and technical malfunctions',
                'color': '#dc2626'  # Red
            },
            {
                'name': 'Billing & Payment',
                'description': 'Incorrect charges, payment failures, billing disputes, and invoice issues',
                'color': '#ea580c'  # Orange
            },
            {
                'name': 'Service Quality',
                'description': 'Poor service delivery, unmet expectations, and quality concerns',
                'color': '#ca8a04'  # Yellow
            },
            {
                'name': 'Delivery Problems',
                'description': 'Late delivery, damaged goods, missing items, and shipping issues',
                'color': '#16a34a'  # Green
            },
            {
                'name': 'Product Defects',
                'description': 'Manufacturing defects, broken items, and product quality issues',
                'color': '#2563eb'  # Blue
            },
            {
                'name': 'Customer Support',
                'description': 'Unresponsive support, poor communication, and service attitude issues',
                'color': '#7c3aed'  # Purple
            },
            {
                'name': 'Account Issues',
                'description': 'Login problems, account access, password reset, and profile issues',
                'color': '#db2777'  # Pink
            },
            {
                'name': 'Privacy & Security',
                'description': 'Data privacy concerns, security breaches, and unauthorized access',
                'color': '#059669'  # Emerald
            },
            {
                'name': 'Website/App Issues',
                'description': 'Navigation problems, broken links, mobile app crashes, and UI issues',
                'color': '#0891b2'  # Cyan
            },
            {
                'name': 'Refund Requests',
                'description': 'Product returns, refund processing, and cancellation requests',
                'color': '#65a30d'  # Lime
            },
            {
                'name': 'Communication',
                'description': 'Missing notifications, spam messages, and communication preferences',
                'color': '#dc2626'  # Red
            },
            {
                'name': 'Policy Violations',
                'description': 'Terms of service violations, policy concerns, and compliance issues',
                'color': '#991b1b'  # Dark Red
            }
        ]

        created_count = 0
        for category_data in categories:
            category, created = ComplaintCategory.objects.get_or_create(
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
            self.style.SUCCESS(f'Successfully created {created_count} new categories')
        )