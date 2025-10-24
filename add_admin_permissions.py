#!/usr/bin/env python
"""
Add admin permissions to a user in tenant database
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from hr_management.models import Tenant, TenantModule

User = get_user_model()

def setup_tenant_database(tenant_subdomain):
    """Setup tenant database connection dynamically"""
    try:
        # Get tenant from main database
        tenant = Tenant.objects.get(subdomain=tenant_subdomain)
        
        # Database configuration
        db_alias = f"tenant_{tenant.subdomain}"
        db_path = os.path.join(settings.BASE_DIR, f'{db_alias}.sqlite3')
        
        # Configure database if not exists
        if db_alias not in settings.DATABASES:
            settings.DATABASES[db_alias] = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': db_path,
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
        
        print(f"✅ Configured database: {db_path}")
        return db_alias, tenant
        
    except Tenant.DoesNotExist:
        print(f'❌ Tenant "{tenant_subdomain}" not found')
        sys.exit(1)
    except Exception as e:
        print(f'❌ Error setting up database: {str(e)}')
        raise

def add_user_to_admin_module(tenant_subdomain, username):
    """Add user to admin module"""
    db_alias, tenant = setup_tenant_database(tenant_subdomain)
    
    try:
        # Get user
        user = User.objects.using(db_alias).get(username=username)
        print(f"✅ Found user: {username}")
        print(f"   - is_superuser: {user.is_superuser}")
        print(f"   - is_staff: {user.is_staff}")
        
        # Get all modules
        modules = TenantModule.objects.using(db_alias).all()
        print(f"\n📋 Available modules:")
        for module in modules:
            print(f"   - {module.name} (slug: {module.slug})")
        
        # Find admin module
        admin_module = TenantModule.objects.using(db_alias).filter(
            slug__in=['admin', 'administration', 'admin_panel']
        ).first()
        
        if not admin_module:
            print(f"\n⚠️  No admin module found. Available modules:")
            for module in modules:
                print(f"   - {module.slug}")
            
            # Try to create admin module if it doesn't exist
            print(f"\n🔧 Creating admin module...")
            admin_module = TenantModule(
                tenant=tenant,
                name='Administration',
                slug='admin',
                description='Admin panel access',
                is_active=True
            )
            admin_module.save(using=db_alias)
            print(f"✅ Created admin module: {admin_module.name}")
        
        # Check if user already has access
        if user in admin_module.users.all():
            print(f"\n✅ User '{username}' already has admin access")
        else:
            # Add user to admin module
            admin_module.users.add(user)
            print(f"\n✅ Added user '{username}' to admin module: {admin_module.name}")
        
        # Show user's modules
        user_modules = TenantModule.objects.using(db_alias).filter(users=user)
        print(f"\n📌 User '{username}' has access to modules:")
        for module in user_modules:
            print(f"   - {module.name} ({module.slug})")
        
        return True
        
    except User.DoesNotExist:
        print(f'❌ User "{username}" not found in tenant database')
        return False
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

# Main execution
if __name__ == '__main__':
    print("=" * 60)
    print("ADD ADMIN PERMISSIONS")
    print("=" * 60)
    
    # Configuration
    TENANT = 'testc'
    USERNAME = 'ahmed'
    
    print(f"\nTenant: {TENANT}")
    print(f"Username: {USERNAME}")
    print()
    
    # Add permissions
    success = add_user_to_admin_module(TENANT, USERNAME)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ DONE!")
        print("=" * 60)
        print(f"\nUser '{USERNAME}' now has admin access.")
        print("Try logging in again at http://testc.localhost:3000/login")
    else:
        print("❌ FAILED!")
        print("=" * 60)
