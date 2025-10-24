#!/usr/bin/env python
"""
Test script to verify automatic tenant module creation
Run with: python test_tenant_creation.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant, TenantModule, ModuleDefinition


def test_tenant_creation():
    """Test creating a tenant and verify modules are auto-created"""
    
    print("=" * 60)
    print("TENANT MODULE AUTO-CREATION TEST")
    print("=" * 60)
    
    # Check module definitions first
    module_defs = ModuleDefinition.objects.all()
    print(f"\n✓ Module Definitions Found: {module_defs.count()}")
    for mod in module_defs:
        print(f"  - {mod.module_key}: {mod.module_name} (core: {mod.is_core})")
    
    if module_defs.count() == 0:
        print("\n❌ ERROR: No module definitions found!")
        print("Run: python manage.py init_modules")
        return
    
    # Create a test tenant
    print("\n" + "-" * 60)
    print("Creating test tenant...")
    
    # Delete any existing test tenant first
    Tenant.objects.filter(subdomain='testcompany').delete()
    
    tenant = Tenant.objects.create(
        name='Test Company',
        subdomain='testcompany',
        is_active=True
    )
    
    print(f"✓ Created tenant: {tenant.name} (ID: {tenant.id})")
    
    # Check if modules were auto-created
    print("\n" + "-" * 60)
    print("Checking auto-created modules...")
    
    tenant_modules = TenantModule.objects.filter(tenant=tenant)
    print(f"\n✓ Tenant Modules Created: {tenant_modules.count()}")
    
    if tenant_modules.count() == 0:
        print("\n❌ SIGNAL NOT WORKING - No modules were auto-created!")
        print("\nTroubleshooting:")
        print("1. Make sure Django server is restarted")
        print("2. Check apps.py has: import hr_management.tenant_signals")
        print("3. Check tenant_signals.py is in hr_management folder")
        return
    
    for tm in tenant_modules:
        status = "✓ ENABLED" if tm.is_enabled else "○ disabled"
        print(f"  {status} {tm.module_key}: {tm.module_name}")
    
    # Check config.json
    print("\n" + "-" * 60)
    print("Checking tenant configuration...")
    
    config_path = f"tenant_configs/{tenant.subdomain}/config.json"
    if os.path.exists(config_path):
        print(f"✓ Config file created: {config_path}")
        with open(config_path, 'r') as f:
            import json
            config = json.load(f)
            enabled = [m for m in config.get('modules', {}).values() if m.get('enabled')]
            print(f"  Enabled modules in config: {len(enabled)}")
    else:
        print(f"⚠ Config file not found: {config_path}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    # Summary
    core_count = sum(1 for m in tenant_modules if m.is_enabled)
    print(f"\n✓ Auto-created {tenant_modules.count()} modules")
    print(f"✓ {core_count} core modules enabled by default")
    print("\nYou can now create tenants via Django admin and modules")
    print("will be automatically created!")
    

if __name__ == '__main__':
    test_tenant_creation()
