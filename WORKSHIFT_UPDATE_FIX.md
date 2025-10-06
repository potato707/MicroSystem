# WorkShift Update API Test

## Issue Fixed
The WorkShift PUT request was failing with:
```json
{"attendance":["هذا الحقل مطلوب."]}
```

## Root Cause
The WorkShift model requires an `attendance` field (ForeignKey to EmployeeAttendance), but the frontend wasn't sending this field in update requests.

## Solution
Added `perform_update` method to WorkShiftViewSet that automatically handles the attendance field:

```python
def perform_update(self, serializer):
    user = self.request.user
    
    # Get employee (from request or existing instance)
    if user.role != 'admin' and hasattr(user, 'employee'):
        employee = user.employee
    else:
        employee_id = self.request.data.get('employee')
        if employee_id:
            employee = get_object_or_404(Employee, id=employee_id)
        else:
            employee = serializer.instance.employee
    
    # Auto-create attendance record if needed
    shift_date = serializer.validated_data['check_in'].date()
    attendance, created = EmployeeAttendance.objects.get_or_create(
        employee=employee,
        date=shift_date,
        defaults={'status': 'present'}
    )
    
    serializer.save(employee=employee, attendance=attendance)
```

## Test Request
```http
PUT http://localhost:8000/hr/shifts/9d2f0217-4403-45e9-8f41-d8dc111ef992/
{
  "employee": "e70fe696-8c4a-4f73-83a0-64c66429caab",
  "shift_type": "regular", 
  "check_in": "2025-10-06T07:00:00.000Z",
  "check_out": "2025-10-06T14:00:00.000Z",
  "break_start": null,
  "break_end": null,
  "location": "",
  "notes": "",
  "status": "present",
  "is_paid_leave": true
}
```

## Expected Result
✅ 200 OK - WorkShift updated successfully
✅ Attendance record automatically created/updated
✅ Frontend WorkShiftDialog can now edit shifts properly

## Benefits
- Frontend no longer needs to manage attendance field
- Automatic attendance record management
- Consistent behavior between create and update operations
- Proper admin/employee permission handling