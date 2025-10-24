from rest_framework.permissions import BasePermission

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
