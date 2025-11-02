from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
import datetime
from datetime import date, time, timedelta
from decimal import Decimal
from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status as rest_status  # Explicit import to avoid conflicts
from .custom_permissions import IsEmployer, IsAdminOrComplaintAdmin, HasModuleAccess
from .models import (
    Employee, EmployeeDocument, EmployeeNote, EmployeeAttendance, WorkShift, 
    LeaveRequest, Complaint, ComplaintReply, ComplaintAttachment, Wallet, WalletTransaction, 
    ReimbursementRequest, Task, Subtask, TaskReport, TaskComment, Team, TeamMembership, 
    TeamTask, OfficeLocation,
    # Multi-wallet models
    EmployeeWalletSystem, MainWallet, ReimbursementWallet, AdvanceWallet, 
    MultiWalletTransaction, WalletTransfer,
    # Client Complaint System models
    ComplaintCategory, ClientComplaint, ClientComplaintAttachment, 
    ClientComplaintAssignment, ClientComplaintEmployeeAssignment, ClientComplaintTask, ClientComplaintComment,
    ClientComplaintStatusHistory, ClientComplaintAccessToken, ClientComplaintReply,
    ClientComplaintStatus, TeamComplaintAdminPermission, EmployeeComplaintAdminPermission,
    # Ticket Automation models
    TicketDelayThreshold,
    # Shift Scheduling models
    WeeklyShiftSchedule, ShiftOverride, ShiftAttendance,
    # Utility functions
    has_complaint_admin_permission, get_complaint_admin_permissions,
    get_employee_shift_for_date, get_employees_on_shift_now, calculate_weekly_hours
)
from .serializers import (
    EmployeeSerializer, EmployeeDocumentSerializer, EmployeeNoteSerializer, 
    EmployeeAttendanceSerializer, WorkShiftSerializer, LeaveRequestSerializer, 
    LeaveRequestReviewSerializer, ComplaintSerializer, ComplaintReplySerializer, 
    WalletSerializer, WalletTransactionSerializer, CentralWalletSerializer, 
    CentralWalletTransactionSerializer, ReimbursementAttachmentSerializer, 
    ReimbursementRequestSerializer, ReimbursementReviewSerializer, TaskSerializer, 
    TaskCreateSerializer, TaskUpdateSerializer, SubtaskSerializer, TaskReportSerializer, 
    TaskCommentSerializer, ManagerTaskDashboardSerializer, TeamSerializer, 
    TeamCreateSerializer, TeamMembershipSerializer, TeamTaskSerializer, OfficeLocationSerializer,
    # Multi-wallet serializers
    EmployeeWalletSystemSerializer, MultiWalletTransactionSerializer, WalletTransferSerializer,
    # Client Complaint System serializers
    ComplaintCategorySerializer, ClientComplaintSerializer, ClientComplaintSubmissionSerializer,
    ClientComplaintStatusSerializer, ClientComplaintStatusUpdateSerializer,
    ClientComplaintAttachmentSerializer, ClientComplaintCommentSerializer, 
    ClientComplaintStatusHistorySerializer, ClientComplaintAssignmentSerializer,
    ClientComplaintEmployeeAssignmentSerializer, ClientComplaintTaskSerializer, ClientPortalComplaintSerializer, ClientComplaintReplySerializer,
    ClientComplaintReplyCreateSerializer, ClientComplaintAccessTokenSerializer,
    # Ticket Automation serializers
    TicketDelayThresholdSerializer,
    # Shift Scheduling serializers
    WeeklyShiftScheduleSerializer, BulkWeeklyScheduleSerializer, ShiftOverrideSerializer,
    ShiftAttendanceSerializer, ClockInSerializer, ClockOutSerializer,
    EmployeeShiftSummarySerializer, CurrentShiftStatusSerializer, LateAbsentReportSerializer
)
from utils.timezone_utils import system_now
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class EmployeeViewSet(viewsets.ModelViewSet):
    """Employee management - requires 'employees' module"""
    module_key = 'employees'  # Require employees module access
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsEmployer(), HasModuleAccess()]
        return [IsAuthenticated(), HasModuleAccess()]

    def get_queryset(self):
        queryset = Employee.objects.all()
        if getattr(self.request.user, "role", None) == "employee":
            # For employees, show themselves and their team members from teams they lead
            employee = getattr(self.request.user, 'employee', None)
            if employee:
                # Get teams where this employee is the leader
                led_teams = Team.objects.filter(team_leader=employee, is_active=True)
                
                # Get all team members from teams they lead
                team_member_ids = []
                for team in led_teams:
                    team_member_ids.extend(
                        team.memberships.filter(is_active=True).values_list('employee_id', flat=True)
                    )
                
                # Include themselves and their team members
                team_member_ids.append(employee.id)
                queryset = queryset.filter(id__in=team_member_ids)
            else:
                queryset = queryset.filter(user=self.request.user)
        return queryset

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            if hasattr(user, 'employee'):
                employee = user.employee
                # Return employee data with user role, but use user.id for consistency
                data = {
                    'id': str(user.id),
                    'employee_id': str(employee.id),
                    'name': employee.name,
                    'position': employee.position,
                    'department': employee.department,
                    'hire_date': employee.hire_date,
                    'salary': str(employee.salary),
                    'status': employee.status,
                    'phone': employee.phone,
                    'email': employee.email,
                    'address': employee.address,
                    'emergency_contact': employee.emergency_contact,
                    'profile_picture': employee.profile_picture,
                    'username': user.username,
                    'role': user.role,
                    'payroll_time_left': '',  # You can calculate this if needed
                }
                return Response(data)
            else:
                # Return user data only (for non-employee users)
                data = {
                    'id': str(user.id),
                    'name': user.name,
                    'username': user.username,
                    'role': user.role,
                    'email': user.email,
                    'profile_picture': user.profile_picture,
                }
                return Response(data)
        except Exception as e:
            return Response({"error": "Failed to get current user"}, status=500)

class EmployeeDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            if not hasattr(user, 'employee'):
                return Response({"error": "User is not an employee"}, status=400)
            
            employee = user.employee
            today = timezone.now().date()
            
            # Get today's work shifts (NEW - using WorkShift model)
            today_shifts = WorkShift.objects.filter(
                employee=employee,
                check_in__date=today
            ).order_by('check_in')
            
            # Check if there's an active (ongoing) shift
            active_shift = today_shifts.filter(check_out__isnull=True).first()
            latest_shift = today_shifts.last()
            
            # Determine attendance status based on shifts
            has_checked_in = today_shifts.exists()
            has_active_shift = active_shift is not None
            
            # Check if employee is late based on shift schedule
            attendance_status = 'absent'
            is_late = False
            late_minutes = 0
            
            if has_checked_in and latest_shift:
                # Get the shift schedule for today
                day_of_week = today.weekday()
                our_day_of_week = (day_of_week + 1) % 7  # Convert to Sunday=0
                
                try:
                    shift_schedule = WeeklyShiftSchedule.objects.get(
                        employee=employee,
                        day_of_week=our_day_of_week,
                        is_active=True
                    )
                    
                    expected_start = shift_schedule.start_time
                    if isinstance(expected_start, str):
                        import datetime as dt
                        expected_start = dt.datetime.strptime(expected_start, '%H:%M:%S').time() if len(expected_start) > 5 else dt.datetime.strptime(expected_start, '%H:%M').time()
                    
                    # Compare check-in time with expected start time (grace period: 15 minutes)
                    check_in_time = latest_shift.check_in.time()
                    expected_start_dt = timezone.datetime.combine(today, expected_start)
                    check_in_dt = timezone.datetime.combine(today, check_in_time)
                    grace_period = timezone.timedelta(minutes=15)
                    
                    if check_in_dt > (expected_start_dt + grace_period):
                        is_late = True
                        late_minutes = int((check_in_dt - expected_start_dt).total_seconds() / 60)
                        attendance_status = 'late'
                    else:
                        attendance_status = 'present'
                
                except WeeklyShiftSchedule.DoesNotExist:
                    # No schedule defined - default to present
                    attendance_status = 'present'
            
            # Get wallet system balances (new multi-wallet system) 
            try:
                wallet_system = EmployeeWalletSystem.objects.get(employee=employee)
                main_wallet = wallet_system.main_wallet
                reimbursement_wallet = wallet_system.reimbursement_wallet
                advance_wallet = wallet_system.advance_wallet
                
                wallet_data = {
                    "main_balance": str(main_wallet.balance),
                    "reimbursement_balance": str(reimbursement_wallet.balance),
                    "advance_balance": str(advance_wallet.balance),
                    "total_balance": str(main_wallet.balance + reimbursement_wallet.balance - advance_wallet.balance)
                }
            except EmployeeWalletSystem.DoesNotExist:
                # Create wallet system if it doesn't exist
                from .signals import get_or_create_wallet_system
                wallet_system = get_or_create_wallet_system(employee)
                main_wallet = wallet_system.main_wallet
                reimbursement_wallet = wallet_system.reimbursement_wallet 
                advance_wallet = wallet_system.advance_wallet
                
                wallet_data = {
                    "main_balance": str(main_wallet.balance),
                    "reimbursement_balance": str(reimbursement_wallet.balance),
                    "advance_balance": str(advance_wallet.balance),
                    "total_balance": str(main_wallet.balance + reimbursement_wallet.balance - advance_wallet.balance)
                }

            # Get pending leave requests
            pending_leaves = LeaveRequest.objects.filter(
                employee=employee,
                status='pending'
            ).count()

            # Get total leave requests
            total_leaves = LeaveRequest.objects.filter(employee=employee).count()

            # Get recent complaints
            recent_complaints = Complaint.objects.filter(
                employee=employee
            ).order_by('-created_at')[:3]
            
            data = {
                'attendance_today': {
                    'checked_in': latest_shift.check_in.strftime('%H:%M') if latest_shift else None,
                    'checked_out': latest_shift.check_out.strftime('%H:%M') if latest_shift and latest_shift.check_out else None,
                    'status': attendance_status,
                    'is_late': is_late,
                    'late_minutes': late_minutes,
                    'has_active_shift': has_active_shift,
                    'active_shift_id': str(active_shift.id) if active_shift else None
                },
                'wallet_data': wallet_data,
                'pending_leaves': pending_leaves,
                'total_leaves': total_leaves,
                'recent_complaints': [
                    {
                        'id': str(complaint.id),
                        'title': complaint.title,
                        'status': complaint.status,
                        'created_at': complaint.created_at
                    } for complaint in recent_complaints
                ]
            }
            
            return Response(data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error in EmployeeDashboardStatsView: {str(e)}")
            return Response({"error": f"Failed to get employee dashboard stats: {str(e)}"}, status=500)

class EmployeeDocumentViewSet(viewsets.ModelViewSet):
    queryset = EmployeeDocument.objects.all()
    serializer_class = EmployeeDocumentSerializer
    permission_classes = [IsAuthenticated]

class EmployeeNoteViewSet(viewsets.ModelViewSet):
    queryset = EmployeeNote.objects.all()
    serializer_class = EmployeeNoteSerializer
    permission_classes = [IsAuthenticated]

class EmployeeAttendanceListCreateView(generics.ListCreateAPIView):
    queryset = EmployeeAttendance.objects.all().order_by("-date")
    serializer_class = EmployeeAttendanceSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name="user_id", description="Filter by Employee User ID", required=False, type=str),
            OpenApiParameter(name="date", description="Filter by date (YYYY-MM-DD)", required=False, type=str),
        ]
    )
    def get(self, request):
        date_query = request.query_params.get("date")
        user_id_query = request.query_params.get("user_id")
        if getattr(self.request.user, "role", None) != "admin":
            attendance = EmployeeAttendance.objects.filter(employee__id=request.user.employee.id, date=date_query)
        if date_query or user_id_query:
            if user_id_query:
                if not date_query:
                    attendance = EmployeeAttendance.objects.filter(employee__id=user_id_query)
                else:
                    attendance = EmployeeAttendance.objects.filter(date=date_query, employee__id=user_id_query)
                serializer = EmployeeAttendanceSerializer(attendance, many=True)
                return Response(serializer.data)
            if date_query:
                if not user_id_query:
                    attendance = EmployeeAttendance.objects.filter(date=date_query)
                else:
                    attendance = EmployeeAttendance.objects.filter(employee__id=user_id_query, date=date_query)
                serializer = EmployeeAttendanceSerializer(attendance, many=True)
                return Response(serializer.data)
        else:
            return Response({"error": "Date or user_id parameter is required"}, status=400)
# Retrieve, update, delete attendance record
class EmployeeAttendanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = EmployeeAttendance.objects.all()
    serializer_class = EmployeeAttendanceSerializer
    permission_classes = [IsAuthenticated]

class CheckInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)

        now = system_now()
        today = now.date()
        current_time = now.time()
        day_of_week = today.weekday()  # Monday=0, Sunday=6
        # Convert Python weekday to our model's day_of_week (Sunday=0)
        our_day_of_week = (day_of_week + 1) % 7
        
        # Get employee's shift schedule for today
        try:
            shift_schedule = WeeklyShiftSchedule.objects.get(
                employee=employee,
                day_of_week=our_day_of_week,
                is_active=True
            )
            expected_start = shift_schedule.start_time
            
            # Check if employee is late (grace period: 15 minutes)
            if isinstance(expected_start, str):
                expected_start = datetime.datetime.strptime(expected_start, '%H:%M:%S').time() if len(expected_start) > 5 else datetime.datetime.strptime(expected_start, '%H:%M').time()
            
            grace_period = datetime.timedelta(minutes=15)
            start_dt = datetime.datetime.combine(today, expected_start)
            current_dt = datetime.datetime.combine(today, current_time)
            
            is_late = current_dt > (start_dt + grace_period)
            late_minutes = int((current_dt - start_dt).total_seconds() / 60) if is_late else 0
            
        except WeeklyShiftSchedule.DoesNotExist:
            # No schedule defined for today - allow check-in but mark as present
            is_late = False
            late_minutes = 0
            expected_start = None
        
        # Get or create attendance record for today
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={"status": "late" if is_late else "present"}
        )

        # Check if employee has an active shift (checked in but not checked out)
        active_shifts = WorkShift.objects.filter(
            employee=employee,
            attendance=attendance,
            is_active=True,
            check_out__isnull=True
        )
        
        if active_shifts.exists():
            return Response({"error": "Already checked in. Please check out first."}, status=400)

        # Create a new shift for this check-in
        shift = WorkShift.objects.create(
            employee=employee,
            attendance=attendance,
            shift_type='regular',
            check_in=now,
            is_active=True
        )
        
        # Update attendance status based on lateness
        attendance.status = "late" if is_late else "present"
        attendance.check_in = current_time
        attendance.save()

        response_data = EmployeeAttendanceSerializer(attendance).data
        response_data['is_late'] = is_late
        response_data['late_minutes'] = late_minutes
        response_data['expected_start'] = str(expected_start) if expected_start else None

        return Response(response_data, status=200)


class CheckOutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, employee_id):
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({"error": "Employee not found"}, status=404)

        now = system_now()
        today = now.date()
        
        # Get today's attendance record
        try:
            attendance = EmployeeAttendance.objects.get(employee=employee, date=today)
        except EmployeeAttendance.DoesNotExist:
            return Response({"error": "No check-in record found for today"}, status=400)

        # Find active shift to check out
        active_shift = WorkShift.objects.filter(
            employee=employee,
            attendance=attendance,
            is_active=True,
            check_out__isnull=True
        ).first()
        
        if not active_shift:
            return Response({"error": "No active shift found to check out"}, status=400)

        # Check out from the active shift
        active_shift.check_out = now
        active_shift.is_active = False
        
        # Calculate hours and overtime based on shift schedule
        today = now.date()
        current_time = now.time()
        day_of_week = today.weekday()
        our_day_of_week = (day_of_week + 1) % 7
        
        overtime_minutes = 0
        total_hours = 0
        
        try:
            shift_schedule = WeeklyShiftSchedule.objects.get(
                employee=employee,
                day_of_week=our_day_of_week,
                is_active=True
            )
            
            expected_end = shift_schedule.end_time
            if isinstance(expected_end, str):
                expected_end = datetime.datetime.strptime(expected_end, '%H:%M:%S').time() if len(expected_end) > 5 else datetime.datetime.strptime(expected_end, '%H:%M').time()
            
            # Calculate total hours worked
            work_duration = active_shift.check_out - active_shift.check_in
            total_minutes = work_duration.total_seconds() / 60
            
            # Deduct break time (1 hour for shifts > 6 hours)
            if total_minutes > 360:  # 6 hours
                total_minutes -= 60  # 1 hour break
            
            total_hours = total_minutes / 60
            
            # Calculate overtime (grace period: 30 minutes after expected end)
            end_dt = datetime.datetime.combine(today, expected_end)
            current_dt = datetime.datetime.combine(today, current_time)
            overtime_threshold = datetime.timedelta(minutes=30)
            
            if current_dt > (end_dt + overtime_threshold):
                overtime_minutes = int((current_dt - end_dt).total_seconds() / 60)
        
        except WeeklyShiftSchedule.DoesNotExist:
            # No schedule - just calculate raw hours
            work_duration = active_shift.check_out - active_shift.check_in
            total_hours = work_duration.total_seconds() / 3600
        
        active_shift.save()
        
        # Update attendance check_out time
        attendance.check_out = current_time
        attendance.save()

        response_data = EmployeeAttendanceSerializer(attendance).data
        response_data['total_hours'] = round(total_hours, 2)
        response_data['overtime_minutes'] = overtime_minutes

        return Response(response_data, status=200)


class WorkShiftViewSet(viewsets.ModelViewSet):
    """ViewSet for managing work shifts"""
    serializer_class = WorkShiftSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        employee_id = self.request.query_params.get('employee_id', None)
        date = self.request.query_params.get('date', None)
        
        if user.role == 'admin':
            queryset = WorkShift.objects.all()
        elif hasattr(user, 'employee'):
            queryset = WorkShift.objects.filter(employee=user.employee)
        else:
            return WorkShift.objects.none()
        
        # Filter by employee if specified (admin only)
        if employee_id and user.role == 'admin':
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by date if specified
        if date:
            queryset = queryset.filter(check_in__date=date)
        
        return queryset.order_by('-check_in')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # For employees, use their own employee record
        if user.role != 'admin' and hasattr(user, 'employee'):
            employee = user.employee
        else:
            # Admin can specify employee
            employee_id = self.request.data.get('employee')
            if employee_id:
                employee = get_object_or_404(Employee, id=employee_id)
            else:
                raise ValidationError("Employee is required")
        
        # Get or create attendance record for the shift date
        shift_date = serializer.validated_data['check_in'].date()
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=shift_date,
            defaults={'status': 'present'}
        )
        
        serializer.save(employee=employee, attendance=attendance)

    def perform_update(self, serializer):
        user = self.request.user
        
        # For employees, use their own employee record
        if user.role != 'admin' and hasattr(user, 'employee'):
            employee = user.employee
        else:
            # Admin can specify employee
            employee_id = self.request.data.get('employee')
            if employee_id:
                employee = get_object_or_404(Employee, id=employee_id)
            else:
                # If employee not specified, keep the existing employee
                employee = serializer.instance.employee
        
        # Get or create attendance record for the shift date
        shift_date = serializer.validated_data['check_in'].date()
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=shift_date,
            defaults={'status': 'present'}
        )
        
        serializer.save(employee=employee, attendance=attendance)


class ShiftCheckInView(APIView):
    """Start a new work shift with GPS location validation"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        # Get employee
        if hasattr(user, 'employee'):
            employee = user.employee
        else:
            return Response({'error': 'Employee profile not found'}, status=400)
        
        # Get GPS coordinates from request
        user_latitude = request.data.get('latitude')
        user_longitude = request.data.get('longitude')
        
        if not user_latitude or not user_longitude:
            return Response({
                'error': 'GPS coordinates are required for check-in'
            }, status=400)
        
        # Validate location against office location
        office_location = OfficeLocation.get_active_location()
        if office_location:
            distance = calculate_distance(
                user_latitude, user_longitude,
                office_location.latitude, office_location.longitude
            )
            
            if distance > office_location.radius_meters:
                return Response({
                    'error': f'You are too far from the office. Distance: {int(distance)}m, Required: within {office_location.radius_meters}m',
                    'distance_meters': int(distance),
                    'required_radius': office_location.radius_meters
                }, status=400)
        
        # Check for active shifts
        active_shifts = WorkShift.objects.filter(
            employee=employee,
            is_active=True,
            check_out__isnull=True
        )
        
        if active_shifts.exists():
            return Response({
                'error': 'You have an active shift. Please check out first.',
                'active_shift': WorkShiftSerializer(active_shifts.first()).data
            }, status=400)
        
        # Create new shift
        now = system_now()
        today = now.date()
        
        # Get or create attendance record
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'status': 'present'}
        )
        
        # Create shift with GPS coordinates
        shift_data = {
            'employee': employee,
            'attendance': attendance,
            'shift_type': request.data.get('shift_type', 'regular'),
            'check_in': now,
            'location': request.data.get('location', ''),
            'checkin_latitude': user_latitude,
            'checkin_longitude': user_longitude,
            'notes': request.data.get('notes', ''),
            'is_active': True
        }
        
        shift = WorkShift.objects.create(**shift_data)
        
        return Response(WorkShiftSerializer(shift).data, status=201)


class ShiftCheckOutView(APIView):
    """End current work shift with GPS location validation"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, shift_id=None):
        user = request.user
        
        # Get employee
        if hasattr(user, 'employee'):
            employee = user.employee
        else:
            return Response({'error': 'Employee profile not found'}, status=400)
        
        # Get GPS coordinates from request
        user_latitude = request.data.get('latitude')
        user_longitude = request.data.get('longitude')
        
        if not user_latitude or not user_longitude:
            return Response({
                'error': 'GPS coordinates are required for check-out'
            }, status=400)
        
        # Validate location against office location
        office_location = OfficeLocation.get_active_location()
        if office_location:
            distance = calculate_distance(
                user_latitude, user_longitude,
                office_location.latitude, office_location.longitude
            )
            
            if distance > office_location.radius_meters:
                return Response({
                    'error': f'You are too far from the office. Distance: {int(distance)}m, Required: within {office_location.radius_meters}m',
                    'distance_meters': int(distance),
                    'required_radius': office_location.radius_meters
                }, status=400)
        
        # Get shift to check out
        if shift_id:
            try:
                shift = WorkShift.objects.get(id=shift_id, employee=employee)
            except WorkShift.DoesNotExist:
                return Response({'error': 'Shift not found'}, status=404)
        else:
            # Get active shift
            shift = WorkShift.objects.filter(
                employee=employee,
                is_active=True,
                check_out__isnull=True
            ).first()
            
            if not shift:
                return Response({'error': 'No active shift found'}, status=400)
        
        if shift.check_out:
            return Response({'error': 'Shift already completed'}, status=400)
        
        # Complete shift with GPS coordinates
        now = system_now()
        shift.check_out = now
        shift.checkout_latitude = user_latitude
        shift.checkout_longitude = user_longitude
        shift.is_active = False
        
        # End break if active
        if shift.break_start and not shift.break_end:
            shift.break_end = now
        
        shift.save()
        
        return Response(WorkShiftSerializer(shift).data, status=200)


class ShiftBreakView(APIView):
    """Start or end break during shift"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, shift_id):
        user = request.user
        
        # Get employee
        if hasattr(user, 'employee'):
            employee = user.employee
        else:
            return Response({'error': 'Employee profile not found'}, status=400)
        
        try:
            shift = WorkShift.objects.get(id=shift_id, employee=employee)
        except WorkShift.DoesNotExist:
            return Response({'error': 'Shift not found'}, status=404)
        
        if not shift.is_active or shift.check_out:
            return Response({'error': 'Shift is not active'}, status=400)
        
        now = system_now()
        action = request.data.get('action', 'start')
        
        if action == 'start':
            if shift.break_start and not shift.break_end:
                return Response({'error': 'Break already started'}, status=400)
            
            shift.break_start = now
            shift.break_end = None
            
        elif action == 'end':
            if not shift.break_start or shift.break_end:
                return Response({'error': 'No active break to end'}, status=400)
            
            shift.break_end = now
        
        else:
            return Response({'error': 'Invalid action'}, status=400)
        
        shift.save()
        
        return Response(WorkShiftSerializer(shift).data, status=200)


class LeaveRequestCreateView(generics.CreateAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # ربط الطلب بالموظف الحالي
        employee = self.request.user.employee
        serializer.save(employee=employee)

class LeaveRequestListView(generics.ListAPIView):
    queryset = LeaveRequest.objects.all().order_by("-created_at")
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]  # Add role check if needed
    pagination_class = StandardResultsSetPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(name="user_id", description="Filter by Employee User ID", required=False, type=str),
            OpenApiParameter(name="status", description="Filter by leave status", required=False, type=str),
        ]
    )
    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.all().order_by("-created_at")

        if getattr(user, "role", None) == "employee":
            queryset = queryset.filter(employee__user=user)

        user_id = self.request.query_params.get("user_id")
        status = self.request.query_params.get("status")

        if user_id:
            queryset = queryset.filter(employee__id=user_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class LeaveRequestUpdateStatusView(generics.UpdateAPIView):
    queryset = LeaveRequest.objects.all()
    serializer_class = LeaveRequestReviewSerializer
    permission_classes = [IsEmployer]

    def update(self, request, *args, **kwargs):
        leave_request = self.get_object()
        
        # Use the review serializer for validation
        serializer = self.get_serializer(leave_request, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Set review metadata
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = system_now()
        
        # Save the changes
        self.perform_update(serializer)

        status_param = serializer.validated_data.get("status", leave_request.status)
        is_paid = serializer.validated_data.get("is_paid", leave_request.is_paid)

        # إذا تم الموافقة على الإجازة
        if status_param == "approved":
            start_date = leave_request.start_date
            end_date = leave_request.end_date
            employee = leave_request.employee

            current_date = start_date
            while current_date <= end_date:
                attendance, created = EmployeeAttendance.objects.get_or_create(
                    employee=employee,
                    date=current_date,
                    defaults={
                        "status": "on_leave",
                        "paid": is_paid if is_paid is not None else True  # Default to paid if not specified
                    }
                )
                if not created:
                    attendance.status = "on_leave"
                    attendance.paid = is_paid if is_paid is not None else True
                    attendance.check_in = None
                    attendance.check_out = None
                    attendance.save()
                current_date += datetime.timedelta(days=1)

        return Response(LeaveRequestSerializer(leave_request).data)


# إنشاء شكوى
class ComplaintCreateView(generics.CreateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # لو المستخدم موظف، نخليه صاحب الشكوى
        # employee = Employee.objects.get(user=self.request.user)
        serializer.save()

# عرض الشكاوى (موظف يرى شكاويه فقط، مسؤول يرى الجميع)
class ComplaintListView(generics.ListAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "role", None) == "employee":
            return Complaint.objects.filter(employee__user=user)
        return Complaint.objects.all().order_by("-created_at")

# الرد على شكوى
class ComplaintReplyCreateView(generics.CreateAPIView):
    serializer_class = ComplaintReplySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        complaint_id = self.kwargs.get("complaint_id")
        complaint = get_object_or_404(Complaint, id=complaint_id)
        # Prevent replies to closed complaints
        if complaint.status == 'closed':
            raise ValidationError("Cannot reply to a closed complaint")
        user = self.request.user
        author_name = getattr(user, 'name', None) or getattr(user, 'username', None) or user.get_full_name() or user.email
        serializer.save(complaint=complaint, author=user, author_name=author_name)

class ComplaintCloseView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, complaint_id):
        try:
            complaint = get_object_or_404(Complaint, id=complaint_id)
            
            # Check if user can close this complaint
            if hasattr(request.user, 'employee') and complaint.employee != request.user.employee:
                return Response({"error": "You can only close your own complaints"}, status=403)
            
            # Update complaint status to closed
            complaint.status = 'closed'
            complaint.save()
            
            return Response({"message": "Complaint closed successfully"}, status=200)
        except Exception as e:
            return Response({"error": "Failed to close complaint"}, status=500)

class WalletDetailView(generics.RetrieveAPIView):
    # queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        employee_id = self.kwargs["employee_id"]
        if getattr(self.request.user, "role", None) != "employee" or self.request.user.employee.id == employee_id: #The admi can see all transactions or the employee's own transactions
            return WalletTransaction.objects.filter(wallet__employee__id=employee_id)
        else:
            #No permission
            return WalletTransaction.objects.none()

    def get_object(self):
        employee_id = self.kwargs.get("employee_id")
        return Wallet.objects.get(employee__id=employee_id)


class WalletTransactionCreateView(generics.CreateAPIView):
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        employee_id = self.kwargs["employee_id"]
        wallet = Wallet.objects.get(employee__id=employee_id)

        transaction = serializer.save(wallet=wallet)

        #Edit credits
        if transaction.transaction_type == "deposit":
            if self.request.user.role != "admin":
                raise PermissionDenied("Only admins can deposit to the wallet.")
            wallet.balance += transaction.amount
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="deposit",
                amount=transaction.amount,
                description=f"Deposit to wallet by {self.request.user.username}"
            )
            central_wallet = get_central_wallet()
            central_wallet.balance -= transaction.amount
            central_wallet.save()
            WalletTransaction.objects.create(
                wallet=central_wallet,
                transaction_type="withdrawal",
                amount=transaction.amount,
                description=f"Withdraw from the central wallet by {self.request.user.username} to the wallet {wallet.employee.user.username}"
            )

            central_wallet.save()
        elif transaction.transaction_type == "withdrawal":
            # Check if employee has sufficient balance
            if wallet.balance < transaction.amount:
                raise ValidationError("Insufficient wallet balance for withdrawal.")
            wallet.balance -= transaction.amount
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="withdrawal",
                amount=transaction.amount,
                description=f"Withdrawal from wallet by {self.request.user.username}"
            )

        wallet.save()

class WalletTransactionListView(generics.ListAPIView):
    """Legacy wallet transaction view - now redirects to multi-wallet data for better UX"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        # Use multi-wallet serializer to show the new transaction format
        return MultiWalletTransactionSerializer

    def get_queryset(self):
        employee_id = self.kwargs["employee_id"]
        
        # Check permissions - admin can see all, employees can only see their own
        if self.request.user.role != 'admin' and (not hasattr(self.request.user, 'employee') or str(self.request.user.employee.id) != str(employee_id)):
            return MultiWalletTransaction.objects.none()
        
        # Return multi-wallet transactions for better user experience
        return MultiWalletTransaction.objects.filter(wallet_system__employee__id=employee_id).order_by("-created_at")

def get_central_wallet():
    """
    Get or create the central wallet for the tenant.
    Central wallet has no employee (employee__isnull=True).
    If multiple exist (data corruption), returns the first and logs warning.
    """
    try:
        # Try to get existing central wallet
        wallet = Wallet.objects.filter(employee__isnull=True).first()
        
        if wallet:
            # Check if there are duplicates (data corruption)
            duplicate_count = Wallet.objects.filter(employee__isnull=True).count()
            if duplicate_count > 1:
                print(f'[Central Wallet] WARNING: Found {duplicate_count} central wallets, using first one. Consider cleanup.')
            return wallet
        
        # Create new central wallet if none exists
        wallet = Wallet.objects.create(employee=None, balance=0.00)
        print(f'[Central Wallet] Created new central wallet with balance: {wallet.balance}')
        return wallet
        
    except Exception as e:
        print(f'[Central Wallet] Error: {e}')
        raise

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"

class CentralWalletDetailView(generics.RetrieveAPIView):
    serializer_class = CentralWalletSerializer
    permission_classes = [IsAdminRole]

    def get_object(self):
        return get_central_wallet()

class CentralWalletTransactionCreateView(generics.CreateAPIView):
    serializer_class = CentralWalletTransactionSerializer
    permission_classes = [IsAdminRole]

    def perform_create(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can deposit to the central wallet.")
        
        wallet = get_central_wallet()
        
        # Get transaction data
        transaction_type = serializer.validated_data['transaction_type']
        amount = abs(serializer.validated_data['amount'])  # Ensure positive amount
        description = serializer.validated_data.get('description', '')
        
        # Update wallet balance
        if transaction_type == "deposit":
            wallet.balance += amount
            if not description:
                description = f"Deposit to central wallet by {self.request.user.username}"
        elif transaction_type == "withdrawal":
            wallet.balance -= amount
            if not description:
                description = f"Withdrawal from central wallet by {self.request.user.username}"
        
        wallet.save()
        
        # Create the transaction record (only once!)
        serializer.save(
            wallet=wallet,
            amount=amount,  # Always positive
            description=description
        )

class CentralWalletTransactionListView(generics.ListAPIView):
    serializer_class = CentralWalletTransactionSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        wallet = get_central_wallet()
        return WalletTransaction.objects.filter(wallet=wallet)

class ReimbursementRequestCreateView(generics.CreateAPIView):
    serializer_class = ReimbursementRequestSerializer
    permission_classes = [IsAuthenticated]

class ReimbursementRequestListView(generics.ListAPIView):
    serializer_class = ReimbursementRequestSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return ReimbursementRequest.objects.filter(status="pending").order_by("-created_at")
        else:
            return ReimbursementRequest.objects.filter(employee=user.employee)

class ReimbursementRequestApproveRejectView(generics.UpdateAPIView):
    queryset = ReimbursementRequest.objects.all()   # 👈 add this
    serializer_class = ReimbursementReviewSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if request.user.role != "admin":
            raise PermissionDenied("Admins only can approve/deny requests.")

        reimbursement = self.get_object()
        review_status = request.data.get("status")
        comment = request.data.get("admin_comment", "")

        if review_status not in ["approved", "rejected"]:
            raise ValidationError("Status must be 'approved' or 'rejected'.")

        # If approving, check central wallet balance BEFORE making any changes
        if review_status == "approved":
            central_wallet = get_central_wallet()
            if central_wallet.balance < reimbursement.amount:
                return Response({
                    'error': f'Insufficient balance in central wallet. Available: {central_wallet.balance}, Required: {reimbursement.amount}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Now safe to update status after validation
        reimbursement.status = review_status
        reimbursement.admin_comment = comment
        reimbursement.save()

        if review_status == "approved":
            # Update reimbursement with approval details
            reimbursement.approved_at = timezone.now()
            reimbursement.approved_by = request.user
            reimbursement.save()
            
            # Deduct from central wallet (already validated above)
            central_wallet = get_central_wallet()
            central_wallet.balance -= reimbursement.amount
            central_wallet.save()
            
            # Record the central wallet transaction
            WalletTransaction.objects.create(
                wallet=central_wallet,
                transaction_type='withdrawal',
                amount=reimbursement.amount,
                description=f"Reimbursement approved for {reimbursement.employee.name}: {reimbursement.description}"
            )
            
            # Add money to employee's reimbursement wallet
            wallet_system = get_or_create_wallet_system(reimbursement.employee)
            
            # Create multi-wallet transaction for reimbursement approval
            create_wallet_transaction(
                wallet_system=wallet_system,
                wallet_type='reimbursement',
                transaction_type='reimbursement_approved',
                amount=reimbursement.amount,
                description=f"Reimbursement approved: {reimbursement.description}",
                reimbursement_request=reimbursement,
                created_by=request.user
            )

        serializer = self.get_serializer(reimbursement)
        return Response(serializer.data)


class ReimbursementPaymentView(generics.UpdateAPIView):
    """Pay approved reimbursements - transfers money from reimbursement wallet to main wallet"""
    queryset = ReimbursementRequest.objects.all()
    serializer_class = ReimbursementReviewSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if request.user.role != "admin":
            raise PermissionDenied("Admins only can pay reimbursements.")

        reimbursement = self.get_object()
        
        if reimbursement.status != "approved":
            raise ValidationError("Only approved reimbursements can be paid.")
            
        if reimbursement.status == "paid":
            raise ValidationError("Reimbursement has already been paid.")

        # Update reimbursement status
        reimbursement.status = "paid"
        reimbursement.paid_at = timezone.now() 
        reimbursement.paid_by = request.user
        reimbursement.save()

        # Transfer money from reimbursement wallet to main wallet
        wallet_system = get_or_create_wallet_system(reimbursement.employee)
        
        # Create the wallet transfer
        transfer_between_wallets(
            wallet_system=wallet_system,
            from_wallet_type='reimbursement',
            to_wallet_type='main',
            amount=reimbursement.amount,
            description=f"Paid: {reimbursement.description}",
            transfer_type='reimbursement_to_main',
            created_by=request.user
        )

        serializer = self.get_serializer(reimbursement)
        return Response(serializer.data)


# TO-DO System Views

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """Use different serializers for create vs other operations"""
        if self.action == 'create':
            return TaskCreateSerializer
        return TaskSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()
        
        # For individual task operations (retrieve, update, partial_update, destroy), don't apply date filter
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            # Still apply role-based filtering for security
            if user.role == 'employee':
                try:
                    employee = user.employee
                    # Allow access to tasks assigned directly to employee or to their teams
                    team_ids = list(employee.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
                    queryset = queryset.filter(
                        Q(employee=employee) |  # Tasks assigned directly to employee
                        Q(team_id__in=team_ids)  # Team tasks (with or without specific employee)
                    )
                except Employee.DoesNotExist:
                    queryset = queryset.none()
            # Admins can access any task for individual operations
            return queryset
        
        # For list view, apply date filtering
        date_param = self.request.query_params.get('date')
        if date_param:
            try:
                date = datetime.datetime.strptime(date_param, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date)
            except ValueError:
                pass
        else:
            queryset = queryset.filter(date=datetime.date.today())
        
        # Role-based filtering for list view
        if user.role == 'employee':
            # Employees see tasks assigned to them directly or tasks assigned to their teams
            try:
                employee = user.employee
                # Get tasks assigned directly to the employee or to teams they belong to
                team_ids = list(employee.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
                queryset = queryset.filter(
                    Q(employee=employee) |  # Tasks assigned directly to employee
                    Q(team_id__in=team_ids, employee__isnull=True)  # Team tasks without specific employee
                )
            except Employee.DoesNotExist:
                queryset = queryset.none()
        elif user.role == 'admin':
            # Admins see all tasks, can filter by employee or team
            employee_id = self.request.query_params.get('employee_id')
            team_id = self.request.query_params.get('team_id')
            
            if employee_id:
                # Filter by employee_id - include tasks assigned to employee
                # OR tasks created by this user but not assigned to anyone
                queryset = queryset.filter(
                    Q(employee_id=employee_id) |
                    Q(employee__isnull=True, created_by_id=employee_id)
                )
            elif team_id:
                queryset = queryset.filter(team_id=team_id)
        
        return queryset.order_by('-priority', 'created_at')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Set employee based on user role and data
        if user.role == 'employee':
            try:
                employee = user.employee
                # Employees can only create tasks for themselves
                task = serializer.save(employee=employee, created_by=user)
            except Employee.DoesNotExist:
                raise ValidationError("Employee profile not found. Please contact administrator.")
        elif user.role in ['admin', 'manager']:
            # Check if employee was specified in the request
            employee_id = self.request.data.get('employee')
            team_id = self.request.data.get('team')
            
            employee = None
            if employee_id:
                # Admin/Manager is creating task for a specific employee
                try:
                    employee = Employee.objects.get(id=employee_id)
                except Employee.DoesNotExist:
                    raise ValidationError("Employee not found")
            else:
                # No employee specified - try to assign to current user's employee profile
                try:
                    employee = user.employee
                    print(f"✅ Auto-assigning task to user's employee profile: {employee.id}")
                except (Employee.DoesNotExist, AttributeError) as e:
                    print(f"⚠️ User {user.username} (role={user.role}) has no employee profile: {e}")
                    # If team is specified, keep employee as None (team task)
                    # If no team, keep employee as None (unassigned admin task)
                    employee = None
            
            task = serializer.save(
                employee=employee, 
                created_by=user, 
                assigned_by_manager=True
            )
        else:
            raise PermissionDenied("You don't have permission to create tasks")
        
        # Handle team assignment if provided
        team_id = self.request.data.get('team')
        if team_id:
            try:
                team = Team.objects.get(id=team_id)
                task.team = team
                task.save()
            except Team.DoesNotExist:
                raise ValidationError("Team not found")
        
        return task


class AdminTaskManagementView(generics.ListAPIView):
    """Enhanced task management view for admins and team managers"""
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.select_related('employee', 'team', 'created_by').prefetch_related('subtasks')
        
        # Permission filtering
        if user.role == 'admin':
            # Admins can see all tasks
            pass
        elif user.role == 'employee':
            # Check if user is a team manager
            try:
                employee = user.employee
                managed_teams = Team.objects.filter(manager=employee)
                if managed_teams.exists():
                    # Team manager: see tasks from managed teams
                    team_ids = list(managed_teams.values_list('id', flat=True))
                    # Also include employee's own tasks and team member tasks
                    member_team_ids = list(employee.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
                    all_team_ids = list(set(team_ids + member_team_ids))
                    
                    queryset = queryset.filter(
                        Q(employee=employee) |  # Own tasks
                        Q(team_id__in=all_team_ids)  # Managed team tasks + member team tasks
                    )
                else:
                    # Regular employee: no access to management view
                    return Task.objects.none()
            except Employee.DoesNotExist:
                return Task.objects.none()
        else:
            return Task.objects.none()
        
        # Search filtering
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(employee__name__icontains=search) |
                Q(team__name__icontains=search)
            )
        
        # Status filtering
        status = self.request.query_params.get('status')
        if status and status != 'all':
            queryset = queryset.filter(status=status)
        
        # Priority filtering
        priority = self.request.query_params.get('priority')
        if priority and priority != 'all':
            queryset = queryset.filter(priority=priority)
        
        # Employee filtering
        employee_id = self.request.query_params.get('employee_id')
        if employee_id and employee_id != 'all':
            queryset = queryset.filter(employee_id=employee_id)
        
        # Team filtering
        team_id = self.request.query_params.get('team_id')
        if team_id and team_id != 'all':
            queryset = queryset.filter(team_id=team_id)
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            try:
                date_from_parsed = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=date_from_parsed)
            except ValueError:
                pass
        if date_to:
            try:
                date_to_parsed = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=date_to_parsed)
            except ValueError:
                pass
        
        # Sorting
        sort_by = self.request.query_params.get('sort_by', 'created_at')
        sort_order = self.request.query_params.get('sort_order', 'desc')
        
        valid_sort_fields = ['created_at', 'date', 'priority', 'status', 'title', 'employee__name', 'team__name']
        if sort_by in valid_sort_fields:
            if sort_order == 'desc':
                sort_by = f'-{sort_by}'
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')
            
        return queryset


class TaskUpdateView(generics.UpdateAPIView):
    """Quick update endpoint for task status changes"""
    serializer_class = TaskUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()
        
        if user.role == 'employee':
            # Employees can update tasks assigned to them directly or to their teams
            if hasattr(user, 'employee'):
                employee = user.employee
                team_ids = list(employee.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
                queryset = queryset.filter(
                    Q(employee=employee) |  # Tasks assigned directly to employee
                    Q(team_id__in=team_ids)  # Team tasks
                )
            else:
                queryset = queryset.none()
        
        return queryset
    
    def perform_update(self, serializer):
        instance = serializer.save()
        
        # Auto-update timestamps based on status
        if instance.status == 'doing' and not instance.started_at:
            instance.started_at = system_now()
            instance.save()
        elif instance.status == 'done' and not instance.completed_at:
            instance.completed_at = system_now()
            instance.save()


class TodayTasksView(APIView):
    """Get today's tasks for current user"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        today = datetime.date.today()
        
        # Both employees and admins can view their own tasks
        if user.role in ['employee', 'admin']:
            try:
                employee = user.employee
                tasks = Task.objects.filter(employee=employee, date=today)
                serializer = TaskSerializer(tasks, many=True, context={'request': request})
                
                # Calculate summary stats
                total_tasks = tasks.count()
                completed_tasks = tasks.filter(status='done').count()
                in_progress_tasks = tasks.filter(status='doing').count()
                overdue_tasks = sum(1 for task in tasks if task.is_overdue)
                
                completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                return Response({
                    'tasks': serializer.data,
                    'summary': {
                        'total_tasks': total_tasks,
                        'completed_tasks': completed_tasks,
                        'in_progress_tasks': in_progress_tasks,
                        'not_completed_tasks': total_tasks - completed_tasks - in_progress_tasks,
                        'overdue_tasks': overdue_tasks,
                        'completion_rate': round(completion_rate, 2)
                    }
                })
            except Employee.DoesNotExist:
                # User doesn't have an employee profile - this is an error
                return Response({
                    'error': 'Employee profile not found. Please contact administrator.'
                }, status=400)
        else:
            return Response({'error': 'Access denied'}, status=403)


class ManagerDashboardView(APIView):
    """Manager dashboard showing team tasks overview"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        if user.role != 'admin':
            return Response({'error': 'Access denied'}, status=403)
        
        # Get date parameter (default to today)
        date_param = request.query_params.get('date')
        if date_param:
            try:
                date = datetime.datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                date = datetime.date.today()
        else:
            date = datetime.date.today()
        
        # Get all employees with their tasks for the date
        employees = Employee.objects.all()
        dashboard_data = []
        
        for employee in employees:
            tasks = Task.objects.filter(employee=employee, date=date)
            
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='done').count()
            in_progress_tasks = tasks.filter(status='doing').count()
            not_completed_tasks = tasks.filter(status='to_do').count()
            overdue_tasks = sum(1 for task in tasks if task.is_overdue)
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            dashboard_data.append({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'not_completed_tasks': not_completed_tasks,
                'completion_rate': round(completion_rate, 2),
                'overdue_tasks': overdue_tasks,
                'tasks': TaskSerializer(tasks, many=True, context={'request': request}).data
            })
        
        # Overall team stats
        all_tasks = Task.objects.filter(date=date)
        team_total = all_tasks.count()
        team_completed = all_tasks.filter(status='done').count()
        team_completion_rate = (team_completed / team_total * 100) if team_total > 0 else 0
        
        return Response({
            'date': date,
            'employees': dashboard_data,
            'team_summary': {
                'total_tasks': team_total,
                'completed_tasks': team_completed,
                'completion_rate': round(team_completion_rate, 2),
                'total_employees': employees.count(),
                'active_employees': len([emp for emp in dashboard_data if emp['total_tasks'] > 0])
            }
        })


class TaskReportViewSet(viewsets.ModelViewSet):
    serializer_class = TaskReportSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user = self.request.user
        queryset = TaskReport.objects.all()
        
        if user.role == 'employee':
            # Employees see only their own reports
            if hasattr(user, 'employee'):
                queryset = queryset.filter(employee=user.employee)
            else:
                queryset = queryset.none()
        elif user.role == 'admin':
            # Admins see all reports, can filter by employee
            employee_id = self.request.query_params.get('employee_id')
            if employee_id:
                queryset = queryset.filter(employee_id=employee_id)
        
        return queryset.order_by('-date')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        if user.role == 'employee' and hasattr(user, 'employee'):
            serializer.save(employee=user.employee)
        else:
            raise PermissionDenied("Only employees can create task reports")


class TaskCommentViewSet(viewsets.ModelViewSet):
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        task_id = self.request.query_params.get('task_id')
        if task_id:
            return TaskComment.objects.filter(task_id=task_id)
        return TaskComment.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        task_id = self.request.data.get('task')
        
        try:
            task = Task.objects.get(id=task_id)
            
            # Check permissions
            if user.role == 'employee':
                if not hasattr(user, 'employee') or task.employee != user.employee:
                    raise PermissionDenied("You can only comment on your own tasks")
                is_manager_note = False
            else:
                is_manager_note = True
            
            serializer.save(author=user, is_manager_note=is_manager_note)
            
        except Task.DoesNotExist:
            raise ValidationError("Task not found")


class QuickTaskActionsView(APIView):
    """Quick actions for task management (mobile-friendly)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, task_id):
        user = request.user
        action = request.data.get('action')
        
        try:
            task = Task.objects.get(id=task_id)
            
            # Check permissions
            if user.role == 'employee':
                if not hasattr(user, 'employee') or task.employee != user.employee:
                    raise PermissionDenied("You can only update your own tasks")
            
            # Perform action
            if action == 'start':
                task.status = 'doing'
                if not task.started_at:
                    task.started_at = system_now()
                # If resuming from pause, clear pause time and add to total
                if task.paused_at:
                    pause_duration = (system_now() - task.paused_at).total_seconds() / 60
                    task.total_pause_time += round(pause_duration, 2)
                    task.paused_at = None
            elif action == 'complete':
                task.status = 'done'
                task.completed_at = system_now()
                # If completing from pause, add pause time to total
                if task.paused_at:
                    pause_duration = (system_now() - task.paused_at).total_seconds() / 60
                    task.total_pause_time += round(pause_duration, 2)
                    task.paused_at = None
            elif action == 'pause':
                task.paused_at = system_now()
                # Keep status as 'doing' so progress is maintained
            elif action == 'resume':
                if task.paused_at:
                    pause_duration = (system_now() - task.paused_at).total_seconds() / 60
                    print(f"[DEBUG RESUME] Task {task.id}:")
                    print(f"  - Paused at: {task.paused_at}")
                    print(f"  - Pause duration: {pause_duration:.2f} minutes")
                    print(f"  - Old total_pause_time: {task.total_pause_time}")
                    # استخدم round() بدلاً من int() لتقريب الدقائق
                    task.total_pause_time += round(pause_duration, 2)
                    print(f"  - New total_pause_time: {task.total_pause_time}")
                    task.paused_at = None
                    print(f"  - paused_at cleared: {task.paused_at}")
            elif action == 'reset_timer':
                task.started_at = None
                task.paused_at = None
                task.total_pause_time = 0
                task.status = 'to_do'
            elif action == 'add_note':
                note = request.data.get('note', '')
                task.notes = f"{task.notes}\n{note}" if task.notes else note
            else:
                return Response({'error': 'Invalid action'}, status=400)
            
            task.save()
            
            serializer = TaskSerializer(task, context={'request': request})
            return Response(serializer.data)
            
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=404)


class SubtaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing subtasks"""
    serializer_class = SubtaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        parent_task_id = self.request.query_params.get('parent_task', None)
        
        if parent_task_id:
            # Get subtasks for a specific parent task
            parent_task = get_object_or_404(Task, id=parent_task_id)
            
            # Check permissions - admin, task owner, team members, or team leader
            if user.role == 'admin':
                return Subtask.objects.filter(parent_task=parent_task)
            elif hasattr(user, 'employee'):
                employee = user.employee
                
                # Task owner can view all subtasks
                if parent_task.employee == employee:
                    return Subtask.objects.filter(parent_task=parent_task)
                # Team leader can view subtasks for team tasks
                elif parent_task.team and parent_task.team.team_leader == employee:
                    return Subtask.objects.filter(parent_task=parent_task)
                # Team members can view subtasks for team tasks or assigned to them
                elif parent_task.team and parent_task.team.memberships.filter(employee=employee, is_active=True).exists():
                    # If task is assigned to team without specific employee, team members can view all subtasks
                    if not parent_task.employee:
                        return Subtask.objects.filter(parent_task=parent_task)
                    # Otherwise, only view subtasks assigned to them
                    else:
                        return Subtask.objects.filter(parent_task=parent_task, assigned_employee=employee)
                # Individual assigned subtasks
                else:
                    return Subtask.objects.filter(parent_task=parent_task, assigned_employee=employee)
            else:
                return Subtask.objects.none()
        
        # If no parent_task specified, return relevant subtasks
        if user.role == 'admin':
            return Subtask.objects.all()
        elif hasattr(user, 'employee'):
            # Return subtasks for tasks owned by user or assigned to user
            return Subtask.objects.filter(
                Q(parent_task__employee=user.employee) |
                Q(assigned_employee=user.employee)
            ).distinct()
        else:
            return Subtask.objects.none()
    
    def perform_create(self, serializer):
        parent_task = serializer.validated_data['parent_task']
        user = self.request.user
        
        # Check if user can create subtasks for this task
        can_create = False
        
        if user.role == 'admin':
            can_create = True
        elif hasattr(user, 'employee'):
            employee = user.employee
            # Task owner can create subtasks
            if parent_task.employee == employee:
                can_create = True
            # Team leader can create subtasks for team tasks
            elif parent_task.team and parent_task.team.team_leader == employee:
                can_create = True
            # Team members can create subtasks for team tasks without specific assignee
            elif parent_task.team and not parent_task.employee and parent_task.team.memberships.filter(employee=employee, is_active=True).exists():
                can_create = True
            # Task creator (admin/manager) can create subtasks
            elif parent_task.created_by == user:
                can_create = True
        
        if not can_create:
            raise PermissionDenied("You don't have permission to create subtasks for this task")
        
        serializer.save()
    
    def perform_update(self, serializer):
        subtask = self.get_object()
        user = self.request.user
        
        # Check if user can update this subtask
        can_update = False
        
        if user.role == 'admin':
            can_update = True
        elif hasattr(user, 'employee'):
            # Task owner can update subtasks
            if subtask.parent_task.employee == user.employee:
                can_update = True
            # Team leader can update subtasks for team tasks
            elif subtask.parent_task.team and subtask.parent_task.team.team_leader == user.employee:
                can_update = True
            # Assigned employee can update their own subtasks (limited fields)
            elif subtask.assigned_employee == user.employee:
                # Only allow status, notes updates for assigned employees
                allowed_fields = {'status', 'notes'}
                if set(serializer.validated_data.keys()).issubset(allowed_fields):
                    can_update = True
        
        if not can_update:
            raise PermissionDenied("You don't have permission to update this subtask")
        
        serializer.save()


class SubtaskQuickActionsView(APIView):
    """Quick actions for subtasks (start, pause, complete, etc.)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, subtask_id):
        try:
            subtask = Subtask.objects.get(id=subtask_id)
            user = request.user
            
            # Check permissions - admin, task owner, team leader, or assigned employee
            can_perform_action = False
            
            if user.role == 'admin':
                can_perform_action = True
            elif hasattr(user, 'employee'):
                # Task owner can perform any action
                if subtask.parent_task.employee == user.employee:
                    can_perform_action = True
                # Team leader can perform actions on team tasks
                elif subtask.parent_task.team and subtask.parent_task.team.team_leader == user.employee:
                    can_perform_action = True
                # Assigned employee can perform actions on their subtasks
                elif subtask.assigned_employee == user.employee:
                    can_perform_action = True
            
            if not can_perform_action:
                raise PermissionDenied("You don't have permission to perform actions on this subtask")
            
            action = request.data.get('action')
            
            if action == 'start':
                subtask.status = 'doing'
                subtask.started_at = system_now()
                subtask.paused_at = None
            elif action == 'pause':
                if subtask.status == 'doing' and not subtask.paused_at:
                    subtask.paused_at = system_now()
            elif action == 'resume':
                if subtask.paused_at:
                    # Add current pause duration to total
                    pause_duration = (system_now() - subtask.paused_at).total_seconds() / 60
                    subtask.total_pause_time += round(pause_duration, 2)
                    subtask.paused_at = None
            elif action == 'complete':
                subtask.status = 'done'
                subtask.completed_at = system_now()
                if subtask.paused_at:
                    # Add final pause duration to total
                    pause_duration = (system_now() - subtask.paused_at).total_seconds() / 60
                    subtask.total_pause_time += round(pause_duration, 2)
                    subtask.paused_at = None
            elif action == 'reset_timer':
                subtask.started_at = None
                subtask.paused_at = None
                subtask.total_pause_time = 0
                subtask.status = 'to_do'
            elif action == 'add_note':
                note = request.data.get('note', '')
                subtask.notes = f"{subtask.notes}\n{note}" if subtask.notes else note
            else:
                return Response({'error': 'Invalid action'}, status=400)
            
            subtask.save()
            
            serializer = SubtaskSerializer(subtask)
            return Response(serializer.data)
            
        except Subtask.DoesNotExist:
            return Response({'error': 'Subtask not found'}, status=404)


class AssignableEmployeesView(APIView):
    """Get employees that can be assigned to subtasks for a specific task"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id)
            user = request.user
            
            # Check if user can assign subtasks for this task
            can_assign = False
            if user.role == 'admin':
                can_assign = True
            elif hasattr(user, 'employee'):
                # Task owner can assign subtasks
                if task.employee == user.employee:
                    can_assign = True
                # Team leader can assign subtasks for team tasks
                elif task.team and task.team.team_leader == user.employee:
                    can_assign = True
                # Task creator can assign subtasks
                elif task.created_by == user:
                    can_assign = True
            
            if not can_assign:
                return Response({'error': 'Permission denied'}, status=403)
            
            # Get assignable employees
            assignable_employees = []
            
            if task.team:
                # If task is assigned to a team, get active team members
                team_memberships = TeamMembership.objects.filter(
                    team=task.team, 
                    is_active=True
                ).select_related('employee')
                
                for membership in team_memberships:
                    employee = membership.employee
                    assignable_employees.append({
                        'id': str(employee.id),
                        'name': employee.name,
                        'position': employee.position,
                        'department': employee.department,
                        'team_role': membership.role
                    })
            else:
                # If no specific team, task owner can assign to themselves
                if hasattr(user, 'employee'):
                    employee = user.employee
                    assignable_employees.append({
                        'id': str(employee.id),
                        'name': employee.name,
                        'position': employee.position,
                        'department': employee.department,
                        'team_role': 'task_owner'
                    })
            
            return Response({'employees': assignable_employees})
            
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=404)


class TeamMembersView(APIView):
    """Get team members for subtask assignment during task creation"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id)
            user = request.user
            
            # Check if user can view team members
            can_view = False
            if user.role == 'admin':
                can_view = True
            elif hasattr(user, 'employee'):
                # Team members can see their team members
                if team.memberships.filter(employee=user.employee, is_active=True).exists():
                    can_view = True
                # Team leader can see team members
                elif team.team_leader == user.employee:
                    can_view = True
            
            if not can_view:
                return Response({'error': 'Permission denied'}, status=403)
            
            # Get team members
            team_memberships = TeamMembership.objects.filter(
                team=team, 
                is_active=True
            ).select_related('employee')
            
            employees = []
            for membership in team_memberships:
                employee = membership.employee
                employees.append({
                    'id': str(employee.id),
                    'name': employee.name,
                    'position': employee.position,
                    'department': employee.department,
                    'team_role': membership.role
                })
            
            return Response({'employees': employees})
            
        except Team.DoesNotExist:
            return Response({'error': 'Team not found'}, status=404)


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for team management"""
    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TeamCreateSerializer
        return TeamSerializer
    
    def get_queryset(self):
        queryset = Team.objects.select_related('team_leader', 'created_by')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by team leader
        team_leader = self.request.query_params.get('team_leader')
        if team_leader:
            queryset = queryset.filter(team_leader_id=team_leader)
        
        # Search by name
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TeamMembershipViewSet(viewsets.ModelViewSet):
    """ViewSet for team membership management"""
    queryset = TeamMembership.objects.all()
    serializer_class = TeamMembershipSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = TeamMembership.objects.select_related('team', 'employee')
        
        # Filter by team
        team = self.request.query_params.get('team')
        if team:
            queryset = queryset.filter(team_id=team)
        
        # Filter by employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(employee_id=employee)
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-joined_at')


class TeamTaskViewSet(viewsets.ModelViewSet):
    """ViewSet for team task management"""
    queryset = TeamTask.objects.all()
    serializer_class = TeamTaskSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = TeamTask.objects.select_related('task', 'team', 'assigned_by')
        
        # Filter by team
        team = self.request.query_params.get('team')
        if team:
            queryset = queryset.filter(team_id=team)
        
        # Filter by task status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(task__status=status)
        
        # Filter by assigned employee
        employee = self.request.query_params.get('employee')
        if employee:
            queryset = queryset.filter(task__employee_id=employee)
        
        # Filter by team priority
        priority = self.request.query_params.get('team_priority')
        if priority:
            queryset = queryset.filter(team_priority=priority)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class AssignTaskToTeamView(APIView):
    """View to assign a task to a team"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        task_id = request.data.get('task_id')
        team_id = request.data.get('team_id')
        team_priority = request.data.get('team_priority', 'medium')
        team_notes = request.data.get('team_notes', '')
        can_reassign = request.data.get('can_reassign', True)
        
        # For backward compatibility: if task_id is provided, assign existing task
        # If not provided, create a new task with the provided parameters
        title = request.data.get('title')
        description = request.data.get('description')
        priority = request.data.get('priority', 'medium')
        estimated_minutes = request.data.get('estimated_minutes')
        
        if not team_id:
            return Response({'error': 'team_id is required'}, status=400)
        
        # If task_id is not provided, create a task with defaults if needed
        if not task_id:
            # Provide reasonable defaults if title/description not provided
            if not title:
                title = f"Team Task - {team_priority.title()} Priority"
            if not description:
                description = f"Task assigned to team on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
            if estimated_minutes is None:
                estimated_minutes = 60  # Default to 1 hour
        
        try:
            team = Team.objects.get(id=team_id)
            
            if task_id:
                # Assign existing task to team
                task = Task.objects.get(id=task_id)
                
                # Check if task is already assigned to a team
                if hasattr(task, 'team_assignment'):
                    return Response({'error': 'Task is already assigned to a team'}, status=400)
                
                # Update task with team
                task.team = team
                task.save()
            else:
                # Create new task and assign to team
                # Check if a specific employee is requested
                employee_id = request.data.get('employee_id')
                employee_to_assign = None
                
                if employee_id:
                    # Assign to specific employee if requested
                    try:
                        employee_to_assign = Employee.objects.get(id=employee_id)
                        # Verify the employee is part of the team
                        if not team.memberships.filter(employee=employee_to_assign, is_active=True).exists():
                            return Response({'error': 'Employee is not an active member of this team'}, status=400)
                    except Employee.DoesNotExist:
                        return Response({'error': 'Employee not found'}, status=404)
                # If no specific employee requested, leave as team-only assignment
                
                task = Task.objects.create(
                    title=title,
                    description=description,
                    priority=priority,
                    estimated_minutes=estimated_minutes,
                    notes=team_notes,
                    created_by=request.user,
                    team=team,
                    employee=employee_to_assign  # Can be None for team-only assignments
                )
            
            # Create team task assignment
            team_task = TeamTask.objects.create(
                task=task,
                team=team,
                assigned_by=request.user,
                team_priority=team_priority,
                team_notes=team_notes,
                can_reassign=can_reassign
            )
            
            serializer = TeamTaskSerializer(team_task)
            return Response({
                'message': 'Task successfully assigned to team' if task_id else 'Task created and assigned to team',
                'team_task': serializer.data
            }, status=201)
            
        except Task.DoesNotExist:
            return Response({'error': 'Task not found'}, status=404)
        except Team.DoesNotExist:
            return Response({'error': 'Team not found'}, status=404)


class TeamDashboardView(APIView):
    """View for team dashboard data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id)
            
            # Get team statistics
            team_tasks = TeamTask.objects.filter(team=team)
            total_tasks = team_tasks.count()
            completed_tasks = team_tasks.filter(task__status='completed').count()
            in_progress_tasks = team_tasks.filter(task__status='in_progress').count()
            overdue_tasks = team_tasks.filter(
                task__due_date__lt=timezone.now().date(),
                task__status__in=['to_do', 'in_progress']
            ).count()
            
            # Get team members with their task counts
            members_data = []
            for membership in team.memberships.filter(is_active=True):
                member_tasks = team_tasks.filter(task__employee=membership.employee)
                member_completed = member_tasks.filter(task__status='completed').count()
                member_total = member_tasks.count()
                
                members_data.append({
                    'employee_id': membership.employee.id,
                    'employee_name': membership.employee.name,
                    'role': membership.role,
                    'total_tasks': member_total,
                    'completed_tasks': member_completed,
                    'completion_rate': (member_completed / member_total * 100) if member_total > 0 else 0
                })
            
            # Get recent tasks
            recent_tasks = team_tasks.order_by('-created_at')[:10]
            tasks_serializer = TeamTaskSerializer(recent_tasks, many=True)
            
            dashboard_data = {
                'team': TeamSerializer(team).data,
                'statistics': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'in_progress_tasks': in_progress_tasks,
                    'overdue_tasks': overdue_tasks,
                    'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                },
                'members': members_data,
                'recent_tasks': tasks_serializer.data
            }
            
            return Response(dashboard_data)
            
        except Team.DoesNotExist:
            return Response({'error': 'Team not found'}, status=404)


# GPS Utility Functions
import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two GPS coordinates using Haversine formula
    Returns distance in meters
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in meters
    r = 6371000
    
    return c * r


# Office Location Management Views
class OfficeLocationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing office locations (Admin only)"""
    queryset = OfficeLocation.objects.all()
    serializer_class = OfficeLocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Only admins can create, update, or delete office locations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsEmployer]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        # Deactivate all other office locations when creating a new one
        OfficeLocation.objects.filter(is_active=True).update(is_active=False)
        serializer.save(set_by=self.request.user, is_active=True)
    
    def perform_update(self, serializer):
        instance = serializer.save()
        # If this location is being activated, deactivate others
        if instance.is_active:
            OfficeLocation.objects.exclude(id=instance.id).update(is_active=False)


class SetOfficeLocationView(APIView):
    """API view for admin to set office location using their current GPS coordinates"""
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def post(self, request):
        try:
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            name = request.data.get('name', 'Main Office')
            radius_meters = request.data.get('radius_meters', 100)
            
            if not latitude or not longitude:
                return Response({
                    'error': 'Latitude and longitude are required'
                }, status=400)
            
            # Deactivate all existing office locations
            OfficeLocation.objects.filter(is_active=True).update(is_active=False)
            
            # Create new office location
            office_location = OfficeLocation.objects.create(
                name=name,
                latitude=latitude,
                longitude=longitude,
                radius_meters=radius_meters,
                set_by=request.user,
                is_active=True
            )
            
            serializer = OfficeLocationSerializer(office_location)
            return Response({
                'message': 'Office location set successfully',
                'office_location': serializer.data
            }, status=201)
            
        except Exception as e:
            return Response({
                'error': f'Failed to set office location: {str(e)}'
            }, status=500)


class CurrentOfficeLocationView(APIView):
    """Get the currently active office location"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        office_location = OfficeLocation.get_active_location()
        if office_location:
            serializer = OfficeLocationSerializer(office_location)
            return Response(serializer.data)
        else:
            return Response({
                'message': 'No active office location set'
            }, status=404)


# Multi-Wallet System Utilities
from decimal import Decimal
from django.db import transaction

def get_or_create_wallet_system(employee):
    """Get or create the complete wallet system for an employee"""
    wallet_system, created = EmployeeWalletSystem.objects.get_or_create(employee=employee)
    
    # Ensure all wallet types exist
    if not hasattr(wallet_system, 'main_wallet'):
        MainWallet.objects.create(wallet_system=wallet_system)
    if not hasattr(wallet_system, 'reimbursement_wallet'):
        ReimbursementWallet.objects.create(wallet_system=wallet_system)
    if not hasattr(wallet_system, 'advance_wallet'):
        AdvanceWallet.objects.create(wallet_system=wallet_system)
    
    return wallet_system

def create_wallet_transaction(wallet_system, wallet_type, transaction_type, amount, description, created_by=None, reimbursement_request=None):
    """Create a transaction and update the appropriate wallet balance"""
    with transaction.atomic():
        # Create the transaction record
        wallet_transaction = MultiWalletTransaction.objects.create(
            wallet_system=wallet_system,
            wallet_type=wallet_type,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            created_by=created_by,
            reimbursement_request=reimbursement_request
        )
        
        # Update the appropriate wallet balance
        if wallet_type == 'main':
            wallet = wallet_system.main_wallet
        elif wallet_type == 'reimbursement':
            wallet = wallet_system.reimbursement_wallet
        elif wallet_type == 'advance':
            wallet = wallet_system.advance_wallet
        else:
            raise ValueError(f"Invalid wallet type: {wallet_type}")
        
        # Determine if this is a credit or debit based on transaction type
        credit_transactions = [
            'salary_credit', 'bonus_credit', 'manual_deposit', 'reimbursement_payment',
            'reimbursement_approved', 'advance_taken'
        ]
        debit_transactions = [
            'advance_withdrawal', 'manual_withdrawal', 'advance_deduction', 
            'reimbursement_paid', 'advance_repaid'
        ]
        
        if transaction_type in credit_transactions:
            wallet.balance = Decimal(str(wallet.balance)) + Decimal(str(amount))
        elif transaction_type in debit_transactions:
            wallet.balance = Decimal(str(wallet.balance)) - Decimal(str(amount))
        else:
            raise ValueError(f"Unknown transaction type: {transaction_type}")
        
        wallet.save()
        return wallet_transaction

def transfer_between_wallets(wallet_system, from_wallet_type, to_wallet_type, amount, description, transfer_type, created_by=None):
    """Transfer money between different wallet types for the same employee"""
    with transaction.atomic():
        # Create debit transaction for source wallet
        debit_transaction_types = {
            'reimbursement_to_main': 'reimbursement_paid',
            'main_to_advance': 'advance_deduction'
        }
        
        # Create credit transaction for destination wallet  
        credit_transaction_types = {
            'reimbursement_to_main': 'reimbursement_payment',
            'main_to_advance': 'advance_repaid'
        }
        
        from_transaction = create_wallet_transaction(
            wallet_system, from_wallet_type, debit_transaction_types[transfer_type],
            amount, description, created_by
        )
        
        to_transaction = create_wallet_transaction(
            wallet_system, to_wallet_type, credit_transaction_types[transfer_type],
            amount, description, created_by
        )
        
        # Create transfer record
        wallet_transfer = WalletTransfer.objects.create(
            wallet_system=wallet_system,
            transfer_type=transfer_type,
            amount=amount,
            description=description,
            from_wallet_type=from_wallet_type,
            to_wallet_type=to_wallet_type,
            from_transaction=from_transaction,
            to_transaction=to_transaction,
            created_by=created_by
        )
        
        # Link transactions to each other
        from_transaction.related_transaction = to_transaction
        to_transaction.related_transaction = from_transaction
        from_transaction.save()
        to_transaction.save()
        
        return wallet_transfer

# Multi-Wallet System Views
class EmployeeWalletSystemView(generics.RetrieveAPIView):
    """Get employee's complete wallet system (all three wallets)"""
    serializer_class = EmployeeWalletSystemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        employee_id = self.kwargs.get("employee_id")
        employee = Employee.objects.get(id=employee_id)
        
        # Check permissions - admin can see all, employees can only see their own
        if self.request.user.role != 'admin' and self.request.user.employee.id != employee_id:
            raise PermissionDenied("You can only view your own wallet")
        
        return get_or_create_wallet_system(employee)

class WalletTransactionCreateView(generics.CreateAPIView):
    """Create transactions for specific wallet types"""
    serializer_class = MultiWalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        employee_id = self.kwargs["employee_id"]
        employee = Employee.objects.get(id=employee_id)
        wallet_system = get_or_create_wallet_system(employee)
        
        # Only admins can create manual transactions for employees
        if self.request.user.role != 'admin':
            raise PermissionDenied("Only admins can create wallet transactions")
        
        transaction_data = serializer.validated_data
        transaction_type = transaction_data['transaction_type']
        amount = transaction_data['amount']
        description = transaction_data['description']
        
        # Handle special transfer-type transactions
        if transaction_type == 'reimbursement_paid':
            # This should be a transfer from reimbursement to main wallet
            transfer_between_wallets(
                wallet_system=wallet_system,
                from_wallet_type='reimbursement',
                to_wallet_type='main', 
                amount=amount,
                description=description,
                transfer_type='reimbursement_to_main',
                created_by=self.request.user
            )
        elif transaction_type == 'advance_repaid':
            # This should be a transfer from main to advance wallet
            transfer_between_wallets(
                wallet_system=wallet_system,
                from_wallet_type='main',
                to_wallet_type='advance',
                amount=amount, 
                description=description,
                transfer_type='main_to_advance',
                created_by=self.request.user
            )
        elif transaction_type == 'advance_withdrawal':
            # Employee takes advance: money leaves main wallet, advance debt increases
            create_wallet_transaction(
                wallet_system=wallet_system,
                wallet_type='main',
                transaction_type='advance_withdrawal',
                amount=amount,
                description=description,
                created_by=self.request.user
            )
            # Create corresponding advance debt record
            advance_transaction = create_wallet_transaction(
                wallet_system=wallet_system,
                wallet_type='advance',
                transaction_type='advance_taken',
                amount=amount,
                description=f"Advance debt: {description}",
                created_by=self.request.user
            )
        elif transaction_type == 'advance_deduction':
            # Salary deduction to repay advance: main wallet reduced, advance debt reduced
            create_wallet_transaction(
                wallet_system=wallet_system,
                wallet_type='main',
                transaction_type='advance_deduction',
                amount=amount,
                description=description,
                created_by=self.request.user
            )
            # Create corresponding advance repayment record
            repayment_transaction = create_wallet_transaction(
                wallet_system=wallet_system,
                wallet_type='advance',
                transaction_type='advance_repaid',
                amount=amount,
                description=f"Advance repayment: {description}",
                created_by=self.request.user
            )
        else:
            # Create regular single transaction
            create_wallet_transaction(
                wallet_system=wallet_system,
                wallet_type=transaction_data['wallet_type'],
                transaction_type=transaction_type,
                amount=amount,
                description=description,
                created_by=self.request.user
            )

class WalletTransactionListView(generics.ListAPIView):
    """List all transactions for an employee's wallet system"""
    serializer_class = MultiWalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        employee_id = self.kwargs["employee_id"]
        
        # Check permissions
        if self.request.user.role != 'admin' and self.request.user.employee.id != employee_id:
            raise PermissionDenied("You can only view your own transactions")
        
        return MultiWalletTransaction.objects.filter(wallet_system__employee__id=employee_id)

class WalletTransferCreateView(generics.CreateAPIView):
    """Create transfers between wallet types (admin only)"""
    serializer_class = WalletTransferSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        if self.request.user.role != 'admin':
            raise PermissionDenied("Only admins can create wallet transfers")
        
        employee_id = self.kwargs["employee_id"]
        employee = Employee.objects.get(id=employee_id)
        wallet_system = get_or_create_wallet_system(employee)
        
        transfer_data = serializer.validated_data
        
        transfer_between_wallets(
            wallet_system=wallet_system,
            from_wallet_type=transfer_data['from_wallet_type'],
            to_wallet_type=transfer_data['to_wallet_type'],
            amount=transfer_data['amount'],
            description=transfer_data['description'],
            transfer_type=transfer_data['transfer_type'],
            created_by=self.request.user
        )


# Client Complaint System Views

class ComplaintCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing complaint categories"""
    queryset = ComplaintCategory.objects.all()
    serializer_class = ComplaintCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Admins and complaint admins with manage_categories permission can see all categories
        if self.request.user.role == 'admin' or has_complaint_admin_permission(self.request.user, 'can_manage_categories'):
            return ComplaintCategory.objects.all()
        return ComplaintCategory.objects.filter(is_active=True)


class PublicComplaintCategoryListView(generics.ListAPIView):
    """Public view for listing active complaint categories"""
    queryset = ComplaintCategory.objects.filter(is_active=True)
    serializer_class = ComplaintCategorySerializer
    permission_classes = []  # No authentication required


class ClientComplaintViewSet(viewsets.ModelViewSet):
    """ViewSet for managing client complaints"""
    queryset = ClientComplaint.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClientComplaintSubmissionSerializer
        return ClientComplaintSerializer
    
    def get_queryset(self):
        queryset = ClientComplaint.objects.select_related(
            'category', 'reviewed_by', 'resolved_by'
        ).prefetch_related(
            'attachments', 'assignments__team', 'tasks__task', 'comments__author', 'status_history__changed_by'
        )
        
        # Filter based on user role and team assignments (unless filtering by specific team)
        team_filter = self.request.query_params.get('team')
        if not team_filter:  # Only apply general team filtering if not filtering by specific team
            if self.request.user.role == 'admin':
                # Admins can see all complaints
                pass
            elif self.request.user.role == 'manager':
                # Managers can see complaints assigned to their teams
                user_teams = Team.objects.filter(memberships__employee__user=self.request.user)
                queryset = queryset.filter(assignments__team__in=user_teams, assignments__is_active=True).distinct()
            else:
                # Regular employees can see complaints assigned to their teams
                user_teams = Team.objects.filter(memberships__employee__user=self.request.user)
                queryset = queryset.filter(assignments__team__in=user_teams, assignments__is_active=True).distinct()
        
        # Apply query parameter filters
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by specific team (for task assignment)
        if team_filter:
            # Ensure user has access to this team
            if self.request.user.role == 'admin':
                # Admins can filter by any team
                queryset = queryset.filter(assignments__team=team_filter, assignments__is_active=True)
            else:
                # Check if user is member of the requested team
                user_teams = Team.objects.filter(memberships__employee__user=self.request.user)
                if user_teams.filter(id=team_filter).exists():
                    queryset = queryset.filter(assignments__team=team_filter, assignments__is_active=True)
                else:
                    # User doesn't have access to this team, return empty queryset
                    queryset = queryset.none()
        
        return queryset.order_by('-created_at')
    
    def destroy(self, request, *args, **kwargs):
        """Delete a complaint - Only admins can delete complaints"""
        complaint = self.get_object()
        user = request.user
        
        # Only admins can delete complaints
        if user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can delete complaints.")
        
        # Log the deletion for audit purposes
        complaint_id = complaint.id
        complaint_title = complaint.title
        print(f"Admin {user.username} ({user.id}) deleted complaint {complaint_id}: '{complaint_title}'")
        
        return super().destroy(request, *args, **kwargs)


class PublicClientComplaintCreateView(generics.CreateAPIView):
    """Public endpoint for clients to submit complaints"""
    queryset = ClientComplaint.objects.all()
    serializer_class = ClientComplaintSubmissionSerializer
    permission_classes = []  # No authentication required
    
    def perform_create(self, serializer):
        complaint = serializer.save()
        
        # Create status history entry
        ClientComplaintStatusHistory.objects.create(
            complaint=complaint,
            old_status='pending_review',
            new_status='pending_review',
            changed_by=None,  # System created
            reason="شكوى جديدة من العميل"
        )


class ClientComplaintReviewView(APIView):
    """View for reviewing complaints (approve/reject)"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'enum': ['approved', 'rejected']},
                    'review_notes': {'type': 'string'},
                    'rejection_reason': {'type': 'string'}
                },
                'required': ['status']
            }
        }
    )
    def post(self, request, pk):
        # Check if user has complaint admin permission or is regular admin/manager
        if not (request.user.role in ['admin', 'manager'] or has_complaint_admin_permission(request.user, 'can_review')):
            raise PermissionDenied("You don't have permission to review complaints")
        
        complaint = get_object_or_404(ClientComplaint, pk=pk)
        
        if complaint.status != 'pending_review':
            return Response({'error': 'يمكن مراجعة الشكاوى في حالة انتظار المراجعة فقط'}, status=400)
        
        status = request.data.get('status')
        review_notes = request.data.get('review_notes', '')
        rejection_reason = request.data.get('rejection_reason', '')
        
        if status not in ['approved', 'rejected']:
            return Response({'error': 'حالة غير صالحة'}, status=400)
        
        if status == 'rejected' and not rejection_reason:
            return Response({'error': 'سبب الرفض مطلوب'}, status=400)
        
        # Record status history
        ClientComplaintStatusHistory.objects.create(
            complaint=complaint,
            old_status=complaint.status,
            new_status=status,
            changed_by=request.user,
            reason=rejection_reason if status == 'rejected' else review_notes
        )
        
        # Update complaint
        complaint.status = status
        complaint.reviewed_by = request.user
        complaint.reviewed_at = timezone.now()
        complaint.review_notes = review_notes
        if status == 'rejected':
            complaint.rejection_reason = rejection_reason
        complaint.save()
        
        return Response({
            'message': 'تم تحديث حالة الشكوى بنجاح',
            'status': status,
            'complaint_id': str(complaint.id)
        })


class ClientComplaintAssignmentView(APIView):
    """View for assigning complaints to teams"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'team_id': {'type': 'string'},
                    'notes': {'type': 'string'}
                },
                'required': ['team_id']
            }
        }
    )
    def post(self, request, pk):
        if request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can assign complaints")
        
        complaint = get_object_or_404(ClientComplaint, pk=pk)
        
        if complaint.status not in ['approved', 'in_progress']:
            return Response({'error': 'يمكن تخصيص الشكاوى المعتمدة أو قيد المعالجة فقط'}, status=400)
        
        team_id = request.data.get('team_id')
        notes = request.data.get('notes', '')
        
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response({'error': 'الفريق غير موجود'}, status=404)
        
        # Check if already assigned
        existing_assignment = ClientComplaintAssignment.objects.filter(
            complaint=complaint, team=team, is_active=True
        ).first()
        
        if existing_assignment:
            return Response({'error': 'تم تخصيص هذه الشكوى للفريق مسبقاً'}, status=400)
        
        # Create assignment
        assignment = ClientComplaintAssignment.objects.create(
            complaint=complaint,
            team=team,
            assigned_by=request.user,
            notes=notes
        )
        
        # Update complaint status if not already in progress
        if complaint.status == 'approved':
            ClientComplaintStatusHistory.objects.create(
                complaint=complaint,
                old_status=complaint.status,
                new_status='in_progress',
                changed_by=request.user,
                reason=f"تم تخصيص الشكوى للفريق: {team.name}"
            )
            complaint.status = 'in_progress'
            complaint.save()
        
        return Response({
            'message': 'تم تخصيص الشكوى للفريق بنجاح',
            'assignment_id': assignment.id,
            'team_name': team.name
        })


class ClientComplaintEmployeeAssignmentView(APIView):
    """View for assigning complaints to individual employees"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'employee_id': {'type': 'string'},
                    'notes': {'type': 'string'}
                },
                'required': ['employee_id']
            }
        }
    )
    def post(self, request, pk):
        if request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can assign complaints")
        
        complaint = get_object_or_404(ClientComplaint, pk=pk)
        
        if complaint.status not in ['approved', 'in_progress']:
            return Response({'error': 'يمكن تخصيص الشكاوى المعتمدة أو قيد المعالجة فقط'}, status=400)
        
        employee_id = request.data.get('employee_id')
        notes = request.data.get('notes', '')
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'error': 'الموظف غير موجود'}, status=404)
        
        # Check if already assigned
        existing_assignment = ClientComplaintEmployeeAssignment.objects.filter(
            complaint=complaint, employee=employee, is_active=True
        ).first()
        
        if existing_assignment:
            return Response({'error': 'تم تخصيص هذه الشكوى للموظف مسبقاً'}, status=400)
        
        # Create assignment
        assignment = ClientComplaintEmployeeAssignment.objects.create(
            complaint=complaint,
            employee=employee,
            assigned_by=request.user,
            notes=notes
        )
        
        # Update complaint status if not already in progress
        if complaint.status == 'approved':
            ClientComplaintStatusHistory.objects.create(
                complaint=complaint,
                old_status=complaint.status,
                new_status='in_progress',
                changed_by=request.user,
                reason=f"تم تخصيص الشكوى للموظف: {employee.name}"
            )
            complaint.status = 'in_progress'
            complaint.save()
        
        return Response({
            'message': 'تم تخصيص الشكوى للموظف بنجاح',
            'assignment_id': assignment.id,
            'employee_name': employee.name
        })


class ClientComplaintMultipleAssignmentView(APIView):
    """View for assigning complaints to multiple teams and employees simultaneously"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'team_ids': {'type': 'array', 'items': {'type': 'string'}},
                    'employee_ids': {'type': 'array', 'items': {'type': 'string'}},
                    'notes': {'type': 'string'}
                }
            }
        }
    )
    def post(self, request, pk):
        if request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can assign complaints")
        
        complaint = get_object_or_404(ClientComplaint, pk=pk)
        
        if complaint.status not in ['approved', 'in_progress']:
            return Response({'error': 'يمكن تخصيص الشكاوى المعتمدة أو قيد المعالجة فقط'}, status=400)
        
        team_ids = request.data.get('team_ids', [])
        employee_ids = request.data.get('employee_ids', [])
        notes = request.data.get('notes', '')
        
        if not team_ids and not employee_ids:
            return Response({'error': 'يجب تحديد فريق واحد أو موظف واحد على الأقل'}, status=400)
        
        created_assignments = []
        errors = []
        
        # Assign to teams
        for team_id in team_ids:
            try:
                team = Team.objects.get(id=team_id)
                existing_assignment = ClientComplaintAssignment.objects.filter(
                    complaint=complaint, team=team, is_active=True
                ).first()
                
                if not existing_assignment:
                    assignment = ClientComplaintAssignment.objects.create(
                        complaint=complaint,
                        team=team,
                        assigned_by=request.user,
                        notes=notes
                    )
                    created_assignments.append({
                        'type': 'team',
                        'id': assignment.id,
                        'name': team.name
                    })
                else:
                    errors.append(f'الفريق {team.name} مخصص مسبقاً')
            except Team.DoesNotExist:
                errors.append(f'الفريق {team_id} غير موجود')
        
        # Assign to employees
        for employee_id in employee_ids:
            try:
                employee = Employee.objects.get(id=employee_id)
                existing_assignment = ClientComplaintEmployeeAssignment.objects.filter(
                    complaint=complaint, employee=employee, is_active=True
                ).first()
                
                if not existing_assignment:
                    assignment = ClientComplaintEmployeeAssignment.objects.create(
                        complaint=complaint,
                        employee=employee,
                        assigned_by=request.user,
                        notes=notes
                    )
                    created_assignments.append({
                        'type': 'employee',
                        'id': assignment.id,
                        'name': employee.name
                    })
                else:
                    errors.append(f'الموظف {employee.name} مخصص مسبقاً')
            except Employee.DoesNotExist:
                errors.append(f'الموظف {employee_id} غير موجود')
        
        # Update complaint status if assignments were created
        if created_assignments and complaint.status == 'approved':
            assignment_names = [a['name'] for a in created_assignments]
            ClientComplaintStatusHistory.objects.create(
                complaint=complaint,
                old_status=complaint.status,
                new_status='in_progress',
                changed_by=request.user,
                reason=f"تم تخصيص الشكوى إلى: {', '.join(assignment_names)}"
            )
            complaint.status = 'in_progress'
            complaint.save()
        
        return Response({
            'message': 'تم إجراء التخصيصات',
            'created_assignments': created_assignments,
            'errors': errors,
            'success_count': len(created_assignments)
        })


class ClientComplaintRemoveTeamAssignmentView(APIView):
    """View for removing team assignment from a complaint"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk, assignment_id):
        if not (request.user.role in ['admin', 'manager'] or has_complaint_admin_permission(request.user, 'can_manage_assignments')):
            raise PermissionDenied("You don't have permission to remove assignments")
        
        complaint = get_object_or_404(ClientComplaint, pk=pk)
        assignment = get_object_or_404(ClientComplaintAssignment, pk=assignment_id, complaint=complaint)
        
        # Mark assignment as inactive instead of deleting
        assignment.is_active = False
        assignment.save()
        
        # Add status history record
        ClientComplaintStatusHistory.objects.create(
            complaint=complaint,
            old_status=complaint.status,
            new_status=complaint.status,  # Status doesn't change
            changed_by=request.user,
            reason=f"تم إلغاء تخصيص الفريق: {assignment.team.name}"
        )
        
        return Response({
            'message': f'تم إلغاء تخصيص الفريق {assignment.team.name} بنجاح',
            'assignment_id': assignment_id
        })


class ClientComplaintRemoveEmployeeAssignmentView(APIView):
    """View for removing employee assignment from a complaint"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, pk, assignment_id):
        if not (request.user.role in ['admin', 'manager'] or has_complaint_admin_permission(request.user, 'can_manage_assignments')):
            raise PermissionDenied("You don't have permission to remove assignments")
        
        complaint = get_object_or_404(ClientComplaint, pk=pk)
        assignment = get_object_or_404(ClientComplaintEmployeeAssignment, pk=assignment_id, complaint=complaint)
        
        # Mark assignment as inactive instead of deleting
        assignment.is_active = False
        assignment.save()
        
        # Add status history record
        ClientComplaintStatusHistory.objects.create(
            complaint=complaint,
            old_status=complaint.status,
            new_status=complaint.status,  # Status doesn't change
            changed_by=request.user,
            reason=f"تم إلغاء تخصيص الموظف: {assignment.employee.name}"
        )
        
        return Response({
            'message': f'تم إلغاء تخصيص الموظف {assignment.employee.name} بنجاح',
            'assignment_id': assignment_id
        })


class ClientComplaintStatusViewSet(viewsets.ModelViewSet):
    """ViewSet for managing custom complaint statuses"""
    queryset = ClientComplaintStatus.objects.all()
    serializer_class = ClientComplaintStatusSerializer
    permission_classes = [IsAuthenticated, IsAdminOrComplaintAdmin]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        responses={200: ClientComplaintStatusSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='active')
    def active_statuses(self, request):
        """Get all active custom statuses"""
        active_statuses = ClientComplaintStatus.objects.filter(is_active=True).order_by('display_order', 'name')
        serializer = self.get_serializer(active_statuses, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'default_statuses': {'type': 'array'},
                'custom_statuses': {'type': 'array'},
                'all_statuses': {'type': 'array'}
            }
        }}
    )
    @action(detail=False, methods=['get'], url_path='all-available')
    def all_available_statuses(self, request):
        """Get all available statuses (default + custom)"""
        from .models import ClientComplaint
        
        # Get default statuses
        default_statuses = [
            {
                'type': 'default',
                'name': key,
                'label': value,
                'color': '#6b7280',
                'id': key
            }
            for key, value in ClientComplaint.STATUS_CHOICES
        ]
        
        # Get custom statuses
        custom_statuses = []
        for status in ClientComplaintStatus.objects.filter(is_active=True).order_by('display_order', 'name'):
            custom_statuses.append({
                'type': 'custom',
                'name': status.name,
                'label': status.label,
                'color': status.color,
                'id': status.id,
                'description': status.description,
                'is_final_status': status.is_final_status
            })
        
        all_statuses = default_statuses + custom_statuses
        
        return Response({
            'default_statuses': default_statuses,
            'custom_statuses': custom_statuses,
            'all_statuses': all_statuses
        })


class ClientComplaintStatusUpdateView(APIView):
    """View for updating complaint status (supports both default and custom statuses)"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=ClientComplaintStatusUpdateSerializer,
        responses={200: {
            'type': 'object',
            'properties': {
                'message': {'type': 'string'},
                'old_status': {'type': 'string'},
                'new_status': {'type': 'string'},
                'status_display': {'type': 'string'},
                'status_color': {'type': 'string'}
            }
        }}
    )
    def post(self, request, pk):
        complaint = get_object_or_404(ClientComplaint, pk=pk)
        
        # Check if user has permission to update this complaint
        if request.user.role == 'admin':
            # Admins can update any complaint
            pass
        elif has_complaint_admin_permission(request.user, 'can_update_status'):
            # Users with complaint admin permission can update any complaint
            pass
        else:
            # Check if user is in a team assigned to this complaint
            user_teams = Team.objects.filter(memberships__employee__user=request.user)
            assigned_teams = Team.objects.filter(
                client_complaint_assignments__complaint=complaint,
                client_complaint_assignments__is_active=True
            )
            
            if not user_teams.filter(id__in=assigned_teams).exists():
                raise PermissionDenied("ليس لديك صلاحية تحديث هذه الشكوى")
        
        # Validate input data
        serializer = ClientComplaintStatusUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=400)
        
        status_type = serializer.validated_data['status_type']
        status_value = serializer.validated_data['status_value']
        notes = serializer.validated_data.get('notes', '')
        
        # Store old status info
        old_effective_status = complaint.effective_status
        old_status_display = complaint.current_status_display
        
        # Check if complaint is already in the requested status
        if status_type == 'default' and complaint.status == status_value and not complaint.custom_status:
            return Response({'error': 'الشكوى في هذه الحالة مسبقاً'}, status=400)
        elif status_type == 'custom' and complaint.custom_status and str(complaint.custom_status.id) == status_value:
            return Response({'error': 'الشكوى في هذه الحالة مسبقاً'}, status=400)
        
        # Check if current status is final
        if complaint.custom_status and complaint.custom_status.is_final_status:
            return Response({'error': 'لا يمكن تغيير حالة الشكوى من حالة نهائية'}, status=400)
        
        try:
            # Update complaint status using the model method
            if status_type == 'custom':
                complaint.update_status(None, custom_status_id=int(status_value), updated_by=request.user)
            else:
                complaint.update_status(status_value, updated_by=request.user)
            
            # Handle special cases for default statuses
            if status_type == 'default':
                if status_value == 'resolved':
                    complaint.resolved_by = request.user
                    complaint.resolved_at = timezone.now()
                    if notes:
                        complaint.resolution_notes = notes
                    complaint.save()
            
            # Get updated status info
            new_effective_status = complaint.effective_status
            new_status_display = complaint.current_status_display
            new_status_color = complaint.current_status_color
            
            return Response({
                'message': 'تم تحديث حالة الشكوى بنجاح',
                'old_status': old_effective_status,
                'new_status': new_effective_status,
                'status_display': new_status_display,
                'status_color': new_status_color
            })
            
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': 'حدث خطأ أثناء تحديث الحالة'}, status=500)


class ClientComplaintCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing complaint comments"""
    serializer_class = ClientComplaintCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        complaint_id = self.kwargs.get('complaint_pk')
        return ClientComplaintComment.objects.filter(complaint_id=complaint_id)
    
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        user = request.user
        # Admins can delete any comment
        if user.role == 'admin':
            return super().destroy(request, *args, **kwargs)
        # Company users can delete their own comments
        if comment.author == user:
            return super().destroy(request, *args, **kwargs)
        # Clients can delete their own replies (if using ClientComplaintReply model, handle separately)
        # Otherwise, deny
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to delete this comment.")
    
    def perform_create(self, serializer):
        complaint_id = self.kwargs.get('complaint_pk')
        complaint = get_object_or_404(ClientComplaint, pk=complaint_id)
        
        # Check if user has permission to comment on this complaint
        if self.request.user.role == 'admin':
            pass
        else:
            user_teams = Team.objects.filter(memberships__employee__user=self.request.user)
            assigned_teams = Team.objects.filter(
                client_complaint_assignments__complaint=complaint,
                client_complaint_assignments__is_active=True
            )
            
            if not user_teams.filter(id__in=assigned_teams).exists():
                raise PermissionDenied("ليس لديك صلاحية التعليق على هذه الشكوى")
        
        serializer.save(complaint=complaint, author=self.request.user)
        
        # Automatic status transition - system/admin replied
        from .ticket_automation import TicketStatusManager
        from .notifications import NotificationService
        TicketStatusManager.transition_on_system_response(complaint)
        
        # Send notification to client
        try:
            NotificationService.notify_new_system_message(complaint)
        except Exception as e:
            # Log but don't fail if notification fails
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send system message notification: {e}')


class TeamComplaintDashboardView(generics.ListAPIView):
    """Dashboard view for teams to see their assigned complaints"""
    serializer_class = ClientComplaintSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        user_teams = Team.objects.filter(memberships__employee__user=self.request.user)
        
        queryset = ClientComplaint.objects.filter(
            assignments__team__in=user_teams,
            assignments__is_active=True
        ).distinct().select_related(
            'category', 'reviewed_by', 'resolved_by'
        ).prefetch_related(
            'attachments', 'assignments__team', 'tasks__task', 'comments__author', 'status_history__changed_by'
        )
        
        # Filter by status if provided
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority if provided
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-created_at')


class ComplaintDashboardStatsView(APIView):
    """Dashboard statistics for client complaints"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins and managers can view dashboard stats")
        
        # Get all complaints or team-filtered complaints
        if request.user.role == 'admin':
            complaints = ClientComplaint.objects.all()
        else:
            user_teams = Team.objects.filter(memberships__employee__user=request.user)
            complaints = ClientComplaint.objects.filter(
                assignments__team__in=user_teams,
                assignments__is_active=True
            ).distinct()
        
        # Basic counts
        total_complaints = complaints.count()
        pending_review = complaints.filter(status='pending_review').count()
        approved = complaints.filter(status='approved').count()
        rejected = complaints.filter(status='rejected').count()
        in_progress = complaints.filter(status='in_progress').count()
        resolved = complaints.filter(status='resolved').count()
        closed = complaints.filter(status='closed').count()
        overdue_complaints = complaints.filter(status__in=['pending_review', 'approved', 'in_progress']).count()
        urgent_complaints = complaints.filter(priority='urgent').count()
        
        # Recent complaints (last 10)
        recent_complaints = complaints.select_related('category').order_by('-created_at')[:10]
        recent_complaints_data = ClientComplaintSerializer(recent_complaints, many=True).data
        
        # Complaints by category
        complaints_by_category = []
        categories = ComplaintCategory.objects.filter(is_active=True)
        for category in categories:
            count = complaints.filter(category=category).count()
            if count > 0:
                complaints_by_category.append({
                    'category_name': category.name,
                    'count': count,
                    'color': category.color
                })
        
        # Complaints by priority
        complaints_by_priority = [
            {
                'priority': 'urgent',
                'count': complaints.filter(priority='urgent').count()
            },
            {
                'priority': 'medium',
                'count': complaints.filter(priority='medium').count()
            },
            {
                'priority': 'low',
                'count': complaints.filter(priority='low').count()
            }
        ]
        
        # Resolution times (simplified - would need more complex query for accurate times)
        resolved_complaints = complaints.filter(status='resolved', resolved_at__isnull=False)
        if resolved_complaints.exists():
            # Calculate average resolution time in hours
            total_time = 0
            count = 0
            for complaint in resolved_complaints:
                if complaint.created_at and complaint.resolved_at:
                    time_diff = complaint.resolved_at - complaint.created_at
                    total_time += time_diff.total_seconds() / 3600  # Convert to hours
                    count += 1
            
            avg_resolution = total_time / count if count > 0 else 0
            resolution_times = {
                'average_resolution_hours': round(avg_resolution, 2),
                'fastest_resolution_hours': 1,  # Placeholder
                'slowest_resolution_hours': round(avg_resolution * 2, 2)  # Placeholder
            }
        else:
            resolution_times = {
                'average_resolution_hours': 0,
                'fastest_resolution_hours': 0,
                'slowest_resolution_hours': 0
            }
        
        return Response({
            'total_complaints': total_complaints,
            'pending_review': pending_review,
            'approved': approved,
            'rejected': rejected,
            'in_progress': in_progress,
            'resolved': resolved,
            'closed': closed,
            'overdue_complaints': overdue_complaints,
            'urgent_complaints': urgent_complaints,
            'recent_complaints': recent_complaints_data,
            'complaints_by_category': complaints_by_category,
            'complaints_by_priority': complaints_by_priority,
            'resolution_times': resolution_times
        })


class ClientComplaintTaskCreateView(APIView):
    """Create a task linked to a client complaint"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'complaint_id': {'type': 'string', 'format': 'uuid'},
                    'task_id': {'type': 'string', 'format': 'uuid'},
                    'team_id': {'type': 'string', 'format': 'uuid'},
                    'title': {'type': 'string'},
                    'description': {'type': 'string'},
                    'priority': {'type': 'string', 'enum': ['low', 'medium', 'high', 'urgent']},
                    'estimated_minutes': {'type': 'integer'},
                    'notes': {'type': 'string'}
                },
                'required': ['complaint_id', 'team_id']
            }
        }
    )
    def post(self, request):
        complaint_id = request.data.get('complaint_id')
        task_id = request.data.get('task_id')
        team_id = request.data.get('team_id')
        notes = request.data.get('notes', '')
        title = request.data.get('title')
        description = request.data.get('description')
        priority = request.data.get('priority', 'medium')
        estimated_minutes = request.data.get('estimated_minutes')
        
        if not complaint_id or not team_id:
            return Response(
                {'error': 'complaint_id and team_id are required'}, 
                status=rest_status.HTTP_400_BAD_REQUEST
            )
        
        # If task_id is not provided, create a task - we'll use complaint data as defaults
        
        try:
            # Verify complaint exists and user has permission
            complaint = ClientComplaint.objects.get(id=complaint_id)
            team = Team.objects.get(id=team_id)
            
            # Check permissions - user must be admin or member of the team
            if request.user.role not in ['admin', 'manager']:
                user_teams = Team.objects.filter(memberships__employee__user=request.user)
                if not user_teams.filter(id=team_id).exists():
                    raise PermissionDenied("You can only create/link tasks to complaints for teams you're a member of")
            
            # Check if complaint is assigned to this team
            if not complaint.assignments.filter(team_id=team_id, is_active=True).exists():
                return Response(
                    {'error': 'Complaint is not assigned to this team'}, 
                    status=rest_status.HTTP_400_BAD_REQUEST
                )
            
            if task_id:
                # Link existing task to complaint
                task = Task.objects.get(id=task_id)
                
                # Check if task already linked to a complaint
                if hasattr(task, 'client_complaint_task'):
                    return Response(
                        {'error': 'Task is already linked to a complaint'}, 
                        status=rest_status.HTTP_400_BAD_REQUEST
                    )
            else:
                # Create new task from complaint
                # Use complaint title and description as defaults if not provided
                if not title:
                    title = f"Task for complaint: {complaint.title}"
                if not description:
                    description = complaint.description
                if priority is None:
                    priority = 'medium'
                if estimated_minutes is None:
                    estimated_minutes = 60  # Default to 1 hour
                    
                # Assign to team leader by default, or first active member if no leader
                employee_to_assign = team.team_leader
                if not employee_to_assign:
                    # Get first active team member
                    first_member = team.memberships.filter(is_active=True).first()
                    if first_member:
                        employee_to_assign = first_member.employee
                    else:
                        return Response(
                            {'error': 'Team has no active members to assign task to'}, 
                            status=rest_status.HTTP_400_BAD_REQUEST
                        )
                
                task = Task.objects.create(
                    title=title,
                    description=description,
                    priority=priority,
                    estimated_minutes=estimated_minutes,
                    notes=notes,
                    created_by=request.user,
                    team=team,
                    employee=employee_to_assign
                )
            
            # Create the complaint task link
            complaint_task = ClientComplaintTask.objects.create(
                complaint=complaint,
                task=task,
                team=team,
                created_by=request.user,
                notes=notes
            )
            
            message = 'Task successfully linked to complaint' if task_id else 'Task created and linked to complaint'
            
            return Response({
                'message': message,
                'complaint_task_id': str(complaint_task.id),
                'task_id': str(task.id),
                'complaint_title': complaint.title,
                'task_title': task.title,
                'team_name': team.name
            }, status=rest_status.HTTP_201_CREATED)
            
        except ClientComplaint.DoesNotExist:
            return Response(
                {'error': 'Complaint not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )
        except Task.DoesNotExist:
            return Response(
                {'error': 'Task not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )
        except Team.DoesNotExist:
            return Response(
                {'error': 'Team not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=rest_status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateTaskForComplaintView(APIView):
    """Create a new task and link it to a client complaint"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'complaint_id': {'type': 'string', 'format': 'uuid'},
                    'team_id': {'type': 'string', 'format': 'uuid'},
                    'title': {'type': 'string'},
                    'description': {'type': 'string'},
                    'priority': {'type': 'string', 'enum': ['low', 'medium', 'high', 'urgent']},
                    'estimated_minutes': {'type': 'integer'},
                    'notes': {'type': 'string'}
                },
                'required': ['complaint_id', 'team_id', 'title', 'description']
            }
        }
    )
    def post(self, request):
        complaint_id = request.data.get('complaint_id')
        team_id = request.data.get('team_id')
        title = request.data.get('title')
        description = request.data.get('description')
        priority = request.data.get('priority', 'medium')
        estimated_minutes = request.data.get('estimated_minutes')
        notes = request.data.get('notes', '')
        
        if not all([complaint_id, team_id, title, description]):
            return Response(
                {'error': 'complaint_id, team_id, title, and description are required'}, 
                status=rest_status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify complaint exists and user has permission
            complaint = ClientComplaint.objects.get(id=complaint_id)
            team = Team.objects.get(id=team_id)
            
            # Check permissions - user must be admin or member of the team
            if request.user.role not in ['admin', 'manager']:
                user_teams = Team.objects.filter(memberships__employee__user=request.user)
                if not user_teams.filter(id=team_id).exists():
                    raise PermissionDenied("You can only create tasks for teams you're a member of")
            
            # Check if complaint is assigned to this team
            if not complaint.assignments.filter(team_id=team_id, is_active=True).exists():
                return Response(
                    {'error': 'Complaint is not assigned to this team'}, 
                    status=rest_status.HTTP_400_BAD_REQUEST
                )
            
            # Create the task
            task = Task.objects.create(
                title=title,
                description=description,
                priority=priority,
                estimated_minutes=estimated_minutes,
                notes=notes,
                created_by=request.user,
                team=team
            )
            
            # Create the complaint task link
            complaint_task = ClientComplaintTask.objects.create(
                complaint=complaint,
                task=task,
                team=team,
                created_by=request.user,
                notes=notes
            )
            
            return Response({
                'message': 'Task created and linked to complaint successfully',
                'task_id': str(task.id),
                'complaint_task_id': str(complaint_task.id),
                'complaint_title': complaint.title,
                'task_title': task.title,
                'team_name': team.name
            }, status=rest_status.HTTP_201_CREATED)
            
        except ClientComplaint.DoesNotExist:
            return Response(
                {'error': 'Complaint not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )
        except Team.DoesNotExist:
            return Response(
                {'error': 'Team not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=rest_status.HTTP_500_INTERNAL_SERVER_ERROR
            )



# Complaint Admin Permission Management Views
class TeamComplaintAdminPermissionView(APIView):
    """View for managing complaint admin permissions for teams"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all team complaint admin permissions"""
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can view complaint admin permissions")
        
        permissions = TeamComplaintAdminPermission.objects.select_related('team', 'granted_by').all()
        data = []
        for perm in permissions:
            data.append({
                'id': perm.id,
                'team': {
                    'id': perm.team.id,
                    'name': perm.team.name
                },
                'granted_by': perm.granted_by.username,
                'granted_at': perm.granted_at,
                'is_active': perm.is_active,
                'notes': perm.notes,
                'permissions': {
                    'can_review': perm.can_review,
                    'can_assign': perm.can_assign,
                    'can_update_status': perm.can_update_status,
                    'can_add_comments': perm.can_add_comments,
                    'can_create_tasks': perm.can_create_tasks,
                    'can_manage_assignments': perm.can_manage_assignments
                }
            })
        return Response(data)
    
    def post(self, request):
        """Grant complaint admin permissions to a team"""
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can grant complaint admin permissions")
        
        team_id = request.data.get('team_id')
        if not team_id:
            return Response({'error': 'Team ID is required'}, status=400)
        
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            return Response({'error': 'Team not found'}, status=404)
        
        # Check if permission already exists
        existing_permission = TeamComplaintAdminPermission.objects.filter(team=team).first()
        if existing_permission:
            # Update existing permission
            for key, value in request.data.items():
                if hasattr(existing_permission, key) and key not in ['team_id', 'granted_by', 'granted_at']:
                    setattr(existing_permission, key, value)
            existing_permission.is_active = True
            existing_permission.granted_by = request.user
            existing_permission.granted_at = timezone.now()
            existing_permission.save()
            
            return Response({
                'message': f'Complaint admin permissions updated for team {team.name}',
                'permission_id': existing_permission.id
            })
        else:
            # Create new permission
            permission_data = {
                'team': team,
                'granted_by': request.user,
                'notes': request.data.get('notes', ''),
                'can_review': request.data.get('can_review', True),
                'can_assign': request.data.get('can_assign', True),
                'can_update_status': request.data.get('can_update_status', True),
                'can_add_comments': request.data.get('can_add_comments', True),
                'can_create_tasks': request.data.get('can_create_tasks', True),
                'can_manage_assignments': request.data.get('can_manage_assignments', True)
            }
            
            permission = TeamComplaintAdminPermission.objects.create(**permission_data)
            
            return Response({
                'message': f'Complaint admin permissions granted to team {team.name}',
                'permission_id': permission.id
            }, status=201)
    
    def delete(self, request, pk):
        """Revoke complaint admin permissions from a team"""
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can revoke complaint admin permissions")
        
        try:
            permission = TeamComplaintAdminPermission.objects.get(pk=pk)
            team_name = permission.team.name
            permission.is_active = False
            permission.save()
            
            return Response({
                'message': f'Complaint admin permissions revoked from team {team_name}'
            })
        except TeamComplaintAdminPermission.DoesNotExist:
            return Response({'error': 'Permission not found'}, status=404)


class EmployeeComplaintAdminPermissionView(APIView):
    """View for managing complaint admin permissions for individual employees"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List all employee complaint admin permissions"""
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can view complaint admin permissions")
        
        permissions = EmployeeComplaintAdminPermission.objects.select_related('employee', 'employee__user', 'granted_by').all()
        data = []
        for perm in permissions:
            data.append({
                'id': perm.id,
                'employee': {
                    'id': perm.employee.id,
                    'name': perm.employee.name,
                    'username': perm.employee.user.username if perm.employee.user else None,
                    'position': perm.employee.position,
                    'department': perm.employee.department
                },
                'granted_by': perm.granted_by.username,
                'granted_at': perm.granted_at,
                'is_active': perm.is_active,
                'notes': perm.notes,
                'permissions': {
                    'can_review': perm.can_review,
                    'can_assign': perm.can_assign,
                    'can_update_status': perm.can_update_status,
                    'can_add_comments': perm.can_add_comments,
                    'can_create_tasks': perm.can_create_tasks,
                    'can_manage_assignments': perm.can_manage_assignments
                }
            })
        return Response(data)
    
    def post(self, request):
        """Grant complaint admin permissions to an employee"""
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can grant complaint admin permissions")
        
        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=400)
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=404)
        
        # Check if permission already exists
        existing_permission = EmployeeComplaintAdminPermission.objects.filter(employee=employee).first()
        if existing_permission:
            # Update existing permission
            for key, value in request.data.items():
                if hasattr(existing_permission, key) and key not in ['employee_id', 'granted_by', 'granted_at']:
                    setattr(existing_permission, key, value)
            existing_permission.is_active = True
            existing_permission.granted_by = request.user
            existing_permission.granted_at = timezone.now()
            existing_permission.save()
            
            return Response({
                'id': existing_permission.id,
                'employee': {
                    'id': employee.id,
                    'name': employee.name,
                    'username': employee.user.username if employee.user else None,
                    'position': employee.position,
                    'department': employee.department
                },
                'granted_by': request.user.username,
                'granted_at': existing_permission.granted_at,
                'is_active': existing_permission.is_active,
                'notes': existing_permission.notes,
                'permissions': {
                    'can_review': existing_permission.can_review,
                    'can_assign': existing_permission.can_assign,
                    'can_update_status': existing_permission.can_update_status,
                    'can_add_comments': existing_permission.can_add_comments,
                    'can_create_tasks': existing_permission.can_create_tasks,
                    'can_manage_assignments': existing_permission.can_manage_assignments
                }
            })
        else:
            # Create new permission
            permission_data = {
                'employee': employee,
                'granted_by': request.user,
                'notes': request.data.get('notes', ''),
                'can_review': request.data.get('can_review', True),
                'can_assign': request.data.get('can_assign', True),
                'can_update_status': request.data.get('can_update_status', True),
                'can_add_comments': request.data.get('can_add_comments', True),
                'can_create_tasks': request.data.get('can_create_tasks', True),
                'can_manage_assignments': request.data.get('can_manage_assignments', True)
            }
            
            permission = EmployeeComplaintAdminPermission.objects.create(**permission_data)
            
            return Response({
                'id': permission.id,
                'employee': {
                    'id': employee.id,
                    'name': employee.name,
                    'username': employee.user.username if employee.user else None,
                    'position': employee.position,
                    'department': employee.department
                },
                'granted_by': request.user.username,
                'granted_at': permission.granted_at,
                'is_active': permission.is_active,
                'notes': permission.notes,
                'permissions': {
                    'can_review': permission.can_review,
                    'can_assign': permission.can_assign,
                    'can_update_status': permission.can_update_status,
                    'can_add_comments': permission.can_add_comments,
                    'can_create_tasks': permission.can_create_tasks,
                    'can_manage_assignments': permission.can_manage_assignments
                }
            }, status=201)
    
    def delete(self, request, pk):
        """Revoke complaint admin permissions from an employee"""
        if request.user.role != 'admin':
            raise PermissionDenied("Only admins can revoke complaint admin permissions")
        
        try:
            permission = EmployeeComplaintAdminPermission.objects.get(pk=pk)
            employee_name = permission.employee.name
            permission.is_active = False
            permission.save()
            
            return Response({
                'message': f'Complaint admin permissions revoked from employee {employee_name}'
            })
        except EmployeeComplaintAdminPermission.DoesNotExist:
            return Response({'error': 'Permission not found'}, status=404)


class UserComplaintAdminPermissionsView(APIView):
    """View to get current user's complaint admin permissions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get complaint admin permissions for current user"""
        permissions = get_complaint_admin_permissions(request.user)
        return Response(permissions)


# ==================== Ticket Automation Views ====================

class TicketDelayThresholdViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ticket delay thresholds
    Admin users can view, create, update thresholds
    """
    serializer_class = TicketDelayThresholdSerializer
    permission_classes = [IsAuthenticated]
    queryset = TicketDelayThreshold.objects.all()
    
    def get_queryset(self):
        # Admin can see all thresholds
        if self.request.user.role == 'admin':
            queryset = TicketDelayThreshold.objects.all()
        else:
            # Regular users can only view active thresholds
            queryset = TicketDelayThreshold.objects.filter(is_active=True)
        
        # Filter by threshold type if specified
        threshold_type = self.request.query_params.get('threshold_type')
        if threshold_type:
            queryset = queryset.filter(threshold_type=threshold_type)
        
        # Filter by priority if specified
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('threshold_type', 'priority')
    
    def perform_create(self, serializer):
        # Only admins can create thresholds
        if self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can create thresholds")
        serializer.save()
    
    def perform_update(self, serializer):
        # Only admins can update thresholds
        if self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can update thresholds")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only admins can delete thresholds
        if self.request.user.role != 'admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only admins can delete thresholds")
        # Soft delete instead of hard delete
        instance.is_active = False
        instance.save()


class TicketAutomationStatsView(APIView):
    """
    Get statistics about automated ticket management
    Shows delayed tickets, auto-closed tickets, etc.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .ticket_automation import TicketStatusManager
        
        # Get all active complaints
        all_complaints = ClientComplaint.objects.exclude(
            status='closed',
            automated_status=TicketStatusManager.STATUS_AUTO_CLOSED
        )
        
        # Count tickets by delay status
        stats = {
            'total_active_tickets': all_complaints.count(),
            'waiting_for_system': all_complaints.filter(
                automated_status=TicketStatusManager.STATUS_WAITING_SYSTEM
            ).count(),
            'waiting_for_client': all_complaints.filter(
                automated_status=TicketStatusManager.STATUS_WAITING_CLIENT
            ).count(),
            'delayed_by_system': all_complaints.filter(
                delay_status=TicketStatusManager.STATUS_DELAYED_SYSTEM
            ).count(),
            'delayed_by_client': all_complaints.filter(
                delay_status=TicketStatusManager.STATUS_DELAYED_CLIENT
            ).count(),
            'resolved_pending_confirmation': all_complaints.filter(
                automated_status=TicketStatusManager.STATUS_RESOLVED_PENDING
            ).count(),
            'reopened': all_complaints.filter(
                automated_status=TicketStatusManager.STATUS_REOPENED
            ).count(),
        }
        
        # Get recently auto-closed tickets
        from django.utils import timezone
        from datetime import timedelta
        last_24h = timezone.now() - timedelta(hours=24)
        
        stats['auto_closed_last_24h'] = ClientComplaint.objects.filter(
            automated_status=TicketStatusManager.STATUS_AUTO_CLOSED,
            updated_at__gte=last_24h
        ).count()
        
        return Response(stats)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing in-app notifications
    Provides endpoints for listing, reading, and marking notifications
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return notifications for the authenticated user"""
        from hr_management.models import Notification
        return Notification.objects.filter(recipient=self.request.user)
    
    def get_serializer_class(self):
        """Return the appropriate serializer"""
        from hr_management.serializers import NotificationSerializer
        return NotificationSerializer
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a single notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({
            'message': 'All notifications marked as read',
            'updated_count': updated
        })
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get only unread notifications"""
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ========== Shift Scheduling System ViewSets ==========

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
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(employee__department=department)
        
        return queryset.select_related('employee')
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Create a full week schedule for an employee
        POST /api/shifts/schedules/bulk_create/
        Body: {
            "employee": "employee-uuid",
            "schedules": [
                {"day_of_week": 0, "start_time": "09:00", "end_time": "17:00"},
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
        GET /api/shifts/schedules/department_schedules/?department=<name>&day_of_week=0
        """
        department = request.query_params.get('department')
        day_of_week = request.query_params.get('day_of_week')
        
        if not department:
            return Response(
                {'error': 'department parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = WeeklyShiftSchedule.objects.filter(
            employee__department=department,
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
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        reason = request.data.get('reason', '')
        
        if not employee_id or not start_date_str or not end_date_str:
            return Response(
                {'error': 'employee, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        
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
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(employee__department=department)
        
        return queryset.select_related('employee', 'approved_by')
    
    @action(detail=False, methods=['post'])
    def clock_in(self, request):
        """
        Clock in for current shift
        POST /api/shifts/attendance/clock_in/
        Body: {
            "employee": "employee-uuid",
            "clock_in_time": "09:15" (optional)
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
                {'error': f'لا يوجد دوام مجدول لـ {employee.name} اليوم'},
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
                {'error': 'لا يوجد سجل حضور. يرجى تسجيل الدخول أولاً.'},
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
            try:
                employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return Response({'error': 'موظف غير موجود'}, status=status.HTTP_404_NOT_FOUND)
                
            today = timezone.now().date()
            current_time = timezone.now().time()
            
            shift = get_employee_shift_for_date(employee_id, today)
            
            if shift:
                # Check actual attendance from WorkShift (old system)
                try:
                    # Get today's work shifts
                    today_shifts = WorkShift.objects.filter(
                        employee=employee,
                        check_in__date=today
                    ).order_by('check_in')
                    
                    latest_shift = today_shifts.last()
                    active_shift = today_shifts.filter(check_out__isnull=True).first()
                    
                    has_clocked_in = latest_shift is not None
                    clock_in_time = latest_shift.check_in.time() if latest_shift else None
                    
                    # Get attendance status
                    try:
                        attendance_record = EmployeeAttendance.objects.get(employee=employee, date=today)
                        att_status = attendance_record.get_status_display()
                        
                        # Calculate late minutes if late
                        if attendance_record.status == 'late' and clock_in_time:
                            expected_start = shift['start_time']
                            check_in_dt = timezone.datetime.combine(today, clock_in_time)
                            expected_dt = timezone.datetime.combine(today, expected_start)
                            late_minutes = int((check_in_dt - expected_dt).total_seconds() / 60)
                        else:
                            late_minutes = 0
                    except EmployeeAttendance.DoesNotExist:
                        att_status = 'لم يسجل دخول'
                        late_minutes = 0
                    
                except Exception as e:
                    has_clocked_in = False
                    clock_in_time = None
                    att_status = 'لم يسجل دخول'
                    late_minutes = 0
                
                data = {
                    'employee_id': str(employee.id),
                    'employee_name': employee.name,
                    'is_on_shift': shift['start_time'] <= current_time <= shift['end_time'],
                    'shift_start': shift['start_time'].strftime('%H:%M'),
                    'shift_end': shift['end_time'].strftime('%H:%M'),
                    'has_clocked_in': has_clocked_in,
                    'clock_in_time': clock_in_time.strftime('%H:%M') if clock_in_time else None,
                    'clock_out_time': today_shift.check_out.strftime('%H:%M') if has_clocked_in and today_shift.check_out else None,
                    'status': att_status,
                    'late_minutes': late_minutes
                }
            else:
                data = {
                    'employee_id': str(employee.id),
                    'employee_name': employee.name,
                    'is_on_shift': False,
                    'shift_start': None,
                    'shift_end': None,
                    'has_clocked_in': False,
                    'clock_in_time': None,
                    'status': 'عطلة',
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
                
                # Check actual attendance from WorkShift (old system)
                try:
                    today_shifts = WorkShift.objects.filter(
                        employee=employee,
                        check_in__date=today
                    ).order_by('check_in')
                    
                    latest_shift = today_shifts.last()
                    
                    has_clocked_in = latest_shift is not None
                    clock_in_time = latest_shift.check_in.time() if latest_shift else None
                    
                    # Get attendance status
                    try:
                        attendance_record = EmployeeAttendance.objects.get(employee=employee, date=today)
                        att_status = attendance_record.get_status_display()
                        
                        # Calculate late minutes if late
                        if attendance_record.status == 'late' and clock_in_time:
                            expected_start = emp_shift['start_time']
                            check_in_dt = timezone.datetime.combine(today, clock_in_time)
                            expected_dt = timezone.datetime.combine(today, expected_start)
                            late_minutes = int((check_in_dt - expected_dt).total_seconds() / 60)
                        else:
                            late_minutes = 0
                    except EmployeeAttendance.DoesNotExist:
                        att_status = 'لم يسجل دخول'
                        late_minutes = 0
                        
                except Exception as e:
                    has_clocked_in = False
                    clock_in_time = None
                    att_status = 'لم يسجل دخول'
                    late_minutes = 0
                
                status_data.append({
                    'employee_id': str(employee.id),
                    'employee_name': employee.name,
                    'is_on_shift': True,
                    'shift_start': emp_shift['start_time'].strftime('%H:%M'),
                    'shift_end': emp_shift['end_time'].strftime('%H:%M'),
                    'has_clocked_in': has_clocked_in,
                    'clock_in_time': clock_in_time.strftime('%H:%M') if clock_in_time else None,
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
        report_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all employees scheduled for this date
        day_of_week = report_date.weekday()
        # Convert Python weekday (0=Monday) to our system (0=Sunday)
        if day_of_week == 6:
            day_of_week = 0
        else:
            day_of_week += 1
        
        scheduled_employees = WeeklyShiftSchedule.objects.filter(
            day_of_week=day_of_week,
            is_active=True
        ).exclude(
            employee__shift_overrides__date=report_date,
            employee__shift_overrides__override_type__in=['day_off', 'vacation', 'sick_leave', 'holiday'],
            employee__shift_overrides__status='approved'
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
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'error': 'موظف غير موجود'}, status=status.HTTP_404_NOT_FOUND)
            
        start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        
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
            'employee_id': str(employee.id),
            'employee_name': employee.name,
            'department': employee.department,
            'weekly_hours': weekly_hours,
            'days_present': days_present,
            'days_late': days_late,
            'days_absent': days_absent,
            'total_hours_worked': float(total_hours),
            'attendance_rate': round(attendance_rate, 2)
        })
