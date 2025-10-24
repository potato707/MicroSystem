# Add to hr_management/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, date, timedelta, time
from decimal import Decimal

from .models import (
    WeeklyShiftSchedule, ShiftOverride, ShiftAttendance, Employee,
    get_employee_shift_for_date, get_employees_on_shift_now, calculate_weekly_hours
)
from .serializers import (
    WeeklyShiftScheduleSerializer, BulkWeeklyScheduleSerializer,
    ShiftOverrideSerializer, ShiftAttendanceSerializer,
    ClockInSerializer, ClockOutSerializer, EmployeeShiftSummarySerializer,
    CurrentShiftStatusSerializer, LateAbsentReportSerializer
)


class WeeklyShiftScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing weekly shift schedules
    """
    queryset = WeeklyShiftSchedule.objects.all()
    serializer_class = WeeklyShiftScheduleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'day_of_week', 'is_active']
    search_fields = ['employee__name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by employee if specified
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by department
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        
        return queryset.select_related('employee', 'employee__department')
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create a full week schedule for an employee
        POST /api/shifts/schedules/bulk_create/
        Body: {
            "employee": "employee-uuid",
            "schedules": [
                {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
                {"day_of_week": 1, "start_time": "09:00", "end_time": "17:00"},
                ...
            ]
        }
        """
        serializer = BulkWeeklyScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedules = serializer.save()
        
        output_serializer = WeeklyShiftScheduleSerializer(schedules, many=True)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def employee_schedule(self, request):
        """
        Get the full week schedule for an employee
        GET /api/shifts/schedules/employee_schedule/?employee_id=<uuid>
        """
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {'error': 'employee_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        schedules = WeeklyShiftSchedule.objects.filter(
            employee_id=employee_id,
            is_active=True
        ).order_by('day_of_week')
        
        serializer = self.get_serializer(schedules, many=True)
        total_hours = calculate_weekly_hours(employee_id)
        
        return Response({
            'schedules': serializer.data,
            'total_weekly_hours': total_hours
        })
    
    @action(detail=False, methods=['get'])
    def department_schedules(self, request):
        """
        Get all schedules for a department
        GET /api/shifts/schedules/department_schedules/?department_id=<uuid>&day_of_week=0
        """
        department_id = request.query_params.get('department_id')
        day_of_week = request.query_params.get('day_of_week')
        
        if not department_id:
            return Response(
                {'error': 'department_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = WeeklyShiftSchedule.objects.filter(
            employee__department_id=department_id,
            is_active=True
        )
        
        if day_of_week is not None:
            queryset = queryset.filter(day_of_week=int(day_of_week))
        
        schedules = queryset.select_related('employee').order_by('day_of_week', 'start_time')
        serializer = self.get_serializer(schedules, many=True)
        
        return Response(serializer.data)


class ShiftOverrideViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shift overrides (vacations, day offs, custom shifts)
    """
    queryset = ShiftOverride.objects.all()
    serializer_class = ShiftOverrideSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'date', 'override_type', 'status']
    search_fields = ['employee__name', 'reason']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        return queryset.select_related('employee', 'requested_by', 'approved_by')
    
    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a shift override request
        POST /api/shifts/overrides/<id>/approve/
        """
        override = self.get_object()
        override.approve(request.user)
        
        serializer = self.get_serializer(override)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a shift override request
        POST /api/shifts/overrides/<id>/reject/
        """
        override = self.get_object()
        override.reject(request.user)
        
        serializer = self.get_serializer(override)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get all pending override requests
        GET /api/shifts/overrides/pending/
        """
        pending_overrides = self.get_queryset().filter(status='pending').order_by('date')
        serializer = self.get_serializer(pending_overrides, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_create_vacation(self, request):
        """
        Create vacation override for multiple days
        POST /api/shifts/overrides/bulk_create_vacation/
        Body: {
            "employee": "employee-uuid",
            "start_date": "2024-01-01",
            "end_date": "2024-01-05",
            "reason": "Annual vacation"
        }
        """
        employee_id = request.data.get('employee')
        start_date = datetime.strptime(request.data.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.data.get('end_date'), '%Y-%m-%d').date()
        reason = request.data.get('reason', '')
        
        if not employee_id or not start_date or not end_date:
            return Response(
                {'error': 'employee, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        employee = Employee.objects.get(id=employee_id)
        created_overrides = []
        
        current_date = start_date
        while current_date <= end_date:
            override, created = ShiftOverride.objects.get_or_create(
                employee=employee,
                date=current_date,
                defaults={
                    'override_type': 'vacation',
                    'reason': reason,
                    'requested_by': request.user,
                    'status': 'pending'
                }
            )
            created_overrides.append(override)
            current_date += timedelta(days=1)
        
        serializer = self.get_serializer(created_overrides, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ShiftAttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shift attendance records
    """
    queryset = ShiftAttendance.objects.all()
    serializer_class = ShiftAttendanceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['employee', 'date', 'status']
    search_fields = ['employee__name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by department
        department_id = self.request.query_params.get('department_id')
        if department_id:
            queryset = queryset.filter(employee__department_id=department_id)
        
        return queryset.select_related('employee', 'employee__department', 'approved_by')
    
    @action(detail=False, methods=['post'])
    def clock_in(self, request):
        """
        Clock in for current shift
        POST /api/shifts/attendance/clock_in/
        Body: {
            "employee": "employee-uuid",
            "clock_in_time": "09:15" (optional, uses current time if not provided)
        }
        """
        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee = serializer.validated_data['employee']
        clock_in_time = serializer.validated_data.get('clock_in_time') or timezone.now().time()
        notes = serializer.validated_data.get('notes', '')
        
        today = timezone.now().date()
        
        # Get expected shift
        shift = get_employee_shift_for_date(employee.id, today)
        if not shift:
            return Response(
                {'error': f'No shift scheduled for {employee.name} today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or get attendance record
        attendance, created = ShiftAttendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={
                'expected_start': shift['start_time'],
                'expected_end': shift['end_time']
            }
        )
        
        # Clock in
        try:
            attendance.clock_in(clock_in_time)
            if notes:
                attendance.notes = notes
                attendance.save()
            
            output_serializer = ShiftAttendanceSerializer(attendance)
            return Response(output_serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def clock_out(self, request):
        """
        Clock out from current shift
        POST /api/shifts/attendance/clock_out/
        Body: {
            "employee": "employee-uuid",
            "clock_out_time": "17:30" (optional)
        }
        """
        serializer = ClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        employee = serializer.validated_data['employee']
        clock_out_time = serializer.validated_data.get('clock_out_time') or timezone.now().time()
        notes = serializer.validated_data.get('notes', '')
        
        today = timezone.now().date()
        
        try:
            attendance = ShiftAttendance.objects.get(employee=employee, date=today)
        except ShiftAttendance.DoesNotExist:
            return Response(
                {'error': 'No attendance record found. Please clock in first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            attendance.clock_out(clock_out_time)
            if notes:
                attendance.notes = notes
                attendance.save()
            
            output_serializer = ShiftAttendanceSerializer(attendance)
            return Response(output_serializer.data)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def current_status(self, request):
        """
        Get current shift status for all employees or specific employee
        GET /api/shifts/attendance/current_status/?employee_id=<uuid>
        """
        employee_id = request.query_params.get('employee_id')
        
        if employee_id:
            # Single employee status
            employee = Employee.objects.get(id=employee_id)
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            shift = get_employee_shift_for_date(employee_id, today)
            
            if shift:
                try:
                    attendance = ShiftAttendance.objects.get(employee_id=employee_id, date=today)
                    has_clocked_in = attendance.actual_start is not None
                    clock_in_time = attendance.actual_start
                    att_status = attendance.status
                    late_minutes = attendance.late_minutes
                except ShiftAttendance.DoesNotExist:
                    has_clocked_in = False
                    clock_in_time = None
                    att_status = 'not_clocked_in'
                    late_minutes = 0
                
                data = {
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'is_on_shift': shift['start_time'] <= current_time <= shift['end_time'],
                    'shift_start': shift['start_time'],
                    'shift_end': shift['end_time'],
                    'has_clocked_in': has_clocked_in,
                    'clock_in_time': clock_in_time,
                    'status': att_status,
                    'late_minutes': late_minutes
                }
            else:
                data = {
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'is_on_shift': False,
                    'shift_start': None,
                    'shift_end': None,
                    'has_clocked_in': False,
                    'clock_in_time': None,
                    'status': 'off',
                    'late_minutes': 0
                }
            
            return Response(data)
        else:
            # All employees currently on shift
            employees_on_shift = get_employees_on_shift_now()
            
            status_data = []
            today = timezone.now().date()
            
            for emp_shift in employees_on_shift:
                employee = emp_shift['employee']
                
                try:
                    attendance = ShiftAttendance.objects.get(employee=employee, date=today)
                    has_clocked_in = attendance.actual_start is not None
                    clock_in_time = attendance.actual_start
                    att_status = attendance.status
                    late_minutes = attendance.late_minutes
                except ShiftAttendance.DoesNotExist:
                    has_clocked_in = False
                    clock_in_time = None
                    att_status = 'not_clocked_in'
                    late_minutes = 0
                
                status_data.append({
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'is_on_shift': True,
                    'shift_start': emp_shift['start_time'],
                    'shift_end': emp_shift['end_time'],
                    'has_clocked_in': has_clocked_in,
                    'clock_in_time': clock_in_time,
                    'status': att_status,
                    'late_minutes': late_minutes
                })
            
            return Response(status_data)
    
    @action(detail=False, methods=['get'])
    def daily_report(self, request):
        """
        Get late and absent report for a specific date
        GET /api/shifts/attendance/daily_report/?date=2024-01-15
        """
        date_str = request.query_params.get('date', timezone.now().date().isoformat())
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all employees scheduled for this date
        day_of_week = report_date.weekday()
        if day_of_week == 6:  # Python weekday() returns 6 for Sunday
            day_of_week = 0
        else:
            day_of_week += 1
        
        scheduled_employees = WeeklyShiftSchedule.objects.filter(
            day_of_week=day_of_week,
            is_active=True
        ).exclude(
            employee__shiftoverride__date=report_date,
            employee__shiftoverride__override_type__in=['day_off', 'vacation', 'sick_leave', 'holiday']
        ).select_related('employee')
        
        total_scheduled = scheduled_employees.count()
        
        # Get attendance records
        attendance_records = ShiftAttendance.objects.filter(date=report_date).select_related('employee')
        
        present = attendance_records.filter(status='present').count()
        late = attendance_records.filter(status='late').count()
        absent = attendance_records.filter(status='absent').count()
        
        serializer = ShiftAttendanceSerializer(attendance_records, many=True)
        
        return Response({
            'date': report_date,
            'total_scheduled': total_scheduled,
            'present': present,
            'late': late,
            'absent': absent,
            'employees': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def employee_summary(self, request):
        """
        Get attendance summary for an employee over a date range
        GET /api/shifts/attendance/employee_summary/?employee_id=<uuid>&start_date=2024-01-01&end_date=2024-01-31
        """
        employee_id = request.query_params.get('employee_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date', timezone.now().date().isoformat())
        
        if not employee_id or not start_date:
            return Response(
                {'error': 'employee_id and start_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        employee = Employee.objects.get(id=employee_id)
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        attendance_records = ShiftAttendance.objects.filter(
            employee_id=employee_id,
            date__gte=start,
            date__lte=end
        )
        
        days_present = attendance_records.filter(status='present').count()
        days_late = attendance_records.filter(status='late').count()
        days_absent = attendance_records.filter(status='absent').count()
        
        total_hours = attendance_records.aggregate(
            total=Sum('total_hours')
        )['total'] or Decimal('0.00')
        
        weekly_hours = calculate_weekly_hours(employee_id)
        
        # Calculate attendance rate
        total_days = (end - start).days + 1
        attendance_rate = ((days_present + days_late) / total_days * 100) if total_days > 0 else 0
        
        return Response({
            'employee_id': employee.id,
            'employee_name': employee.name,
            'department': employee.department.name if employee.department else '',
            'weekly_hours': weekly_hours,
            'days_present': days_present,
            'days_late': days_late,
            'days_absent': days_absent,
            'total_hours_worked': total_hours,
            'attendance_rate': round(attendance_rate, 2)
        })
