"""
Tenant Middleware
Handles tenant identification and module access enforcement
Supports database-per-tenant routing
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.db import connections
from .tenant_models import Tenant, TenantModule
from .tenant_db_router import set_current_tenant, clear_current_tenant
import logging
import os

logger = logging.getLogger(__name__)


def setup_tenant_database(tenant):
    """
    Dynamically add tenant database to Django settings
    """
    db_alias = f"tenant_{tenant.subdomain}"
    
    # Check if already configured
    if db_alias in settings.DATABASES:
        return db_alias
    
    # Add database configuration with all required settings
    db_path = os.path.join(settings.BASE_DIR, f'tenant_{tenant.subdomain}.sqlite3')
    settings.DATABASES[db_alias] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': db_path,
        'ATOMIC_REQUESTS': False,
        'AUTOCOMMIT': True,
        'CONN_MAX_AGE': 0,
        'CONN_HEALTH_CHECKS': False,
        'OPTIONS': {},
        'TIME_ZONE': None,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'TEST': {
            'CHARSET': None,
            'COLLATION': None,
            'NAME': None,
            'MIRROR': None,
        },
    }
    
    logger.info(f"Configured database for tenant {tenant.subdomain}: {db_path}")
    
    # Close any existing connection to ensure fresh config
    if db_alias in connections:
        connections[db_alias].close()
    
    return db_alias


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to identify tenant from request and attach to request object
    """
    
    def process_request(self, request):
        """
        Identify tenant from subdomain or custom domain or X-Tenant-Subdomain header
        Attach tenant to request.tenant and set in thread-local storage for DB routing
        """
        tenant = None
        
        # First, check for X-Tenant-Subdomain header (for API requests)
        subdomain_header = request.headers.get('X-Tenant-Subdomain')
        if subdomain_header:
            tenant = Tenant.objects.using('default').filter(
                subdomain=subdomain_header,
                is_active=True
            ).first()
            if tenant:
                logger.info(f"Tenant identified from header: {tenant.name}")
                request.tenant = tenant
                
                # Setup tenant database dynamically
                setup_tenant_database(tenant)
                
                set_current_tenant(tenant)  # Set for DB router
                return None
        
        # Otherwise, try to identify from host
        host = request.get_host().split(':')[0]  # Remove port if present
        
        # Try to find tenant by custom domain
        tenant = Tenant.objects.using('default').filter(
            custom_domain=host,
            is_active=True
        ).first()
        
        # If not found, try to extract subdomain
        if not tenant:
            try:
                # Assuming format: subdomain.domain.com
                parts = host.split('.')
                if len(parts) >= 2:
                    subdomain = parts[0]
                    tenant = Tenant.objects.using('default').filter(
                        subdomain=subdomain,
                        is_active=True
                    ).first()
            except Exception as e:
                logger.warning(f"Error extracting subdomain: {e}")
        
        # Attach tenant to request (can be None for main domain)
        request.tenant = tenant
        if tenant:
            logger.info(f"Tenant identified from host: {tenant.name}")
            
            # Setup tenant database dynamically
            setup_tenant_database(tenant)
            
            set_current_tenant(tenant)  # Set for DB router
        else:
            clear_current_tenant()  # Clear for non-tenant requests
        
        return None
    
    def process_response(self, request, response):
        """Clear tenant from thread-local after request"""
        clear_current_tenant()
        return response


class TenantModuleAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce module access restrictions based on tenant configuration
    """
    
    # Map URL patterns to required modules
    MODULE_URL_PATTERNS = {
        '/hr/employees/': 'employees',
        '/hr/attendance/': 'attendance',
        '/hr/wallet/': 'wallet',
        '/hr/tasks/': 'tasks',
        '/hr/complaints/': 'complaints',
        '/hr/shifts/': 'shifts',
        '/hr/reports/': 'reports',
        # Also support /api/ prefix for compatibility
        '/api/employees/': 'employees',
        '/api/attendance/': 'attendance',
        '/api/wallet/': 'wallet',
        '/api/tasks/': 'tasks',
        '/api/complaints/': 'complaints',
        '/api/shifts/': 'shifts',
        '/api/reports/': 'reports',
    }
    
    # URLs that should bypass module checks
    EXEMPT_URLS = [
        '/api/auth/',
        '/api/tenants/',
        '/api/public/',
        '/admin/',
        '/media/',
        '/static/',
    ]
    
    def process_request(self, request):
        """
        Check if tenant has access to the requested module
        """
        # Skip check if no tenant (main domain)
        if not hasattr(request, 'tenant') or request.tenant is None:
            logger.debug(f"No tenant for request: {request.path}")
            return None
        
        # Check if URL should be exempt from module checks
        path = request.path
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                logger.debug(f"Exempt URL: {path}")
                return None
        
        # Check if the URL requires a specific module
        required_module = self._get_required_module(path)
        
        if required_module:
            logger.info(f"Tenant '{request.tenant.name}' accessing {path} - requires module: {required_module}")
            
            # Get tenant database alias
            db_alias = f"tenant_{request.tenant.subdomain}"
            
            # Check if tenant has access to this module
            try:
                tenant_module = TenantModule.objects.using(db_alias).get(
                    tenant=request.tenant,
                    module_key=required_module
                )
                
                if not tenant_module.is_enabled:
                    logger.warning(f"Access DENIED: Tenant '{request.tenant.name}' - module '{required_module}' is disabled")
                    return JsonResponse({
                        'error': 'Module not enabled',
                        'message': f'The {tenant_module.module_name} module is not enabled for your account.',
                        'module': required_module,
                        'tenant': request.tenant.name,
                        'upgrade_required': True
                    }, status=403)
                
                logger.info(f"Access GRANTED: Tenant '{request.tenant.name}' - module '{required_module}' is enabled")
            
            except TenantModule.DoesNotExist:
                logger.error(f"Module not found: {required_module} for tenant {request.tenant.name}")
                return JsonResponse({
                    'error': 'Module not found',
                    'message': 'This feature is not available.',
                    'module': required_module
                }, status=403)
        
        return None
    
    def _get_required_module(self, path):
        """
        Determine which module is required for the given path
        """
        for url_pattern, module_key in self.MODULE_URL_PATTERNS.items():
            if path.startswith(url_pattern):
                return module_key
        return None


class TenantConfigMiddleware(MiddlewareMixin):
    """
    Middleware to add tenant configuration to response headers (optional)
    Useful for frontend to know tenant settings
    """
    
    def process_response(self, request, response):
        """
        Add tenant information to response headers
        """
        if hasattr(request, 'tenant') and request.tenant:
            tenant = request.tenant
            response['X-Tenant-Name'] = tenant.name
            response['X-Tenant-Subdomain'] = tenant.subdomain
            # Note: Don't expose sensitive information in headers
        
        return response
