# Add to hr_management/serializers.py

from rest_framework import serializers
from .models import WeeklyShiftSchedule, ShiftOverride, ShiftAttendance, Employee
from django.utils import timezone
from datetime import datetime, date


class WeeklyShiftScheduleSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    hours = serializers.SerializerMethodField()
    
    class Meta:
        model = WeeklyShiftSchedule
        fields = [
            'id', 'employee', 'employee_name', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'is_active', 'hours', 'notes',
            'created_at', 'updated_at'
        ]
    
    def get_hours(self, obj):
        return obj.calculate_hours()
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError({
                'end_time': 'End time must be after start time'
            })
        return data


class BulkWeeklyScheduleSerializer(serializers.Serializer):
    """
    Create a full week schedule for an employee at once
    """
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    schedules = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of {day_of_week, start_time, end_time, notes}"
    )
    
    def create(self, validated_data):
        employee = validated_data['employee']
        schedules_data = validated_data['schedules']
        
        created_schedules = []
        for schedule_data in schedules_data:
            schedule, created = WeeklyShiftSchedule.objects.update_or_create(
                employee=employee,
                day_of_week=schedule_data['day_of_week'],
                defaults={
                    'start_time': schedule_data['start_time'],
                    'end_time': schedule_data['end_time'],
                    'notes': schedule_data.get('notes', ''),
                    'is_active': schedule_data.get('is_active', True)
                }
            )
            created_schedules.append(schedule)
        
        return created_schedules


class ShiftOverrideSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    override_type_display = serializers.CharField(source='get_override_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ShiftOverride
        fields = [
            'id', 'employee', 'employee_name', 'date', 'override_type', 'override_type_display',
            'start_time', 'end_time', 'reason', 'status', 'status_display',
            'requested_by', 'requested_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['approved_by', 'approved_at', 'requested_by']
    
    def validate(self, data):
        override_type = data.get('override_type')
        
        if override_type == 'custom':
            if not data.get('start_time') or not data.get('end_time'):
                raise serializers.ValidationError({
                    'start_time': 'Custom shifts require start and end times'
                })
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
        elif override_type in ['day_off', 'vacation', 'sick_leave', 'holiday']:
            # Clear times for non-custom overrides
            data['start_time'] = None
            data['end_time'] = None
        
        return data


class ShiftAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_department = serializers.CharField(source='employee.department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = ShiftAttendance
        fields = [
            'id', 'employee', 'employee_name', 'employee_department', 'date',
            'expected_start', 'expected_end', 'actual_start', 'actual_end',
            'status', 'status_display', 'late_minutes', 'early_departure_minutes',
            'overtime_minutes', 'total_hours', 'auto_marked_absent',
            'requires_manager_approval', 'approved_by', 'approved_by_name',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'status', 'late_minutes', 'early_departure_minutes', 'overtime_minutes',
            'total_hours', 'auto_marked_absent', 'approved_by'
        ]


class ClockInSerializer(serializers.Serializer):
    """
    Clock in for the current shift
    """
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    clock_in_time = serializers.TimeField(required=False, help_text="Leave empty for current time")
    notes = serializers.CharField(required=False, allow_blank=True)


class ClockOutSerializer(serializers.Serializer):
    """
    Clock out from the current shift
    """
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    clock_out_time = serializers.TimeField(required=False, help_text="Leave empty for current time")
    notes = serializers.CharField(required=False, allow_blank=True)


class EmployeeShiftSummarySerializer(serializers.Serializer):
    """
    Summary of employee's shifts and attendance
    """
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    department = serializers.CharField()
    weekly_hours = serializers.DecimalField(max_digits=5, decimal_places=2)
    days_present = serializers.IntegerField()
    days_late = serializers.IntegerField()
    days_absent = serializers.IntegerField()
    total_hours_worked = serializers.DecimalField(max_digits=6, decimal_places=2)
    attendance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class CurrentShiftStatusSerializer(serializers.Serializer):
    """
    Current shift status for an employee
    """
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    is_on_shift = serializers.BooleanField()
    shift_start = serializers.TimeField(required=False, allow_null=True)
    shift_end = serializers.TimeField(required=False, allow_null=True)
    has_clocked_in = serializers.BooleanField()
    clock_in_time = serializers.TimeField(required=False, allow_null=True)
    status = serializers.CharField()
    late_minutes = serializers.IntegerField()


class LateAbsentReportSerializer(serializers.Serializer):
    """
    Report of late and absent employees for a specific date
    """
    date = serializers.DateField()
    total_scheduled = serializers.IntegerField()
    present = serializers.IntegerField()
    late = serializers.IntegerField()
    absent = serializers.IntegerField()
    employees = ShiftAttendanceSerializer(many=True)
