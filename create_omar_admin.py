#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import connections
from hr_management.models import Tenant

User = get_user_model()

# Setup tenant database
tenant = Tenant.objects.get(subdomain='omar')
db_alias = f"tenant_{tenant.subdomain}"
db_path = os.path.join(settings.BASE_DIR, f'{db_alias}.sqlite3')

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
    'TEST': {'CHARSET': None, 'COLLATION': None, 'MIGRATE': True, 'MIRROR': None, 'NAME': None},
}

if db_alias in connections:
    connections[db_alias].close()

# Create admin user
admin_user = User(
    username='omaradmin',
    email='admin@omar.com',
    name='Omar Admin',
    is_staff=True,
    is_superuser=True,
    is_active=True,
    role='admin'
)
admin_user.set_password('omar123')
admin_user.save(using=db_alias)

print(f"✅ Created admin user 'omaradmin' for tenant 'omar'")
print(f"   Username: omaradmin")
print(f"   Password: omar123")
