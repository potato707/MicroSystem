# Complaint Admin Permission Access Fix

## Problem
Users with complaint admin permissions were getting a "permission denied" error when trying to access the client complaint statuses endpoint:

```bash
GET /hr/client-complaint-statuses/
Response: {"detail":"ليس لديك صلاحية للقيام بهذا الإجراء."}
# Translation: "You do not have permission to perform this action."
```

Even though the user had been granted complaint admin permissions through the admin panel, they couldn't access endpoints that complaint admins should be able to use.

## Root Cause
The `ClientComplaintStatusViewSet` had `permission_classes = [IsAuthenticated, IsAdminUser]`, which only allowed users with `role='admin'` to access the endpoint. This meant that regular employees with complaint admin permissions were blocked.

## Solution

### 1. Created New Permission Class (`custom_permissions.py`)

Added `IsAdminOrComplaintAdmin` permission class that:
- Allows full access for admin users
- Allows read access (GET, HEAD, OPTIONS) for any user with complaint admin permissions
- Requires `can_manage_categories` permission for write operations (POST, PUT, PATCH, DELETE)

```python
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
        
        from .models import has_complaint_admin_permission
        
        # For read operations, any complaint admin can access
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return has_complaint_admin_permission(request.user)
        
        # For write operations, check specific permissions
        if request.method == 'POST':
            return has_complaint_admin_permission(request.user, 'can_manage_categories')
        
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return has_complaint_admin_permission(request.user, 'can_manage_categories')
        
        return False
```

### 2. Updated ViewSet Permissions (`views.py`)

Changed `ClientComplaintStatusViewSet` to use the new permission class:

```python
# Before
class ClientComplaintStatusViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminUser]

# After
class ClientComplaintStatusViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAdminOrComplaintAdmin]
```

### 3. Updated Category ViewSet Query Logic (`views.py`)

Enhanced `ComplaintCategoryViewSet.get_queryset()` to allow complaint admins with `can_manage_categories` permission to see all categories (including inactive ones):

```python
# Before
def get_queryset(self):
    if self.request.user.role == 'admin':
        return ComplaintCategory.objects.all()
    return ComplaintCategory.objects.filter(is_active=True)

# After
def get_queryset(self):
    if self.request.user.role == 'admin' or has_complaint_admin_permission(self.request.user, 'can_manage_categories'):
        return ComplaintCategory.objects.all()
    return ComplaintCategory.objects.filter(is_active=True)
```

### 4. Updated Imports (`views.py`)

Added the new permission class to imports:

```python
from .custom_permissions import IsEmployer, IsAdminOrComplaintAdmin
```

## Files Changed

1. **`hr_management/custom_permissions.py`**
   - Added `IsAdminOrComplaintAdmin` permission class

2. **`hr_management/views.py`**
   - Imported `IsAdminOrComplaintAdmin`
   - Updated `ClientComplaintStatusViewSet.permission_classes`
   - Updated `ComplaintCategoryViewSet.get_queryset()`

## Permission Logic

The new permission class implements the following logic:

### Read Operations (GET, HEAD, OPTIONS)
- ✅ Admin users: Full access
- ✅ Users with ANY complaint admin permission: Can read statuses
- ❌ Regular users without permissions: No access

### Write Operations (POST, PUT, PATCH, DELETE)
- ✅ Admin users: Full access
- ✅ Users with `can_manage_categories` permission: Can create/update/delete statuses
- ❌ Users without `can_manage_categories`: Cannot modify statuses
- ❌ Regular users: No access

## Testing

### Test Script
Run: `python3 test_complaint_admin_access.py`

### Test Results
```
✓ PASS: User Permissions
✓ PASS: Complaint Statuses  ← Previously failing, now fixed
✓ PASS: Complaint Categories
✓ PASS: Client Complaints
✓ PASS: Active Statuses

✓ ALL TESTS PASSED (5/5)
```

### Manual Testing

Test with a user who has complaint admin permissions:

```bash
# Get statuses (should work now)
curl 'http://localhost:8000/hr/client-complaint-statuses/' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# Expected: 200 OK with list of statuses
```

## Benefits

1. **Proper Permission Segregation**: Complaint admins can now access the endpoints they need
2. **Granular Control**: Different permission levels for read vs write operations
3. **Maintainable**: Centralized permission logic in reusable permission class
4. **Consistent**: Uses the same `has_complaint_admin_permission()` function as other endpoints
5. **Secure**: Still requires authentication and checks specific permissions for write operations

## Related Endpoints

These endpoints now work correctly for complaint admins:

1. **GET `/hr/client-complaint-statuses/`** - List all statuses
2. **GET `/hr/client-complaint-statuses/active/`** - List active statuses
3. **GET `/hr/complaint-categories/`** - List categories
4. **POST `/hr/client-complaint-statuses/`** - Create status (requires `can_manage_categories`)
5. **PUT/PATCH `/hr/client-complaint-statuses/{id}/`** - Update status (requires `can_manage_categories`)
6. **DELETE `/hr/client-complaint-statuses/{id}/`** - Delete status (requires `can_manage_categories`)

## User Experience

Before this fix:
- User granted complaint admin permissions
- User logs in and tries to access complaint management features
- Gets "permission denied" error
- Cannot perform their assigned duties

After this fix:
- User granted complaint admin permissions
- User logs in and can access all necessary endpoints
- Can view and manage complaints according to their permission level
- System works as intended ✅
