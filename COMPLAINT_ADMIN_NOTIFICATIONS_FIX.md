# Complaint Admin Notifications & Status Update Fix

## Issues Fixed

### 1. ✅ Complaint Admin Permissions Not Receiving Notifications
**Problem**: Users with complaint admin permissions (non-admins) weren't receiving notifications when clients sent messages.

**Root Cause**: The notification service only notified:
- Assigned teams/employees
- Category-assigned teams  
- All admins (fallback)

It didn't include users with `EmployeeComplaintAdminPermission` or `TeamComplaintAdminPermission`.

**Fix**: Updated `hr_management/notifications.py` in the `_get_admin_users()` method to include:
- All admins
- All users with individual complaint admin permissions (`EmployeeComplaintAdminPermission`)
- All members of teams with complaint admin permissions (`TeamComplaintAdminPermission`)

**File**: `hr_management/notifications.py` lines 92-120

---

### 2. ✅ Complaint Admins Couldn't View Complaints from Notifications
**Problem**: When clicking a notification, users with complaint admin permissions got redirected to the page but the complaint didn't open because they couldn't see it in their list.

**Root Cause**: Non-admin users called `ComplaintsAPI.getTeamComplaints()` which only returned complaints assigned to their teams. If a complaint wasn't assigned to their team, they couldn't see it even though they had permissions.

**Fix**: Updated `complaints-dashboard.tsx` to check if user has complaint admin permissions (`has_permission=true`). If yes, fetch ALL complaints like admins do using `ComplaintsAPI.getComplaints()`.

**File**: `v0-micro-system/components/complaints/complaints-dashboard.tsx` lines 101-103

**Before**:
```typescript
const [complaintsData] = await Promise.all([
  userRole === 'admin' 
    ? ComplaintsAPI.getComplaints(complaintsParams)
    : ComplaintsAPI.getTeamComplaints(complaintsParams),
  ...
])
```

**After**:
```typescript
const canViewAllComplaints = userRole === 'admin' || complaintAdminPermissions?.has_permission

const [complaintsData] = await Promise.all([
  canViewAllComplaints
    ? ComplaintsAPI.getComplaints(complaintsParams)
    : ComplaintsAPI.getTeamComplaints(complaintsParams),
  ...
])
```

---

### 3. ✅ "Start Progress" Button Failed with Status Update Error
**Problem**: Clicking "Start Progress" button sent request with `{"status": "in_progress"}` but backend returned validation error requiring `status_type` and `status_value` fields.

**Root Cause**: The `handleLegacyStatusUpdate` function was using old API format with `status`, `resolution_notes`, and `reason` fields. The backend now requires:
- `status_type`: 'default' or 'custom'
- `status_value`: the status name or custom status ID
- `notes`: optional notes

**Fix**: Updated `handleLegacyStatusUpdate` in `complaint-detail-modal.tsx` to use new API format.

**File**: `v0-micro-system/components/complaints/complaint-detail-modal.tsx` lines 428-450

**Before**:
```typescript
const updateData: ComplaintStatusUpdateData = {
  status: newStatus,
  resolution_notes: statusUpdateNotes || undefined,
  reason: statusUpdateNotes || undefined
}
```

**After**:
```typescript
const updateData: ComplaintStatusUpdateData = {
  status_type: 'default',
  status_value: newStatus,
  notes: statusUpdateNotes || undefined
}
```

---

## Test Results

### Notification Test
Ran `test_new_notification_to_admins.py` which showed:

**Recipients of new notification:**
- ✅ ahmed (admin)
- ✅ mohammed (admin)  
- ✅ admin (admin)
- ✅ admin_test_tasks (admin)
- ✅ **potato (employee with complaint admin permission)**
- ✅ **string (employee with complaint admin permission)**
- ✅ **sting (employee - team member with permission)**

**Unread counts after notification:**
- potato (employee): **1 unread** ✅
- string (employee): **1 unread** ✅
- sting (employee): **1 unread** ✅

---

## Files Changed

1. **Backend**:
   - `hr_management/notifications.py` - Added complaint admin permission users to notification recipients

2. **Frontend**:
   - `v0-micro-system/components/complaints/complaints-dashboard.tsx` - Allow complaint admins to view all complaints
   - `v0-micro-system/components/complaints/complaint-detail-modal.tsx` - Fixed status update API format

3. **Test Scripts**:
   - `test_complaint_admin_notifications.py` - List users with permissions
   - `test_new_notification_to_admins.py` - Trigger notification and verify delivery

---

## How It Works Now

### Notification Flow
1. Client sends message on complaint
2. Backend checks for assigned teams/employees
3. **If no assignments**, notify:
   - All admins
   - All users with `EmployeeComplaintAdminPermission`
   - All team members of teams with `TeamComplaintAdminPermission`
4. Frontend polls `/notifications/unread_count/` every 30 seconds
5. Bell icon shows red badge with count
6. User clicks notification → Navigates to `/dashboard/client-complaints?id=<complaint-id>`
7. Complaint dashboard auto-opens the complaint detail modal

### Permission Check Flow
1. User loads client complaints dashboard
2. Frontend calls `ComplaintsAPI.getUserComplaintAdminPermissions()`
3. If `has_permission=true`, fetch ALL complaints (not just team complaints)
4. User can now see and manage any complaint like an admin

### Status Update Flow
1. User clicks "Start Progress" button
2. Frontend sends: `{ status_type: 'default', status_value: 'in_progress', notes: '...' }`
3. Backend validates and updates complaint status
4. Automated status manager updates communication status automatically

---

## Summary

✅ **Users with complaint admin permissions now:**
- Receive notifications when clients send messages
- Can view ALL client complaints (not just their team's)
- Can click notifications to open the correct complaint
- Can update complaint status using "Start Progress" and other action buttons

**Date**: October 17, 2025
