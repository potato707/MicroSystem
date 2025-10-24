#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Tenant

# Delete tenant
deleted = Tenant.objects.filter(subdomain='ziad').delete()
print(f"Deleted: {deleted}")

# Delete database file if exists
db_file = 'tenant_ziad.sqlite3'
if os.path.exists(db_file):
    os.remove(db_file)
    print(f"Deleted database file: {db_file}")
else:
    print(f"Database file {db_file} does not exist")
