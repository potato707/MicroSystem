from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
import datetime
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination
from .custom_permissions import IsEmployer
from .models import (
    Employee, EmployeeDocument, EmployeeNote, EmployeeAttendance, WorkShift, 
    LeaveRequest, Complaint, ComplaintReply, ComplaintAttachment, Wallet, WalletTransaction, 
    ReimbursementRequest, Task, Subtask, TaskReport, TaskComment, Team, TeamMembership, 
    TeamTask, OfficeLocation,
    # Multi-wallet models
    EmployeeWalletSystem, MainWallet, ReimbursementWallet, AdvanceWallet, 
    MultiWalletTransaction, WalletTransfer
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
    EmployeeWalletSystemSerializer, MultiWalletTransactionSerializer, WalletTransferSerializer
)
from utils.timezone_utils import system_now
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsEmployer()]
        return [IsAuthenticated()]

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
                # Return employee data with user role
                data = {
                    'id': str(employee.id),
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
                    'status': 'present' if has_checked_in else 'absent',
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
            return Response({"error": "Failed to get employee dashboard stats"}, status=500)

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
        
        # Get or create attendance record for today
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={"status": "present"}
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
        
        # Update attendance status
        attendance.status = "present"
        attendance.save()

        return Response(EmployeeAttendanceSerializer(attendance).data, status=200)


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
        active_shift.save()

        return Response(EmployeeAttendanceSerializer(attendance).data, status=200)


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
        
        serializer.save(complaint=complaint)

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
    # Always return the one central wallet
    return Wallet.objects.get(employee__isnull=True)

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
        transaction = serializer.save(wallet=wallet)

        # Update balance
        if transaction.transaction_type == "deposit":
            wallet.balance += transaction.amount
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="deposit",
                amount=transaction.amount,
                description=f"Deposit to central wallet by {self.request.user.username}"
            )
        elif transaction.transaction_type == "withdrawal":
            wallet.balance -= transaction.amount
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type="withdrawal",
                amount=transaction.amount,
                description=f"Withdrawal from central wallet by {self.request.user.username}"
            )
        wallet.save()

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
        status = request.data.get("status")
        comment = request.data.get("admin_comment", "")

        if status not in ["approved", "rejected"]:
            raise ValidationError("Status must be 'approved' or 'rejected'.")

        reimbursement.status = status
        reimbursement.admin_comment = comment
        reimbursement.save()

        if status == "approved":
            # Update reimbursement with approval details
            reimbursement.approved_at = timezone.now()
            reimbursement.approved_by = request.user
            reimbursement.save()
            
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
        
        # Filter by date (default to today)
        date_param = self.request.query_params.get('date')
        if date_param:
            try:
                date = datetime.datetime.strptime(date_param, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date)
            except ValueError:
                pass
        else:
            queryset = queryset.filter(date=datetime.date.today())
        
        # Role-based filtering
        if user.role == 'employee':
            # Employees see only their own tasks
            try:
                employee = user.employee
                queryset = queryset.filter(employee=employee)
            except Employee.DoesNotExist:
                queryset = queryset.none()
        elif user.role == 'admin':
            # Admins see all tasks, can filter by employee
            employee_id = self.request.query_params.get('employee_id')
            if employee_id:
                queryset = queryset.filter(employee_id=employee_id)
        
        return queryset.order_by('-priority', 'created_at')
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Set employee based on user role and data
        if user.role == 'employee':
            try:
                employee = user.employee
                # Employees can only create tasks for themselves
                serializer.save(employee=employee, created_by=user)
            except Employee.DoesNotExist:
                raise ValidationError("Employee profile not found. Please contact administrator.")
        elif user.role == 'admin':
            # Check if employee was specified in the request
            employee_id = self.request.data.get('employee')
            
            if employee_id:
                # Admin is creating task for a specific employee
                try:
                    employee = Employee.objects.get(id=employee_id)
                    serializer.save(
                        employee=employee, 
                        created_by=user, 
                        assigned_by_manager=True
                    )
                except Employee.DoesNotExist:
                    raise ValidationError("Employee not found")
            else:
                # No employee specified - check if admin has their own employee profile
                try:
                    employee = user.employee
                    # Admin is creating task for themselves
                    serializer.save(employee=employee, created_by=user)
                except Employee.DoesNotExist:
                    raise ValidationError("Employee ID required for admin task creation")
        else:
            raise PermissionDenied("You don't have permission to create tasks")


class TaskUpdateView(generics.UpdateAPIView):
    """Quick update endpoint for task status changes"""
    serializer_class = TaskUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()
        
        if user.role == 'employee':
            # Employees can only update their own tasks
            if hasattr(user, 'employee'):
                queryset = queryset.filter(employee=user.employee)
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
                    task.total_pause_time += int(pause_duration)
                    task.paused_at = None
            elif action == 'complete':
                task.status = 'done'
                task.completed_at = system_now()
                # If completing from pause, add pause time to total
                if task.paused_at:
                    pause_duration = (system_now() - task.paused_at).total_seconds() / 60
                    task.total_pause_time += int(pause_duration)
                    task.paused_at = None
            elif action == 'pause':
                task.paused_at = system_now()
                # Keep status as 'doing' so progress is maintained
            elif action == 'resume':
                if task.paused_at:
                    pause_duration = (system_now() - task.paused_at).total_seconds() / 60
                    task.total_pause_time += int(pause_duration)
                    task.paused_at = None
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
            
            # Check permissions - only task owner or admin can view subtasks
            if user.role == 'admin' or (hasattr(user, 'employee') and parent_task.employee == user.employee):
                return Subtask.objects.filter(parent_task=parent_task)
            else:
                return Subtask.objects.none()
        
        # If no parent_task specified, return user's own subtasks
        if user.role == 'admin':
            return Subtask.objects.all()
        elif hasattr(user, 'employee'):
            return Subtask.objects.filter(parent_task__employee=user.employee)
        else:
            return Subtask.objects.none()
    
    def perform_create(self, serializer):
        # Ensure parent_task belongs to current user (for employees)
        parent_task = serializer.validated_data['parent_task']
        user = self.request.user
        
        if user.role != 'admin' and hasattr(user, 'employee') and parent_task.employee != user.employee:
            raise PermissionDenied("You can only create subtasks for your own tasks")
        
        serializer.save()


class SubtaskQuickActionsView(APIView):
    """Quick actions for subtasks (start, pause, complete, etc.)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, subtask_id):
        try:
            subtask = Subtask.objects.get(id=subtask_id)
            user = request.user
            
            # Check permissions
            if user.role != 'admin' and (not hasattr(user, 'employee') or subtask.parent_task.employee != user.employee):
                raise PermissionDenied("Permission denied")
            
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
                    subtask.total_pause_time += pause_duration
                    subtask.paused_at = None
            elif action == 'complete':
                subtask.status = 'done'
                subtask.completed_at = system_now()
                if subtask.paused_at:
                    # Add final pause duration to total
                    pause_duration = (system_now() - subtask.paused_at).total_seconds() / 60
                    subtask.total_pause_time += pause_duration
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
        
        if not task_id or not team_id:
            return Response({'error': 'task_id and team_id are required'}, status=400)
        
        try:
            task = Task.objects.get(id=task_id)
            team = Team.objects.get(id=team_id)
            
            # Check if task is already assigned to a team
            if hasattr(task, 'team_assignment'):
                return Response({'error': 'Task is already assigned to a team'}, status=400)
            
            # Update task with team
            task.team = team
            task.save()
            
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
            return Response(serializer.data, status=201)
            
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

