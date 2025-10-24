"""
Tenant Database Router
Routes database queries to tenant-specific databases
"""
from threading import local
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Thread-local storage to track current tenant
_thread_locals = local()


def get_current_tenant():
    """Get the current tenant from thread-local storage"""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage"""
    _thread_locals.tenant = tenant
    if tenant:
        logger.debug(f"Set current tenant: {tenant.subdomain}")


def clear_current_tenant():
    """Clear the current tenant from thread-local storage"""
    if hasattr(_thread_locals, 'tenant'):
        delattr(_thread_locals, 'tenant')


class TenantDatabaseRouter:
    """
    Database router that routes queries to tenant-specific databases
    
    Database naming convention: tenant_{subdomain}
    Example: tenant_demo, tenant_company_a
    """
    
    # Models that should always use the default database
    DEFAULT_DB_MODELS = {
        'tenant',  # Tenant model itself (stores tenant metadata)
        'moduledefinition',  # Module definitions (shared)
    }
    
    def get_tenant_db_alias(self, tenant=None):
        """Get database alias for a tenant"""
        if tenant is None:
            tenant = get_current_tenant()
        
        if tenant is None:
            return 'default'
        
        return f"tenant_{tenant.subdomain}"
    
    def db_for_read(self, model, **hints):
        """
        Route read operations to the correct database
        """
        # Check if this model should always use default DB
        if model._meta.model_name.lower() in self.DEFAULT_DB_MODELS:
            return 'default'
        
        # Get tenant from hints or thread-local
        tenant = hints.get('tenant') or get_current_tenant()
        
        if tenant:
            db_alias = self.get_tenant_db_alias(tenant)
            logger.debug(f"Routing read for {model._meta.model_name} to {db_alias}")
            return db_alias
        
        # Fallback to default
        return 'default'
    
    def db_for_write(self, model, **hints):
        """
        Route write operations to the correct database
        """
        # Check if this model should always use default DB
        if model._meta.model_name.lower() in self.DEFAULT_DB_MODELS:
            return 'default'
        
        # Get tenant from hints or thread-local
        tenant = hints.get('tenant') or get_current_tenant()
        
        if tenant:
            db_alias = self.get_tenant_db_alias(tenant)
            logger.debug(f"Routing write for {model._meta.model_name} to {db_alias}")
            return db_alias
        
        # Fallback to default
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the same database
        """
        db1 = obj1._state.db
        db2 = obj2._state.db
        
        if db1 and db2:
            return db1 == db2
        
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Control which models should be migrated to which database
        """
        # Default DB: Only Tenant and ModuleDefinition models
        if db == 'default':
            if model_name and model_name.lower() in self.DEFAULT_DB_MODELS:
                return True
            # Also allow auth and admin models in default
            if app_label in ['auth', 'admin', 'contenttypes', 'sessions']:
                return False  # These will be in tenant DBs
            return model_name and model_name.lower() in self.DEFAULT_DB_MODELS
        
        # Tenant databases: All models except Tenant and ModuleDefinition
        if db.startswith('tenant_'):
            if model_name and model_name.lower() in self.DEFAULT_DB_MODELS:
                return False
            return True
        
        return None


def get_tenant_db_config(subdomain, base_config=None):
    """
    Generate database configuration for a tenant
    
    Args:
        subdomain: Tenant subdomain
        base_config: Base database config (uses default if not provided)
    
    Returns:
        Dict with database configuration
    """
    if base_config is None:
        base_config = settings.DATABASES['default'].copy()
    
    # Create config based on database engine
    engine = base_config.get('ENGINE', '')
    
    # Copy all settings from base config
    config = base_config.copy()
    
    # Override database name based on engine
    if 'postgresql' in engine:
        config['NAME'] = f'tenant_{subdomain}'
    elif 'mysql' in engine:
        config['NAME'] = f'tenant_{subdomain}'
    elif 'sqlite' in engine:
        config['NAME'] = f'tenant_{subdomain}.sqlite3'
    else:
        raise ValueError(f"Unsupported database engine: {engine}")
    
    return config
