#!/usr/bin/env python
"""
Migrate a specific tenant database
Usage: python migrate_tenant.py <tenant_subdomain>
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
from hr_management.models import Tenant

def migrate_tenant(subdomain):
    """Migrate a specific tenant database"""
    
    # Get tenant
    try:
        tenant = Tenant.objects.using('default').get(subdomain=subdomain)
        print(f"Found tenant: {tenant.name} ({tenant.subdomain})")
    except Tenant.DoesNotExist:
        print(f"ERROR: Tenant '{subdomain}' not found!")
        return False
    
    # Database alias
    db_alias = f'tenant_{subdomain}'
    db_path = f'tenant_{subdomain}.sqlite3'
    
    print(f"Database: {db_path}")
    
    # Create database file if it doesn't exist
    if not os.path.exists(db_path):
        print(f"⚠️  Database file '{db_path}' does not exist. Creating...")
        # Touch the file to create it
        open(db_path, 'a').close()
        print(f"✅ Created database file: {db_path}")
    
    # Add database to settings dynamically
    from django.conf import settings
    if db_alias not in settings.DATABASES:
        settings.DATABASES[db_alias] = {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(settings.BASE_DIR, db_path),
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
            'CONN_HEALTH_CHECKS': False,
            'CONN_MAX_AGE': 0,
            'OPTIONS': {},
            'TIME_ZONE': None,
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
            'TEST': {
                'CHARSET': None,
                'COLLATION': None,
                'MIGRATE': True,
                'MIRROR': None,
                'NAME': None,
            },
        }
        print(f"Added database config for {db_alias}")
    
    # Ensure connection is closed before migrate
    if db_alias in connections:
        connections[db_alias].close()
    
    # Run migrations
    print(f"\nRunning migrations on {db_alias}...")
    try:
        call_command('migrate', '--database', db_alias, verbosity=2)
        print(f"\n✅ Successfully migrated {db_alias}!")
        return True
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python migrate_tenant.py <tenant_subdomain>")
        print("Example: python migrate_tenant.py testc")
        sys.exit(1)
    
    subdomain = sys.argv[1]
    success = migrate_tenant(subdomain)
    sys.exit(0 if success else 1)
