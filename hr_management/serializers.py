from rest_framework import serializers
import datetime
import calendar
from .models import (
    Employee, EmployeeDocument, EmployeeNote, EmployeeAttendance, WorkShift, User, 
    LeaveRequest, Complaint, ComplaintReply, ComplaintAttachment, EmployeeDocument, 
    Wallet, WalletTransaction, ReimbursementRequest, ReimbursementAttachment, 
    Task, Subtask, TaskReport, TaskComment, Team, TeamMembership, TeamTask, OfficeLocation,
    ShareableTaskLink,  # Added for task sharing feature
    # Multi-wallet models
    EmployeeWalletSystem, MainWallet, ReimbursementWallet, AdvanceWallet, 
    MultiWalletTransaction, WalletTransfer,
    # Client Complaint System models
    ComplaintCategory, ClientComplaint, ClientComplaintStatus, ClientComplaintAttachment, 
    ClientComplaintAssignment, ClientComplaintEmployeeAssignment, ClientComplaintTask, ClientComplaintComment,
    ClientComplaintStatusHistory, ClientComplaintAccessToken, ClientComplaintReply,
    # Ticket Automation models
    TicketDelayThreshold,
    # Shift Scheduling models
    WeeklyShiftSchedule, ShiftOverride, ShiftAttendance,
    # Helper functions
    get_employee_shift_for_date, calculate_weekly_hours
)
from utils.timezone_utils import system_now


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - used for client authentication"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name', 'role', 'profile_picture']
        read_only_fields = ['id', 'username', 'email', 'role']


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = '__all__'

class EmployeeNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeNote
        fields = '__all__'

class EmployeeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", )
    email = serializers.EmailField(source="user.email", )
    password = serializers.CharField(source="user.password", write_only=True, required=False, allow_blank=True)
    role = serializers.CharField(source="user.role", )
    payroll_time_left = serializers.SerializerMethodField()
    attachments = EmployeeDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id", "name", "position", "department", "hire_date",
            "salary", "status", "phone", "email", "address", "emergency_contact",
            "profile_picture", "username", "password", "role", "payroll_time_left", "attachments"
        ]

    def get_payroll_time_left(self, obj):
        now = system_now()
        # today = datetime.date.today()
        today = now.date()
        # last day of this month
        last_day = calendar.monthrange(today.year, today.month)[1]
        payroll_date = datetime.date(today.year, today.month, last_day)

        # if payroll already passed today, calculate for next month
        if today > payroll_date:
            next_month = today.month + 1 if today.month < 12 else 1
            year = today.year if today.month < 12 else today.year + 1
            last_day = calendar.monthrange(year, next_month)[1]
            payroll_date = datetime.date(year, next_month, last_day)

        delta = payroll_date - today
        return f"{delta.days}"

    def create(self, validated_data):
        print(validated_data)
        user = validated_data.pop("user")
        username = user.pop("username")
        password = user.pop("password")
        role = user.pop("role", "employee")

        user = User.objects.create_user(
            username=username,
            email=user["email"],
            password=password,
            role=role
        )
        employee = Employee.objects.create(**validated_data, user=user)
        return employee

    def update(self, instance, validated_data):

        user = validated_data.pop("user")
        username = user.pop("username", None)
        password = user.pop("password", None)
        role = user.pop("role", "employee")
        if username:
            instance.user.username = username
        if "email" in validated_data:
            instance.user.email = user["email"]
        if password:
            instance.user.set_password(password)
        if role:
            instance.user.role = role
        instance.user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance




class EmployeeAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    shifts = serializers.SerializerMethodField()
    total_hours = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeAttendance
        fields = ["id", "employee", "employee_name", "date", "check_in", "check_out", "status", "paid", "shifts", "total_hours"]
        read_only_fields = ["employee", "shifts", "total_hours"]
    
    def get_shifts(self, obj):
        shifts = obj.shifts.all().order_by('check_in')
        return WorkShiftSerializer(shifts, many=True).data
    
    def get_total_hours(self, obj):
        total_minutes = sum(shift.duration_minutes for shift in obj.shifts.all() if shift.check_out)
        return round(total_minutes / 60, 2)


class WorkShiftSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    duration_minutes = serializers.ReadOnlyField()
    is_on_break = serializers.ReadOnlyField()

    class Meta:
        model = WorkShift
        fields = [
            "id", "employee", "employee_name", "attendance", "shift_type", 
            "check_in", "check_out", "break_start", "break_end", 
            "location", "checkin_latitude", "checkin_longitude", 
            "checkout_latitude", "checkout_longitude", "notes", "is_active", 
            "created_at", "updated_at", "duration_minutes", "is_on_break"
        ]
        read_only_fields = ["employee", "attendance", "created_at", "updated_at", "duration_minutes", "is_on_break"]


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.name", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id", "employee", "employee_name", "start_date", "end_date", "reason", 
            "status", "is_paid", "admin_comment", "reviewed_by", "reviewed_by_name", 
            "reviewed_at", "created_at", "updated_at"
        ]
        read_only_fields = ["created_at", "updated_at", "employee", "reviewed_by", "reviewed_by_name", "reviewed_at"]


class LeaveRequestReviewSerializer(serializers.ModelSerializer):
    """Serializer for admin to review leave requests"""
    
    class Meta:
        model = LeaveRequest
        fields = ["status", "is_paid", "admin_comment"]
    
    def validate(self, data):
        if data.get('status') in ['approved', 'rejected'] and data.get('is_paid') is None:
            raise serializers.ValidationError({
                'is_paid': 'You must specify whether the leave is paid or unpaid when approving/rejecting.'
            })
        return data

class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintAttachment
        fields = ["id", "file_url", "uploaded_at"]

class ComplaintReplySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_name = serializers.CharField(source="user.name", read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)
    attachment_links = serializers.ListField(
        child=serializers.URLField(), write_only=True, required=False
    )

    class Meta:
        model = ComplaintReply
        fields = ["id", "user", "user_name", "message", "created_at", "attachments", "attachment_links"]


    def create(self, validated_data):
        attachment_links = validated_data.pop("attachment_links", [])
        # user = self.context['request'].user  # get employee from user
        #User already there because of the current user default
        complaint_reply = ComplaintReply.objects.create(**validated_data)

        for link in attachment_links:
            ComplaintAttachment.objects.create(reply=complaint_reply, file_url=link)

        return complaint_reply

class ComplaintSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)
    replies = ComplaintReplySerializer(many=True, read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)
    attachment_links = serializers.ListField(
        child=serializers.URLField(), write_only=True, required=False
    )

    class Meta:
        model = Complaint
        fields = ["id", "employee", "employee_name", "title", "description", "status", "urgency", "created_at", "updated_at", "attachments", "replies", "attachment_links"]
        read_only_fields = ["created_at", "updated_at", "employee"]

    def create(self, validated_data):
        attachment_links = validated_data.pop("attachment_links", [])
        employee = self.context['request'].user.employee  # get employee from user
        complaint = Complaint.objects.create(employee=employee, **validated_data)

        for link in attachment_links:
            ComplaintAttachment.objects.create(complaint=complaint, file_url=link)

        return complaint


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ["id", "transaction_type", "amount", "description", "created_at"]


class WalletSerializer(serializers.ModelSerializer):
    transactions = WalletTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Wallet
        fields = ["id", "employee", "balance", "transactions"]
        read_only_fields = ["balance", "transactions"]


class CentralWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "balance"]

class CentralWalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ["id", "transaction_type", "amount", "description", "created_at"]

# Multi-Wallet System Serializers
class MainWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainWallet
        fields = ["id", "balance"]

class ReimbursementWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReimbursementWallet
        fields = ["id", "balance"]

class AdvanceWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvanceWallet
        fields = ["id", "balance"]

class MultiWalletTransactionSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='wallet_system.employee.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = MultiWalletTransaction
        fields = [
            "id", "wallet_type", "transaction_type", "amount", "description",
            "reimbursement_request", "related_transaction", "created_at", 
            "created_by", "created_by_name", "employee_name"
        ]
        read_only_fields = ["created_at", "created_by", "employee_name", "created_by_name"]
    
    def validate(self, data):
        transaction_type = data.get('transaction_type')
        
        # Validate transactions that affect multiple wallets are handled properly
        multi_wallet_transactions = [
            'reimbursement_paid', 'advance_repaid', 
            'advance_withdrawal', 'advance_deduction'
        ]
        
        if transaction_type in multi_wallet_transactions:
            # These will automatically affect multiple wallets in the view
            pass
        
        return data

class EmployeeWalletSystemSerializer(serializers.ModelSerializer):
    main_wallet = MainWalletSerializer(read_only=True)
    reimbursement_wallet = ReimbursementWalletSerializer(read_only=True) 
    advance_wallet = AdvanceWalletSerializer(read_only=True)
    multi_transactions = MultiWalletTransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmployeeWalletSystem
        fields = [
            "id", "employee", "main_wallet", "reimbursement_wallet", 
            "advance_wallet", "multi_transactions", "created_at", "updated_at"
        ]

class WalletTransferSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='wallet_system.employee.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = WalletTransfer
        fields = [
            "id", "transfer_type", "amount", "description", "from_wallet_type",
            "to_wallet_type", "created_at", "created_by", "created_by_name", "employee_name"
        ]
        read_only_fields = ["created_at", "created_by", "employee_name", "created_by_name"]

class ReimbursementAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReimbursementAttachment
        fields = ["id", "file_url", "uploaded_at"]

class ReimbursementRequestSerializer(serializers.ModelSerializer):
    attachments = ReimbursementAttachmentSerializer(many=True, read_only=True)
    attachment_links = serializers.ListField(
        child=serializers.URLField(), write_only=True, required=False
    )
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    paid_by_name = serializers.CharField(source='paid_by.username', read_only=True)

    class Meta:
        model = ReimbursementRequest
        fields = [
            "id", "employee", "employee_name", "amount", "description",
            "status", "admin_comment", "approved_at", "paid_at", 
            "approved_by", "approved_by_name", "paid_by", "paid_by_name",
            "created_at", "updated_at", "attachments", "attachment_links"
        ]
        read_only_fields = ["status", "admin_comment", "created_at", "updated_at", "employee", "employee_name"]

    def create(self, validated_data):
        attachment_links = validated_data.pop("attachment_links", [])
        user = self.context["request"].user
        employee = user.employee  # assume كل user عنده employee

        reimbursement = ReimbursementRequest.objects.create(employee=employee, **validated_data)

        for link in attachment_links:
            ReimbursementAttachment.objects.create(reimbursement=reimbursement, file_url=link)

        return reimbursement

class ReimbursementReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReimbursementRequest
        fields = ["status", "admin_comment"]  # <-- only review fields
        extra_kwargs = {
            "status": {"required": True},
            "review_comment": {"required": False},
        }


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'comment', 'author', 'author_name', 'created_at', 'is_manager_note']
        read_only_fields = ['author', 'created_at']


class SubtaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating subtasks during task creation"""
    
    class Meta:
        model = Subtask
        fields = [
            'assigned_employee', 'title', 'description', 'status', 'priority', 
            'estimated_minutes', 'notes', 'order'
        ]
        
    def validate_assigned_employee(self, value):
        """Validate that assigned employee exists and user has permission to assign"""
        if value:
            request = self.context.get('request')
            if request and request.user.role == 'employee':
                # Employees can only assign subtasks to themselves
                try:
                    if value != request.user.employee:
                        raise serializers.ValidationError("Employees can only assign subtasks to themselves")
                except Employee.DoesNotExist:
                    raise serializers.ValidationError("Employee profile not found")
        return value


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks with subtasks in single request"""
    subtasks = SubtaskCreateSerializer(many=True, required=False, write_only=True)
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 'date', 
            'start_date', 'end_date', 'estimated_minutes', 'notes', 'subtasks'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        # Include employee field for admins, always optional (will be set by perform_create)
        if request and request.user.role == 'admin':
            self.fields['employee'] = serializers.PrimaryKeyRelatedField(
                queryset=Employee.objects.all(), 
                required=False,  # Always optional - perform_create will handle it
                allow_null=True
            )
            self.fields['team'] = serializers.PrimaryKeyRelatedField(
                queryset=Team.objects.all(),
                required=False,
                allow_null=True
            )
    
    def validate(self, data):
        """Custom validation for tasks"""
        # Validate subtasks
        subtasks_data = data.get('subtasks', [])
        if subtasks_data:
            # Ensure subtask titles are unique within the task
            titles = [subtask.get('title', '') for subtask in subtasks_data]
            if len(titles) != len(set(titles)):
                raise serializers.ValidationError({
                    'subtasks': 'Subtask titles must be unique within a task'
                })
        
        # Note: employee field will be set automatically by perform_create based on user role
        # Admin without employee/team specified → assigned to self (if has employee profile)
        # Admin with employee specified → assigned to that employee
        # Admin with team specified → team task (no specific employee)
        # Employee → always assigned to self
        
        return data
    
    def create(self, validated_data):
        """Create task with subtasks in a single transaction"""
        from django.db import transaction
        
        subtasks_data = validated_data.pop('subtasks', [])
        
        with transaction.atomic():
            # Create the main task
            task = Task.objects.create(**validated_data)
            
            # Create subtasks if provided
            for subtask_data in subtasks_data:
                Subtask.objects.create(
                    parent_task=task,
                    **subtask_data
                )
            
            return task


class SubtaskSerializer(serializers.ModelSerializer):
    time_spent = serializers.ReadOnlyField()
    is_paused = serializers.ReadOnlyField()
    assigned_employee_name = serializers.CharField(source='assigned_employee.name', read_only=True)
    assigned_employee_position = serializers.CharField(source='assigned_employee.position', read_only=True)
    
    class Meta:
        model = Subtask
        fields = [
            'id', 'parent_task', 'assigned_employee', 'assigned_employee_name', 'assigned_employee_position',
            'title', 'description', 'status', 'priority', 'estimated_minutes', 'started_at', 
            'completed_at', 'paused_at', 'total_pause_time', 'is_paused', 'created_at', 
            'updated_at', 'notes', 'order', 'time_spent'
        ]
        read_only_fields = ['created_at', 'updated_at', 'time_spent', 'is_paused', 'paused_at', 'total_pause_time', 'assigned_employee_name', 'assigned_employee_position']


class TaskSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True, allow_null=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    subtasks = SubtaskSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    is_paused = serializers.ReadOnlyField()
    time_spent = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'employee', 'employee_name', 'team', 'team_name', 'title', 'description', 'status', 
            'priority', 'date', 'start_date', 'end_date', 'created_by', 'created_by_name', 'assigned_by_manager',
            'estimated_minutes', 'actual_minutes', 'started_at', 'completed_at',
            'paused_at', 'total_pause_time', 'is_paused',
            'created_at', 'updated_at', 'notes', 'comments', 'subtasks', 'is_overdue', 'time_spent'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'time_spent', 'is_overdue', 'is_paused', 'paused_at', 'total_pause_time', 'employee_name', 'team_name']


class ShareableTaskLinkSerializer(serializers.ModelSerializer):
    """Serializer for shareable task links"""
    task_title = serializers.CharField(source='task.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    share_url = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = ShareableTaskLink
        fields = [
            'id', 'task', 'task_title', 'token', 'created_by', 'created_by_name',
            'created_at', 'expires_at', 'is_active', 'view_count', 'last_viewed_at',
            'allow_comments', 'share_url', 'is_expired', 'is_valid'
        ]
        read_only_fields = ['token', 'created_by', 'created_at', 'view_count', 'last_viewed_at']
    
    def get_share_url(self, obj):
        """Get the full shareable URL"""
        request = self.context.get('request')
        if request:
            # Get the frontend URL from settings or use request origin
            from django.conf import settings
            frontend_url = getattr(settings, 'FRONTEND_URL', request.build_absolute_uri('/').rstrip('/'))
            return f"{frontend_url}/shared/task/{obj.token}"
        return f"/shared/task/{obj.token}"
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_is_valid(self, obj):
        return obj.is_valid()
    
    def create(self, validated_data):
        # Generate unique token
        validated_data['token'] = ShareableTaskLink.generate_token()
        return super().create(validated_data)


class SharedTaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for viewing shared task details (public access)"""
    employee_name = serializers.CharField(source='employee.name', read_only=True, allow_null=True)
    team_name = serializers.CharField(source='team.name', read_only=True, allow_null=True)
    subtasks = SubtaskSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority', 'date', 'start_date', 'end_date',
            'employee_name', 'team_name', 'created_by_name',
            'estimated_minutes', 'actual_minutes', 'started_at', 'completed_at',
            'created_at', 'updated_at', 'notes', 'subtasks'
        ]
        # Exclude sensitive fields like employee ID, created_by ID, etc.


class TaskUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating task status and progress"""
    
    class Meta:
        model = Task
        fields = ['status', 'notes', 'actual_minutes', 'started_at', 'completed_at']
    
    def update(self, instance, validated_data):
        # Auto-set timestamps based on status changes
        new_status = validated_data.get('status', instance.status)
        
        if new_status == 'doing' and instance.status == 'to_do' and not instance.started_at:
            validated_data['started_at'] = system_now()
        
        if new_status == 'done' and instance.status != 'done' and not instance.completed_at:
            validated_data['completed_at'] = system_now()
            
        return super().update(instance, validated_data)


class TaskReportSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = TaskReport
        fields = [
            'id', 'employee', 'employee_name', 'date', 'total_tasks', 'completed_tasks',
            'in_progress_tasks', 'not_completed_tasks', 'completion_rate', 'summary_notes',
            'challenges_faced', 'achievements', 'tomorrow_priorities', 'submitted_at',
            'reviewed_by_manager', 'manager_feedback', 'manager_rating', 'tasks'
        ]
        read_only_fields = ['completion_rate', 'submitted_at']
    
    def get_tasks(self, obj):
        """Get tasks for the report date"""
        tasks = Task.objects.filter(employee=obj.employee, date=obj.date)
        return TaskSerializer(tasks, many=True, context=self.context).data
    
    def create(self, validated_data):
        # Auto-calculate task counts from actual tasks
        employee = validated_data['employee']
        date = validated_data['date']
        
        tasks = Task.objects.filter(employee=employee, date=date)
        
        validated_data['total_tasks'] = tasks.count()
        validated_data['completed_tasks'] = tasks.filter(status='done').count()
        validated_data['in_progress_tasks'] = tasks.filter(status='doing').count()
        validated_data['not_completed_tasks'] = tasks.filter(status='to_do').count()
        
        return super().create(validated_data)


class ManagerTaskDashboardSerializer(serializers.Serializer):
    """Serializer for manager dashboard data"""
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    in_progress_tasks = serializers.IntegerField()
    not_completed_tasks = serializers.IntegerField()
    completion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    overdue_tasks = serializers.IntegerField()
    tasks = TaskSerializer(many=True)


class TeamMembershipSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_position = serializers.CharField(source='employee.position', read_only=True)
    
    class Meta:
        model = TeamMembership
        fields = [
            'id', 'team', 'employee', 'employee_name', 'employee_position',
            'role', 'joined_at', 'is_active'
        ]
        read_only_fields = ['joined_at']


class TeamSerializer(serializers.ModelSerializer):
    team_leader_name = serializers.CharField(source='team_leader.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    members = TeamMembershipSerializer(source='memberships', many=True, read_only=True)
    member_count = serializers.ReadOnlyField()
    active_tasks_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'team_leader', 'team_leader_name',
            'created_by', 'created_by_name', 'is_active', 'created_at', 'updated_at',
            'members', 'member_count', 'active_tasks_count'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'member_count', 'active_tasks_count']


class TeamTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_status = serializers.CharField(source='task.status', read_only=True)
    task_employee_name = serializers.CharField(source='task.employee.name', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.name', read_only=True)
    
    class Meta:
        model = TeamTask
        fields = [
            'id', 'task', 'task_title', 'task_status', 'task_employee_name',
            'team', 'team_name', 'assigned_by', 'assigned_by_name',
            'can_reassign', 'team_priority', 'team_notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['assigned_by', 'created_at', 'updated_at']


class TeamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating teams"""
    member_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False,
        allow_empty=True
    )
    
    class Meta:
        model = Team
        fields = ['name', 'description', 'team_leader', 'member_ids']
    
    def validate_team_leader(self, value):
        """Ensure team leader is an active employee"""
        if value and value.status != 'active':
            raise serializers.ValidationError("Team leader must be an active employee")
        return value
    
    def validate_member_ids(self, value):
        """Ensure all member IDs are valid active employees"""
        if value:
            employees = Employee.objects.filter(id__in=value, status='active')
            if len(employees) != len(value):
                raise serializers.ValidationError("Some employee IDs are invalid or inactive")
        return value
    
    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        
        team = Team.objects.create(**validated_data)
        
        # Add members
        for employee_id in member_ids:
            employee = Employee.objects.get(id=employee_id)
            TeamMembership.objects.create(
                team=team,
                employee=employee,
                role='member'
            )
        
        # Add team leader as assistant_leader if not already a member
        if team.team_leader and team.team_leader.id not in member_ids:
            TeamMembership.objects.create(
                team=team,
                employee=team.team_leader,
                role='assistant_leader'
            )
        
        return team


class OfficeLocationSerializer(serializers.ModelSerializer):
    set_by_name = serializers.CharField(source='set_by.name', read_only=True)
    
    class Meta:
        model = OfficeLocation
        fields = ['id', 'name', 'latitude', 'longitude', 'radius_meters', 
                 'is_active', 'set_by', 'set_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'set_by', 'created_at', 'updated_at']


# Client Complaint System Serializers

class ComplaintCategorySerializer(serializers.ModelSerializer):
    assigned_teams_names = serializers.StringRelatedField(source='assigned_teams', many=True, read_only=True)
    
    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 'assigned_teams', 'assigned_teams_names', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClientComplaintAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientComplaintAttachment
        fields = ['id', 'file_url', 'file_name', 'file_size', 'uploaded_at', 'uploaded_by']
        read_only_fields = ['id', 'uploaded_at']


class ClientComplaintCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    
    def get_author_name(self, obj):
        """Get author name, fallback to username if name is empty"""
        if obj.author:
            name = obj.author.name.strip() if obj.author.name else ''
            if name:
                return name
            return obj.author.username or 'Unknown User'
        return 'Unknown User'
    
    class Meta:
        model = ClientComplaintComment
        fields = ['id', 'comment', 'is_internal', 'author', 'author_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class ClientComplaintStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()
    old_status_display = serializers.CharField(source='get_old_status_display', read_only=True)
    new_status_display = serializers.CharField(source='get_new_status_display', read_only=True)
    
    def get_changed_by_name(self, obj):
        return obj.changed_by.name if obj.changed_by else "النظام"
    
    class Meta:
        model = ClientComplaintStatusHistory
        fields = ['id', 'old_status', 'new_status', 'old_status_display', 'new_status_display', 
                 'changed_by', 'changed_by_name', 'reason', 'changed_at']
        read_only_fields = ['id', 'changed_at']


class ClientComplaintAssignmentSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.name', read_only=True)
    
    class Meta:
        model = ClientComplaintAssignment
        fields = ['id', 'team', 'team_name', 'assigned_by', 'assigned_by_name', 'assigned_at', 'notes', 'is_active']
        read_only_fields = ['id', 'assigned_by', 'assigned_at']


class ClientComplaintEmployeeAssignmentSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_position = serializers.CharField(source='employee.position', read_only=True)
    employee_department = serializers.CharField(source='employee.department', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.name', read_only=True)
    
    class Meta:
        model = ClientComplaintEmployeeAssignment
        fields = ['id', 'employee', 'employee_name', 'employee_position', 'employee_department', 
                 'assigned_by', 'assigned_by_name', 'assigned_at', 'notes', 'is_active']
        read_only_fields = ['id', 'assigned_by', 'assigned_at']


class ClientComplaintTaskSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_status = serializers.CharField(source='task.status', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    
    class Meta:
        model = ClientComplaintTask
        fields = ['id', 'task', 'task_title', 'task_status', 'team', 'team_name', 
                 'created_by', 'created_by_name', 'created_at', 'notes']
        read_only_fields = ['id', 'created_by', 'created_at']


class ClientComplaintStatusSerializer(serializers.ModelSerializer):
    """Serializer for custom complaint statuses"""
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    label = serializers.CharField(required=False)  # Make label optional, will auto-generate from name
    
    class Meta:
        model = ClientComplaintStatus
        fields = ['id', 'name', 'label', 'description', 'color', 'is_active', 'status_type',
                 'display_order', 'can_be_set_by_admin', 'is_final_status', 'created_at', 
                 'updated_at', 'created_by', 'created_by_name']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def validate_name(self, value):
        """Ensure status name is unique and valid"""
        # Check against default status names
        default_status_names = [choice[0] for choice in ClientComplaint.STATUS_CHOICES]
        if value in default_status_names:
            raise serializers.ValidationError("Cannot use default status names")
        return value
    
    def validate_color(self, value):
        """Validate hex color format"""
        import re
        if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', value):
            raise serializers.ValidationError("Invalid hex color format")
        return value
    
    def create(self, validated_data):
        """Create a new custom status, auto-generating label if not provided"""
        if 'label' not in validated_data or not validated_data['label']:
            validated_data['label'] = validated_data['name']
        
        # Set the created_by to the current user
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
            
        return super().create(validated_data)


class ClientComplaintSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    status_display = serializers.CharField(source='current_status_display', read_only=True)
    status_color = serializers.CharField(source='current_status_color', read_only=True)
    effective_status = serializers.CharField(read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    task_statistics = serializers.ReadOnlyField()
    
    # Automated status display message
    automated_status_message = serializers.SerializerMethodField()
    # Combined display status (prioritizes automated message for better UX)
    display_status_combined = serializers.SerializerMethodField()
    
    # Custom status details
    custom_status_details = ClientComplaintStatusSerializer(source='custom_status', read_only=True)
    
    # Related objects
    attachments = ClientComplaintAttachmentSerializer(many=True, read_only=True)
    assignments = ClientComplaintAssignmentSerializer(many=True, read_only=True)
    employee_assignments = ClientComplaintEmployeeAssignmentSerializer(many=True, read_only=True)
    tasks = ClientComplaintTaskSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()  # Custom method to include both comments and client replies
    status_history = ClientComplaintStatusHistorySerializer(many=True, read_only=True)
    
    def get_automated_status_message(self, obj):
        """Get user-friendly status message based on automated_status"""
        status_messages = {
            'waiting_for_system_response': 'في انتظار رد فريق الدعم',
            'waiting_for_client_response': 'في انتظار ردك',
            'delayed_by_system': 'متأخر - فريق الدعم',
            'delayed_by_client': 'متأخر - في انتظار ردك',
            'resolved_awaiting_confirmation': 'تم الحل - في انتظار التأكيد',
            'auto_closed': 'مغلق تلقائياً',
            'reopened': 'تم إعادة الفتح',
        }
        return status_messages.get(obj.automated_status, None)
    
    def get_display_status_combined(self, obj):
        """
        Get combined display status that prioritizes automated message
        This provides better UX by showing communication status when available
        """
        automated_msg = self.get_automated_status_message(obj)
        if automated_msg:
            return automated_msg
        # Fall back to main status display
        return obj.current_status_display
    
    def get_comments(self, obj):
        """Get unified comments including both internal comments and client replies"""
        combined_comments = []
        
        # Add internal comments
        for comment in obj.comments.all():
            # Get author name with fallback logic (same as ClientComplaintCommentSerializer)
            if comment.author:
                author_name = comment.author.name.strip() if comment.author.name else ''
                if not author_name:
                    author_name = comment.author.username or 'Unknown User'
            else:
                author_name = 'System'
            
            combined_comments.append({
                'id': f"comment_{comment.id}",
                'type': 'internal_comment' if comment.is_internal else 'external_comment',
                'comment': comment.comment,
                'author_name': author_name,
                'author_id': str(comment.author.id) if comment.author else None,
                'is_internal': comment.is_internal,
                'created_at': comment.created_at,
                'updated_at': comment.updated_at
            })
        
        # Add client replies  
        for reply in obj.client_replies.all():
            combined_comments.append({
                'id': f"reply_{reply.id}",
                'type': 'client_reply',
                'comment': reply.reply_text,
                'author_name': reply.client_name,
                'author_id': None,  # Client doesn't have internal user ID
                'client_email': reply.client_email,
                'is_internal': False,  # Client replies are never internal
                'created_at': reply.created_at,
                'updated_at': reply.created_at  # Client replies don't have updated_at
            })
            
            # Add admin response as a separate comment if it exists
            if reply.admin_response:
                combined_comments.append({
                    'id': f"admin_response_{reply.id}",
                    'type': 'admin_response',
                    'comment': reply.admin_response,
                    'author_name': reply.admin_responded_by.name if reply.admin_responded_by else 'Admin',
                    'author_id': str(reply.admin_responded_by.id) if reply.admin_responded_by else None,
                    'is_internal': True,
                    'created_at': reply.admin_responded_at,
                    'updated_at': reply.admin_responded_at,
                    'reply_to_client': reply.client_name  # Indicator this is responding to client
                })
        
        # Sort by creation date to show chronological order (newest first)
        combined_comments.sort(key=lambda x: x['created_at'], reverse=True)
        
        return combined_comments
    
    class Meta:
        model = ClientComplaint
        fields = [
            'id', 'client_name', 'client_email', 'client_phone', 'project_name', 'project_code',
            'category', 'category_name', 'category_color', 'priority', 'priority_display',
            'title', 'description', 'status', 'status_display', 'status_color', 'effective_status',
            'custom_status', 'custom_status_details', 'is_overdue', 'task_statistics',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'review_notes', 'rejection_reason',
            'resolved_by', 'resolved_by_name', 'resolved_at', 'resolution_notes',
            'created_at', 'updated_at',
            # Automated status tracking fields
            'automated_status', 'automated_status_message', 'display_status_combined', 
            'last_responder', 'last_response_time', 'delay_status',
            'attachments', 'assignments', 'employee_assignments', 'tasks', 'comments', 'status_history'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_overdue', 'task_statistics', 
                           'automated_status', 'last_responder', 'last_response_time', 'delay_status']


class ClientComplaintStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating complaint status"""
    status_type = serializers.ChoiceField(choices=['default', 'custom'], required=True)
    status_value = serializers.CharField(required=True, help_text="Status name for default, or custom status ID")
    notes = serializers.CharField(required=False, allow_blank=True, help_text="Optional notes for the status change")
    
    def validate(self, attrs):
        status_type = attrs.get('status_type')
        status_value = attrs.get('status_value')
        
        if status_type == 'default':
            # Validate against default status choices
            valid_statuses = [choice[0] for choice in ClientComplaint.STATUS_CHOICES]
            if status_value not in valid_statuses:
                raise serializers.ValidationError(f"Invalid default status: {status_value}")
        
        elif status_type == 'custom':
            # Validate custom status exists and is active
            try:
                custom_status = ClientComplaintStatus.objects.get(id=status_value, is_active=True)
                if not custom_status.can_be_set_by_admin:
                    raise serializers.ValidationError("This custom status cannot be set by admin")
            except ClientComplaintStatus.DoesNotExist:
                raise serializers.ValidationError("Invalid custom status ID")
            except ValueError:
                raise serializers.ValidationError("Custom status ID must be a valid integer")
        
        return attrs


class ClientComplaintSubmissionSerializer(serializers.ModelSerializer):
    """Simplified serializer for public complaint submission"""
    class Meta:
        model = ClientComplaint
        fields = [
            'client_name', 'client_email', 'client_phone', 'project_name', 'project_code',
            'category', 'priority', 'title', 'description'
        ]
        
    def validate_category(self, value):
        """Ensure the category is active and available for public submissions"""
        if not value.is_active:
            raise serializers.ValidationError("هذه الفئة غير متاحة حالياً")
        return value
    
    def validate_client_phone(self, value):
        """Validate phone number format"""
        import re
        # Remove spaces and check if it matches phone number pattern
        cleaned_phone = re.sub(r'\s+', '', value)
        if not re.match(r'^[\+]?[1-9][\d]{0,15}$', cleaned_phone):
            raise serializers.ValidationError("رقم الهاتف غير صحيح. يجب أن يكون رقماً صالحاً")
        return value
    
    def create(self, validated_data):
        """
        Create complaint and automatically create/link GlobalClient account
        GlobalClient is stored in main database and works across all tenants
        """
        import secrets
        import string
        from django.core.mail import send_mail
        from django.conf import settings
        from .models import GlobalClient
        
        client_email = validated_data['client_email']
        client_name = validated_data['client_name']
        client_phone = validated_data.get('client_phone', '')
        
        # Check if GlobalClient with this email already exists in main database
        global_client = GlobalClient.objects.using('default').filter(email=client_email).first()
        
        # If GlobalClient doesn't exist, create a new one in main database
        if not global_client:
            # Generate a secure random password
            password_length = 12
            password_chars = string.ascii_letters + string.digits + "!@#$%^&*"
            generated_password = ''.join(secrets.choice(password_chars) for _ in range(password_length))
            
            # Create the GlobalClient account in main database
            global_client = GlobalClient(
                email=client_email,
                name=client_name,
                phone=client_phone,
                is_active=True
            )
            global_client.set_password(generated_password)
            global_client.save(using='default')
            global_client.set_password(generated_password)
            global_client.save(using='default')
            
            # Send welcome email with login credentials
            try:
                subject = "Welcome to Our System - Your Global Account Details"
                
                # Build dashboard URL (update with your actual frontend URL)
                dashboard_url = getattr(settings, 'CLIENT_DASHBOARD_URL', 'http://localhost:3000/client/dashboard')
                login_url = getattr(settings, 'CLIENT_LOGIN_URL', 'http://localhost:3000/client/login')
                
                message = f"""
Hello {client_name},

Thank you for submitting your complaint. We have automatically created a GLOBAL account for you.

Your Login Credentials (works on ALL our systems):
Email: {client_email}
Password: {generated_password}

🌐 This account works across all our tenants - you can use it anywhere!

You can log in at: {login_url}

After logging in, you will be able to:
- View all your complaints in one place
- Track the status and progress of each complaint
- Submit complaints to any tenant
- Access your account from any subdomain

Dashboard URL: {dashboard_url}

IMPORTANT: Please save these credentials securely. You can change your password after your first login.

If you have any questions or need assistance, please don't hesitate to contact us.

Best regards,
The Support Team
                """
                
                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2563eb;">Welcome to Our System 🌐</h2>
                        
                        <p>Hello {client_name},</p>
                        
                        <p>Thank you for submitting your complaint. We have automatically created a <strong>Global Account</strong> for you.</p>
                        
                        <div style="background: #f0fdf4; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10b981;">
                            <h3 style="margin-top: 0;">✅ Global Account Created</h3>
                            <p style="font-size: 14px; color: #059669;">This account works across ALL our tenants - one login for everything!</p>
                        </div>
                        
                        <div style="background: #f8fafc; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #2563eb;">
                            <h3 style="margin-top: 0;">Your Login Credentials</h3>
                            <p style="margin: 10px 0;"><strong>Email:</strong> {client_email}</p>
                            <p style="margin: 10px 0;"><strong>Password:</strong> <code style="background: #e2e8f0; padding: 5px 10px; border-radius: 3px;">{generated_password}</code></p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{login_url}" 
                               style="background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                                Log In to Your Dashboard
                            </a>
                        </div>
                        
                        <h3>What You Can Do:</h3>
                        <ul>
                            <li>✅ View all your complaints in one place</li>
                            <li>✅ Track the status and progress of each complaint</li>
                            <li>✅ Submit complaints to any tenant</li>
                            <li>✅ Access your account from any subdomain</li>
                            <li>✅ One account for all our services</li>
                        </ul>
                        
                        <div style="background: #fef3c7; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>⚠️ Important:</strong> Please save these credentials securely. You can change your password after your first login.
                        </div>
                        
                        <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
                        
                        <p>Best regards,<br>The Support Team</p>
                    </div>
                </body>
                </html>
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    html_message=html_message,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com'),
                    recipient_list=[client_email],
                    fail_silently=False
                )
                
                print(f"✓ Welcome email sent to {client_email} with GLOBAL account credentials")
                
            except Exception as e:
                print(f"✗ Failed to send welcome email to {client_email}: {str(e)}")
                # Don't fail the complaint creation if email fails
        
        # Create the complaint (note: we removed client_user field linking for now)
        # You may want to add a global_client field to ClientComplaint model later
        complaint = ClientComplaint.objects.create(**validated_data)
        
        return complaint


# Client Portal Serializers

class ClientPortalComplaintSerializer(serializers.ModelSerializer):
    """Serializer for client portal - shows complaint info without sensitive internal data"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    task_statistics = serializers.ReadOnlyField()
    
    # Only show public-facing comments/replies
    client_replies = serializers.SerializerMethodField()
    public_attachments = serializers.SerializerMethodField()
    
    class Meta:
        model = ClientComplaint
        fields = [
            'id', 'client_name', 'client_email', 'project_name', 'project_code',
            'category_name', 'category_color', 'priority', 'priority_display',
            'title', 'description', 'status', 'status_display', 'task_statistics',
            'created_at', 'updated_at', 'client_replies', 'public_attachments',
            'resolution_notes', 'resolved_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'task_statistics']
    
    def get_client_replies(self, obj):
        """Get client replies and admin responses - INCLUDING admin comments visible to client"""
        combined_communications = []
        
        # 1. Get all client replies (with admin responses)
        client_replies = obj.client_replies.all().order_by('created_at')
        for reply in client_replies:
            reply_data = ClientComplaintReplySerializer(reply).data
            combined_communications.append({
                **reply_data,
                'type': 'client_reply',
                'author_type': 'client'
            })
        
        # 2. Get admin comments that are NOT internal (visible to client)
        admin_comments = obj.comments.filter(is_internal=False).order_by('created_at')
        for comment in admin_comments:
            # Safely get author attributes with fallback logic
            if comment.author:
                author_name = comment.author.name.strip() if comment.author.name else ''
                if not author_name:
                    author_name = comment.author.username or 'Admin'
            else:
                author_name = 'Admin'
                
            author_email = ''
            if comment.author and hasattr(comment.author, 'email'):
                author_email = comment.author.email
            elif comment.author and hasattr(comment.author, 'username'):
                author_email = comment.author.username
            
            combined_communications.append({
                'id': str(comment.id),  # Ensure string format for consistency
                'reply_text': comment.comment,  # Map to reply_text for consistency
                'client_name': author_name,  # Admin name as "client_name" for display
                'client_email': author_email,
                'created_at': comment.created_at,
                'admin_response': None,  # Admin comments don't have responses
                'admin_responded_at': None,
                'type': 'admin_comment',
                'author_type': 'admin'
            })
        
        # Sort all communications by creation date (handle both datetime objects and strings)
        # Recent messages first (descending order)
        def get_sort_key(comm):
            created_at = comm['created_at']
            if isinstance(created_at, str):
                # Parse string dates to datetime for proper sorting
                from dateutil import parser
                try:
                    return parser.parse(created_at)
                except (ValueError, TypeError):
                    return created_at
            else:
                # Return datetime object as is
                return created_at
        
        combined_communications.sort(key=get_sort_key, reverse=True)
        
        return combined_communications
    
    def get_public_attachments(self, obj):
        """Get attachments uploaded by client (not internal ones)"""
        attachments = obj.attachments.filter(uploaded_by='client')
        return ClientComplaintAttachmentSerializer(attachments, many=True).data


class ClientComplaintReplySerializer(serializers.ModelSerializer):
    """Serializer for client replies"""
    
    class Meta:
        model = ClientComplaintReply
        fields = [
            'id', 'reply_text', 'client_name', 'client_email', 'created_at',
            'admin_response', 'admin_responded_at'
        ]
        read_only_fields = ['id', 'created_at', 'admin_response', 'admin_responded_at']


class ClientComplaintReplyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating client replies"""
    
    class Meta:
        model = ClientComplaintReply
        fields = ['reply_text', 'client_name', 'client_email']
    
    def validate_client_email(self, value):
        """Ensure email matches the complaint's client email"""
        complaint = self.context.get('complaint')
        if complaint and value.lower() != complaint.client_email.lower():
            raise serializers.ValidationError("Email must match the original complaint email")
        return value.lower()

        def create(self, validated_data):
            # Always set client_name and client_email from complaint if not provided
            complaint = self.context.get('complaint')
            if complaint:
                if not validated_data.get('client_name'):
                    validated_data['client_name'] = complaint.client_name
                if not validated_data.get('client_email'):
                    validated_data['client_email'] = complaint.client_email
            return super().create(validated_data)


class ClientComplaintAccessTokenSerializer(serializers.ModelSerializer):
    """Serializer for access tokens"""
    complaint_title = serializers.CharField(source='complaint.title', read_only=True)
    client_name = serializers.CharField(source='complaint.client_name', read_only=True)
    
    class Meta:
        model = ClientComplaintAccessToken
        fields = [
            'id', 'token', 'complaint_title', 'client_name', 'created_at',
            'expires_at', 'last_accessed', 'access_count', 'is_active', 'is_permanent', 'is_expired', 'is_valid'
        ]
        read_only_fields = ['id', 'token', 'created_at', 'last_accessed', 'access_count', 'is_expired', 'is_valid']


class TicketDelayThresholdSerializer(serializers.ModelSerializer):
    """Serializer for ticket delay thresholds"""
    
    class Meta:
        model = TicketDelayThreshold
        fields = [
            'id', 'threshold_type', 'priority', 
            'system_response_hours', 'client_response_hours', 'auto_close_hours',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        # Ensure priority is set for priority-based thresholds
        if data.get('threshold_type') == 'priority' and not data.get('priority'):
            raise serializers.ValidationError({
                'priority': 'Priority must be specified for priority-based thresholds'
            })
        
        # Ensure priority is not set for global thresholds
        if data.get('threshold_type') == 'global' and data.get('priority'):
            raise serializers.ValidationError({
                'priority': 'Priority should not be specified for global thresholds'
            })
        
        return data


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for in-app notifications"""
    complaint_title = serializers.CharField(source='complaint.title', read_only=True)
    complaint_id = serializers.UUIDField(source='complaint.id', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = None  # Will be set dynamically
        fields = [
            'id', 'recipient', 'complaint', 'complaint_id', 'complaint_title',
            'notification_type', 'title', 'message', 'is_read', 
            'created_at', 'read_at', 'time_ago'
        ]
        read_only_fields = [
            'id', 'recipient', 'complaint', 'notification_type', 
            'title', 'message', 'created_at', 'read_at', 'time_ago'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lazy load the model to avoid circular imports
        from hr_management.models import Notification
        self.Meta.model = Notification
    
    def get_time_ago(self, obj):
        """Calculate human-readable time difference"""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 0:
            return f"منذ {diff.days} يوم" if diff.days == 1 else f"منذ {diff.days} أيام"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"منذ {hours} ساعة" if hours == 1 else f"منذ {hours} ساعات"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"منذ {minutes} دقيقة" if minutes == 1 else f"منذ {minutes} دقائق"
        else:
            return "الآن"


# ========== Shift Scheduling System Serializers ==========

class WeeklyShiftScheduleSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    hours = serializers.SerializerMethodField()
    
    class Meta:
        model = WeeklyShiftSchedule
        fields = [
            'id', 'employee', 'employee_name', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'is_active', 'hours', 'notes',
            'created_at', 'updated_at'
        ]
    
    def get_hours(self, obj):
        return obj.calculate_hours()
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({
                    'end_time': 'وقت النهاية يجب أن يكون بعد وقت البداية'
                })
        return data


class BulkWeeklyScheduleSerializer(serializers.Serializer):
    """
    Create a full week schedule for an employee at once
    """
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    schedules = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of {day_of_week, start_time, end_time, notes}"
    )
    
    def create(self, validated_data):
        employee = validated_data['employee']
        schedules_data = validated_data['schedules']
        
        created_schedules = []
        for schedule_data in schedules_data:
            schedule, created = WeeklyShiftSchedule.objects.update_or_create(
                employee=employee,
                day_of_week=schedule_data['day_of_week'],
                defaults={
                    'start_time': schedule_data['start_time'],
                    'end_time': schedule_data['end_time'],
                    'notes': schedule_data.get('notes', ''),
                    'is_active': schedule_data.get('is_active', True)
                }
            )
            created_schedules.append(schedule)
        
        return created_schedules


class ShiftOverrideSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)
    override_type_display = serializers.CharField(source='get_override_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ShiftOverride
        fields = [
            'id', 'employee', 'employee_name', 'date', 'override_type', 'override_type_display',
            'start_time', 'end_time', 'reason', 'status', 'status_display',
            'requested_by', 'requested_by_name', 'approved_by', 'approved_by_name',
            'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['approved_by', 'approved_at', 'requested_by']
    
    def validate(self, data):
        override_type = data.get('override_type')
        
        if override_type == 'custom':
            if not data.get('start_time') or not data.get('end_time'):
                raise serializers.ValidationError({
                    'start_time': 'الدوامات المخصصة تتطلب أوقات البداية والنهاية'
                })
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError({
                    'end_time': 'وقت النهاية يجب أن يكون بعد وقت البداية'
                })
        elif override_type in ['day_off', 'vacation', 'sick_leave', 'holiday']:
            # Clear times for non-custom overrides
            data['start_time'] = None
            data['end_time'] = None
        
        return data


class ShiftAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    employee_department = serializers.CharField(source='employee.department', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = ShiftAttendance
        fields = [
            'id', 'employee', 'employee_name', 'employee_department', 'date',
            'expected_start', 'expected_end', 'actual_start', 'actual_end',
            'status', 'status_display', 'late_minutes', 'early_departure_minutes',
            'overtime_minutes', 'total_hours', 'auto_marked_absent',
            'requires_manager_approval', 'approved_by', 'approved_by_name',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'status', 'late_minutes', 'early_departure_minutes', 'overtime_minutes',
            'total_hours', 'auto_marked_absent', 'approved_by'
        ]


class ClockInSerializer(serializers.Serializer):
    """
    Clock in for the current shift
    """
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    clock_in_time = serializers.TimeField(required=False, help_text="Leave empty for current time")
    notes = serializers.CharField(required=False, allow_blank=True)


class ClockOutSerializer(serializers.Serializer):
    """
    Clock out from the current shift
    """
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    clock_out_time = serializers.TimeField(required=False, help_text="Leave empty for current time")
    notes = serializers.CharField(required=False, allow_blank=True)


class EmployeeShiftSummarySerializer(serializers.Serializer):
    """
    Summary of employee's shifts and attendance
    """
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    department = serializers.CharField()
    weekly_hours = serializers.DecimalField(max_digits=5, decimal_places=2)
    days_present = serializers.IntegerField()
    days_late = serializers.IntegerField()
    days_absent = serializers.IntegerField()
    total_hours_worked = serializers.DecimalField(max_digits=6, decimal_places=2)
    attendance_rate = serializers.DecimalField(max_digits=5, decimal_places=2)


class CurrentShiftStatusSerializer(serializers.Serializer):
    """
    Current shift status for an employee
    """
    employee_id = serializers.UUIDField()
    employee_name = serializers.CharField()
    is_on_shift = serializers.BooleanField()
    shift_start = serializers.TimeField(required=False, allow_null=True)
    shift_end = serializers.TimeField(required=False, allow_null=True)
    has_clocked_in = serializers.BooleanField()
    clock_in_time = serializers.TimeField(required=False, allow_null=True)
    status = serializers.CharField()
    late_minutes = serializers.IntegerField()


class LateAbsentReportSerializer(serializers.Serializer):
    """
    Report of late and absent employees for a specific date
    """
    date = serializers.DateField()
    total_scheduled = serializers.IntegerField()
    present = serializers.IntegerField()
    late = serializers.IntegerField()
    absent = serializers.IntegerField()
    employees = ShiftAttendanceSerializer(many=True)
