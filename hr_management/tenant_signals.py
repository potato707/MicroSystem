# Django Signals for Tenant Management
# Auto-creates TenantModule records when a Tenant is created

from django.db.models.signals import post_save
from django.dispatch import receiver
from .tenant_models import Tenant, TenantModule, ModuleDefinition
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Tenant)
def create_tenant_modules(sender, instance, created, **kwargs):
    """
    Automatically create TenantModule records for all ModuleDefinitions
    when a new Tenant is created.
    """
    if created:  # Only run when tenant is first created
        logger.info(f"Creating modules for new tenant: {instance.name}")
        
        # Get all module definitions
        module_definitions = ModuleDefinition.objects.all()
        
        if not module_definitions.exists():
            logger.warning("No module definitions found. Run: python manage.py init_modules")
            return
        
        # Create TenantModule for each definition
        for module_def in module_definitions:
            # Core modules are enabled by default
            is_enabled = module_def.is_core
            
            TenantModule.objects.create(
                tenant=instance,
                module_key=module_def.module_key,
                module_name=module_def.module_name,
                is_enabled=is_enabled
            )
            
            logger.info(f"  ✓ Created module: {module_def.module_key} (enabled: {is_enabled})")
        
        # Generate config.json
        from .tenant_service import TenantService
        try:
            TenantService.create_tenant_folder_structure(instance)
            TenantService.generate_config_json(instance)
            logger.info(f"✓ Created folder structure and config for tenant: {instance.name}")
        except Exception as e:
            logger.error(f"Error creating tenant resources: {e}")


@receiver(post_save, sender=TenantModule)
def update_tenant_config_on_module_change(sender, instance, **kwargs):
    """
    Regenerate tenant's config.json whenever a module is enabled/disabled
    """
    from .tenant_service import TenantService
    
    try:
        TenantService.update_tenant_config(instance.tenant)
        logger.info(f"✓ Updated config for tenant: {instance.tenant.name}")
    except Exception as e:
        logger.error(f"Error updating tenant config: {e}")
