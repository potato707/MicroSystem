# Add to hr_management/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WeeklyShiftScheduleViewSet,
    ShiftOverrideViewSet,
    ShiftAttendanceViewSet,
    # ... your other viewsets
)

# Create router
router = DefaultRouter()

# ... your existing router registrations ...

# Register shift management endpoints
router.register(r'shifts/schedules', WeeklyShiftScheduleViewSet, basename='shift-schedule')
router.register(r'shifts/overrides', ShiftOverrideViewSet, basename='shift-override')
router.register(r'shifts/attendance', ShiftAttendanceViewSet, basename='shift-attendance')

urlpatterns = [
    path('', include(router.urls)),
    # ... your other URL patterns ...
]

"""
Available Shift Management API Endpoints:

Weekly Schedules:
- GET    /hr/api/shifts/schedules/                      - List all schedules
- POST   /hr/api/shifts/schedules/                      - Create schedule
- GET    /hr/api/shifts/schedules/<id>/                 - Get schedule detail
- PUT    /hr/api/shifts/schedules/<id>/                 - Update schedule
- DELETE /hr/api/shifts/schedules/<id>/                 - Delete schedule
- POST   /hr/api/shifts/schedules/bulk_create/          - Create full week schedule
- GET    /hr/api/shifts/schedules/employee_schedule/    - Get employee's full week
  ?employee_id=<uuid>
- GET    /hr/api/shifts/schedules/department_schedules/ - Get department schedules
  ?department_id=<uuid>&day_of_week=0

Shift Overrides:
- GET    /hr/api/shifts/overrides/                      - List all overrides
- POST   /hr/api/shifts/overrides/                      - Create override
- GET    /hr/api/shifts/overrides/<id>/                 - Get override detail
- PUT    /hr/api/shifts/overrides/<id>/                 - Update override
- DELETE /hr/api/shifts/overrides/<id>/                 - Delete override
- POST   /hr/api/shifts/overrides/<id>/approve/         - Approve override
- POST   /hr/api/shifts/overrides/<id>/reject/          - Reject override
- GET    /hr/api/shifts/overrides/pending/              - Get pending requests
- POST   /hr/api/shifts/overrides/bulk_create_vacation/ - Create multi-day vacation
  Body: {employee, start_date, end_date, reason}

Attendance:
- GET    /hr/api/shifts/attendance/                     - List attendance records
- POST   /hr/api/shifts/attendance/                     - Create attendance record
- GET    /hr/api/shifts/attendance/<id>/                - Get attendance detail
- PUT    /hr/api/shifts/attendance/<id>/                - Update attendance
- DELETE /hr/api/shifts/attendance/<id>/                - Delete attendance
- POST   /hr/api/shifts/attendance/clock_in/            - Clock in for shift
  Body: {employee, clock_in_time (optional), notes (optional)}
- POST   /hr/api/shifts/attendance/clock_out/           - Clock out from shift
  Body: {employee, clock_out_time (optional), notes (optional)}
- GET    /hr/api/shifts/attendance/current_status/      - Get current shift status
  ?employee_id=<uuid> (optional - returns all if not provided)
- GET    /hr/api/shifts/attendance/daily_report/        - Late/absent report
  ?date=2024-01-15
- GET    /hr/api/shifts/attendance/employee_summary/    - Employee attendance summary
  ?employee_id=<uuid>&start_date=2024-01-01&end_date=2024-01-31

Query Parameters (where applicable):
- employee_id=<uuid>      - Filter by employee
- department_id=<uuid>    - Filter by department
- date=YYYY-MM-DD         - Filter by date
- start_date=YYYY-MM-DD   - Filter by date range start
- end_date=YYYY-MM-DD     - Filter by date range end
- day_of_week=0-6         - Filter by day (0=Sunday, 6=Saturday)
- status=pending/approved/rejected - Filter by status
- override_type=custom/day_off/vacation/sick_leave/holiday
"""
