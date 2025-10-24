"""
Module Access Control Configuration

This file maps API ViewSets to their corresponding tenant modules.
Each ViewSet is assigned a module_key that must be enabled for the tenant
to access that API.

Module Keys (from ModuleDefinition):
- employees: Employee Management
- attendance: Attendance Tracking
- shifts: Shift Management
- leaves: Leave Management
- wallets: Wallet & Salary System
- tasks: Task Management
- teams: Team Management
- complaints: Client Complaint System
- reimbursements: Reimbursement System
- scheduling: Shift Scheduling
"""

# Map ViewSet class names to module keys
VIEWSET_MODULE_MAP = {
    # Employee Management Module
    'EmployeeViewSet': 'employees',
    'EmployeeDocumentViewSet': 'employees',
    'EmployeeNoteViewSet': 'employees',
    
    # Attendance Module
    'EmployeeAttendanceViewSet': 'attendance',
    'AttendanceStatsView': 'attendance',
    
    # Shift Management Module
    'WorkShiftViewSet': 'shifts',
    'ShiftAttendanceViewSet': 'shifts',
    'WeeklyShiftScheduleViewSet': 'scheduling',
    'ShiftOverrideViewSet': 'scheduling',
    
    # Leave Management Module
    'LeaveRequestViewSet': 'leaves',
    
    # Wallet & Salary Module
    'WalletViewSet': 'wallets',
    'WalletTransactionViewSet': 'wallets',
    'EmployeeWalletSystemViewSet': 'wallets',
    'MultiWalletTransactionViewSet': 'wallets',
    'WalletTransferViewSet': 'wallets',
    
    # Reimbursement Module
    'ReimbursementRequestViewSet': 'reimbursements',
    
    # Task Management Module
    'TaskViewSet': 'tasks',
    'SubtaskViewSet': 'tasks',
    'TaskReportViewSet': 'tasks',
    'TaskCommentViewSet': 'tasks',
    
    # Team Management Module
    'TeamViewSet': 'teams',
    'TeamMembershipViewSet': 'teams',
    'TeamTaskViewSet': 'teams',
    
    # Client Complaint System Module
    'ComplaintCategoryViewSet': 'complaints',
    'ClientComplaintViewSet': 'complaints',
    'ClientComplaintStatusViewSet': 'complaints',
    'ClientComplaintCommentViewSet': 'complaints',
    'ClientComplaintTaskViewSet': 'complaints',
    'TicketDelayThresholdViewSet': 'complaints',
    
    # Office Location (usually always enabled)
    'OfficeLocationViewSet': None,  # No module restriction
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
