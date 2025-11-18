#!/usr/bin/env python
"""
Script to sync adam tenant modules from config.json to database
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from hr_management.tenant_models import Tenant, TenantModule, ModuleDefinition

def sync_adam_modules():
    # Get adam tenant
    try:
        tenant = Tenant.objects.get(subdomain='adam')
        print(f"✅ Found tenant: {tenant.name}")
    except Tenant.DoesNotExist:
        print("❌ Adam tenant not found!")
        return
    
    # Modules from config.json (updated to new module system)
    enabled_modules = [
        'HR_SYSTEM',
        'TASK_SYSTEM',
        'COMPLAINT_SYSTEM',
        'NOTIFICATION_SYSTEM',
        'ANALYTICS_SYSTEM',
    ]

    disabled_modules = ['FINANCIAL_SYSTEM', 'POS_SYSTEM', 'INVENTORY_SYSTEM', 'PRODUCT_SYSTEM']
    
    # Get all module definitions
    all_modules = ModuleDefinition.objects.all()
    print(f"\n📦 Found {all_modules.count()} module definitions")
    
    # Update each module
    for module_def in all_modules:
        is_enabled = module_def.module_key in enabled_modules or module_def.is_core
        
        tenant_module, created = TenantModule.objects.update_or_create(
            tenant=tenant,
            module_key=module_def.module_key,
            defaults={
                'module_name': module_def.module_name,
                'is_enabled': is_enabled
            }
        )
        
        status = "🆕 Created" if created else "♻️  Updated"
        enabled_icon = "✅" if is_enabled else "❌"
        print(f"{status} {enabled_icon} {module_def.module_key} ({module_def.module_name})")
    
    print(f"\n✨ Done! Updated modules for {tenant.name}")
    
    # Show final status
    print("\n📊 Current module status:")
    modules = TenantModule.objects.filter(tenant=tenant).order_by('module_key')
    for m in modules:
        icon = "✅" if m.is_enabled else "❌"
        print(f"  {icon} {m.module_key}: {m.is_enabled}")

if __name__ == '__main__':
    sync_adam_modules()
