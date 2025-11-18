"""
Module Access Middleware

Automatically checks if the tenant has access to the module being requested
based on the URL path.
"""

from django.http import JsonResponse
from .tenant_models import TenantModule
from .tenant_db_router import get_current_tenant


# Map URL patterns to module keys
URL_MODULE_MAP = {
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

    # ========== FINANCIAL_SYSTEM ==========
    '/s/hr/wallet/': 'FINANCIAL_SYSTEM',
    '/s/hr/wallet-system/': 'FINANCIAL_SYSTEM',
    '/s/hr/multi-wallet/': 'FINANCIAL_SYSTEM',
    '/s/hr/wallet-transfers/': 'FINANCIAL_SYSTEM',
    '/s/hr/central-wallet/': 'FINANCIAL_SYSTEM',
    '/s/hr/reimbursements/': 'FINANCIAL_SYSTEM',
}


class ModuleAccessMiddleware:
    """
    Middleware to check if tenant has access to requested module.
    Should be placed after TenantMiddleware in MIDDLEWARE settings.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip middleware for:
        # - Admin panel
        # - Auth endpoints (including current-user for authentication)
        # - Static files
        # - Public endpoints
        
        path = request.path
        
        if (path.startswith('/admin/') or
            path.startswith('/s/api/token/') or
            path.startswith('/s/api/auth/') or
            path.startswith('/s/api/tenants/') or
            path.startswith('/s/api/modules/') or
            path.startswith('/s/api/public/') or
            path.startswith('/s/hr/api/token/') or
            path.startswith('/s/hr/current-user/') or  # Always allow current user endpoint
            path.startswith('/s/hr/create-tenant/') or
            path.startswith('/s/hr/public/') or
            path.startswith('/s/hr/client-portal/') or
            path.startswith('/s/hr/client/auth/') or
            path.startswith('/static/') or
            path.startswith('/media/')):
            return self.get_response(request)
        
        # Check if this path requires module access
        module_key = self._get_module_key_for_path(path)
        
        if not module_key:
            # No module restriction for this path
            return self.get_response(request)
        
        # Get current tenant
        tenant = get_current_tenant()
        
        print(f"\n🔍 MODULE ACCESS CHECK:")
        print(f"   Path: {path}")
        print(f"   Module Key: {module_key}")
        print(f"   Tenant: {tenant}")
        print(f"   Tenant ID: {tenant.id if tenant else 'None'}")
        print(f"   X-Tenant-Subdomain Header: {request.headers.get('X-Tenant-Subdomain', 'NOT SET')}")
        
        if not tenant:
            # No tenant context (might be in main database context)
            print(f"   ❌ No tenant context found!")
            return self.get_response(request)
        
        # Check if module is enabled for tenant
        # NOTE: TenantModule is in the main database, not tenant database
        # Must explicitly use .using('default') to query main database
        try:
            tenant_module = TenantModule.objects.using('default').get(
                tenant=tenant,
                module_key=module_key
            )
            
            print(f"   ✅ Found TenantModule: {tenant_module.module_name}")
            print(f"   Is Enabled: {tenant_module.is_enabled}")
            
            if not tenant_module.is_enabled:
                print(f"   ❌ Module is disabled!")
                return JsonResponse({
                    'error': 'module_not_enabled',
                    'message_ar': f'الوحدة "{tenant_module.module_name}" غير مفعلة لهذا العميل',
                    'message_en': f'Module "{tenant_module.module_name}" is not enabled for this tenant',
                    'module_key': module_key,
                    'module_name': tenant_module.module_name
                }, status=403)
            
        except TenantModule.DoesNotExist:
            print(f"   ❌ TenantModule.DoesNotExist exception!")
            return JsonResponse({
                'error': 'module_not_found',
                'message_ar': f'الوحدة "{module_key}" غير متاحة',
                'message_en': f'Module "{module_key}" is not available',
                'module_key': module_key
            }, status=403)
        
        # Module is enabled, continue with request
        print(f"   ✅ Module access granted!\n")
        return self.get_response(request)
    
    def _get_module_key_for_path(self, path):
        """
        Get module key for a given path.
        Returns None if path doesn't require module access.
        """
        for url_pattern, module_key in URL_MODULE_MAP.items():
            if path.startswith(url_pattern):
                return module_key
        
        return None
