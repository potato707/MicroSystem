# Django Signals for Tenant Management
# Auto-creates TenantModule records and Complaint Categories when a Tenant is created

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connections
from .tenant_models import Tenant, TenantModule, ModuleDefinition
from .models import ComplaintCategory
import logging
import os

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
        
        # Create complaint categories for the new tenant
        try:
            populate_tenant_complaint_categories(instance)
        except Exception as e:
            logger.error(f"Error creating complaint categories for tenant {instance.name}: {e}")


def populate_tenant_complaint_categories(tenant):
    """
    Automatically populate complaint categories for a new tenant
    """
    from django.conf import settings
    
    logger.info(f"Creating complaint categories for tenant: {tenant.name}")
    
    # Build the tenant database path
    db_filename = f"tenant_{tenant.subdomain}.sqlite3"
    db_path = os.path.join(settings.BASE_DIR, db_filename)
    
    # Check if database exists
    if not os.path.exists(db_path):
        logger.warning(f"Tenant database not found: {db_path}")
        return
    
    # Create dynamic database alias
    db_alias = f'tenant_{tenant.subdomain}_signal'
    
    # Setup dynamic connection
    connections.databases[db_alias] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
        'TIME_ZONE': 'Asia/Riyadh',
        'CONN_HEALTH_CHECKS': False,
        'CONN_MAX_AGE': 0,
        'OPTIONS': {},
        'AUTOCOMMIT': True,
    }
    
    # Default complaint categories
    categories = [
        {
            'name': 'Technical Issues',
            'description': 'Software bugs, system errors, performance problems, and technical malfunctions',
            'color': '#dc2626'
        },
        {
            'name': 'Billing & Payment',
            'description': 'Incorrect charges, payment failures, billing disputes, and invoice issues',
            'color': '#ea580c'
        },
        {
            'name': 'Service Quality',
            'description': 'Poor service delivery, unmet expectations, and quality concerns',
            'color': '#ca8a04'
        },
        {
            'name': 'Delivery Problems',
            'description': 'Late delivery, damaged goods, missing items, and shipping issues',
            'color': '#16a34a'
        },
        {
            'name': 'Product Defects',
            'description': 'Manufacturing defects, broken items, and product quality issues',
            'color': '#2563eb'
        },
        {
            'name': 'Customer Support',
            'description': 'Unresponsive support, poor communication, and service attitude issues',
            'color': '#7c3aed'
        },
        {
            'name': 'Account Issues',
            'description': 'Login problems, account access, password reset, and profile issues',
            'color': '#db2777'
        },
        {
            'name': 'Privacy & Security',
            'description': 'Data privacy concerns, security breaches, and unauthorized access',
            'color': '#059669'
        },
        {
            'name': 'Website/App Issues',
            'description': 'Navigation problems, broken links, mobile app crashes, and UI issues',
            'color': '#0891b2'
        },
        {
            'name': 'Refund Requests',
            'description': 'Product returns, refund processing, and cancellation requests',
            'color': '#65a30d'
        },
        {
            'name': 'Communication',
            'description': 'Missing notifications, spam messages, and communication preferences',
            'color': '#dc2626'
        },
        {
            'name': 'Policy Violations',
            'description': 'Terms of service violations, policy concerns, and compliance issues',
            'color': '#991b1b'
        }
    ]
    
    created_count = 0
    try:
        for category_data in categories:
            category, created = ComplaintCategory.objects.using(db_alias).get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'color': category_data['color']
                }
            )
            if created:
                created_count += 1
                logger.info(f"  ✓ Created category: {category.name}")
        
        logger.info(f"✓ Successfully created {created_count} complaint categories for tenant: {tenant.name}")
    
    except Exception as e:
        logger.error(f"Error creating categories: {e}")
        raise
    finally:
        # Clean up the connection
        if db_alias in connections.databases:
            connections[db_alias].close()
            del connections.databases[db_alias]


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
