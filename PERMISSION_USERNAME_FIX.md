# Employee Permission Username Display Fix

## Problem
When a new employee permission was granted via the complaint admin permissions page, the table would display:
- Employee: "No name" (gray text)
- Username: "@N/A"

This was because the API response didn't include the `username` field in the employee data.

## Root Cause
The `EmployeeComplaintAdminPermissionView` in `views.py` was constructing the employee data object without including the `username` field, which comes from the related `User` model.

## Changes Made

### 1. Backend API Response (`hr_management/views.py`)

#### GET `/hr/complaint-admin-permissions/employees/`
**Before:**
```python
permissions = EmployeeComplaintAdminPermission.objects.select_related('employee', 'granted_by').all()
data = []
for perm in permissions:
    data.append({
        'id': perm.id,
        'employee': {
            'id': perm.employee.id,
            'name': perm.employee.name,
            'position': perm.employee.position,
            'department': perm.employee.department
        },
        # ...
    })
```

**After:**
```python
permissions = EmployeeComplaintAdminPermission.objects.select_related('employee', 'employee__user', 'granted_by').all()
data = []
for perm in permissions:
    data.append({
        'id': perm.id,
        'employee': {
            'id': perm.employee.id,
            'name': perm.employee.name,
            'username': perm.employee.user.username if perm.employee.user else None,
            'position': perm.employee.position,
            'department': perm.employee.department
        },
        # ...
    })
```

**Changes:**
- Added `employee__user` to `select_related()` for efficient database query
- Added `username` field to employee data, safely accessing via `perm.employee.user.username`

#### POST `/hr/complaint-admin-permissions/employees/`
**Before:**
```python
return Response({
    'message': f'Complaint admin permissions granted to employee {employee.name}',
    'permission_id': permission.id
}, status=201)
```

**After:**
```python
return Response({
    'id': permission.id,
    'employee': {
        'id': employee.id,
        'name': employee.name,
        'username': employee.user.username if employee.user else None,
        'position': employee.position,
        'department': employee.department
    },
    'granted_by': request.user.username,
    'granted_at': permission.granted_at,
    'is_active': permission.is_active,
    'notes': permission.notes,
    'permissions': {
        'can_review': permission.can_review,
        'can_assign': permission.can_assign,
        'can_update_status': permission.can_update_status,
        'can_add_comments': permission.can_add_comments,
        'can_create_tasks': permission.can_create_tasks,
        'can_manage_assignments': permission.can_manage_assignments
    }
}, status=201)
```

**Changes:**
- Changed from simple message response to full permission object
- Includes complete employee data with `username` field
- Returns structured permission data that matches the GET response format
- Frontend can now use the returned data directly without refetching

### 2. Frontend TypeScript Types (`lib/api/complaints.ts`)

**Added new type definition:**
```typescript
export interface EmployeePermission {
  id: number;
  employee: {
    id: string;
    name: string;
    username?: string;
    position?: string;
    department?: string;
  };
  granted_by: string;
  granted_at: string;
  is_active: boolean;
  notes?: string;
  permissions?: {
    can_review: boolean;
    can_assign: boolean;
    can_update_status: boolean;
    can_add_comments: boolean;
    can_create_tasks: boolean;
    can_manage_assignments: boolean;
  };
}
```

**Updated method signatures:**
```typescript
// Before
async getEmployeeComplaintAdminPermissions(): Promise<Array<{
  id: number;
  employee: { id: string; first_name: string; last_name: string; email: string };
  granted_by: { id: string; first_name: string; last_name: string; email: string };
  granted_at: string;
  is_active: boolean;
}>>

async grantEmployeeComplaintAdminPermission(employeeId: string): Promise<{
  message: string;
  permission_id: number;
  employee_name: string;
}>

// After
async getEmployeeComplaintAdminPermissions(): Promise<EmployeePermission[]>

async grantEmployeeComplaintAdminPermission(employeeId: string): Promise<EmployeePermission>
```

### 3. Frontend Page Component (`app/admin/complaint-permissions/page.tsx`)

**Updated imports:**
```typescript
import { ComplaintsAPI, type EmployeePermission } from '@/lib/api/complaints';
```

**Updated table rendering:**
```typescript
// Before
const empName = `${perm.employee.first_name || ''} ${perm.employee.last_name || ''}`.trim();
const username = perm.employee.username || perm.employee.email?.split('@')[0] || 'N/A';
const displayName = empName || `@${username}`;

// After
const username = perm.employee.username || 'N/A';
const displayName = perm.employee.name || `@${username}`;
```

**Updated granted_by display:**
```typescript
// Before
{perm.granted_by.first_name} {perm.granted_by.last_name}

// After
{perm.granted_by || 'N/A'}
```

## API Response Examples

### GET Response
```json
[
  {
    "id": 1,
    "employee": {
      "id": "e70fe696-8c4a-4f73-83a0-64c66429caab",
      "name": "string",
      "username": "string",
      "position": "string",
      "department": "string"
    },
    "granted_by": "ahmed",
    "granted_at": "2025-10-15T13:51:54.435488Z",
    "is_active": true,
    "notes": "Individual complaint admin access for senior staff",
    "permissions": {
      "can_review": true,
      "can_assign": true,
      "can_update_status": true,
      "can_add_comments": true,
      "can_create_tasks": true,
      "can_manage_assignments": false
    }
  }
]
```

### POST Response
```json
{
  "id": 1,
  "employee": {
    "id": "e70fe696-8c4a-4f73-83a0-64c66429caab",
    "name": "string",
    "username": "string",
    "position": "string",
    "department": "string"
  },
  "granted_by": "ahmed",
  "granted_at": "2025-10-15T13:51:54.435488Z",
  "is_active": true,
  "notes": "Test permission grant",
  "permissions": {
    "can_review": true,
    "can_assign": true,
    "can_update_status": true,
    "can_add_comments": true,
    "can_create_tasks": true,
    "can_manage_assignments": false
  }
}
```

## Testing

Run the test script to verify the fix:
```bash
python3 test_username_in_permissions.py
```

Expected output:
```
✓ ALL TESTS PASSED - Username field is properly included in responses
```

## Benefits

1. **Consistent Data Structure**: Both GET and POST endpoints now return the same structure
2. **Better User Experience**: Employees are displayed with their actual username instead of "N/A"
3. **Reduced API Calls**: Frontend no longer needs to refetch data after granting permissions
4. **Type Safety**: TypeScript types accurately reflect the API response structure
5. **Performance**: Used `select_related()` to optimize database queries and prevent N+1 issues

## Display Format

The frontend now displays employees in the following format:
- **Employee Column**: Shows the full name (e.g., "John Doe") or "No name" if not available
- **Username Column**: Shows `@username` in monospace font (e.g., "@johndoe")
- **Granted By Column**: Shows the username of the admin who granted the permission

This follows modern UI conventions (like social media) where usernames are prefixed with @ symbol.
