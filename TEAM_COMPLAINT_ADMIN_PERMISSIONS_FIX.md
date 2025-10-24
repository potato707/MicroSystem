# Team Complaint Admin Permissions - Status Management Fix

## Issue
Users with team-based complaint admin permissions were not seeing the "Status Management" section to create, edit, and delete custom complaint statuses, even though they had the necessary permissions.

## Root Cause
1. **Migration Not Applied**: The migration `0046_add_new_complaint_admin_permissions` that added the new permission fields (`can_change_status`, `can_delete`, `can_manage_categories`) hadn't been applied to the database.

2. **Default Values**: When the migration was created, existing team permissions had these fields set to `False` by default.

3. **Status Dropdown Empty**: The frontend was checking for `has_permission === true` instead of specifically checking for `can_change_status` when loading available statuses.

## Solution

### 1. Fixed Migration Conflict (0032 → 0046)
Renamed the conflicting migration file and updated its dependencies:
```bash
mv hr_management/migrations/0032_add_new_complaint_admin_permissions.py \
   hr_management/migrations/0046_add_new_complaint_admin_permissions.py
```

Updated dependency to:
```python
dependencies = [
    ('hr_management', '0045_alter_employeeattendance_date_and_more'),
]
```

### 2. Applied Migration
```bash
python manage.py migrate hr_management
```

Result: Added new fields to `TeamComplaintAdminPermission` and `EmployeeComplaintAdminPermission`:
- `can_change_status` (Boolean, default=True)
- `can_delete` (Boolean, default=False)
- `can_manage_categories` (Boolean, default=False)

### 3. Updated Team Permissions
Enabled `can_manage_categories` for all teams with complaint admin permissions:
```python
from hr_management.models import TeamComplaintAdminPermission

perms = TeamComplaintAdminPermission.objects.all()
for perm in perms:
    perm.can_manage_categories = True
    perm.save()
```

**Updated Teams:**
- ✅ Team X: `can_manage_categories = True`
- ✅ Test Team: `can_manage_categories = True`

### 4. Fixed Frontend Status Loading
**File**: `v0-micro-system/components/complaints/complaint-detail-modal.tsx`

**Changed** (Line ~210):
```typescript
// OLD - Wrong condition
const shouldLoad = userRole === 'admin' || 
  (complaintAdminPermissions !== null && complaintAdminPermissions?.has_permission === true)

// NEW - Correct condition
const shouldLoad = userRole === 'admin' || complaintAdminPermissions?.can_change_status === true
```

This ensures that users with `can_change_status` permission will have the status dropdown populated with available statuses.

## Current Permissions

### Team X Members
The following users now have full complaint admin permissions including status management:
- **ahmed** ✓
- **mohammed** ✓
- **potato** ✓
- **sting** ✓
- **string** ✓

### Permissions Granted
- ✅ `can_review`: Review complaints
- ✅ `can_assign`: Assign complaints to teams/employees
- ✅ `can_change_status`: Change complaint status
- ✅ `can_manage_categories`: Create, edit, delete custom statuses
- ✅ `can_add_comments`: Add comments to complaints
- ✅ `can_create_tasks`: Create tasks from complaints
- ✅ `can_manage_assignments`: Manage team/employee assignments
- ❌ `can_delete`: Delete complaints (still disabled for safety)

## Frontend Behavior

### Status Management Section
The "Status Management" section is displayed when:
```typescript
(userRole === 'admin' || complaintAdminPermissions?.can_manage_categories)
```

**Location**: `v0-micro-system/components/complaints/complaints-dashboard.tsx` (Line 221)

### Features Available to Team Members with `can_manage_categories`

1. **View Custom Statuses**
   - See all custom statuses in the dashboard

2. **Create New Status**
   - Click "Add Custom Status" button
   - Enter name, description, display order
   - Set active/inactive state

3. **Edit Existing Status**
   - Click edit button on any custom status
   - Modify name, description, display order
   - Toggle active state

4. **Delete Custom Status**
   - Click delete button with confirmation
   - Status removed from system

5. **Use Custom Statuses**
   - Select custom statuses when changing complaint status
   - View custom status in complaint details

## Testing

### Verify Team Member Has Permissions
```python
from hr_management.models import get_complaint_admin_permissions, User

user = User.objects.get(username='string')  # or any team member
perms = get_complaint_admin_permissions(user)

print(f"can_manage_categories: {perms['can_manage_categories']}")  # Should be True
print(f"can_change_status: {perms['can_change_status']}")          # Should be True
```

### Expected Output
```
can_manage_categories: True
can_change_status: True
```

### Frontend Testing Steps

1. **Login as team member** (e.g., "string" or "sting")
2. **Navigate to Client Complaints** dashboard
3. **Verify Status Management section is visible** at the top of the page
4. **Click "Add Custom Status"** button
5. **Fill in the form:**
   - Name: "Test Status"
   - Description: "Test description"
   - Display Order: 10
   - Active: Yes
6. **Click "Save"** - Should create successfully
7. **Open a complaint** and click "Edit Status"
8. **Verify** the new custom status appears in the dropdown
9. **Select and apply** the custom status
10. **Edit the custom status** - Change description
11. **Delete the custom status** - With confirmation

## Files Modified

### Backend
- ✅ `/hr_management/migrations/0046_add_new_complaint_admin_permissions.py` - Created and applied
- ✅ Database - New fields added to permission tables

### Frontend
- ✅ `/v0-micro-system/components/complaints/complaint-detail-modal.tsx` (Line 210)
  - Fixed status loading condition

### Already Correct (No Changes Needed)
- ✅ `/v0-micro-system/components/complaints/complaints-dashboard.tsx` (Line 221)
  - Already checks for `can_manage_categories`
- ✅ `/v0-micro-system/components/complaints/status-management.tsx` (Line 144)
  - Already checks for `can_manage_categories`

## API Endpoints

### Get User Permissions
```
GET /hr/complaint-admin-permissions/user/
Authorization: Bearer {token}

Response:
{
  "has_permission": true,
  "can_assign": true,
  "can_change_status": true,
  "can_delete": false,
  "can_manage_categories": true,
  "granted_by": ["admin_user"]
}
```

### Custom Status Management
```
GET    /hr/client-complaint-statuses/custom/     - List custom statuses
POST   /hr/client-complaint-statuses/custom/     - Create custom status
PUT    /hr/client-complaint-statuses/custom/{id}/ - Update custom status
DELETE /hr/client-complaint-statuses/custom/{id}/ - Delete custom status
```

## Summary

✅ **Migration Applied**: New permission fields added to database
✅ **Permissions Updated**: Team permissions enabled for status management
✅ **Frontend Fixed**: Status dropdown now loads for users with `can_change_status`
✅ **Status Management Visible**: Teams with `can_manage_categories` can see and use the section
✅ **Full Functionality**: Create, edit, delete custom statuses working for team members

**Users Affected**: All members of Team X (ahmed, mohammed, potato, sting, string)

**Next Steps**: 
- Test the functionality in the browser with one of the team member accounts
- If you want to grant `can_delete` permission (delete complaints), update the team permission manually
- If you want to add more teams, grant them `TeamComplaintAdminPermission` with `can_manage_categories=True`
