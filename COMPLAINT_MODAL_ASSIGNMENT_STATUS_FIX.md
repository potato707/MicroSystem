# Complaint Modal - Assignment and Status Update Fixes

## Date: October 15, 2025

## Problems Identified

### 1. Empty Employee Dropdown in Assignment Section
**Issue:** The "Select Individual Employees" dropdown was appearing empty when non-admin users with complaint admin permissions tried to assign employees to a complaint.

**Root Cause:**
- Employees were only loaded when `userRole === 'admin' || complaintAdminPermissions?.has_permission`
- This condition was evaluated in a `useEffect` that ran before `complaintAdminPermissions` was loaded
- Due to the race condition, `complaintAdminPermissions` was `null` when the check ran, causing the employees not to load for non-admin users
- Even when permissions were eventually loaded, the `useEffect` dependencies didn't trigger a re-load of employees

### 2. Status Update Notes Not Being Saved
**Issue:** When users updated a complaint's status (using the custom status selector or quick action buttons), their custom notes in the "Status Update Notes" textarea were not being saved. Instead, the system was always saving a hardcoded message "Status updated by admin".

**Root Cause:**
- The `handleStatusUpdate` function had hardcoded notes: `notes: 'Status updated by admin'`
- The `statusUpdateNotes` state variable (which captured the user's input) was never being used
- This affected both custom status updates and default status updates

---

## Solutions Implemented

### Fix 1: Separate Employee Loading with Permission Check

**File:** `v0-micro-system/components/complaints/complaint-detail-modal.tsx`

**Changes:**
1. Split the `loadData` useEffect into two separate effects:
   - One for loading statuses (kept existing behavior)
   - One specifically for loading employees

2. Created a new `useEffect` that loads employees separately:
```typescript
// Load employees separately for assignment functionality
useEffect(() => {
  const loadEmployees = async () => {
    try {
      const employeesData = await api.getEmployees()
      setEmployees(Array.isArray(employeesData) ? employeesData : employeesData.results || [])
    } catch (error) {
      console.error('Failed to load employees:', error)
      setEmployees([])
    }
  }

  // Load employees if user can assign
  if (userRole === 'admin' || complaintAdminPermissions?.can_assign) {
    loadEmployees()
  }
}, [userRole, complaintAdminPermissions])
```

**Key Improvements:**
- Employees now load based on the specific `can_assign` permission
- The `useEffect` has `complaintAdminPermissions` as a dependency, so it re-runs when permissions are loaded
- This eliminates the race condition by properly waiting for permissions to be available
- Error handling with fallback to empty array

### Fix 2: Use User-Provided Notes in Status Updates

**File:** `v0-micro-system/components/complaints/complaint-detail-modal.tsx`

**Changes:**
Updated the `handleStatusUpdate` function to use the `statusUpdateNotes` state variable:

```typescript
const handleStatusUpdate = async (newStatusId?: number, newCustomStatusId?: number) => {
  if (!complaint) return;
  
  try {
    let statusData: any = {};
    
    if (newCustomStatusId) {
      // For custom status
      statusData = {
        status_type: 'custom',
        status_value: newCustomStatusId.toString(),
        notes: statusUpdateNotes.trim() || 'Status updated'  // ✅ Now uses user input
      };
    } else if (newStatusId) {
      // For default status, map ID back to status name
      const statusMap: Record<number, string> = {
        1: 'pending_review',
        2: 'approved', 
        3: 'rejected',
        4: 'in_progress',
        5: 'resolved',
        6: 'closed'
      };
      statusData = {
        status_type: 'default',
        status_value: statusMap[newStatusId] || 'pending_review',
        notes: statusUpdateNotes.trim() || 'Status updated'  // ✅ Now uses user input
      };
    }
    
    await ComplaintsAPI.updateComplaintStatus(complaint.id, statusData);
    
    // Clear the notes after successful update
    setStatusUpdateNotes('');
    
    // Refresh the complaint data after status update
    window.location.reload();
  } catch (error) {
    console.error('Error updating complaint status:', error);
    alert('Failed to update status');
  }
};
```

**Key Improvements:**
- Now uses `statusUpdateNotes.trim()` to capture user's input
- Falls back to `'Status updated'` if notes are empty (instead of the confusing "Status updated by admin")
- Clears the notes field after successful update for better UX
- Works for both custom statuses and default statuses

---

## Testing

### Test Case 1: Employee Assignment Dropdown
**Steps:**
1. Log in as a user with complaint admin permissions (not a full admin)
2. Open a complaint in the modal
3. Navigate to the "Actions" tab
4. Scroll to the "Assignment" section
5. Check the "Select Individual Employees" dropdown

**Expected Result:**
- ✅ Dropdown should show all available employees
- ✅ Each employee should display with their name and position
- ✅ Multiple employees can be selected via checkboxes

**Previous Behavior:**
- ❌ Dropdown was empty
- ❌ No employees appeared in the list

### Test Case 2: Status Update Notes
**Steps:**
1. Log in as any user with complaint admin permissions
2. Open a complaint in the modal
3. Navigate to the "Actions" tab
4. Scroll to the "Status Update" section
5. Enter custom notes in the "Status Update Notes" textarea (e.g., "Issue resolved after debugging")
6. Select a new status from the dropdown
7. Click "Update to: [Status Name]"
8. Check the complaint history

**Expected Result:**
- ✅ Status should update successfully
- ✅ The notes field should show your custom message in the history
- ✅ The textarea should clear after successful update

**Previous Behavior:**
- ❌ Always saved "Status updated by admin" regardless of user input
- ❌ Custom notes were ignored

---

## Impact

### Users Affected
- All non-admin users with complaint admin permissions
- Specifically those with `can_assign` or `can_change_status` permissions

### Features Fixed
1. **Employee Assignment**: Users can now properly assign individual employees to complaints
2. **Status Update Tracking**: Status changes now include meaningful, user-provided context
3. **Audit Trail**: Better tracking of why statuses were changed (actual user notes vs. generic message)

---

## Technical Notes

### Race Condition Prevention
The fix for employee loading demonstrates a common React pattern for handling dependent data:
- Load base permissions first (in their own useEffect)
- Load dependent data in a separate useEffect that watches permissions
- This ensures proper ordering without complex async chains

### Permission Granularity
The fix improves permission checking by using specific permissions (`can_assign`) rather than generic ones (`has_permission`). This follows the principle of least privilege and makes the code more maintainable.

### UX Improvement
Clearing the notes field after a successful update prevents accidental reuse of old notes and provides visual feedback that the action completed.

---

## Related Files

- `v0-micro-system/components/complaints/complaint-detail-modal.tsx` - Main component with both fixes
- `v0-micro-system/lib/api.ts` - Employee API endpoint (unchanged)
- `v0-micro-system/lib/api/complaints.ts` - Status update API (unchanged)
- `hr_management/views.py` - Backend employee endpoint (unchanged)

---

## Verification

Run TypeScript compilation to verify no errors:
```bash
cd v0-micro-system
npx tsc --noEmit
```

Check complaint detail modal specifically:
```bash
npx tsc --noEmit components/complaints/complaint-detail-modal.tsx
```

Both commands should complete without errors.
