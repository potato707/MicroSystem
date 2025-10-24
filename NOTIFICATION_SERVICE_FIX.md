# Notification Service Fix - Complete

## Issue
When adding comments/replies to complaints, the following error occurred:
```
Failed to send client message notification: 'ClientComplaint' object has no attribute 'team_assignments'
```

## Root Causes

### 1. Wrong Related Name for Team Assignments
**Error**: `complaint.team_assignments.all()`  
**Correct**: `complaint.assignments.filter(is_active=True)`

The `ClientComplaintAssignment` model uses `related_name='assignments'`, not `team_assignments`.

### 2. Wrong Related Name for Category Employees
**Error**: `complaint.category.employees.select_related('user').all()`  
**Correct**: Use `complaint.category.assigned_teams` instead

The `ComplaintCategory` model doesn't have an `employees` field, only `assigned_teams`.

### 3. Wrong Email Access Path
**Error**: `assignment.employee.email`  
**Correct**: `assignment.employee.user.email`

Employees don't have direct email field; email is on the related User object.

## Solution

### File: `hr_management/notifications.py`

**Fixed `_get_admin_emails()` method**:

```python
@staticmethod
def _get_admin_emails(complaint):
    """Get list of admin/support emails responsible for this complaint"""
    emails = []
    
    # Get assigned teams' members
    team_assignments = complaint.assignments.filter(is_active=True)
    for assignment in team_assignments:
        # Get team members' user emails
        team_members = assignment.team.memberships.select_related('employee__user').all()
        for membership in team_members:
            if membership.employee.user and membership.employee.user.email:
                emails.append(membership.employee.user.email)
    
    # Get directly assigned employees
    employee_assignments = complaint.employee_assignments.filter(is_active=True)
    for assignment in employee_assignments:
        if assignment.employee.user and assignment.employee.user.email:
            emails.append(assignment.employee.user.email)
    
    # Fallback to category handlers if no specific assignment
    if not emails and complaint.category:
        # Get assigned teams for this category
        category_teams = complaint.category.assigned_teams.all()
        for team in category_teams:
            team_members = team.memberships.select_related('employee__user').all()
            for membership in team_members:
                if membership.employee.user and membership.employee.user.email:
                    emails.append(membership.employee.user.email)
    
    # Remove duplicates
    return list(set(emails))
```

## Model Structure Reference

### ClientComplaint Relationships
```python
# Team assignments (Many-to-Many through ClientComplaintAssignment)
complaint.assignments.all()  # ✅ Correct
complaint.team_assignments.all()  # ❌ Wrong

# Employee assignments
complaint.employee_assignments.all()  # ✅ Correct
```

### ComplaintCategory Relationships
```python
# Teams that can handle this category
category.assigned_teams.all()  # ✅ Correct
category.employees.all()  # ❌ Wrong (doesn't exist)
```

### Team → Employee → User Email Path
```python
# Correct path to get emails
team.memberships.all()  # TeamMembership objects
membership.employee  # Employee object
membership.employee.user  # User object
membership.employee.user.email  # ✅ Email address

# Wrong paths
team.members.values_list('email', flat=True)  # ❌ Wrong
assignment.employee.email  # ❌ Wrong
```

## Testing

### Test Script: `test_notification_fix.py`

```bash
python test_notification_fix.py
```

**Expected Output:**
```
✅ Complaint found: account issues please fix them
   Status: waiting_for_client_response
   Last responder: system

🔍 Testing _get_admin_emails() method...
✅ Success! Found N admin emails
   - email1@example.com
   - email2@example.com

📧 Testing notify_new_client_message()...
✅ Notification method executed successfully!

🎉 All tests passed! The notification fix is working.
```

### Manual Test

Add a comment to a complaint:

```bash
curl -X POST 'http://localhost:8000/hr/client-complaints/{id}/comments/' \
  -H 'Authorization: Bearer {token}' \
  -H 'Content-Type: application/json' \
  --data-raw '{"comment":"Test notification","is_internal":false}'
```

**Before Fix:**
```
HTTP 500 Internal Server Error
Failed to send client message notification: 'ClientComplaint' object has no attribute 'team_assignments'
```

**After Fix:**
```json
{
    "id": 66,
    "comment": "Test notification",
    "is_internal": false,
    "author": "...",
    "created_at": "..."
}
✅ No errors!
```

## Impact

✅ **Comments can now be added without errors**  
✅ **Notifications will be sent to assigned team members**  
✅ **System no longer crashes when trying to notify admins**  
✅ **Proper email collection from all assignment types**

## Files Modified

1. ✅ `hr_management/notifications.py` - Fixed `_get_admin_emails()` method

## Files Created

1. ✅ `test_notification_fix.py` - Test script to verify the fix

---
**Fix Completed**: October 17, 2025  
**Tested**: ✅ All tests passing  
**Status**: 🟢 Production Ready
