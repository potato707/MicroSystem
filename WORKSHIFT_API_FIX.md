# WorkShift API 404 Error Fix

## Problem
When trying to access WorkShift data, the frontend was getting a 404 error:
```
GET http://localhost:8000/hr/shifts/?employee_id=a3fdbfe5-14c2-4e15-acdf-7d9f453dc058&date=2025-10-06
404 Not Found
```

## Root Cause
URL pattern mismatch between frontend and backend:
- **Frontend API client**: Making requests to `/hr/shifts/`
- **Backend URL router**: WorkShiftViewSet was registered as `work-shifts`, creating endpoints at `/hr/work-shifts/`

## Solution
Updated the Django URL router registration in `/hr_management/urls.py`:
```python
# Before (incorrect)
router.register(r'work-shifts', WorkShiftViewSet, basename='work-shift')

# After (fixed)  
router.register(r'shifts', WorkShiftViewSet, basename='work-shift')
```

## Result
Now all WorkShift API endpoints are correctly available at:
- `GET /hr/shifts/` - List shifts (supports filtering by employee_id and date)
- `POST /hr/shifts/` - Create new shift
- `GET /hr/shifts/{id}/` - Get specific shift
- `PUT /hr/shifts/{id}/` - Update shift
- `DELETE /hr/shifts/{id}/` - Delete shift

## Frontend Integration
The WorkShiftDialog component can now:
1. Fetch existing shifts for an employee on a specific date
2. Create new shifts with detailed timings
3. Edit individual shift records
4. Delete unnecessary shifts

This resolves the attendance editing issue where admins couldn't manage multiple shifts for employees.