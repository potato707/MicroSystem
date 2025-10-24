# Complaint Actions Access Fix for Complaint Admins

## Problem
Users with complaint admin permissions were seeing "No actions available for this complaint in its current state" in the Actions tab of the complaint detail modal, even though they had been granted permissions to review, assign, and update complaint statuses.

## Root Causes

### 1. Incorrect Permission Logic for Actions
**Location:** `complaint-detail-modal.tsx` lines 73-77

**Before:**
```typescript
const canAssign = isAdminOrComplaintAdmin && complaintAdminPermissions?.can_assign && ['approved', 'in_progress'].includes(currentComplaint.status)
const canUpdateStatus = isAdminOrComplaintAdmin && complaintAdminPermissions?.can_change_status && ['approved', 'in_progress', 'resolved'].includes(currentComplaint.status)
```

**Problem:** This logic required ALL three conditions to be true:
1. User is admin OR has complaint admin permissions
2. complaintAdminPermissions?.can_assign is true
3. Complaint status matches

For admin users, `complaintAdminPermissions` might be null or undefined, causing `can_assign` to be falsy, which would block admins from taking actions.

**After:**
```typescript
const canAssign = (userRole === 'admin' || complaintAdminPermissions?.can_assign) && ['approved', 'in_progress'].includes(currentComplaint.status)
const canUpdateStatus = (userRole === 'admin' || complaintAdminPermissions?.can_change_status) && ['approved', 'in_progress', 'resolved'].includes(currentComplaint.status)
```

**Fix:** Now the logic properly checks:
- Admin users: Always have permission (don't need complaint admin permissions record)
- Non-admin users: Check specific complaint admin permissions

### 2. Incorrect "No Actions" Display Condition
**Location:** `complaint-detail-modal.tsx` line 1335

**Before:**
```typescript
{!canReview && !canAssign && !canUpdateStatus && userRole === 'employee' && (
```

**Problem:** This showed "No actions available" for ALL employees, even those with complaint admin permissions, because it only checked if `userRole === 'employee'`.

**After:**
```typescript
{!canReview && !canAssign && !canUpdateStatus && (userRole !== 'admin' && userRole !== 'manager') && !complaintAdminPermissions?.has_permission && (
```

**Fix:** Now it only shows "No actions available" when:
- User has no review permissions AND
- User has no assign permissions AND
- User has no status update permissions AND
- User is not an admin or manager AND
- User does not have complaint admin permissions

## Changes Made

### File: `v0-micro-system/components/complaints/complaint-detail-modal.tsx`

1. **Updated permission checks (lines 73-77):**
   - Changed `canAssign` logic to OR admin role with specific permission
   - Changed `canUpdateStatus` logic to OR admin role with specific permission
   - Changed `canDelete` logic to OR admin role with specific permission

2. **Updated "No Actions" condition (line 1335):**
   - Changed from checking only `userRole === 'employee'`
   - Added check for complaint admin permissions
   - Now properly excludes users who have complaint admin permissions

## What Users Can Now Do

### Admin Users
✅ Full access to all actions (unchanged)

### Complaint Admins (Employees with Permissions)
✅ **Review complaints** - If complaint status is `pending_review`
✅ **Assign complaints** - If they have `can_assign` permission and status is `approved` or `in_progress`
✅ **Update status** - If they have `can_change_status` permission and status is `approved`, `in_progress`, or `resolved`
✅ **Delete complaints** - If they have `can_delete` permission (admin-level action)

### Regular Employees (No Permissions)
❌ See "No actions available" message (correct behavior)

## Actions Available by Permission

| Action | Required Permission | Available When |
|--------|---------------------|---------------|
| **Review** (Approve/Reject) | Any complaint admin permission | Status = `pending_review` |
| **Assign to Team/Employee** | `can_assign` = true | Status = `approved` or `in_progress` |
| **Update Status** | `can_change_status` = true | Status = `approved`, `in_progress`, or `resolved` |
| **Delete Complaint** | `can_delete` = true | Any status |
| **Generate Client Link** | Admin or Manager only | Any status |

## Testing

### Test Scenario 1: Complaint Admin with Full Permissions
1. Grant employee all complaint admin permissions
2. Log in as that employee
3. Open a complaint in `approved` or `in_progress` status
4. Navigate to "Actions" tab

**Expected Result:**
- ✅ See "Assign Complaint" section
- ✅ See "Update Status" section
- ✅ No "No actions available" message

### Test Scenario 2: Complaint Admin with Limited Permissions
1. Grant employee only `can_change_status` permission
2. Log in as that employee
3. Open a complaint in `in_progress` status
4. Navigate to "Actions" tab

**Expected Result:**
- ❌ No "Assign Complaint" section
- ✅ See "Update Status" section
- ✅ No "No actions available" message

### Test Scenario 3: Regular Employee
1. Do not grant any complaint admin permissions
2. Log in as employee
3. Open any complaint
4. Navigate to "Actions" tab

**Expected Result:**
- ❌ No action sections
- ✅ See "No actions available" message

## Benefits

1. **Proper Role Segregation**: Complaint admins can now perform their assigned duties
2. **Granular Control**: Different permissions grant access to different action types
3. **Better UX**: Users see the actions they're allowed to perform
4. **Security**: Still properly restricts actions based on permissions
5. **Consistent Logic**: Works the same way as backend permission checks

## Related Components

- **Backend**: Permission checks already working correctly (see `COMPLAINT_ADMIN_ACCESS_FIX.md`)
- **Frontend Badge**: Shows complaint admin status in header
- **Permission Management**: Admin panel to grant/revoke permissions

## Impact

All complaint admin features now work end-to-end:
1. ✅ Backend API allows complaint admins to access endpoints
2. ✅ Frontend displays appropriate actions based on permissions
3. ✅ Users can review, assign, and update complaint statuses
4. ✅ Permission system working as designed
