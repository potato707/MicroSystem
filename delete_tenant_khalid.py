#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant

# Delete tenant
deleted = Tenant.objects.filter(subdomain='khalid').delete()
print(f"Deleted: {deleted}")

# Delete database file if exists
db_file = 'tenant_khalid.sqlite3'
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Deleted database file: {db_file}")
else:
    print(f"Database file {db_file} does not exist")
