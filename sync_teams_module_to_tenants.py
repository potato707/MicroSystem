#!/usr/bin/env python
"""
Script to sync Teams module to all existing tenants
Run this on the production server after adding Teams to ModuleDefinition
"""
import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, '/root/saas/MicroSystem')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import ModuleDefinition, Tenant, TenantModule
from django.utils import timezone

def sync_teams_module():
    """Sync Teams module to all existing tenants"""
    
    # Get Teams module from ModuleDefinition
    try:
        teams_module = ModuleDefinition.objects.get(module_key='teams')
    except ModuleDefinition.DoesNotExist:
        print("✗ Teams module not found in ModuleDefinition!")
        print("  Please run add_teams_module.py first")
        return
    
    print(f"✓ Found Teams module: {teams_module.module_name}")
    print("\nSyncing to all tenants...")
    print("-" * 60)
    
    # Get all tenants
    tenants = Tenant.objects.all()
    total_tenants = tenants.count()
    synced_count = 0
    already_exists = 0
    updated_count = 0
    
    for tenant in tenants:
        # Check if tenant already has Teams module
        tenant_module, created = TenantModule.objects.get_or_create(
            tenant=tenant,
            module_key=teams_module.module_key,
            defaults={
                'module_name': teams_module.module_name,
                'is_enabled': False  # Disabled by default
            }
        )
        
        if created:
            synced_count += 1
            print(f"✓ Added Teams to: {tenant.name} ({tenant.subdomain})")
            
            # Regenerate config.json for this tenant
            from hr_management.tenant_service import TenantService
            try:
                TenantService.update_tenant_config(tenant)
                print(f"  └─ Updated config.json")
            except Exception as e:
                print(f"  └─ Warning: Failed to update config.json: {e}")
        else:
            already_exists += 1
            status = "enabled" if tenant_module.is_enabled else "disabled"
            print(f"  Teams already exists for {tenant.name} ({status})")
            
            # Update module name if it's different
            if tenant_module.module_name != teams_module.module_name:
                tenant_module.module_name = teams_module.module_name
                tenant_module.save()
                updated_count += 1
                print(f"  └─ Updated module name")
    
    print("-" * 60)
    print(f"\nSync complete!")
    print(f"  Total tenants: {total_tenants}")
    print(f"  Teams added: {synced_count}")
    print(f"  Already existed: {already_exists}")
    if updated_count > 0:
        print(f"  Updated: {updated_count}")
    
    if synced_count > 0:
        print(f"\n⚠️  Note: Teams module is DISABLED by default")
        print(f"  Tenants can enable it from their admin panel")
        print(f"\n💡 To enable Teams for a specific tenant:")
        print(f"  1. Go to Admin Panel → Tenant Modules")
        print(f"  2. Find the tenant and the 'teams' module")
        print(f"  3. Check 'Enabled' and save")

if __name__ == '__main__':
    try:
        sync_teams_module()
        print("\n✓ Sync completed successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
