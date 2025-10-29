#!/usr/bin/env python
"""
Sync all tenant modules from config.json to database
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant, TenantModule

# Complete module definitions with proper names
MODULE_DEFINITIONS = {
    'employees': 'Employee Management',
    'attendance': 'Attendance Tracking',
    'shifts': 'Shift Management',
    'leaves': 'Leave Management',
    'wallet': 'Wallet & Salary',
    'tasks': 'Task Management',
    'teams': 'Team Management',
    'complaints': 'Complaint System',
    'reports': 'Reports & Analytics',
    'notifications': 'Notifications',
}

def sync_tenant_modules(tenant_subdomain):
    """Sync modules for a specific tenant"""
    try:
        # Get tenant
        tenant = Tenant.objects.using('default').get(subdomain=tenant_subdomain)
        print(f"✅ Found tenant: {tenant.name}")
        
        # Load config from file
        import json
        config_path = f'tenants/{tenant_subdomain}/config.json'
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            return
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        modules_config = config.get('modules', {})
        print(f"📦 Found {len(modules_config)} modules in config")
        
        # Sync each module
        synced_count = 0
        for module_key, is_enabled in modules_config.items():
            module_name = MODULE_DEFINITIONS.get(module_key, module_key.title())
            
            tenant_module, created = TenantModule.objects.using('default').update_or_create(
                tenant=tenant,
                module_key=module_key,
                defaults={
                    'module_name': module_name,
                    'is_enabled': is_enabled,
                }
            )
            
            action = "Created" if created else "Updated"
            status = "✅" if is_enabled else "❌"
            print(f"   {action} {status} {module_key} ({module_name})")
            synced_count += 1
        
        print(f"\n✅ Synced {synced_count} modules for tenant '{tenant.name}'")
        
        # Show current status
        print(f"\n📊 Current module status for '{tenant.name}':")
        all_modules = TenantModule.objects.using('default').filter(tenant=tenant)
        for tm in all_modules:
            status = "✅" if tm.is_enabled else "❌"
            print(f"  {status} {tm.module_key}: {tm.is_enabled}")
        
        return True
        
    except Tenant.DoesNotExist:
        print(f"❌ Tenant '{tenant_subdomain}' not found")
        return False
    except Exception as e:
        print(f"❌ Error syncing modules: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1:
        tenant_subdomain = sys.argv[1]
    else:
        tenant_subdomain = 'adam'  # Default
    
    print(f"🔄 Syncing modules for tenant: {tenant_subdomain}")
    print("=" * 60)
    success = sync_tenant_modules(tenant_subdomain)
    
    if success:
        print("\n✅ Sync completed successfully!")
    else:
        print("\n❌ Sync failed!")
        sys.exit(1)
