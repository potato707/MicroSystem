#!/usr/bin/env python
"""
Quick script to create a superuser for a tenant database
Usage: python create_tenant_user.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connections
from django.conf import settings

User = get_user_model()

def create_tenant_superuser(tenant_subdomain, username, email, password):
    """Create superuser for a specific tenant"""
    
    db_alias = f'tenant_{tenant_subdomain}'
    
    # Setup database connection if not exists
    if db_alias not in settings.DATABASES:
        db_path = os.path.join(settings.BASE_DIR, f'tenant_{tenant_subdomain}.sqlite3')
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
                'NAME': None,
                'MIRROR': None,
            },
        }
        print(f"✅ Configured database: {db_path}")
    
    # Close any existing connection
    if db_alias in connections:
        connections[db_alias].close()
    
    try:
        # Check if user already exists
        if User.objects.using(db_alias).filter(username=username).exists():
            print(f'⚠️  User "{username}" already exists in tenant "{tenant_subdomain}"')
            
            # Update password
            user = User.objects.using(db_alias).get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.role = 'admin'  # Set role to admin
            user.save(using=db_alias)
            print(f'✅ Password updated for user "{username}"')
            print(f'✅ Role set to: admin')
            return user
        
        # Create new superuser manually
        user = User(
            username=username,
            email=email,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            role='admin'  # Set role to admin
        )
        user.set_password(password)
        user.save(using=db_alias)
        
        print(f'✅ Superuser "{username}" created successfully for tenant "{tenant_subdomain}"')
        print(f'   Email: {email}')
        print(f'   Role: admin')
        print(f'   Password: {password}')
        return user
        
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        raise

# Main execution
if __name__ == '__main__':
    print("=" * 60)
    print("CREATE TENANT SUPERUSER")
    print("=" * 60)
    
    # Configuration
    TENANT = 'khalid'
    USERNAME = 'khalid'
    EMAIL = 'khalid@khalid.com'
    PASSWORD = 'khalid123'
    
    print(f"\nTenant: {TENANT}")
    print(f"Username: {USERNAME}")
    print(f"Email: {EMAIL}")
    print(f"Password: {PASSWORD}")
    print()
    
    # Create user
    user = create_tenant_superuser(TENANT, USERNAME, EMAIL, PASSWORD)
    
    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print(f"\nYou can now login with:")
    print(f"  Username: {USERNAME}")
    print(f"  Password: {PASSWORD}")
    print()
