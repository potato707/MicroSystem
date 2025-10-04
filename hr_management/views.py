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
from .models import Employee, EmployeeDocument, EmployeeNote, EmployeeAttendance, LeaveRequest, Complaint, ComplaintReply, ComplaintAttachment, Wallet, WalletTransaction, ReimbursementRequest, Task, TaskReport, TaskComment
from .serializers import EmployeeSerializer, EmployeeDocumentSerializer, EmployeeNoteSerializer, EmployeeAttendanceSerializer, LeaveRequestSerializer, ComplaintSerializer, ComplaintReplySerializer, WalletSerializer, WalletTransactionSerializer, CentralWalletSerializer, CentralWalletTransactionSerializer, ReimbursementAttachmentSerializer, ReimbursementRequestSerializer, ReimbursementReviewSerializer, TaskSerializer, TaskCreateSerializer, TaskUpdateSerializer, TaskReportSerializer, TaskCommentSerializer, ManagerTaskDashboardSerializer
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
            
            # Get today's attendance
            today_attendance = EmployeeAttendance.objects.filter(
                employee=employee, 
                date=today
            ).first()
            
            # Get wallet balance
            try:
                wallet = Wallet.objects.get(employee=employee)
                wallet_balance = str(wallet.balance)
            except Wallet.DoesNotExist:
                wallet_balance = "0.00"
            
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
                    'checked_in': today_attendance.check_in if today_attendance else None,
                    'checked_out': today_attendance.check_out if today_attendance else None,
                    # 'status': 'present' if today_attendance else 'absent'
                    'status': today_attendance.status
                },
                'wallet_balance': wallet_balance,
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
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={"check_in": now.time()}
        )

        # If already checked in
        if not created and attendance.check_in:
            return Response({"error": "Already checked in"}, status=400)

        # Set check-in and status
        # attendance.check_in = now.time()
        # if attendance.check_in > employee.shift_start_time:
        #     attendance.status = "late" #TODO: Based on the grace period
        # else:
        #     attendance.status = "present"
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
        try:
            attendance = EmployeeAttendance.objects.get(employee=employee, date=today)
        except EmployeeAttendance.DoesNotExist:
            return Response({"error": "No check-in record found for today"}, status=400)

        # If already checked out
        if attendance.check_out:
            return Response({"error": "Already checked out"}, status=400)

        attendance.check_out = now.time()
        attendance.save()

        return Response(EmployeeAttendanceSerializer(attendance).data, status=200)

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
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsEmployer]

    def update(self, request, *args, **kwargs):
        leave_request = self.get_object()
        status_param = request.data.get("status")
        if status_param not in ["approved", "rejected"]:
            return Response({"error": "Status must be 'approved' or 'rejected'"}, status=400)

        leave_request.status = status_param
        leave_request.save()

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
                    defaults={"status": "on_leave"}
                )
                if not created:
                    attendance.status = "on_leave"
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
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        employee_id = self.kwargs["employee_id"]
        if getattr(self.request.user, "role", None) != "employee" or self.request.user.employee.id == employee_id: #The admi can see all transactions or the employee's own transactions
            return WalletTransaction.objects.filter(wallet__employee__id=employee_id).order_by("-created_at")
        else:
            #No permission
            return WalletTransaction.objects.none()

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
            central_wallet = get_central_wallet()
            employee_wallet = reimbursement.employee.wallet

            # خصم من الشركة
            WalletTransaction.objects.create(
                wallet=central_wallet,
                transaction_type="withdrawal",
                amount=reimbursement.amount,
                description=f"Reimbursement for {reimbursement.employee.name}"
            )
            central_wallet.balance -= reimbursement.amount
            central_wallet.save()

            # إيداع في محفظة الموظف
            WalletTransaction.objects.create(
                wallet=employee_wallet,
                transaction_type="deposit",
                amount=reimbursement.amount,
                description=f"Reimbursement approved"
            )
            employee_wallet.balance += reimbursement.amount
            employee_wallet.save()

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
        
        # Only employees can view their own tasks
        if user.role == 'employee':
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
                # Employee user doesn't have an employee profile - this is an error
                return Response({
                    'error': 'Employee profile not found. Please contact administrator.'
                }, status=400)
        elif user.role == 'admin':
            # Admins don't have personal tasks - redirect them to manager dashboard
            return Response({
                'error': 'Admins do not have personal tasks. Use the manager dashboard instead.'
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

