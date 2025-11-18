"""
Django management command to migrate tenant modules to new system
"""
from django.core.management.base import BaseCommand
from hr_management.tenant_models import Tenant, TenantModule, ModuleDefinition
from hr_management.tenant_service import TenantService


class Command(BaseCommand):
    help = 'Migrate tenant modules from old keys to new module system'

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

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔄 MIGRATING TENANT MODULES TO NEW SYSTEM"))
        self.stdout.write("=" * 80)
        
        # Step 1: Initialize new module definitions
        self.stdout.write("\n📦 Step 1: Initializing new module definitions...")
        TenantService.initialize_module_definitions()
        self.stdout.write(self.style.SUCCESS("✅ Module definitions initialized"))
        
        # Step 2: Get all tenants
        tenants = Tenant.objects.all()
        self.stdout.write(f"\n👥 Step 2: Found {tenants.count()} tenants to migrate")
        
        for tenant in tenants:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"🏢 Migrating tenant: {tenant.name} ({tenant.subdomain})")
            self.stdout.write(f"{'='*60}")
            
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
                    self.stdout.write(f"  ✓ {old_key} - Already using new system")
                    new_modules_status[old_key] = old_module.is_enabled
                    continue
                
                # Map old key to new key
                new_key = self.OLD_TO_NEW_MODULE_MAP.get(old_key)
                
                if new_key:
                    self.stdout.write(f"  🔄 {old_key} -> {new_key} (enabled: {old_module.is_enabled})")
                    
                    # If new module is already tracked, enable it if ANY old module was enabled
                    if new_key in new_modules_status:
                        new_modules_status[new_key] = new_modules_status[new_key] or old_module.is_enabled
                    else:
                        new_modules_status[new_key] = old_module.is_enabled
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  {old_key} - No mapping found, skipping"))
            
            # Create/update new module entries
            self.stdout.write(f"\n  📝 Creating/updating new module entries...")
            all_new_modules = ModuleDefinition.objects.all()
            
            for module_def in all_new_modules:
                # Determine if module should be enabled
                # Core modules are enabled by default, others use mapped status
                is_enabled = new_modules_status.get(module_def.module_key, module_def.is_core)
                
                _, created = TenantModule.objects.update_or_create(
                    tenant=tenant,
                    module_key=module_def.module_key,
                    defaults={
                        'module_name': module_def.module_name,
                        'is_enabled': is_enabled
                    }
                )
                
                status_icon = "🆕" if created else "♻️ "
                enabled_icon = "✅" if is_enabled else "❌"
                self.stdout.write(f"    {status_icon} {enabled_icon} {module_def.module_key}")
            
            # Delete old module entries
            self.stdout.write(f"\n  🗑️  Cleaning up old module entries...")
            deleted_count = 0
            for old_module in old_modules:
                if old_module.module_key not in ['HR_SYSTEM', 'TASK_SYSTEM', 'COMPLAINT_SYSTEM', 
                                                  'POS_SYSTEM', 'BRANCH_SYSTEM', 'INVENTORY_SYSTEM', 
                                                  'DOCUMENT_SYSTEM', 'PRODUCT_SYSTEM', 'NOTIFICATION_SYSTEM', 
                                                  'ANALYTICS_SYSTEM', 'SETTINGS_SYSTEM', 'FINANCIAL_SYSTEM']:
                    self.stdout.write(f"    🗑️  Deleting old module: {old_module.module_key}")
                    old_module.delete()
                    deleted_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"  ✅ Deleted {deleted_count} old module entries"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✨ MIGRATION COMPLETE!"))
        self.stdout.write("=" * 80)
        self.stdout.write("\n📊 Summary:")
        self.stdout.write(f"  • Tenants migrated: {tenants.count()}")
        self.stdout.write(f"  • New module system: 12 modules")
        self.stdout.write(self.style.SUCCESS("\n🎉 All tenants have been migrated to the new module system!"))

