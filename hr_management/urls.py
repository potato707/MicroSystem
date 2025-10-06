from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmployeeViewSet, EmployeeDocumentViewSet, EmployeeNoteViewSet, EmployeeAttendanceListCreateView, 
    EmployeeAttendanceDetailView, CheckInView, CheckOutView, WorkShiftViewSet, ShiftCheckInView, 
    ShiftCheckOutView, ShiftBreakView, LeaveRequestCreateView, LeaveRequestUpdateStatusView, 
    LeaveRequestListView, ComplaintCreateView, ComplaintReplyCreateView, ComplaintListView, 
    ComplaintCloseView, WalletDetailView, WalletTransactionCreateView, WalletTransactionListView, 
    CentralWalletDetailView, CentralWalletTransactionCreateView, CentralWalletTransactionListView, 
    ReimbursementRequestListView, ReimbursementRequestApproveRejectView, ReimbursementRequestCreateView, ReimbursementPaymentView, 
    CurrentUserView, EmployeeDashboardStatsView, TaskViewSet, TaskUpdateView, TodayTasksView, 
    ManagerDashboardView, TaskReportViewSet, TaskCommentViewSet, QuickTaskActionsView, SubtaskViewSet, 
    SubtaskQuickActionsView, TeamViewSet, TeamMembershipViewSet, TeamTaskViewSet, AssignTaskToTeamView, 
    TeamDashboardView, OfficeLocationViewSet, SetOfficeLocationView, CurrentOfficeLocationView,
    # Multi-wallet views
    EmployeeWalletSystemView, WalletTransferCreateView
)


router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'documents', EmployeeDocumentViewSet)
router.register(r'notes', EmployeeNoteViewSet)
router.register(r'task-reports', TaskReportViewSet, basename='task-report')
router.register(r'task-comments', TaskCommentViewSet, basename='task-comment')
router.register(r'subtasks', SubtaskViewSet, basename='subtask')
router.register(r'shifts', WorkShiftViewSet, basename='work-shift')
router.register(r'teams', TeamViewSet, basename='team')
router.register(r'team-memberships', TeamMembershipViewSet, basename='team-membership')
router.register(r'team-tasks', TeamTaskViewSet, basename='team-task')
router.register(r'office-locations', OfficeLocationViewSet, basename='office-location')

urlpatterns = [
    # TO-DO System - specific task URLs must come before router patterns
    path("tasks/today/", TodayTasksView.as_view(), name="today-tasks"),
    path("tasks/<uuid:task_id>/update/", TaskUpdateView.as_view(), name="task-update"),
    path("tasks/<uuid:task_id>/actions/", QuickTaskActionsView.as_view(), name="task-actions"),
    path("subtasks/<uuid:subtask_id>/actions/", SubtaskQuickActionsView.as_view(), name="subtask-actions"),
    path("manager/dashboard/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    
    # Teams
    path("teams/<uuid:team_id>/dashboard/", TeamDashboardView.as_view(), name="team-dashboard"),
    path("tasks/assign-to-team/", AssignTaskToTeamView.as_view(), name="assign-task-to-team"),
    
    # Current user
    path("current-user/", CurrentUserView.as_view(), name="current-user"),
    path("employee-dashboard-stats/", EmployeeDashboardStatsView.as_view(), name="employee-dashboard-stats"),
    
    # Attendance
    path("attendance/", EmployeeAttendanceListCreateView.as_view(), name="attendance_list"),
    path("attendance/<uuid:pk>/", EmployeeAttendanceDetailView.as_view(), name="attendance_detail"),
    path("attendance/<uuid:employee_id>/checkin/", CheckInView.as_view(), name="employee-checkin"),
    path("attendance/<uuid:employee_id>/checkout/", CheckOutView.as_view(), name="employee-checkout"),
    
    # Work Shifts
    path("shifts/checkin/", ShiftCheckInView.as_view(), name="shift-checkin"),
    path("shifts/checkout/", ShiftCheckOutView.as_view(), name="shift-checkout"),
    path("shifts/<uuid:shift_id>/checkout/", ShiftCheckOutView.as_view(), name="shift-checkout-specific"),
    path("shifts/<uuid:shift_id>/break/", ShiftBreakView.as_view(), name="shift-break"),
    
    # Office Location Management
    path("office-location/set/", SetOfficeLocationView.as_view(), name="set-office-location"),
    path("office-location/current/", CurrentOfficeLocationView.as_view(), name="current-office-location"),
    
    #leave requests
    path("leave_requests/", LeaveRequestCreateView.as_view(), name="leave_request_create"),
    path("leave_requests/<uuid:pk>/status/", LeaveRequestUpdateStatusView.as_view(), name="leave_request_update_status"),
    path("leave_requests/list/", LeaveRequestListView.as_view(), name="leave_request_list"),
    
    #complaints
    path("complaints/", ComplaintCreateView.as_view(), name="complaint_create"),
    path("complaints/list/", ComplaintListView.as_view(), name="complaint_list"),
    path("complaints/<uuid:complaint_id>/reply/", ComplaintReplyCreateView.as_view(), name="complaint_reply"),
    path("complaints/<uuid:complaint_id>/close/", ComplaintCloseView.as_view(), name="complaint_close"),
    
    #wallet (legacy)
    path("employees/<uuid:employee_id>/wallet/", WalletDetailView.as_view(), name="wallet-detail"),
    path("employees/<uuid:employee_id>/wallet/transactions/", WalletTransactionCreateView.as_view(), name="wallet-transaction"),
    path("employees/<uuid:employee_id>/wallet/transactions/history/", WalletTransactionListView.as_view(), name="wallet-transaction-history"),
    
    # Multi-wallet system
    path("employees/<uuid:employee_id>/wallet-system/", EmployeeWalletSystemView.as_view(), name="employee-wallet-system"),
    path("employees/<uuid:employee_id>/multi-wallet/transactions/", WalletTransactionCreateView.as_view(), name="multi-wallet-transaction"),
    path("employees/<uuid:employee_id>/multi-wallet/transactions/history/", WalletTransactionListView.as_view(), name="multi-wallet-transaction-history"),
    path("employees/<uuid:employee_id>/wallet-transfers/", WalletTransferCreateView.as_view(), name="wallet-transfer"),
    
    #central wallet
    path("central-wallet/", CentralWalletDetailView.as_view(), name="central-wallet-detail"),
    path("central-wallet/transactions/", CentralWalletTransactionCreateView.as_view(), name="central-wallet-transaction"),
    path("central-wallet/transactions/history/", CentralWalletTransactionListView.as_view(), name="central-wallet-transactions-history"),
    
    #reimbursement
    path("reimbursements/", ReimbursementRequestListView.as_view(), name="reimbursement-list"),
    path("reimbursements/create/", ReimbursementRequestCreateView.as_view(), name="reimbursement-create"),
    path("reimbursements/<uuid:pk>/review/", ReimbursementRequestApproveRejectView.as_view(), name="reimbursement-review"),
    path("reimbursements/<uuid:pk>/pay/", ReimbursementPaymentView.as_view(), name="reimbursement-pay"),
    
    # Router URLs - these come last so specific patterns above take precedence
    path('', include(router.urls)),
]

# Add tasks router separately to avoid conflicts
tasks_router = DefaultRouter() 
tasks_router.register(r'tasks', TaskViewSet, basename='task')
urlpatterns += [
    path('', include(tasks_router.urls)),
]

