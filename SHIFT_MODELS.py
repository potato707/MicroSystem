# Add to hr_management/models.py

import uuid
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, time, date, timedelta


class WeeklyShiftSchedule(models.Model):
    """
    Permanent weekly schedule for employees - same hours repeat every week
    """
    DAYS_OF_WEEK = (
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'Employee', 
        on_delete=models.CASCADE, 
        related_name='weekly_shifts',
        verbose_name="الموظف"
    )
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="يوم الأسبوع"
    )
    start_time = models.TimeField(verbose_name="وقت البداية")
    end_time = models.TimeField(verbose_name="وقت النهاية")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "جدول دوام أسبوعي"
        verbose_name_plural = "جداول الدوام الأسبوعية"
        unique_together = ['employee', 'day_of_week']
        ordering = ['employee', 'day_of_week']
        indexes = [
            models.Index(fields=['employee', 'day_of_week']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        """Validate shift times"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("وقت النهاية يجب أن يكون بعد وقت البداية")
    
    def calculate_hours(self):
        """Calculate total hours for this shift"""
        if not self.start_time or not self.end_time:
            return 0
        
        # Convert to datetime for calculation
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        
        # Handle overnight shifts
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        
        hours = (end_dt - start_dt).total_seconds() / 3600
        
        # Deduct 1 hour break for shifts > 6 hours
        if hours > 6:
            hours -= 1
            
        return round(hours, 2)
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"


class ShiftOverride(models.Model):
    """
    Temporary changes to employee shifts for specific dates
    """
    OVERRIDE_TYPES = (
        ('custom', 'Custom Hours'),
        ('day_off', 'Day Off'),
        ('vacation', 'Vacation'),
        ('sick_leave', 'Sick Leave'),
        ('holiday', 'Public Holiday'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='shift_overrides',
        verbose_name="الموظف"
    )
    date = models.DateField(verbose_name="التاريخ")
    override_type = models.CharField(
        max_length=20,
        choices=OVERRIDE_TYPES,
        verbose_name="نوع الاستثناء"
    )
    start_time = models.TimeField(null=True, blank=True, verbose_name="وقت البداية")
    end_time = models.TimeField(null=True, blank=True, verbose_name="وقت النهاية")
    reason = models.TextField(verbose_name="السبب")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="الحالة"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shift_override_requests',
        verbose_name="طلب بواسطة"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_shift_overrides',
        verbose_name="وافق عليه"
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "استثناء دوام"
        verbose_name_plural = "استثناءات الدوام"
        unique_together = ['employee', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['status']),
        ]
    
    def clean(self):
        """Validate override"""
        if self.override_type == 'custom':
            if not self.start_time or not self.end_time:
                raise ValidationError("Custom shifts require start and end times")
            if self.start_time >= self.end_time:
                raise ValidationError("End time must be after start time")
        elif self.override_type in ['day_off', 'vacation', 'sick_leave', 'holiday']:
            # These should not have times
            self.start_time = None
            self.end_time = None
    
    def approve(self, approved_by_user):
        """Approve this override"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, approved_by_user):
        """Reject this override"""
        self.status = 'rejected'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.get_override_type_display()})"


class ShiftAttendance(models.Model):
    """
    Daily attendance tracking with automatic late/absent detection
    """
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('present', 'Present'),
        ('late', 'Late'),
        ('absent', 'Absent'),
        ('early_departure', 'Early Departure'),
        ('overtime', 'Overtime'),
        ('day_off', 'Day Off'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        related_name='shift_attendances',
        verbose_name="الموظف"
    )
    date = models.DateField(verbose_name="التاريخ")
    
    # Expected times (from schedule or override)
    expected_start = models.TimeField(null=True, blank=True, verbose_name="وقت البداية المتوقع")
    expected_end = models.TimeField(null=True, blank=True, verbose_name="وقت النهاية المتوقع")
    
    # Actual times (clock in/out)
    actual_start = models.TimeField(null=True, blank=True, verbose_name="وقت البداية الفعلي")
    actual_end = models.TimeField(null=True, blank=True, verbose_name="وقت النهاية الفعلي")
    
    # Calculated fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name="الحالة"
    )
    late_minutes = models.IntegerField(default=0, verbose_name="دقائق التأخير")
    early_departure_minutes = models.IntegerField(default=0, verbose_name="دقائق المغادرة المبكرة")
    overtime_minutes = models.IntegerField(default=0, verbose_name="دقائق الوقت الإضافي")
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="مجموع الساعات"
    )
    
    # System flags
    auto_marked_absent = models.BooleanField(default=False, verbose_name="تم وضع علامة غائب تلقائياً")
    requires_manager_approval = models.BooleanField(default=False, verbose_name="يتطلب موافقة المدير")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_attendances',
        verbose_name="وافق عليه"
    )
    
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "حضور دوام"
        verbose_name_plural = "سجل الحضور"
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee']
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['auto_marked_absent']),
        ]
    
    def clock_in(self, clock_in_time=None):
        """
        Record clock in and calculate if late
        """
        if clock_in_time is None:
            clock_in_time = timezone.now().time()
        
        self.actual_start = clock_in_time
        
        if self.expected_start:
            # Calculate late minutes
            expected_dt = datetime.combine(date.today(), self.expected_start)
            actual_dt = datetime.combine(date.today(), clock_in_time)
            
            grace_period = timedelta(minutes=15)  # 15 minute grace period
            
            if actual_dt > expected_dt + grace_period:
                self.late_minutes = int((actual_dt - expected_dt).total_seconds() / 60)
                self.status = 'late'
            else:
                self.late_minutes = 0
                self.status = 'present'
        else:
            self.status = 'present'
        
        self.auto_marked_absent = False
        self.save()
    
    def clock_out(self, clock_out_time=None):
        """
        Record clock out and calculate total hours, overtime, early departure
        """
        if clock_out_time is None:
            clock_out_time = timezone.now().time()
        
        self.actual_end = clock_out_time
        
        if self.actual_start:
            # Calculate total hours
            start_dt = datetime.combine(date.today(), self.actual_start)
            end_dt = datetime.combine(date.today(), clock_out_time)
            
            # Handle overnight shifts
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            hours = (end_dt - start_dt).total_seconds() / 3600
            
            # Deduct 1 hour break for shifts > 6 hours
            if hours > 6:
                hours -= 1
            
            self.total_hours = round(hours, 2)
            
            # Check for early departure or overtime
            if self.expected_end:
                expected_end_dt = datetime.combine(date.today(), self.expected_end)
                
                if end_dt < expected_end_dt - timedelta(minutes=15):
                    self.early_departure_minutes = int((expected_end_dt - end_dt).total_seconds() / 60)
                    if self.status == 'present':
                        self.status = 'early_departure'
                elif end_dt > expected_end_dt + timedelta(minutes=30):
                    self.overtime_minutes = int((end_dt - expected_end_dt).total_seconds() / 60)
                    if self.status == 'present':
                        self.status = 'overtime'
        
        self.save()
    
    def mark_absent(self, auto=False):
        """Mark employee as absent"""
        self.status = 'absent'
        self.auto_marked_absent = auto
        self.save()
    
    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.get_status_display()})"


# Helper functions to add to the Employee model or as utility functions

def get_employee_shift_for_date(employee, target_date):
    """
    Get the effective shift for an employee on a specific date
    Checks overrides first, then falls back to weekly schedule
    """
    from hr_management.models import ShiftOverride, WeeklyShiftSchedule
    
    # Check for approved override
    try:
        override = ShiftOverride.objects.get(
            employee=employee,
            date=target_date,
            status='approved'
        )
        
        if override.override_type in ['day_off', 'vacation', 'sick_leave', 'holiday']:
            return None  # No shift
        elif override.override_type == 'custom':
            return {
                'start_time': override.start_time,
                'end_time': override.end_time,
                'is_override': True,
                'override_type': override.get_override_type_display()
            }
    except ShiftOverride.DoesNotExist:
        pass
    
    # Check weekly schedule
    day_of_week = target_date.weekday()
    # Convert Python weekday (0=Monday) to our system (0=Sunday)
    day_of_week = (day_of_week + 1) % 7
    
    try:
        schedule = WeeklyShiftSchedule.objects.get(
            employee=employee,
            day_of_week=day_of_week,
            is_active=True
        )
        return {
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'is_override': False
        }
    except WeeklyShiftSchedule.DoesNotExist:
        return None  # No shift scheduled


def get_employees_on_shift_now():
    """
    Get list of employees who should currently be on shift
    """
    from hr_management.models import Employee
    from django.utils import timezone
    
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    on_shift = []
    
    for employee in Employee.objects.filter(is_active=True):
        shift = get_employee_shift_for_date(employee, current_date)
        
        if shift and shift['start_time'] <= current_time <= shift['end_time']:
            on_shift.append({
                'employee': employee,
                'start_time': shift['start_time'],
                'end_time': shift['end_time'],
                'is_override': shift.get('is_override', False)
            })
    
    return on_shift


def calculate_weekly_hours(employee):
    """
    Calculate total weekly hours for an employee based on their schedule
    """
    from hr_management.models import WeeklyShiftSchedule
    
    schedules = WeeklyShiftSchedule.objects.filter(
        employee=employee,
        is_active=True
    )
    
    total_hours = sum(schedule.calculate_hours() for schedule in schedules)
    return round(total_hours, 2)
