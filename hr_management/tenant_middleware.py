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
from .tenant_db_router import set_current_tenant, clear_current_tenant, get_current_tenant as get_tenant_from_router
import logging
import os
import threading
from django.core.management import call_command

logger = logging.getLogger(__name__)

# Thread-local storage for current request
_thread_local = threading.local()


def get_current_tenant():
    """
    Get the current tenant from thread-local storage.
    This is set by TenantMiddleware during request processing.
    """
    # First try to get from thread-local
    tenant = getattr(_thread_local, 'tenant', None)
    if tenant:
        return tenant
    
    # Fallback to DB router's storage
    return get_tenant_from_router()


def set_thread_local_tenant(tenant):
    """
    Set the current tenant in thread-local storage
    """
    _thread_local.tenant = tenant


def clear_thread_local_tenant():
    """
    Clear the current tenant from thread-local storage
    """
    if hasattr(_thread_local, 'tenant'):
        del _thread_local.tenant


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
    try:
        call_command('migrate', database=db_alias, interactive=False, run_syncdb=True)
    except Exception as e:
        pass
    
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
        Identify tenant with priority order:
        1. X-Requested-From header (custom domains)
        2. X-Tenant-Subdomain header (subdomain-based access)
        3. Host extraction (fallback for direct access)
        """
        tenant = None
        
        # PRIORITY 1: Check for X-Requested-From header (custom domains)
        requested_from = request.headers.get('X-Requested-From')
        if requested_from:
            # Try to find tenant by custom domain
            tenant = Tenant.objects.using('default').filter(
                domain_type='custom',
                custom_domain=requested_from,
                is_active=True
            ).first()
            if tenant:
                logger.info(f"✅ [P1] Tenant from X-Requested-From: {tenant.name} (domain: {requested_from})")
                request.tenant = tenant
                setup_tenant_database(tenant)
                set_current_tenant(tenant)
                set_thread_local_tenant(tenant)
                return None
            else:
                logger.warning(f"⚠️ Custom domain '{requested_from}' not found in database")
        
        # PRIORITY 2: Check for X-Tenant-Subdomain header (subdomain-based access)
        subdomain_header = request.headers.get('X-Tenant-Subdomain')
        if subdomain_header:
            tenant = Tenant.objects.using('default').filter(
                subdomain=subdomain_header,
                is_active=True
            ).first()
            if tenant:
                logger.info(f"✅ [P2] Tenant from X-Tenant-Subdomain: {tenant.name} ({subdomain_header})")
                request.tenant = tenant
                setup_tenant_database(tenant)
                set_current_tenant(tenant)
                set_thread_local_tenant(tenant)
                return None
            else:
                logger.warning(f"⚠️ Subdomain '{subdomain_header}' not found in database")
        
        # PRIORITY 3: Try to identify from Host header (fallback for direct access)
        host = request.get_host().split(':')[0]  # Remove port if present
        logger.info(f"🌐 [P3] Fallback: Extracting tenant from host: {host}")
        
        # Try custom domain first
        tenant = Tenant.objects.using('default').filter(
            domain_type='custom',
            custom_domain=host,
            is_active=True
        ).first()
        
        if tenant:
            logger.info(f"✅ Tenant identified by custom domain from host: {tenant.name} ({host})")
        else:
            # Try subdomain extraction
            subdomain = self._extract_subdomain(host)
            if subdomain:
                logger.info(f"🔍 Extracted subdomain from host: {subdomain}")
                tenant = Tenant.objects.using('default').filter(
                    subdomain=subdomain,
                    is_active=True
                ).first()
                if tenant:
                    logger.info(f"✅ Tenant identified by subdomain from host: {tenant.name} ({subdomain})")
            else:
                logger.info(f"⚪ Main domain detected (no subdomain): {host}")
        
        # Attach tenant to request
        request.tenant = tenant
        if tenant:
            setup_tenant_database(tenant)
            set_current_tenant(tenant)
            set_thread_local_tenant(tenant)
        else:
            # Clear for non-tenant requests
            clear_current_tenant()
            clear_thread_local_tenant()
        
        return None
    
    def _extract_subdomain(self, host):
        """
        Extract subdomain from host
        
        Examples:
        - adam.client-radar.org → 'adam'
        - khalid.client-radar.org → 'khalid'
        - client-radar.org → None (main domain)
        - www.client-radar.org → None (www is reserved)
        - adam.localhost → 'adam' (for local dev)
        """
        parts = host.split('.')
        
        # localhost or single domain (no subdomain)
        if len(parts) < 2:
            return None
        
        # Get first part as potential subdomain
        subdomain = parts[0]
        
        # Skip reserved subdomains
        if subdomain in ['www', 'api', 'admin', 'mail', 'ftp', 'cpanel']:
            return None
        
        # client-radar.org (2 parts) → no subdomain
        # adam.client-radar.org (3 parts) → 'adam'
        # adam.localhost (2 parts, but localhost is special) → 'adam'
        
        if len(parts) == 2:
            # Check if it's localhost (special case for development)
            if parts[1] == 'localhost':
                return subdomain
            # Otherwise it's main domain (e.g., client-radar.org)
            return None
        
        # 3+ parts means subdomain.domain.tld
        return subdomain
    
    def process_response(self, request, response):
        """Clear tenant from thread-local after request"""
        clear_current_tenant()
        clear_thread_local_tenant()
        return response


class TenantModuleAccessMiddleware(MiddlewareMixin):
    """
    Middleware to enforce module access restrictions based on tenant configuration
    """
    
    # Map URL patterns to required modules
    MODULE_URL_PATTERNS = {
        # ========== HR_SYSTEM ==========
        '/s/hr/employees/': 'HR_SYSTEM',
        '/s/hr/employee-dashboard-stats/': 'HR_SYSTEM',
        '/s/hr/attendance/': 'HR_SYSTEM',
        '/s/hr/leave_requests/': 'HR_SYSTEM',
        '/s/hr/location-ping/': 'HR_SYSTEM',
        '/s/hr/location-tracking-report/': 'HR_SYSTEM',
        '/s/hr/location-tracking-events/': 'HR_SYSTEM',
        '/s/hr/employee-branches/': 'HR_SYSTEM',
        '/s/hr/daily-schedules/': 'HR_SYSTEM',
        '/s/hr/shifts/': 'HR_SYSTEM',
        '/s/hr/shift-attendance/': 'HR_SYSTEM',
        '/s/hr/shift-schedules/': 'HR_SYSTEM',
        '/s/hr/shift-overrides/': 'HR_SYSTEM',
        '/s/api/employees/': 'HR_SYSTEM',
        '/s/api/attendance/': 'HR_SYSTEM',
        '/s/api/shifts/': 'HR_SYSTEM',

        # ========== TASK_SYSTEM ==========
        '/s/hr/tasks/': 'TASK_SYSTEM',
        '/s/hr/subtasks/': 'TASK_SYSTEM',
        '/s/hr/task-reports/': 'TASK_SYSTEM',
        '/s/hr/task-comments/': 'TASK_SYSTEM',
        '/s/hr/manager/dashboard/': 'TASK_SYSTEM',
        '/s/hr/share-links/': 'TASK_SYSTEM',
        '/s/hr/teams/': 'TASK_SYSTEM',
        '/s/hr/team-memberships/': 'TASK_SYSTEM',
        '/s/hr/team-tasks/': 'TASK_SYSTEM',
        '/s/api/tasks/': 'TASK_SYSTEM',
        '/s/api/teams/': 'TASK_SYSTEM',

        # ========== COMPLAINT_SYSTEM ==========
        '/s/hr/complaints/': 'COMPLAINT_SYSTEM',
        '/s/hr/complaint-categories/': 'COMPLAINT_SYSTEM',
        '/s/hr/client-complaints/': 'COMPLAINT_SYSTEM',
        '/s/hr/client-complaint-statuses/': 'COMPLAINT_SYSTEM',
        '/s/hr/ticket-thresholds/': 'COMPLAINT_SYSTEM',
        '/s/hr/ticket-automation/': 'COMPLAINT_SYSTEM',
        '/s/hr/team-complaints/': 'COMPLAINT_SYSTEM',
        '/s/hr/complaint-admin-permissions/': 'COMPLAINT_SYSTEM',
        '/s/hr/client/complaints/': 'COMPLAINT_SYSTEM',
        '/s/hr/client/categories/': 'COMPLAINT_SYSTEM',
        '/s/api/complaints/': 'COMPLAINT_SYSTEM',

        # ========== POS_SYSTEM ==========
        '/s/pos/client-types/': 'POS_SYSTEM',
        '/s/pos/clients/': 'POS_SYSTEM',
        '/s/pos/products-old/': 'POS_SYSTEM',
        '/s/pos/distributions/': 'POS_SYSTEM',
        '/s/pos/dashboard/': 'POS_SYSTEM',

        # ========== BRANCH_SYSTEM ==========
        '/s/hr/branches/': 'BRANCH_SYSTEM',
        '/s/hr/office-locations/': 'BRANCH_SYSTEM',
        '/s/hr/office-location/': 'BRANCH_SYSTEM',

        # ========== INVENTORY_SYSTEM ==========
        '/s/pos/inventory/': 'INVENTORY_SYSTEM',
        '/s/pos/product-stocks/': 'INVENTORY_SYSTEM',

        # ========== DOCUMENT_SYSTEM ==========
        '/s/hr/documents/': 'DOCUMENT_SYSTEM',
        '/s/hr/notes/': 'DOCUMENT_SYSTEM',

        # ========== PRODUCT_SYSTEM ==========
        '/s/products/categories/': 'PRODUCT_SYSTEM',
        '/s/products/units/': 'PRODUCT_SYSTEM',
        '/s/products/products/': 'PRODUCT_SYSTEM',
        '/s/pos/product-categories/': 'PRODUCT_SYSTEM',
        '/s/pos/product-units/': 'PRODUCT_SYSTEM',
        '/s/pos/category-units/': 'PRODUCT_SYSTEM',
        '/s/pos/products/': 'PRODUCT_SYSTEM',

        # ========== NOTIFICATION_SYSTEM ==========
        '/s/hr/notifications/': 'NOTIFICATION_SYSTEM',

        # ========== ANALYTICS_SYSTEM ==========
        '/s/hr/employee-dashboard-stats/': 'ANALYTICS_SYSTEM',
        '/s/pos/dashboard/stats/': 'ANALYTICS_SYSTEM',
        '/s/api/reports/': 'ANALYTICS_SYSTEM',

        # ========== FINANCIAL_SYSTEM ==========
        '/s/hr/wallet/': 'FINANCIAL_SYSTEM',
        '/s/hr/wallet-system/': 'FINANCIAL_SYSTEM',
        '/s/hr/multi-wallet/': 'FINANCIAL_SYSTEM',
        '/s/hr/wallet-transfers/': 'FINANCIAL_SYSTEM',
        '/s/hr/central-wallet/': 'FINANCIAL_SYSTEM',
        '/s/hr/reimbursements/': 'FINANCIAL_SYSTEM',
        '/s/api/wallet/': 'FINANCIAL_SYSTEM',
    }

    # URLs that should bypass module checks
    EXEMPT_URLS = [
        '/s/api/auth/',
        '/s/api/token/',
        '/s/api/tenants/',
        '/s/api/public/',
        '/s/api/modules/',
        '/s/hr/api/token/',
        '/s/hr/current-user/',
        '/s/hr/create-tenant/',
        '/s/hr/public/',
        '/s/hr/client-portal/',
        '/s/hr/client/auth/',
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
