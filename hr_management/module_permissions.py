"""
Module Access Control Configuration

This file maps API ViewSets to their corresponding tenant modules.
Each ViewSet is assigned a module_key that must be enabled for the tenant
to access that API.

Module Keys (from ModuleDefinition):
- HR_SYSTEM: HR Management System (employees, attendance, shifts, leaves)
- TASK_SYSTEM: Task Management System (tasks, teams)
- COMPLAINT_SYSTEM: Complaint Management System
- POS_SYSTEM: POS Management System
- BRANCH_SYSTEM: Branch Management System
- INVENTORY_SYSTEM: Inventory Management System
- DOCUMENT_SYSTEM: Document Management System
- PRODUCT_SYSTEM: Product Management System
- NOTIFICATION_SYSTEM: Notification System
- ANALYTICS_SYSTEM: Analytics & Reporting System
- SETTINGS_SYSTEM: Settings & Configuration System
- FINANCIAL_SYSTEM: Financial Management System (wallets, reimbursements)
"""

# Map ViewSet class names to module keys
VIEWSET_MODULE_MAP = {
    # HR_SYSTEM - Employee Management, Attendance, Shifts, Leaves
    'EmployeeViewSet': 'HR_SYSTEM',
    'EmployeeAttendanceViewSet': 'HR_SYSTEM',
    'AttendanceStatsView': 'HR_SYSTEM',
    'WorkShiftViewSet': 'HR_SYSTEM',
    'ShiftAttendanceViewSet': 'HR_SYSTEM',
    'WeeklyShiftScheduleViewSet': 'HR_SYSTEM',
    'ShiftOverrideViewSet': 'HR_SYSTEM',
    'LeaveRequestViewSet': 'HR_SYSTEM',

    # TASK_SYSTEM - Tasks and Teams
    'TaskViewSet': 'TASK_SYSTEM',
    'SubtaskViewSet': 'TASK_SYSTEM',
    'TaskReportViewSet': 'TASK_SYSTEM',
    'TaskCommentViewSet': 'TASK_SYSTEM',
    'TeamViewSet': 'TASK_SYSTEM',
    'TeamMembershipViewSet': 'TASK_SYSTEM',
    'TeamTaskViewSet': 'TASK_SYSTEM',

    # COMPLAINT_SYSTEM - Client Complaints
    'ComplaintCategoryViewSet': 'COMPLAINT_SYSTEM',
    'ClientComplaintViewSet': 'COMPLAINT_SYSTEM',
    'ClientComplaintStatusViewSet': 'COMPLAINT_SYSTEM',
    'ClientComplaintCommentViewSet': 'COMPLAINT_SYSTEM',
    'ClientComplaintTaskViewSet': 'COMPLAINT_SYSTEM',
    'TicketDelayThresholdViewSet': 'COMPLAINT_SYSTEM',

    # DOCUMENT_SYSTEM - Documents and Notes
    'EmployeeDocumentViewSet': 'DOCUMENT_SYSTEM',
    'EmployeeNoteViewSet': 'DOCUMENT_SYSTEM',

    # FINANCIAL_SYSTEM - Wallets and Reimbursements
    'WalletViewSet': 'FINANCIAL_SYSTEM',
    'WalletTransactionViewSet': 'FINANCIAL_SYSTEM',
    'EmployeeWalletSystemViewSet': 'FINANCIAL_SYSTEM',
    'MultiWalletTransactionViewSet': 'FINANCIAL_SYSTEM',
    'WalletTransferViewSet': 'FINANCIAL_SYSTEM',
    'ReimbursementRequestViewSet': 'FINANCIAL_SYSTEM',

    # BRANCH_SYSTEM - Office Locations and Branches
    'OfficeLocationViewSet': 'BRANCH_SYSTEM',
    'BranchViewSet': 'BRANCH_SYSTEM',

    # NOTIFICATION_SYSTEM
    'NotificationViewSet': 'NOTIFICATION_SYSTEM',
}


def get_module_key_for_viewset(viewset_class_name):
    """
    Get the module key for a given ViewSet class name.
    Returns None if the ViewSet doesn't require module access.
    """
    return VIEWSET_MODULE_MAP.get(viewset_class_name)


def apply_module_permission(viewset_class):
    """
    Decorator to automatically apply module permission to a ViewSet.
    
    Usage:
        @apply_module_permission
        class EmployeeViewSet(viewsets.ModelViewSet):
            ...
    """
    module_key = get_module_key_for_viewset(viewset_class.__name__)
    
    if module_key:
        # Add module_key attribute
        viewset_class.module_key = module_key
        
        # Add HasModuleAccess to permission_classes if not already present
        from .custom_permissions import HasModuleAccess
        
        if hasattr(viewset_class, 'permission_classes'):
            if HasModuleAccess not in viewset_class.permission_classes:
                viewset_class.permission_classes = list(viewset_class.permission_classes) + [HasModuleAccess]
        else:
            viewset_class.permission_classes = [HasModuleAccess]
    
    return viewset_class
