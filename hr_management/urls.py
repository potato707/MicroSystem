from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .tenant_creator_view import tenant_creator_view
from .views import (
    EmployeeViewSet, EmployeeDocumentViewSet, EmployeeNoteViewSet, EmployeeAttendanceListCreateView, 
    EmployeeAttendanceDetailView, CheckInView, CheckOutView, WorkShiftViewSet, ShiftCheckInView, 
    ShiftCheckOutView, ShiftBreakView, LeaveRequestCreateView, LeaveRequestUpdateStatusView, 
    LeaveRequestListView, ComplaintCreateView, ComplaintReplyCreateView, ComplaintListView, 
    ComplaintCloseView, WalletDetailView, WalletTransactionCreateView, WalletTransactionListView, 
    CentralWalletDetailView, CentralWalletTransactionCreateView, CentralWalletTransactionListView, 
    ReimbursementRequestListView, ReimbursementRequestApproveRejectView, ReimbursementRequestCreateView, ReimbursementPaymentView, 
    CurrentUserView, EmployeeDashboardStatsView, TaskViewSet, TaskUpdateView, TodayTasksView, 
    ManagerDashboardView, TaskReportViewSet, TaskCommentViewSet, QuickTaskActionsView, SubtaskViewSet, AdminTaskManagementView, 
    SubtaskQuickActionsView, AssignableEmployeesView, TeamMembersView, TeamViewSet, TeamMembershipViewSet, TeamTaskViewSet, AssignTaskToTeamView, 
    TeamDashboardView, OfficeLocationViewSet, SetOfficeLocationView, CurrentOfficeLocationView,
    # Multi-wallet views
    EmployeeWalletSystemView, WalletTransferCreateView,
    # Client Complaint System views
    ComplaintCategoryViewSet, PublicComplaintCategoryListView, ClientComplaintViewSet,
    ClientComplaintStatusViewSet, PublicClientComplaintCreateView, ClientComplaintReviewView, 
    ClientComplaintAssignmentView, ClientComplaintEmployeeAssignmentView, ClientComplaintMultipleAssignmentView,
    ClientComplaintRemoveTeamAssignmentView, ClientComplaintRemoveEmployeeAssignmentView,
    ClientComplaintStatusUpdateView, ClientComplaintCommentViewSet, 
    TeamComplaintDashboardView, ComplaintDashboardStatsView, ClientComplaintTaskCreateView, CreateTaskForComplaintView,
    # Complaint Admin Permission Views
    TeamComplaintAdminPermissionView, EmployeeComplaintAdminPermissionView, UserComplaintAdminPermissionsView,
    # Ticket Automation Views
    TicketDelayThresholdViewSet, TicketAutomationStatsView,
    # Notification Views
    NotificationViewSet,
    # Shift Scheduling Views
    WeeklyShiftScheduleViewSet, ShiftOverrideViewSet, ShiftAttendanceViewSet
)

# Import client portal views separately
from .client_portal_views import (
    ClientPortalAccessView, ClientPortalReplyView, GenerateClientAccessLinkView,
    AdminRespondToClientReplyView, ClientRepliesListView, ClientPortalTokenDeactivateView,
    ClientPortalReplyDeleteView
)

# Import client authentication and dashboard views
from .client_auth_views import (
    ClientRegisterView, ClientLoginView, ClientLogoutView, ClientCurrentUserView,
    ClientChangePasswordView, ClientProfileUpdateView,
    CheckPhoneExistsView, CheckEmailExistsView, PasswordResetRequestView, PasswordResetConfirmView,
    SendEmailVerificationCodeView, VerifyEmailCodeAndUpdateView, AllClientsFromAllTenantsView,
    AllClientsDashboardView
)
from .client_dashboard_views import (
    ClientDashboardStatsView, ClientComplaintsListView, ClientComplaintDetailView,
    ClientSubmitComplaintView, ClientAvailableCategoriesView, ClientComplaintStatusHistoryView,
    ClientComplaintRepliesView, ClientComplaintAddReplyView, ClientComplaintDeleteReplyView
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

# Client Complaint System
router.register(r'complaint-categories', ComplaintCategoryViewSet, basename='complaint-category')
router.register(r'client-complaint-statuses', ClientComplaintStatusViewSet, basename='client-complaint-status')
router.register(r'client-complaints', ClientComplaintViewSet, basename='client-complaint')
# Nested route for comments - this will create /hr/client-complaints/{complaint_pk}/comments/
router.register(r'client-complaints/(?P<complaint_pk>[^/.]+)/comments', ClientComplaintCommentViewSet, basename='client-complaint-comment')

# Ticket Automation System
router.register(r'ticket-thresholds', TicketDelayThresholdViewSet, basename='ticket-threshold')

# Notification System
router.register(r'notifications', NotificationViewSet, basename='notification')

# Shift Scheduling System
router.register(r'shift-schedules', WeeklyShiftScheduleViewSet, basename='shift-schedule')
router.register(r'shift-overrides', ShiftOverrideViewSet, basename='shift-override')
router.register(r'shift-attendance', ShiftAttendanceViewSet, basename='shift-attendance')

urlpatterns = [
    # JWT Authentication endpoints (for admin/employee login)
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # TO-DO System - specific task URLs must come before router patterns
    path("tasks/today/", TodayTasksView.as_view(), name="today-tasks"),
    path("tasks/manage/", AdminTaskManagementView.as_view(), name="admin-task-management"),
    path("tasks/<uuid:task_id>/update/", TaskUpdateView.as_view(), name="task-update"),
    path("tasks/<uuid:task_id>/actions/", QuickTaskActionsView.as_view(), name="task-actions"),
    path("subtasks/<uuid:subtask_id>/actions/", SubtaskQuickActionsView.as_view(), name="subtask-actions"),
    path("tasks/<uuid:task_id>/assignable-employees/", AssignableEmployeesView.as_view(), name="task-assignable-employees"),
    path("manager/dashboard/", ManagerDashboardView.as_view(), name="manager-dashboard"),
    
    # Teams
    path("teams/<uuid:team_id>/dashboard/", TeamDashboardView.as_view(), name="team-dashboard"),
    path("teams/<uuid:team_id>/members/", TeamMembersView.as_view(), name="team-members"),
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
    
    # Complaint Admin Permission Management
    path("complaint-admin-permissions/teams/", TeamComplaintAdminPermissionView.as_view(), name="team-complaint-admin-permissions"),
    path("complaint-admin-permissions/teams/<int:pk>/", TeamComplaintAdminPermissionView.as_view(), name="team-complaint-admin-permission-detail"),
    path("complaint-admin-permissions/employees/", EmployeeComplaintAdminPermissionView.as_view(), name="employee-complaint-admin-permissions"),
    path("complaint-admin-permissions/employees/<int:pk>/", EmployeeComplaintAdminPermissionView.as_view(), name="employee-complaint-admin-permission-detail"),
    path("complaint-admin-permissions/user/", UserComplaintAdminPermissionsView.as_view(), name="user-complaint-admin-permissions"),
    
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
    
    # Client Complaint System - Public endpoints (no authentication required)
    path("public/complaint-categories/", PublicComplaintCategoryListView.as_view(), name="public-complaint-categories"),
    path("public/client-complaints/", PublicClientComplaintCreateView.as_view(), name="public-client-complaint-create"),
    path("public/check-phone/", CheckPhoneExistsView.as_view(), name="check-phone-exists"),
    path("public/check-email/", CheckEmailExistsView.as_view(), name="check-email-exists"),
    path("public/password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("public/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    
    # Client Authentication Endpoints (for client login/logout)
    path("client/auth/register/", ClientRegisterView.as_view(), name="client-register"),
    path("client/auth/login/", ClientLoginView.as_view(), name="client-login"),
    path("client/auth/logout/", ClientLogoutView.as_view(), name="client-logout"),
    path("client/auth/me/", ClientCurrentUserView.as_view(), name="client-current-user"),
    path("client/auth/change-password/", ClientChangePasswordView.as_view(), name="client-change-password"),
    path("client/auth/profile/", ClientProfileUpdateView.as_view(), name="client-profile-update"),
    path("client/auth/send-verification-code/", SendEmailVerificationCodeView.as_view(), name="send-email-verification"),
    path("client/auth/verify-email-code/", VerifyEmailCodeAndUpdateView.as_view(), name="verify-email-code"),
    
    # Admin endpoint to view all clients from all tenants
    path("admin/all-clients/", AllClientsFromAllTenantsView.as_view(), name="all-clients-from-all-tenants"),
    
    # Django template view for all clients (requires admin login)
    path("admin/dashboard/all-clients/", AllClientsDashboardView.as_view(), name="admin-all-clients-dashboard"),
    
    # Client Dashboard Endpoints (authenticated clients only)
    path("client/dashboard/stats/", ClientDashboardStatsView.as_view(), name="client-dashboard-stats"),
    path("client/complaints/", ClientComplaintsListView.as_view(), name="client-complaints-list"),
    path("client/complaints/<uuid:complaint_id>/", ClientComplaintDetailView.as_view(), name="client-complaint-detail"),
    path("client/complaints/<uuid:complaint_id>/history/", ClientComplaintStatusHistoryView.as_view(), name="client-complaint-history"),
    path("client/complaints/<uuid:complaint_id>/replies/", ClientComplaintRepliesView.as_view(), name="client-complaint-replies"),
    path("client/complaints/<uuid:complaint_id>/replies/add/", ClientComplaintAddReplyView.as_view(), name="client-complaint-add-reply"),
    path("client/complaints/<uuid:complaint_id>/replies/<int:reply_id>/delete/", ClientComplaintDeleteReplyView.as_view(), name="client-complaint-delete-reply"),
    path("client/complaints/submit/", ClientSubmitComplaintView.as_view(), name="client-submit-complaint"),
    path("client/categories/", ClientAvailableCategoriesView.as_view(), name="client-available-categories"),
    
    # Client Complaint System - Internal endpoints (authentication required)
    path("client-complaints/<uuid:pk>/review/", ClientComplaintReviewView.as_view(), name="client-complaint-review"),
    path("client-complaints/<uuid:pk>/assign/", ClientComplaintAssignmentView.as_view(), name="client-complaint-assign"),
    path("client-complaints/<uuid:pk>/assign-employee/", ClientComplaintEmployeeAssignmentView.as_view(), name="client-complaint-assign-employee"),
    path("client-complaints/<uuid:pk>/assign-multiple/", ClientComplaintMultipleAssignmentView.as_view(), name="client-complaint-assign-multiple"),
    path("client-complaints/<uuid:pk>/remove-team/<int:assignment_id>/", ClientComplaintRemoveTeamAssignmentView.as_view(), name="client-complaint-remove-team"),
    path("client-complaints/<uuid:pk>/remove-employee/<int:assignment_id>/", ClientComplaintRemoveEmployeeAssignmentView.as_view(), name="client-complaint-remove-employee"),
    path("client-complaints/<uuid:pk>/status/", ClientComplaintStatusUpdateView.as_view(), name="client-complaint-status"),
    path("client-complaints/tasks/create/", ClientComplaintTaskCreateView.as_view(), name="client-complaint-task-create"),
    path("client-complaints/create-task/", CreateTaskForComplaintView.as_view(), name="create-task-for-complaint"),
    path("client-complaints/dashboard-stats/", ComplaintDashboardStatsView.as_view(), name="client-complaint-dashboard-stats"),
    path("team-complaints/", TeamComplaintDashboardView.as_view(), name="team-complaint-dashboard"),
    
    # Ticket Automation URLs
    path("ticket-automation/stats/", TicketAutomationStatsView.as_view(), name="ticket-automation-stats"),
    
    # Tenant Creator - Custom page for creating tenants
    path("create-tenant/", tenant_creator_view, name="create-tenant"),
    
    # Client Portal URLs - Public access endpoints
    path("client-portal/<str:token>/", ClientPortalAccessView.as_view(), name="client-portal-access"),
    path("client-portal/<str:token>/reply/", ClientPortalReplyView.as_view(), name="client-portal-reply"),
    path("client-portal/<str:token>/deactivate/", ClientPortalTokenDeactivateView.as_view(), name="client-portal-deactivate"),
    path("client-portal/<str:token>/reply/<int:reply_id>/delete/", ClientPortalReplyDeleteView.as_view(), name="client-portal-reply-delete"),
    
    # Internal client management endpoints
    path("client-complaints/<uuid:complaint_id>/generate-link/", GenerateClientAccessLinkView.as_view(), name="generate-client-access-link"),
    path("client-complaints/<uuid:complaint_id>/replies/", ClientRepliesListView.as_view(), name="client-replies-list"),
    path("client-replies/<uuid:reply_id>/respond/", AdminRespondToClientReplyView.as_view(), name="admin-respond-to-client-reply"),
    
    # Router URLs - these come last so specific patterns above take precedence
    path('', include(router.urls)),
]

# Add tasks router separately to avoid conflicts
tasks_router = DefaultRouter() 
tasks_router.register(r'tasks', TaskViewSet, basename='task')
urlpatterns += [
    path('', include(tasks_router.urls)),
]

