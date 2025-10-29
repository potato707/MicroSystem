from rest_framework.permissions import BasePermission
from django.http import JsonResponse


class HasModuleAccess(BasePermission):
    """
    Permission class to check if tenant has access to a specific module.
    Usage: Add 'module_name' attribute to the view class.
    
    Example:
        class EmployeeViewSet(viewsets.ModelViewSet):
            module_name = 'employees'
            permission_classes = [IsAuthenticated, HasModuleAccess]
    """
    
    def has_permission(self, request, view):
        # Get module name from view
        module_key = getattr(view, 'module_key', None)
        
        if not module_key:
            # If no module specified, allow access (backward compatibility)
            return True
        
        # Check if tenant has this module enabled
        from .tenant_models import TenantModule
        from .tenant_middleware import get_current_tenant
        
        try:
            tenant = get_current_tenant()
            
            if not tenant:
                # No tenant context, deny access
                return False
            
            # Check if module is enabled for this tenant
            # NOTE: TenantModule is in the main database, must use .using('default')
            try:
                tenant_module = TenantModule.objects.using('default').get(
                    tenant=tenant,
                    module_key=module_key
                )
                
                if not tenant_module.is_enabled:
                    # Store error message for custom response
                    self.message = f'الوحدة "{tenant_module.module_name}" غير مفعلة لهذا العميل'
                    return False
                
                return True
                
            except TenantModule.DoesNotExist:
                # Module not found for tenant
                self.message = f'الوحدة "{module_key}" غير متاحة'
                return False
                
        except Exception as e:
            # Error checking module access
            self.message = f'خطأ في التحقق من صلاحيات الوحدة: {str(e)}'
            return False


class IsEmployer(BasePermission):
    """
    Allows access only to users with role='admin'
    """
    def has_permission(self, request, view):
        return bool(
            request.user 
            and request.user.is_authenticated 
            and getattr(request.user, "role", None) in ["admin", "manager"]
        )


class IsAdminOrComplaintAdmin(BasePermission):
    """
    Allows access to admin users or users with complaint admin permissions.
    For read operations, any complaint admin can access.
    For write operations (POST, PUT, PATCH, DELETE), checks specific permissions.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Admins have full access
        if getattr(request.user, "role", None) == "admin":
            return True
        
        # Import here to avoid circular import
        from .models import has_complaint_admin_permission
        
        # For read operations, any complaint admin can access
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return has_complaint_admin_permission(request.user)
        
        # For write operations, check specific permissions
        if request.method == 'POST':
            # Creating statuses requires manage_categories permission
            return has_complaint_admin_permission(request.user, 'can_manage_categories')
        
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            # Updating/deleting statuses requires manage_categories permission
            return has_complaint_admin_permission(request.user, 'can_manage_categories')
        
        return False
