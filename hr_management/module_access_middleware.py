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
    '/hr/employees/': 'employees',
    '/hr/documents/': 'employees',
    '/hr/notes/': 'employees',
    '/hr/employee-dashboard-stats/': 'employees',
    '/hr/office-locations/': 'employees',
    '/hr/office-location/': 'employees',
    
    # Attendance
    '/hr/attendance/': 'attendance',
    
    # Shifts & Scheduling
    '/hr/shifts/': 'shifts',
    '/hr/shift-attendance/': 'shifts',
    '/hr/shift-schedules/': 'shifts',
    '/hr/shift-overrides/': 'shifts',
    
    # Leave Management
    '/hr/leave_requests/': 'leaves',
    
    # Wallet System (module_key is 'wallet' singular, not 'wallets')
    '/hr/wallet/': 'wallet',
    '/hr/wallet-system/': 'wallet',
    '/hr/multi-wallet/': 'wallet',
    '/hr/wallet-transfers/': 'wallet',
    '/hr/central-wallet/': 'wallet',
    '/hr/reimbursements/': 'wallet',
    
    # Tasks
    '/hr/tasks/': 'tasks',
    '/hr/subtasks/': 'tasks',
    '/hr/task-reports/': 'tasks',
    '/hr/task-comments/': 'tasks',
    '/hr/manager/dashboard/': 'tasks',
    
    # Teams
    '/hr/teams/': 'teams',
    '/hr/team-memberships/': 'teams',
    '/hr/team-tasks/': 'teams',
    
    # Internal Complaints (Employee)
    '/hr/complaints/': 'complaints',
    
    # Client Complaint System
    '/hr/complaint-categories/': 'complaints',
    '/hr/client-complaints/': 'complaints',
    '/hr/client-complaint-statuses/': 'complaints',
    '/hr/ticket-thresholds/': 'complaints',
    '/hr/ticket-automation/': 'complaints',
    '/hr/team-complaints/': 'complaints',
    '/hr/complaint-admin-permissions/': 'complaints',
    
    # Notifications
    '/hr/notifications/': 'notifications',
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
            path.startswith('/hr/api/token/') or
            path.startswith('/hr/current-user/') or  # Always allow current user endpoint
            path.startswith('/hr/create-tenant/') or
            path.startswith('/hr/public/') or
            path.startswith('/hr/client-portal/') or
            path.startswith('/hr/client/auth/') or
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
