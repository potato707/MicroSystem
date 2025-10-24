# hr_management/management/commands/mark_absent_employees.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from hr_management.models import (
    Employee, WeeklyShiftSchedule, ShiftOverride, ShiftAttendance,
    get_employee_shift_for_date
)
from hr_management.notifications import NotificationService


class Command(BaseCommand):
    help = 'Mark employees as absent if they have not clocked in within 2 hours of shift start'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to check (YYYY-MM-DD format). Defaults to today.',
        )
        parser.add_argument(
            '--hours-threshold',
            type=int,
            default=2,
            help='Hours after shift start to mark as absent (default: 2)',
        )
        parser.add_argument(
            '--notify',
            action='store_true',
            help='Send notifications to managers',
        )

    def handle(self, *args, **options):
        # Get the date to check
        if options['date']:
            check_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            check_date = timezone.now().date()
        
        hours_threshold = options['hours_threshold']
        should_notify = options['notify']
        
        current_time = timezone.now().time()
        
        self.stdout.write(f"Checking for absent employees on {check_date}...")
        
        # Get the day of week (0=Sunday in our system)
        day_of_week = check_date.weekday()
        if day_of_week == 6:  # Python's weekday() returns 6 for Sunday
            day_of_week = 0
        else:
            day_of_week += 1
        
        # Get all employees scheduled for this day
        scheduled_shifts = WeeklyShiftSchedule.objects.filter(
            day_of_week=day_of_week,
            is_active=True
        ).select_related('employee')
        
        absent_count = 0
        skipped_count = 0
        already_marked_count = 0
        
        for shift_schedule in scheduled_shifts:
            employee = shift_schedule.employee
            
            # Check if employee has an override for this date
            try:
                override = ShiftOverride.objects.get(
                    employee=employee,
                    date=check_date,
                    status='approved'
                )
                
                # If override is day off, vacation, sick leave, or holiday, skip
                if override.override_type in ['day_off', 'vacation', 'sick_leave', 'holiday']:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping {employee.name} - {override.get_override_type_display()}"
                        )
                    )
                    skipped_count += 1
                    continue
                
                # If custom override, use override times
                shift_start = override.start_time
            except ShiftOverride.DoesNotExist:
                # Use regular weekly schedule
                shift_start = shift_schedule.start_time
            
            # Calculate threshold time (shift start + hours_threshold)
            threshold_datetime = datetime.combine(check_date, shift_start) + timedelta(hours=hours_threshold)
            threshold_time = threshold_datetime.time()
            
            # Only mark absent if current time is past threshold
            if current_time < threshold_time:
                continue
            
            # Check if attendance record exists
            try:
                attendance = ShiftAttendance.objects.get(
                    employee=employee,
                    date=check_date
                )
                
                # If already has actual start time (clocked in), skip
                if attendance.actual_start:
                    continue
                
                # If already marked as absent, skip
                if attendance.status == 'absent':
                    already_marked_count += 1
                    continue
                
            except ShiftAttendance.DoesNotExist:
                # Create attendance record
                shift = get_employee_shift_for_date(employee.id, check_date)
                if not shift:
                    continue
                
                attendance = ShiftAttendance.objects.create(
                    employee=employee,
                    date=check_date,
                    expected_start=shift['start_time'],
                    expected_end=shift['end_time']
                )
            
            # Mark as absent
            attendance.mark_absent(auto_marked=True)
            absent_count += 1
            
            self.stdout.write(
                self.style.ERROR(
                    f"Marked {employee.name} as ABSENT (shift started at {shift_start}, "
                    f"threshold: {threshold_time})"
                )
            )
            
            # Send notification to managers if enabled
            if should_notify:
                self._notify_managers(employee, check_date, shift_start)
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary for {check_date}:"
            )
        )
        self.stdout.write(f"  - Marked absent: {absent_count}")
        self.stdout.write(f"  - Already marked: {already_marked_count}")
        self.stdout.write(f"  - Skipped (override): {skipped_count}")
    
    def _notify_managers(self, employee, date, shift_start):
        """Send notification to department managers about absent employee"""
        # Get department managers
        if not employee.department:
            return
        
        # Assuming you have a way to get department managers
        # This is a placeholder - adjust based on your actual model structure
        managers = Employee.objects.filter(
            department=employee.department,
            user__groups__name='Manager'
        )
        
        for manager in managers:
            if manager.user:
                NotificationService.create_notification(
                    recipient=manager.user,
                    title=f"غياب موظف - {employee.name}",
                    message=f"الموظف {employee.name} غائب اليوم ({date}). موعد الدوام: {shift_start}",
                    notification_type='attendance_alert',
                    link=f'/dashboard/attendance?employee_id={employee.id}&date={date}'
                )
        
        self.stdout.write(
            self.style.WARNING(
                f"  -> Sent notifications to {managers.count()} managers"
            )
        )
