#!/usr/bin/env python
"""
Script to migrate existing tenant modules from old module keys to new module system.

This script will:
1. Create new module definitions if they don't exist
2. Migrate tenant modules from old keys to new keys
3. Preserve enabled/disabled status based on mapping

Old Module Keys -> New Module Keys Mapping:
- employees, attendance, shifts, leaves -> HR_SYSTEM
- tasks, teams -> TASK_SYSTEM
- complaints -> COMPLAINT_SYSTEM
- wallet, reimbursements -> FINANCIAL_SYSTEM
- notifications -> NOTIFICATION_SYSTEM
- reports -> ANALYTICS_SYSTEM
"""
import os
import sys

# Setup Django environment before importing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Disable celery for this script
os.environ['CELERY_TASK_ALWAYS_EAGER'] = 'True'

import django
django.setup()

from hr_management.tenant_models import Tenant, TenantModule, ModuleDefinition
from hr_management.tenant_service import TenantService

# Mapping from old module keys to new module keys
OLD_TO_NEW_MODULE_MAP = {
    'employees': 'HR_SYSTEM',
    'attendance': 'HR_SYSTEM',
    'shifts': 'HR_SYSTEM',
    'leaves': 'HR_SYSTEM',
    'tasks': 'TASK_SYSTEM',
    'teams': 'TASK_SYSTEM',
    'complaints': 'COMPLAINT_SYSTEM',
    'wallet': 'FINANCIAL_SYSTEM',
    'wallets': 'FINANCIAL_SYSTEM',
    'reimbursements': 'FINANCIAL_SYSTEM',
    'notifications': 'NOTIFICATION_SYSTEM',
    'reports': 'ANALYTICS_SYSTEM',
}

def migrate_modules():
    print("=" * 80)
    print("🔄 MIGRATING TENANT MODULES TO NEW SYSTEM")
    print("=" * 80)
    
    # Step 1: Initialize new module definitions
    print("\n📦 Step 1: Initializing new module definitions...")
    TenantService.initialize_module_definitions()
    print("✅ Module definitions initialized")
    
    # Step 2: Get all tenants
    tenants = Tenant.objects.all()
    print(f"\n👥 Step 2: Found {tenants.count()} tenants to migrate")
    
    for tenant in tenants:
        print(f"\n{'='*60}")
        print(f"🏢 Migrating tenant: {tenant.name} ({tenant.subdomain})")
        print(f"{'='*60}")
        
        # Get existing tenant modules
        old_modules = TenantModule.objects.filter(tenant=tenant)
        
        # Track which new modules should be enabled
        new_modules_status = {}
        
        # Process old modules
        for old_module in old_modules:
            old_key = old_module.module_key
            
            # Check if this is already a new module key
            if old_key in ['HR_SYSTEM', 'TASK_SYSTEM', 'COMPLAINT_SYSTEM', 'POS_SYSTEM', 
                          'BRANCH_SYSTEM', 'INVENTORY_SYSTEM', 'DOCUMENT_SYSTEM', 
                          'PRODUCT_SYSTEM', 'NOTIFICATION_SYSTEM', 'ANALYTICS_SYSTEM', 
                          'SETTINGS_SYSTEM', 'FINANCIAL_SYSTEM']:
                print(f"  ✓ {old_key} - Already using new system")
                new_modules_status[old_key] = old_module.is_enabled
                continue
            
            # Map old key to new key
            new_key = OLD_TO_NEW_MODULE_MAP.get(old_key)
            
            if new_key:
                print(f"  🔄 {old_key} -> {new_key} (enabled: {old_module.is_enabled})")
                
                # If new module is already tracked, enable it if ANY old module was enabled
                if new_key in new_modules_status:
                    new_modules_status[new_key] = new_modules_status[new_key] or old_module.is_enabled
                else:
                    new_modules_status[new_key] = old_module.is_enabled
            else:
                print(f"  ⚠️  {old_key} - No mapping found, skipping")
        
        # Create/update new module entries
        print(f"\n  📝 Creating/updating new module entries...")
        all_new_modules = ModuleDefinition.objects.all()
        
        for module_def in all_new_modules:
            # Determine if module should be enabled
            # Core modules are enabled by default, others use mapped status
            is_enabled = new_modules_status.get(module_def.module_key, module_def.is_core)
            
            tenant_module, created = TenantModule.objects.update_or_create(
                tenant=tenant,
                module_key=module_def.module_key,
                defaults={
                    'module_name': module_def.module_name,
                    'is_enabled': is_enabled
                }
            )
            
            status = "🆕" if created else "♻️ "
            enabled_icon = "✅" if is_enabled else "❌"
            print(f"    {status} {enabled_icon} {module_def.module_key}")
        
        # Delete old module entries
        print(f"\n  🗑️  Cleaning up old module entries...")
        deleted_count = 0
        for old_module in old_modules:
            if old_module.module_key not in ['HR_SYSTEM', 'TASK_SYSTEM', 'COMPLAINT_SYSTEM', 
                                              'POS_SYSTEM', 'BRANCH_SYSTEM', 'INVENTORY_SYSTEM', 
                                              'DOCUMENT_SYSTEM', 'PRODUCT_SYSTEM', 'NOTIFICATION_SYSTEM', 
                                              'ANALYTICS_SYSTEM', 'SETTINGS_SYSTEM', 'FINANCIAL_SYSTEM']:
                print(f"    🗑️  Deleting old module: {old_module.module_key}")
                old_module.delete()
                deleted_count += 1
        
        print(f"  ✅ Deleted {deleted_count} old module entries")
    
    print("\n" + "=" * 80)
    print("✨ MIGRATION COMPLETE!")
    print("=" * 80)
    print("\n📊 Summary:")
    print(f"  • Tenants migrated: {tenants.count()}")
    print(f"  • New module system: 12 modules")
    print("\n🎉 All tenants have been migrated to the new module system!")

if __name__ == '__main__':
    migrate_modules()

