# Fixed Weekly Shift Scheduling System - Design Document

## Overview
A comprehensive shift scheduling system where each employee has one permanent weekly schedule that repeats automatically unless overridden.

## Database Models

### 1. WeeklyShiftSchedule
Stores the default weekly schedule for each employee (repeats every week).

**Fields:**
- `id` (UUID) - Primary key
- `employee` (FK) - Reference to Employee
- `day_of_week` (Integer) - 0=Sunday, 1=Monday, ..., 6=Saturday
- `start_time` (Time) - Shift start time
- `end_time` (Time) - Shift end time
- `is_active` (Boolean) - Whether this shift is currently active
- `notes` (Text) - Optional notes about this shift
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Constraints:**
- Unique together: (employee, day_of_week)
- Validation: end_time must be after start_time

### 2. ShiftOverride
Temporary changes to an employee's shift for specific dates.

**Fields:**
- `id` (UUID) - Primary key
- `employee` (FK) - Reference to Employee
- `date` (Date) - Specific date for override
- `override_type` (Choice) - 'custom', 'day_off', 'vacation', 'sick_leave'
- `start_time` (Time, nullable) - New start time (null for day off)
- `end_time` (Time, nullable) - New end time (null for day off)
- `reason` (Text) - Reason for override
- `approved_by` (FK User) - Admin who approved
- `created_at` (DateTime)

**Constraints:**
- Unique together: (employee, date)

### 3. ShiftAttendance
Actual clock-in/clock-out records for tracking attendance.

**Fields:**
- `id` (UUID) - Primary key
- `employee` (FK) - Reference to Employee
- `date` (Date) - Attendance date
- `expected_start` (Time) - Expected shift start
- `expected_end` (Time) - Expected shift end
- `actual_start` (Time, nullable) - Actual clock-in time
- `actual_end` (Time, nullable) - Actual clock-out time
- `status` (Choice) - 'present', 'late', 'absent', 'early_departure', 'overtime'
- `late_minutes` (Integer) - Minutes late
- `total_hours` (Decimal) - Total hours worked
- `notes` (Text) - Notes about attendance
- `auto_marked_absent` (Boolean) - Whether system marked as absent
- `created_at` (DateTime)
- `updated_at` (DateTime)

**Constraints:**
- Unique together: (employee, date)

## API Endpoints

### Weekly Schedule Management
- `GET /api/shifts/weekly-schedules/` - List all schedules
- `GET /api/shifts/weekly-schedules/?employee=<id>` - Get employee's schedule
- `POST /api/shifts/weekly-schedules/` - Create schedule entry
- `PUT /api/shifts/weekly-schedules/<id>/` - Update schedule entry
- `DELETE /api/shifts/weekly-schedules/<id>/` - Delete schedule entry
- `POST /api/shifts/weekly-schedules/bulk-create/` - Create full week for employee

### Shift Overrides
- `GET /api/shifts/overrides/` - List overrides
- `GET /api/shifts/overrides/?employee=<id>&month=<YYYY-MM>` - Get employee overrides
- `POST /api/shifts/overrides/` - Create override
- `PUT /api/shifts/overrides/<id>/` - Update override
- `DELETE /api/shifts/overrides/<id>/` - Delete override

### Attendance Tracking
- `GET /api/shifts/attendance/` - List attendance records
- `POST /api/shifts/attendance/clock-in/` - Clock in
- `POST /api/shifts/attendance/clock-out/` - Clock out
- `GET /api/shifts/attendance/current-shift/` - Check if on shift
- `POST /api/shifts/attendance/mark-absent/` - Manually mark absent

### Reports & Analytics
- `GET /api/shifts/reports/employee-summary/` - Weekly hours summary per employee
- `GET /api/shifts/reports/current-employees/` - Who's currently on shift
- `GET /api/shifts/reports/late-absent/` - Late/absent employees today
- `GET /api/shifts/reports/monthly-summary/` - Monthly attendance summary
- `GET /api/shifts/reports/employee-details/?employee=<id>&month=<YYYY-MM>` - Detailed employee report

## Business Logic

### Shift Resolution
For any given date, the system determines the expected shift:
1. Check for ShiftOverride on that date → Use override
2. If no override → Use WeeklyShiftSchedule for that day of week
3. If no weekly schedule → Employee has day off

### Automatic Absence Detection
- Cron job runs every hour during business hours
- For each employee with a shift today:
  - If current_time > expected_start + grace_period (15 min)
  - AND no clock-in recorded
  - → Mark as absent automatically

### Late Detection
- When employee clocks in:
  - Calculate: late_minutes = actual_start - expected_start
  - If late_minutes > grace_period → status = 'late'
  - Otherwise → status = 'present'

### Total Hours Calculation
```python
if actual_start and actual_end:
    total_hours = (actual_end - actual_start).total_seconds() / 3600
    
    # Handle breaks (1 hour unpaid break for shifts > 6 hours)
    if total_hours > 6:
        total_hours -= 1
```

### Overtime Detection
- If actual_end > expected_end + 30 minutes → status = 'overtime'
- Calculate overtime_hours for payroll

## Frontend Components

### 1. Weekly Schedule Editor (`/dashboard/shifts/schedules`)
- Calendar view showing employee's weekly schedule
- Edit mode: Click day to set hours
- Bulk actions: Copy week, reset to default
- Visual indicators: Active shifts, total weekly hours

### 2. Shift Override Manager (`/dashboard/shifts/overrides`)
- Calendar picker for selecting date
- Form: Override type, custom hours, reason
- List view: Upcoming overrides with edit/delete
- Filter by employee, date range

### 3. Live Shift Monitor (`/dashboard/shifts/monitor`)
- Real-time dashboard showing:
  - Currently on shift (green)
  - Late employees (yellow)
  - Absent employees (red)
  - Expected soon (blue)
- Auto-refresh every 30 seconds

### 4. Attendance Reports (`/dashboard/shifts/reports`)
- **Summary Cards:**
  - Total employees scheduled today
  - Present / Late / Absent counts
  - Average hours worked this week
  
- **Employee Table:**
  - Employee name, expected shift, actual times, status, hours
  - Filter by status, department, date range
  - Export to Excel

- **Monthly View:**
  - Calendar grid with color-coded attendance
  - Click day → See detailed records
  - Summary: Total hours, attendance rate, late count

### 5. Individual Employee Schedule (`/dashboard/employees/<id>/schedule`)
- Weekly schedule overview
- Upcoming overrides
- Attendance history (last 30 days)
- Edit weekly schedule button (admin only)

## User Permissions

### Admin
- ✅ Create/edit/delete weekly schedules
- ✅ Create/approve overrides
- ✅ View all reports
- ✅ Manually mark attendance
- ✅ Export reports

### Manager
- ✅ View team schedules
- ✅ Request overrides (requires approval)
- ✅ View team reports
- ❌ Edit weekly schedules

### Employee
- ✅ View own schedule
- ✅ Request overrides
- ✅ Clock in/out
- ✅ View own attendance
- ❌ View others' schedules

## Notifications

### Automatic Notifications
1. **Shift Reminder** - 30 min before shift starts
2. **Late Alert** - To manager when employee is 15+ min late
3. **Absence Alert** - To manager when employee marked absent
4. **Override Approved** - To employee when override approved
5. **Schedule Changed** - To employee when weekly schedule updated

## Sample User Flows

### Flow 1: Admin Sets Up Employee Schedule
1. Navigate to `/dashboard/shifts/schedules`
2. Select employee from dropdown
3. Click "Create Weekly Schedule"
4. For each day:
   - Toggle "Working" switch
   - Set start/end times
5. Click "Save Schedule"
6. System validates times and saves
7. Employee receives notification of new schedule

### Flow 2: Employee Requests Day Off
1. Navigate to `/dashboard/shifts/my-schedule`
2. Click date on calendar
3. Select "Day Off" override type
4. Enter reason
5. Submit request
6. Manager receives notification
7. Manager approves/denies
8. Employee receives notification of decision

### Flow 3: Auto Absence Detection
1. Cron job runs at 9:15 AM
2. Query: Employees with shift starting at 9:00 AM
3. Filter: Those without clock-in record
4. For each:
   - Create ShiftAttendance with status='absent'
   - Send notification to manager
   - Log event

### Flow 4: Generate Monthly Report
1. Admin navigates to `/dashboard/shifts/reports`
2. Select month: October 2025
3. System calculates:
   - Total days worked per employee
   - Total hours worked
   - Late days count
   - Absent days count
   - Attendance rate %
4. Display table with export button
5. Click "Export" → Download Excel file

## Implementation Priority

### Phase 1: Core Models & Basic CRUD
- ✅ Create models with migrations
- ✅ Basic serializers and viewsets
- ✅ Admin panel configuration

### Phase 2: Shift Resolution Logic
- ✅ Get effective shift for date
- ✅ Validate shift times
- ✅ Handle overrides

### Phase 3: Attendance Tracking
- ✅ Clock in/out endpoints
- ✅ Late detection
- ✅ Auto absence marking (cron)

### Phase 4: Frontend UI
- ✅ Weekly schedule editor
- ✅ Live shift monitor
- ✅ Basic reports

### Phase 5: Advanced Features
- ✅ Excel export
- ✅ Notifications integration
- ✅ Mobile clock in/out
- ✅ Geolocation verification

## Technical Considerations

### Performance
- Index on (employee, date) for quick lookups
- Cache current shift status (Redis)
- Paginate report results

### Data Integrity
- Prevent overlapping shifts for same employee
- Validate time ranges (start < end)
- Prevent backdated clock-ins (configurable)

### Timezone Handling
- Store all times in UTC
- Display in user's timezone
- Handle DST transitions

### Audit Trail
- Log all schedule changes
- Track who approved overrides
- Record attendance modifications

---

**Status**: Design Complete - Ready for Implementation
**Date**: October 17, 2025
