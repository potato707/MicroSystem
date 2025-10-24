# Status Message Button Fix for Complaint Admins

## Issues Fixed

### 1. "Edit Status" Button Not Visible
The "Edit Status" button (which allows changing the status message/label of a complaint) was only visible to full admins (`userRole === 'admin'`). Users with complaint admin permissions could not access this feature even though they had the `can_change_status` permission.

### 2. Empty Status Dropdown
When complaint admins clicked the "Edit Status" button, the dropdown was empty because the available statuses weren't being loaded for non-admin users.

## Solutions

### Fix 1: Button Visibility
Updated the complaint detail modal to show the "Edit Status" button for both:
1. Full admins (`userRole === 'admin'`)
2. Complaint admins with `can_change_status` permission

### Fix 2: Status Loading Logic
Fixed the `useEffect` dependency logic to ensure statuses load properly for complaint admins. The issue was that `complaintAdminPermissions` starts as `null`, and the condition wasn't explicitly checking for the loaded state.

## Changes Made

### File: `v0-micro-system/components/complaints/complaint-detail-modal.tsx`

**Change 1: Edit Status Button Visibility (Line ~503)**
```tsx
// BEFORE
{userRole === 'admin' && (
  <Button
    variant="outline"
    size="sm"
    onClick={() => setShowStatusEditor(!showStatusEditor)}
  >
    Edit Status
  </Button>
)}

// AFTER
{(userRole === 'admin' || complaintAdminPermissions?.can_change_status) && (
  <Button
    variant="outline"
    size="sm"
    onClick={() => setShowStatusEditor(!showStatusEditor)}
  >
    Edit Status
  </Button>
)}
```

**Change 2: Status Editor Modal Visibility (Line ~534)**
```tsx
// BEFORE
{userRole === 'admin' && showStatusEditor && (
  <Card className="mb-4">
    <CardHeader>
      <CardTitle>Edit Status</CardTitle>
    </CardHeader>
    ...
  </Card>
)}

// AFTER
{(userRole === 'admin' || complaintAdminPermissions?.can_change_status) && showStatusEditor && (
  <Card className="mb-4">
    <CardHeader>
      <CardTitle>Edit Status</CardTitle>
    </CardHeader>
    ...
  </Card>
)}
```

**Change 3: Status Loading Logic (Line ~202)**
```tsx
// BEFORE
if (userRole === 'admin' || complaintAdminPermissions?.has_permission) {
  loadData()
}

// AFTER
// Load statuses if user is admin OR if they have complaint admin permissions
// Note: complaintAdminPermissions might be null initially, so we check explicitly for false
const shouldLoad = userRole === 'admin' || 
  (complaintAdminPermissions !== null && complaintAdminPermissions?.has_permission === true)

if (shouldLoad) {
  loadData()
}
```

## How It Works

1. **Permission Check**: When the modal loads, it fetches the user's complaint admin permissions using `ComplaintsAPI.getUserComplaintAdminPermissions()`

2. **Button Display**: The "Edit Status" button appears next to the status badge in the modal header if:
   - User is a full admin (`userRole === 'admin'`), OR
   - User has complaint admin permission with `can_change_status: true`

3. **Status Loading**: Available statuses are loaded when:
   - User is admin, OR
   - Complaint admin permissions have been loaded AND `has_permission` is `true`

4. **Editor Access**: When clicked, the status editor card appears with:
   - Dropdown populated with all available statuses (default + custom)
   - Update button to apply the new status
   - Cancel button to close the editor

## Button Location
The "Edit Status" button appears in the complaint detail modal header, next to the status badge:
```
[Status Badge: In Progress] [Edit Status Button]
```

## Permissions Required
For complaint admins to see this button and dropdown, they need:
- `can_change_status: true` in their complaint admin permission record
- `has_permission: true` (granted via team or employee assignment)

This permission is automatically set to `true` for all existing complaint admin permission records after the database migration.

## Testing

1. Log in with a complaint admin account (e.g., "string" user)
2. Navigate to Complaints Dashboard
3. Click on any complaint to open the detail modal
4. Look for the "Edit Status" button next to the status badge in the modal header
5. Click the button to open the status editor
6. **Verify the dropdown is populated** with all available statuses (default + custom)
7. Select a new status from the dropdown
8. Click "Update Status" to apply the change
9. Verify the status badge updates immediately

## Technical Details

### Race Condition Fix
The original code had a subtle race condition:
- On mount, `complaintAdminPermissions` is `null`
- First useEffect runs with `complaintAdminPermissions?.has_permission` evaluating to `undefined` (falsy)
- Statuses don't load
- Permissions load and update `complaintAdminPermissions`
- useEffect should re-run, but the condition needed to be more explicit

The fix explicitly checks if `complaintAdminPermissions !== null` before checking `has_permission`, ensuring that:
1. For admins: statuses load immediately
2. For complaint admins: statuses load after permissions are fetched
3. For regular users: statuses never load (no unnecessary API calls)

## Related Permissions

The complaint admin permission system includes:
- ✅ `can_change_status` - Allows editing the status message/label (THIS FIX)
- `can_review` - Approve/reject complaints
- `can_assign` - Assign teams/employees
- `can_update_status` - Update status via Actions tab
- `can_manage_categories` - Manage custom statuses
- `can_delete` - Delete complaints
- `can_add_comments` - Add internal comments
- `can_create_tasks` - Create linked tasks
- `can_manage_assignments` - Manage team/employee assignments

## Notes
- The `can_change_status` field is an alias for `can_update_status` but specifically controls access to the inline status editor
- All existing complaint admin permission records have this field set to `true` by default
- The button respects the same permission structure as other complaint admin features (team-based OR employee-based permissions)
- The dropdown shows both default statuses (pending_review, approved, etc.) and custom statuses created by admins
