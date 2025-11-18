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
    # Employee Management
    '/s/hr/employees/': 'employees',
    '/s/hr/documents/': 'employees',
    '/s/hr/notes/': 'employees',
    '/s/hr/employee-dashboard-stats/': 'employees',
    '/s/hr/office-locations/': 'employees',
    '/s/hr/office-location/': 'employees',

    # Attendance
    '/s/hr/attendance/': 'attendance',

    # Shifts & Scheduling
    '/s/hr/shifts/': 'shifts',
    '/s/hr/shift-attendance/': 'shifts',
    '/s/hr/shift-schedules/': 'shifts',
    '/s/hr/shift-overrides/': 'shifts',

    # Leave Management
    '/s/hr/leave_requests/': 'leaves',

    # Wallet System (module_key is 'wallet' singular, not 'wallets')
    '/s/hr/wallet/': 'wallet',
    '/s/hr/wallet-system/': 'wallet',
    '/s/hr/multi-wallet/': 'wallet',
    '/s/hr/wallet-transfers/': 'wallet',
    '/s/hr/central-wallet/': 'wallet',
    '/s/hr/reimbursements/': 'wallet',

    # Tasks
    '/s/hr/tasks/': 'tasks',
    '/s/hr/subtasks/': 'tasks',
    '/s/hr/task-reports/': 'tasks',
    '/s/hr/task-comments/': 'tasks',
    '/s/hr/manager/dashboard/': 'tasks',

    # Teams
    '/s/hr/teams/': 'teams',
    '/s/hr/team-memberships/': 'teams',
    '/s/hr/team-tasks/': 'teams',

    # Internal Complaints (Employee)
    '/s/hr/complaints/': 'complaints',

    # Client Complaint System
    '/s/hr/complaint-categories/': 'complaints',
    '/s/hr/client-complaints/': 'complaints',
    '/s/hr/client-complaint-statuses/': 'complaints',
    '/s/hr/ticket-thresholds/': 'complaints',
    '/s/hr/ticket-automation/': 'complaints',
    '/s/hr/team-complaints/': 'complaints',
    '/s/hr/complaint-admin-permissions/': 'complaints',

    # Notifications
    '/s/hr/notifications/': 'notifications',
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
