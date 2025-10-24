# Complaint Admin Permission System - Complete Implementation

## Overview
Implemented a comprehensive complaint admin permission system that allows designated teams and individual employees to have admin-level complaint management capabilities without requiring full system admin access. This helps distribute workload and enables better delegation of complaint management responsibilities.

## Backend Implementation

### Models (`hr_management/models.py`)

#### ComplaintAdminPermission (Abstract Base)
- Base model for permission tracking
- Fields: `granted_by`, `granted_at`, `revoked_at`, `is_active`

#### TeamComplaintAdminPermission
- Grants complaint admin permissions to entire teams
- All team members inherit the permissions
- Fields: `team` (ForeignKey to Team)

#### EmployeeComplaintAdminPermission
- Grants complaint admin permissions to individual employees
- Fields: `employee` (ForeignKey to Employee)

### Permission Utility Functions

#### `has_complaint_admin_permission(user)`
Returns `True` if user has complaint admin permissions via team membership or direct grant.

#### `get_complaint_admin_permissions(user)`
Returns detailed permission information:
```python
{
    'has_permission': bool,
    'can_assign': bool,
    'can_change_status': bool,
    'can_delete': bool,
    'can_manage_categories': bool,
    'granted_by': [list of sources],
    'team_permissions': [list of team permissions],
    'employee_permissions': [list of employee permissions]
}
```

### API Endpoints (`hr_management/views.py` & `urls.py`)

#### Team Permissions
- `GET /hr/complaint-admin-permissions/teams/` - List all team permissions
- `POST /hr/complaint-admin-permissions/teams/` - Grant permission to a team
- `DELETE /hr/complaint-admin-permissions/teams/<id>/` - Revoke team permission

#### Employee Permissions
- `GET /hr/complaint-admin-permissions/employees/` - List all employee permissions
- `POST /hr/complaint-admin-permissions/employees/` - Grant permission to an employee
- `DELETE /hr/complaint-admin-permissions/employees/<id>/` - Revoke employee permission

#### User Permissions Check
- `GET /hr/complaint-admin-permissions/user/` - Get current user's permissions

### Updated Complaint Views
All complaint management views now check for admin permissions using:
```python
user_is_admin = request.user.is_staff or has_complaint_admin_permission(request.user)
```

## Frontend Implementation

### 1. API Integration (`v0-micro-system/lib/api/complaints.ts`)

Added 7 new API methods to `ComplaintsAPI`:

```typescript
// Permission checking
getUserComplaintAdminPermissions(): Promise<PermissionResponse>

// Team permissions
getTeamComplaintAdminPermissions(): Promise<TeamPermission[]>
grantTeamComplaintAdminPermission(teamId: string): Promise<GrantResponse>
revokeTeamComplaintAdminPermission(permissionId: number): Promise<RevokeResponse>

// Employee permissions
getEmployeeComplaintAdminPermissions(): Promise<EmployeePermission[]>
grantEmployeeComplaintAdminPermission(employeeId: string): Promise<GrantResponse>
revokeEmployeeComplaintAdminPermission(permissionId: number): Promise<RevokeResponse>
```

### 2. Permission Management Page (`app/admin/complaint-permissions/page.tsx`)

Comprehensive admin interface for managing complaint admin permissions:

**Features:**
- **Dashboard Overview**: Shows count of active team and employee permissions
- **Team Permissions Table**: 
  - Lists all granted team permissions
  - Shows who granted each permission and when
  - Active/Revoked status indicators
  - One-click revoke with confirmation
- **Employee Permissions Table**:
  - Lists all individual employee permissions
  - Full audit trail (granted by, date)
  - Status tracking and revoke functionality
- **Grant Dialogs**:
  - Team selection dropdown (filtered to exclude already-granted teams)
  - Employee selection dropdown (filtered to exclude already-granted employees)
  - Real-time validation and error handling
- **Success/Error Alerts**: User-friendly feedback for all actions

**Access:** `/admin/complaint-permissions` (Admin only)

### 3. Complaint Admin Badge (`components/complaints/complaint-admin-badge.tsx`)

Visual indicator component that shows when a user has complaint admin permissions:

**Features:**
- Auto-loads user's permission status
- Only displays if user has permissions
- Purple badge with shield icon
- Hover tooltip showing who granted permissions
- Lightweight and reusable

**Usage:**
```tsx
<ComplaintAdminBadge className="ml-2" showLabel={true} />
```

### 4. Updated Complaint Detail Modal (`components/complaints/complaint-detail-modal.tsx`)

Enhanced to support complaint admin permissions:

**Changes:**
- Added `complaintAdminPermissions` state
- Loads permissions on component mount
- Updated permission checks:
  ```typescript
  const isAdminOrComplaintAdmin = userRole === 'admin' || complaintAdminPermissions?.has_permission
  const canReview = isAdminOrComplaintAdmin && ...
  const canAssign = isAdminOrComplaintAdmin && complaintAdminPermissions?.can_assign && ...
  const canUpdateStatus = isAdminOrComplaintAdmin && complaintAdminPermissions?.can_change_status && ...
  const canDelete = isAdminOrComplaintAdmin && complaintAdminPermissions?.can_delete
  ```
- Comment deletion now works for complaint admins
- All admin actions respect granular permissions

### 5. Client Complaints Page (`app/dashboard/client-complaints/page.tsx`)

Updated to display complaint admin badge:
- Badge appears next to page title
- Shows automatically if user has permissions
- Provides visual confirmation of elevated privileges

## Permission Capabilities

Users with complaint admin permissions can:

✅ **Review Complaints**: Approve or reject pending complaints
✅ **Assign Complaints**: Assign to teams or individual employees (multiple assignments supported)
✅ **Update Status**: Change complaint status (including custom statuses)
✅ **Delete Complaints**: Remove complaints (if granted)
✅ **Manage Comments**: Add internal/external comments, delete any comment
✅ **Generate Client Links**: Create portal access for clients
✅ **Respond to Client Replies**: Handle client communication
✅ **Create Tasks**: Convert complaints to tasks

## Security & Validation

- **Admin-Only Grant/Revoke**: Only system admins can manage permissions
- **Soft Delete**: Permissions are marked inactive rather than deleted (audit trail)
- **Duplicate Prevention**: Cannot grant same permission twice to same team/employee
- **Permission Inheritance**: Team permissions apply to all current and future members
- **Granular Control**: Individual permissions for assign, status change, delete operations
- **Audit Trail**: Tracks who granted permissions and when

## Testing

Comprehensive test script: `test_complaint_admin_frontend.py`

**Tests:**
1. ✅ Fetch teams and employees
2. ✅ Grant team permission
3. ✅ Grant employee permission
4. ✅ List all team permissions
5. ✅ List all employee permissions
6. ✅ Check current user permissions
7. ✅ Revoke team permission
8. ✅ Revoke employee permission
9. ✅ Frontend component verification

**Run tests:**
```bash
cd /home/ahmedyasser/lab/MicroSystem
python3 test_complaint_admin_frontend.py
```

## Usage Guide

### For System Admins

**Grant Permissions:**
1. Navigate to `/admin/complaint-permissions`
2. Click "Grant to Team" or "Grant to Employee"
3. Select team/employee from dropdown
4. Click "Grant Permission"
5. Confirmation message appears

**Revoke Permissions:**
1. Find the permission in the table
2. Click the trash icon
3. Confirm the revocation
4. Permission marked as revoked (audit trail preserved)

### For Complaint Admins

**Accessing Features:**
1. Navigate to `/dashboard/client-complaints`
2. Purple "Complaint Admin" badge appears if you have permissions
3. Click on any complaint to open detail modal
4. Admin-level actions are automatically available based on your permissions

**Available Actions:**
- Review pending complaints (approve/reject)
- Assign complaints to teams or employees
- Update complaint status
- Delete complaints (if permission granted)
- Manage comments and client communication
- Generate client portal links
- Convert complaints to tasks

## Database Migrations

Migrations applied:
- Created `TeamComplaintAdminPermission` table
- Created `EmployeeComplaintAdminPermission` table
- Added indexes for performance
- Foreign key relationships established

## API Response Examples

### Get User Permissions
```json
{
  "has_permission": true,
  "can_assign": true,
  "can_change_status": true,
  "can_delete": false,
  "can_manage_categories": true,
  "granted_by": ["Test Team", "Admin Direct Grant"]
}
```

### List Team Permissions
```json
[
  {
    "id": 1,
    "team": {
      "id": "uuid",
      "name": "Test Team"
    },
    "granted_by": {
      "id": "uuid",
      "first_name": "Admin",
      "last_name": "User",
      "email": "admin@example.com"
    },
    "granted_at": "2025-10-15T10:30:00Z",
    "is_active": true
  }
]
```

## Files Modified/Created

### Backend
- ✅ `hr_management/models.py` - Added permission models and utility functions
- ✅ `hr_management/views.py` - Added permission management views
- ✅ `hr_management/urls.py` - Added permission endpoints
- ✅ Database migrations applied

### Frontend
- ✅ `v0-micro-system/lib/api/complaints.ts` - Added API methods
- ✅ `v0-micro-system/app/admin/complaint-permissions/page.tsx` - Permission management page (NEW)
- ✅ `v0-micro-system/components/complaints/complaint-admin-badge.tsx` - Badge component (NEW)
- ✅ `v0-micro-system/components/complaints/complaint-detail-modal.tsx` - Updated with permission checks
- ✅ `v0-micro-system/app/dashboard/client-complaints/page.tsx` - Added badge display

### Testing
- ✅ `test_complaint_admin_permissions.py` - Backend API tests
- ✅ `test_complaint_admin_frontend.py` - Complete integration tests

## URLs

### Backend API
- `http://localhost:8000/hr/complaint-admin-permissions/teams/`
- `http://localhost:8000/hr/complaint-admin-permissions/employees/`
- `http://localhost:8000/hr/complaint-admin-permissions/user/`

### Frontend Pages
- `http://localhost:3000/admin/complaint-permissions` - Permission Management
- `http://localhost:3000/dashboard/client-complaints` - Complaint Dashboard (with badge)

## Next Steps / Future Enhancements

1. **Email Notifications**: Notify users when permissions are granted/revoked
2. **Permission Expiration**: Add optional expiration dates for temporary permissions
3. **Activity Logging**: Detailed audit log of actions taken by complaint admins
4. **Permission Reporting**: Analytics dashboard showing permission usage
5. **Batch Operations**: Grant/revoke permissions to multiple teams/employees at once
6. **Permission Templates**: Pre-defined permission sets for different roles

## Summary

✅ **Complete Backend**: Models, utility functions, API endpoints, permission checks
✅ **Complete Frontend**: Management page, badge component, modal updates, API integration
✅ **Comprehensive Testing**: All features tested and working
✅ **Security**: Admin-only management, audit trails, soft deletes
✅ **User Experience**: Clear UI, visual indicators, real-time feedback
✅ **Documentation**: Complete implementation guide

The complaint admin permission system is fully implemented and ready for use!
