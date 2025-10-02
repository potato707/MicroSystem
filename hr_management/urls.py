from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, EmployeeDocumentViewSet, EmployeeNoteViewSet, EmployeeAttendanceListCreateView, EmployeeAttendanceDetailView, CheckInView, CheckOutView, LeaveRequestCreateView, LeaveRequestUpdateStatusView, LeaveRequestListView, ComplaintCreateView, ComplaintReplyCreateView, ComplaintListView, WalletDetailView, WalletTransactionCreateView, WalletTransactionListView, CentralWalletDetailView, CentralWalletTransactionCreateView, CentralWalletTransactionListView, ReimbursementRequestListView, ReimbursementRequestApproveRejectView, ReimbursementRequestCreateView


router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'documents', EmployeeDocumentViewSet)
router.register(r'notes', EmployeeNoteViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # path('test/', test_page, name="test-page"),
    # path('test2/', attendance_page, name="test-page"),
    # Attendance
    path("attendance/", EmployeeAttendanceListCreateView.as_view(), name="attendance_list"),
    path("attendance/<uuid:pk>/", EmployeeAttendanceDetailView.as_view(), name="attendance_detail"),
    path("attendance/<uuid:employee_id>/checkin/", CheckInView.as_view(), name="employee-checkin"),
    path("attendance/<uuid:employee_id>/checkout/", CheckOutView.as_view(), name="employee-checkout"),
    #leave requests
    path("leave_requests/", LeaveRequestCreateView.as_view(), name="leave_request_create"),
    path("leave_requests/<uuid:pk>/status/", LeaveRequestUpdateStatusView.as_view(), name="leave_request_update_status"),
    path("leave_requests/list/", LeaveRequestListView.as_view(), name="leave_request_list"),
    #complaints
    path("complaints/", ComplaintCreateView.as_view(), name="complaint_create"),
    path("complaints/list/", ComplaintListView.as_view(), name="complaint_list"),
    path("complaints/<uuid:complaint_id>/reply/", ComplaintReplyCreateView.as_view(), name="complaint_reply"),
    #wallet
    path("employees/<uuid:employee_id>/wallet/", WalletDetailView.as_view(), name="wallet-detail"),
    path("employees/<uuid:employee_id>/wallet/transactions/", WalletTransactionCreateView.as_view(), name="wallet-transaction"),
    path("employees/<uuid:employee_id>/wallet/transactions/history/", WalletTransactionListView.as_view(), name="wallet-transaction-history"),
    #central wallet
    path("central-wallet/", CentralWalletDetailView.as_view(), name="central-wallet-detail"),
    path("central-wallet/transactions/", CentralWalletTransactionCreateView.as_view(), name="central-wallet-transaction"),
    path("central-wallet/transactions/history/", CentralWalletTransactionListView.as_view(), name="central-wallet-transactions-history"),
    #reimbursement
    path("reimbursements/", ReimbursementRequestListView.as_view(), name="reimbursement-list"),
    path("reimbursements/create/", ReimbursementRequestCreateView.as_view(), name="reimbursement-create"),
    path("reimbursements/<uuid:pk>/review/", ReimbursementRequestApproveRejectView.as_view(), name="reimbursement-review"),
]

