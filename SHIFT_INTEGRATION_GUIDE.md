# Shift Scheduling System - Integration Guide

## Quick Start Integration

Follow these steps to integrate the shift scheduling system into your Django project.

### Step 1: Add Models to hr_management/models.py

Copy the following code from `SHIFT_MODELS.py` and add to the end of your `hr_management/models.py`:

```python
# At the top, add these imports:
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import time, timedelta
from decimal import Decimal

# Then add the three models at the end of the file:
# - WeeklyShiftSchedule
# - ShiftOverride  
# - ShiftAttendance
# - Helper functions: get_employee_shift_for_date, get_employees_on_shift_now, calculate_weekly_hours
```

**Copy the entire content from SHIFT_MODELS.py** (lines 1-400) into hr_management/models.py

### Step 2: Add Serializers to hr_management/serializers.py

Copy the following from `SHIFT_SERIALIZERS.py` and add to the end of your `hr_management/serializers.py`:

```python
# Add all serializers:
# - WeeklyShiftScheduleSerializer
# - BulkWeeklyScheduleSerializer
# - ShiftOverrideSerializer
# - ShiftAttendanceSerializer
# - ClockInSerializer / ClockOutSerializer
# - EmployeeShiftSummarySerializer
# - CurrentShiftStatusSerializer
# - LateAbsentReportSerializer
```

**Copy the entire content from SHIFT_SERIALIZERS.py**

### Step 3: Add ViewSets to hr_management/views.py

Copy the following from `SHIFT_VIEWS.py` and add to the end of your `hr_management/views.py`:

```python
# Add the three main ViewSets:
# - WeeklyShiftScheduleViewSet (15 actions)
# - ShiftOverrideViewSet (7 actions)
# - ShiftAttendanceViewSet (10 actions)
```

**Copy the entire content from SHIFT_VIEWS.py**

### Step 4: Register URLs in hr_management/urls.py

Add the following to your router in `hr_management/urls.py`:

```python
from .views import (
    WeeklyShiftScheduleViewSet,
    ShiftOverrideViewSet,
    ShiftAttendanceViewSet,
)

# In your router registrations:
router.register(r'shifts/schedules', WeeklyShiftScheduleViewSet, basename='shift-schedule')
router.register(r'shifts/overrides', ShiftOverrideViewSet, basename='shift-override')
router.register(r'shifts/attendance', ShiftAttendanceViewSet, basename='shift-attendance')
```

See `SHIFT_URLS.py` for the complete list of available endpoints.

### Step 5: Create Management Command

Create the directory structure and command file:

```bash
mkdir -p hr_management/management/commands
touch hr_management/management/__init__.py
touch hr_management/management/commands/__init__.py
```

Then copy `SHIFT_MANAGEMENT_COMMAND.py` to `hr_management/management/commands/mark_absent_employees.py`

### Step 6: Create and Run Migrations

```bash
# Create migrations for the new models
python manage.py makemigrations hr_management

# Review the migration file to ensure it looks correct

# Apply migrations
python manage.py migrate hr_management
```

### Step 7: Set Up Cron Job for Auto-Absence Detection

Add to your system crontab (or use Django-cron, Celery Beat, etc.):

```bash
# Run every hour during business hours (8 AM - 6 PM)
0 8-18 * * * cd /path/to/project && python manage.py mark_absent_employees --notify
```

Or use Django-cron:

```python
# In hr_management/cron.py
from django_cron import CronJobBase, Schedule
from django.core.management import call_command

class MarkAbsentEmployeesCronJob(CronJobBase):
    RUN_EVERY_MINS = 60  # Run every hour
    
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'hr_management.mark_absent_employees'
    
    def do(self):
        call_command('mark_absent_employees', '--notify')
```

---

## Testing the Integration

### 1. Test Model Creation

```python
python manage.py shell

from hr_management.models import Employee, WeeklyShiftSchedule, ShiftOverride, ShiftAttendance
from datetime import time, date

# Get an employee
employee = Employee.objects.first()

# Create a weekly schedule
schedule = WeeklyShiftSchedule.objects.create(
    employee=employee,
    day_of_week=0,  # Sunday
    start_time=time(9, 0),
    end_time=time(17, 0),
    notes="Regular morning shift"
)

print(f"Created schedule: {schedule}")
print(f"Hours: {schedule.calculate_hours()}")
```

### 2. Test API Endpoints

```bash
# Get all schedules
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/hr/api/shifts/schedules/

# Create a schedule
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee": "EMPLOYEE_UUID",
    "day_of_week": 0,
    "start_time": "09:00",
    "end_time": "17:00"
  }' \
  http://localhost:8000/hr/api/shifts/schedules/

# Bulk create weekly schedule
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee": "EMPLOYEE_UUID",
    "schedules": [
      {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
      {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
      {"day_of_week": 2, "start_time": "09:00", "end_time": "17:00"},
      {"day_of_week": 3, "start_time": "09:00", "end_time": "17:00"},
      {"day_of_week": 4, "start_time": "09:00", "end_time": "13:00"}
    ]
  }' \
  http://localhost:8000/hr/api/shifts/schedules/bulk_create/

# Clock in
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee": "EMPLOYEE_UUID"
  }' \
  http://localhost:8000/hr/api/shifts/attendance/clock_in/

# Clock out
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee": "EMPLOYEE_UUID"
  }' \
  http://localhost:8000/hr/api/shifts/attendance/clock_out/

# Get current shift status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/hr/api/shifts/attendance/current_status/?employee_id=EMPLOYEE_UUID"

# Get daily late/absent report
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/hr/api/shifts/attendance/daily_report/?date=2024-01-15"
```

### 3. Test Management Command

```bash
# Test without notifications (dry run check)
python manage.py mark_absent_employees

# Test with notifications enabled
python manage.py mark_absent_employees --notify

# Test for a specific date
python manage.py mark_absent_employees --date 2024-01-15

# Custom threshold (3 hours instead of 2)
python manage.py mark_absent_employees --hours-threshold 3 --notify
```

---

## Database Schema

After migrations, you'll have these new tables:

### hr_management_weeklyshiftschedule
- `id` (UUID, PK)
- `employee_id` (FK to Employee)
- `day_of_week` (Integer, 0-6)
- `start_time` (Time)
- `end_time` (Time)
- `is_active` (Boolean)
- `notes` (Text)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- **UNIQUE**: (employee_id, day_of_week)
- **INDEX**: day_of_week, employee_id

### hr_management_shiftoverride
- `id` (UUID, PK)
- `employee_id` (FK to Employee)
- `date` (Date)
- `override_type` (CharField: custom/day_off/vacation/sick_leave/holiday)
- `start_time` (Time, nullable)
- `end_time` (Time, nullable)
- `reason` (Text)
- `status` (CharField: pending/approved/rejected)
- `requested_by_id` (FK to User)
- `approved_by_id` (FK to User, nullable)
- `approved_at` (DateTime, nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- **UNIQUE**: (employee_id, date)
- **INDEX**: date, employee_id, status

### hr_management_shiftattendance
- `id` (UUID, PK)
- `employee_id` (FK to Employee)
- `date` (Date)
- `expected_start` (Time)
- `expected_end` (Time)
- `actual_start` (Time, nullable)
- `actual_end` (Time, nullable)
- `status` (CharField: present/late/absent/half_day)
- `late_minutes` (Integer)
- `early_departure_minutes` (Integer)
- `overtime_minutes` (Integer)
- `total_hours` (Decimal)
- `auto_marked_absent` (Boolean)
- `requires_manager_approval` (Boolean)
- `approved_by_id` (FK to User, nullable)
- `notes` (Text)
- `created_at` (DateTime)
- `updated_at` (DateTime)
- **UNIQUE**: (employee_id, date)
- **INDEX**: date, employee_id, status

---

## Business Logic Summary

### Shift Resolution Priority
1. **ShiftOverride** (if exists for date)
2. **WeeklyShiftSchedule** (regular weekly schedule)
3. **None** (no shift scheduled)

### Late Detection
- Grace period: 15 minutes
- If clock_in > expected_start + 15 minutes → status = 'late'
- late_minutes = difference between clock_in and expected_start

### Absence Detection
- Runs via cron job every hour
- If (current_time > shift_start + 2 hours) AND no clock_in → mark absent
- Sets `auto_marked_absent = True`
- Sends notifications to department managers

### Hours Calculation
- Shifts > 6 hours → automatic 1-hour break deduction
- Overtime = hours worked beyond expected_end
- total_hours = (clock_out - clock_in) - break_time

### Approval Workflow
- Shift overrides start with status='pending'
- Managers can approve/reject
- Only approved overrides are considered in shift resolution

---

## Next Steps

After successful backend integration:

1. **Create Frontend Components** (See SHIFT_SCHEDULING_DESIGN.md for UI specs)
   - Weekly schedule editor
   - Override request form
   - Live monitoring dashboard
   - Attendance reports
   - Employee schedule view

2. **Add Permissions**
   - Define who can create/edit schedules
   - Define who can approve overrides
   - Define who can view attendance reports

3. **Integrate with Notifications**
   - Notify employees when schedule changes
   - Notify managers when override requests submitted
   - Notify managers of absent employees

4. **Add Excel Export**
   - Monthly attendance reports
   - Department schedules
   - Late/absent summaries

5. **Mobile Support**
   - QR code clock-in
   - Geolocation verification
   - Push notifications

---

## Troubleshooting

### Models not found
```bash
# Ensure models are imported in hr_management/models.py
# Check that you ran migrations
python manage.py makemigrations
python manage.py migrate
```

### ViewSets not found
```bash
# Ensure views are imported correctly in urls.py
from .views import WeeklyShiftScheduleViewSet, ShiftOverrideViewSet, ShiftAttendanceViewSet
```

### Clock in/out not working
- Check that employee has a schedule for the current day
- Check for approved overrides
- Verify timezone settings in Django settings.py

### Auto-absence not working
- Verify cron job is running
- Check management command exists in correct directory
- Test manually: `python manage.py mark_absent_employees --notify`

### Permissions errors
- Add IsAuthenticated permission class to ViewSets
- Create custom permission classes as needed

---

## Configuration Options

Add to your `settings.py`:

```python
# Shift scheduling settings
SHIFT_GRACE_PERIOD_MINUTES = 15  # Late detection grace period
SHIFT_ABSENCE_THRESHOLD_HOURS = 2  # Hours before marking absent
SHIFT_BREAK_THRESHOLD_HOURS = 6  # Shifts longer than this get break deduction
SHIFT_BREAK_DURATION_HOURS = 1  # Break duration to deduct
SHIFT_OVERTIME_ENABLED = True  # Track overtime
```

Then update the model methods to use these settings instead of hardcoded values.

---

## Support

For issues or questions:
1. Check SHIFT_SCHEDULING_DESIGN.md for detailed specifications
2. Review the API endpoint documentation in SHIFT_URLS.py
3. Test individual components using the test scripts above
4. Check Django logs for errors
