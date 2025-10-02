from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
import datetime
from rest_framework import viewsets, generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .custom_permissions import IsEmployer
from .models import Employee, EmployeeDocument, EmployeeNote, EmployeeAttendance, LeaveRequest, Complaint, ComplaintReply, ComplaintAttachment, Wallet, WalletTransaction, ReimbursementRequest
from .serializers import EmployeeSerializer, EmployeeDocumentSerializer, EmployeeNoteSerializer, EmployeeAttendanceSerializer, LeaveRequestSerializer, ComplaintSerializer, ComplaintReplySerializer, WalletSerializer, WalletTransactionSerializer, CentralWalletSerializer, CentralWalletTransactionSerializer, ReimbursementAttachmentSerializer, ReimbursementRequestSerializer, ReimbursementReviewSerializer
from utils.timezone_utils import system_now
from rest_framework.response import Response

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsEmployer()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = Employee.objects.all()
        if getattr(self.request.user, "role", None) == "employee":
            queryset = queryset.filter(user=self.request.user)
        return queryset

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
        serializer.save(complaint=complaint)

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

    def get_queryset(self):
        employee_id = self.kwargs["employee_id"]
        if getattr(self.request.user, "role", None) != "employee" or self.request.user.employee.id == employee_id: #The admi can see all transactions or the employee's own transactions
            return WalletTransaction.objects.filter(wallet__employee__id=employee_id)
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

