"""
Django management command to clean up old module definitions
"""
from django.core.management.base import BaseCommand
from hr_management.tenant_models import ModuleDefinition, TenantModule


class Command(BaseCommand):
    help = 'Clean up old module definitions and tenant modules'

    OLD_MODULE_KEYS = [
        'employees', 'attendance', 'shifts', 'leaves', 'tasks', 'teams',
        'complaints', 'wallet', 'wallets', 'reimbursements', 'notifications', 'reports'
    ]

    def handle(self, *args, **options):
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🧹 CLEANING UP OLD MODULE DEFINITIONS"))
        self.stdout.write("=" * 80)
        
        # Step 1: Delete old module definitions
        self.stdout.write("\n📦 Step 1: Deleting old module definitions...")
        deleted_defs = 0
        for old_key in self.OLD_MODULE_KEYS:
            try:
                module_def = ModuleDefinition.objects.get(module_key=old_key)
                self.stdout.write(f"  🗑️  Deleting ModuleDefinition: {old_key}")
                module_def.delete()
                deleted_defs += 1
            except ModuleDefinition.DoesNotExist:
                pass
        
        self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted_defs} old module definitions"))
        
        # Step 2: Delete old tenant modules
        self.stdout.write("\n📝 Step 2: Deleting old tenant modules...")
        deleted_tenant_modules = TenantModule.objects.filter(
            module_key__in=self.OLD_MODULE_KEYS
        ).delete()
        
        self.stdout.write(self.style.SUCCESS(
            f"✅ Deleted {deleted_tenant_modules[0]} old tenant module entries"
        ))
        
        # Step 3: Show remaining modules
        self.stdout.write("\n📊 Step 3: Remaining module definitions:")
        remaining_modules = ModuleDefinition.objects.all().order_by('sort_order')
        for module in remaining_modules:
            self.stdout.write(f"  ✓ {module.module_key} - {module.module_name}")
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("✨ CLEANUP COMPLETE!"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"\n📊 Summary:")
        self.stdout.write(f"  • Module definitions deleted: {deleted_defs}")
        self.stdout.write(f"  • Tenant modules deleted: {deleted_tenant_modules[0]}")
        self.stdout.write(f"  • Remaining module definitions: {remaining_modules.count()}")
        self.stdout.write(self.style.SUCCESS("\n🎉 Old modules have been cleaned up!"))

