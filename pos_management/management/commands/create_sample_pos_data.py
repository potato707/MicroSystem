"""
POS Management Module - Sample Data Generator
Create sample data for testing the POS Management system
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pos_management.models import ClientType, Client, Product, Distribution
from datetime import datetime, timedelta
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample data for POS Management module'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data for POS Management...\n')

        # Get or create a user
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found. Please create a user first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting user: {e}'))
            return

        # 1. Create Client Types
        self.stdout.write('1️⃣  Creating Client Types...')
        
        branch_type = ClientType.objects.create(
            name='Branch',
            description='Physical branch locations',
            icon='store',
            color='#10B981',
            custom_fields=[
                {
                    'name': 'address',
                    'label': 'العنوان',
                    'type': 'text',
                    'required': True
                },
                {
                    'name': 'city',
                    'label': 'المدينة',
                    'type': 'select',
                    'options': ['القاهرة', 'الإسكندرية', 'الجيزة', 'الأقصر', 'أسوان'],
                    'required': True
                },
                {
                    'name': 'branch_size',
                    'label': 'مساحة الفرع (متر مربع)',
                    'type': 'number',
                    'required': False
                }
            ],
            created_by=user
        )

        restaurant_type = ClientType.objects.create(
            name='Restaurant',
            description='Restaurant and cafe clients',
            icon='restaurant',
            color='#F59E0B',
            custom_fields=[
                {
                    'name': 'cuisine_type',
                    'label': 'نوع المطبخ',
                    'type': 'select',
                    'options': ['إيطالي', 'صيني', 'عربي', 'هندي', 'أمريكي'],
                    'required': True
                },
                {
                    'name': 'seating_capacity',
                    'label': 'عدد المقاعد',
                    'type': 'number',
                    'required': True
                },
                {
                    'name': 'delivery_available',
                    'label': 'خدمة التوصيل',
                    'type': 'select',
                    'options': ['نعم', 'لا'],
                    'required': False
                }
            ],
            created_by=user
        )

        website_type = ClientType.objects.create(
            name='E-commerce Website',
            description='Online stores and e-commerce platforms',
            icon='shopping_cart',
            color='#3B82F6',
            custom_fields=[
                {
                    'name': 'website_url',
                    'label': 'رابط الموقع',
                    'type': 'url',
                    'required': True
                },
                {
                    'name': 'monthly_visitors',
                    'label': 'عدد الزوار شهرياً',
                    'type': 'number',
                    'required': False
                },
                {
                    'name': 'platform',
                    'label': 'المنصة',
                    'type': 'select',
                    'options': ['WooCommerce', 'Shopify', 'Custom', 'Magento'],
                    'required': False
                }
            ],
            created_by=user
        )

        self.stdout.write(self.style.SUCCESS(f'  ✅ Created 3 client types'))

        # 2. Create Clients
        self.stdout.write('\n2️⃣  Creating Clients...')
        
        clients_data = [
            {
                'name': 'Cairo Downtown Mall Branch',
                'type': branch_type,
                'contact': 'Ahmed Mohamed',
                'email': 'ahmed@cairomall.com',
                'phone': '+201234567890',
                'category': 'large',
                'status': 'active',
                'custom_data': {
                    'address': '123 Tahrir Square, Downtown',
                    'city': 'القاهرة',
                    'branch_size': 500
                }
            },
            {
                'name': 'Alexandria Corniche Branch',
                'type': branch_type,
                'contact': 'Sara Ali',
                'email': 'sara@alex.com',
                'phone': '+201098765432',
                'category': 'medium',
                'status': 'active',
                'custom_data': {
                    'address': '456 Corniche Road',
                    'city': 'الإسكندرية',
                    'branch_size': 300
                }
            },
            {
                'name': 'Pizza Palace Restaurant',
                'type': restaurant_type,
                'contact': 'Khaled Hassan',
                'email': 'khaled@pizzapalace.com',
                'phone': '+201111222333',
                'category': 'medium',
                'status': 'active',
                'custom_data': {
                    'cuisine_type': 'إيطالي',
                    'seating_capacity': 80,
                    'delivery_available': 'نعم'
                }
            },
            {
                'name': 'Golden Spice Restaurant',
                'type': restaurant_type,
                'contact': 'Fatma Ibrahim',
                'email': 'fatma@goldenspice.com',
                'phone': '+201222333444',
                'category': 'small',
                'status': 'potential',
                'custom_data': {
                    'cuisine_type': 'هندي',
                    'seating_capacity': 40,
                    'delivery_available': 'لا'
                }
            },
            {
                'name': 'TechShop Online',
                'type': website_type,
                'contact': 'Omar Youssef',
                'email': 'omar@techshop.com',
                'phone': '+201333444555',
                'category': 'large',
                'status': 'active',
                'custom_data': {
                    'website_url': 'https://techshop.com',
                    'monthly_visitors': 50000,
                    'platform': 'Shopify'
                }
            }
        ]

        clients = []
        for data in clients_data:
            client = Client.objects.create(
                name=data['name'],
                client_type=data['type'],
                contact_person=data['contact'],
                email=data['email'],
                phone=data['phone'],
                category=data['category'],
                status=data['status'],
                custom_data=data['custom_data'],
                created_by=user,
                assigned_to=user
            )
            clients.append(client)

        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {len(clients)} clients'))

        # 3. Create Products
        self.stdout.write('\n3️⃣  Creating Products...')
        
        products_data = [
            {
                'name': 'Premium Coffee Beans',
                'sku': 'COFFEE-001',
                'description': 'High quality arabica coffee beans from Ethiopia',
                'type': 'product',
                'price': 150.00,
                'unit': 'kg',
                'stock': 200
            },
            {
                'name': 'Organic Green Tea',
                'sku': 'TEA-001',
                'description': 'Premium organic green tea leaves',
                'type': 'product',
                'price': 80.00,
                'unit': 'kg',
                'stock': 150
            },
            {
                'name': 'Fresh Croissants',
                'sku': 'BAKERY-001',
                'description': 'Freshly baked croissants',
                'type': 'product',
                'price': 5.00,
                'unit': 'piece',
                'stock': 500
            },
            {
                'name': 'Consultation Service',
                'sku': 'SERVICE-001',
                'description': 'Business consultation service',
                'type': 'service',
                'price': 500.00,
                'unit': 'hour',
                'stock': None
            },
            {
                'name': 'Installation Service',
                'sku': 'SERVICE-002',
                'description': 'Professional installation service',
                'type': 'service',
                'price': 300.00,
                'unit': 'visit',
                'stock': None
            }
        ]

        products = []
        for data in products_data:
            track_inventory = data['stock'] is not None
            product = Product.objects.create(
                name=data['name'],
                sku=data['sku'],
                description=data['description'],
                product_type=data['type'],
                base_price=data['price'],
                unit=data['unit'],
                track_inventory=track_inventory,
                current_stock=data['stock'] if track_inventory else 0,
                created_by=user
            )
            products.append(product)

        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {len(products)} products'))

        # 4. Create Distributions
        self.stdout.write('\n4️⃣  Creating Distributions...')
        
        today = datetime.now().date()
        distributions_count = 0

        # Past distributions
        for i in range(5):
            days_ago = random.randint(15, 60)
            last_visit = today - timedelta(days=days_ago)
            
            Distribution.objects.create(
                client=random.choice(clients[:3]),
                product=random.choice(products[:3]),
                quantity=random.randint(10, 50),
                price=random.choice(products[:3]).base_price,
                visit_interval_days=random.choice([7, 14, 30]),
                last_visit_date=last_visit,
                status='completed',
                created_by=user
            )
            distributions_count += 1

        # Upcoming distributions
        for i in range(3):
            days_ahead = random.randint(1, 10)
            next_visit = today + timedelta(days=days_ahead)
            last_visit = next_visit - timedelta(days=14)
            
            Distribution.objects.create(
                client=random.choice(clients[:3]),
                product=random.choice(products[:3]),
                quantity=random.randint(5, 30),
                price=random.choice(products[:3]).base_price,
                visit_interval_days=14,
                last_visit_date=last_visit,
                next_visit_date=next_visit,
                status='waiting_visit',
                created_by=user
            )
            distributions_count += 1

        # New distributions
        for i in range(2):
            Distribution.objects.create(
                client=random.choice(clients[3:]),
                product=random.choice(products),
                quantity=random.randint(10, 40),
                price=products[i].base_price,
                visit_interval_days=random.choice([7, 14]),
                status='new',
                created_by=user
            )
            distributions_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✅ Created {distributions_count} distributions'))

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('✅ Sample data created successfully!\n'))
        self.stdout.write('Summary:')
        self.stdout.write(f'  • Client Types: {ClientType.objects.count()}')
        self.stdout.write(f'  • Clients: {Client.objects.count()}')
        self.stdout.write(f'  • Products: {Product.objects.count()}')
        self.stdout.write(f'  • Distributions: {Distribution.objects.count()}')
        self.stdout.write('\n📊 Visit the dashboard at: /pos/dashboard/stats/')
        self.stdout.write('🔧 Manage data at: /admin/pos_management/')
        self.stdout.write('=' * 50)
