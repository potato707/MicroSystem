#!/usr/bin/env python
"""
Script to ENABLE Teams module for all existing tenants
⚠️ WARNING: This will enable Teams for ALL tenants!
Run this only if you want to enable Teams module for everyone.
"""
import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, '/root/saas/MicroSystem')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant, TenantModule
from django.utils import timezone

def enable_teams_for_all():
    """Enable Teams module for all tenants"""
    
    print("⚠️  WARNING: This will ENABLE Teams module for ALL tenants!")
    print("-" * 60)
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cancelled by user")
        return
    
    print("\nEnabling Teams module for all tenants...")
    print("-" * 60)
    
    # Get all tenants
    tenants = Tenant.objects.all()
    total_tenants = tenants.count()
    enabled_count = 0
    not_found = 0
    already_enabled = 0
    
    for tenant in tenants:
        try:
            # Get Teams module for this tenant
            tenant_module = TenantModule.objects.get(
                tenant=tenant,
                module_key='teams'
            )
            
            if tenant_module.is_enabled:
                already_enabled += 1
                print(f"  Teams already enabled for {tenant.name}")
            else:
                tenant_module.is_enabled = True
                tenant_module.enabled_at = timezone.now()
                tenant_module.save()
                enabled_count += 1
                print(f"✓ Enabled Teams for: {tenant.name} ({tenant.subdomain})")
                
        except TenantModule.DoesNotExist:
            not_found += 1
            print(f"✗ Teams module not found for {tenant.name}")
            print(f"  Run sync_teams_module_to_tenants.py first")
    
    print("-" * 60)
    print(f"\nOperation complete!")
    print(f"  Total tenants: {total_tenants}")
    print(f"  Newly enabled: {enabled_count}")
    print(f"  Already enabled: {already_enabled}")
    print(f"  Not found: {not_found}")
    
    if enabled_count > 0:
        print(f"\n✓ Teams module has been enabled for {enabled_count} tenant(s)")
        print(f"  Tenants can now access Teams management features")

if __name__ == '__main__':
    try:
        enable_teams_for_all()
        print("\n✓ Operation completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
