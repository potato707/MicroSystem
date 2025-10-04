from rest_framework import serializers
import datetime
import calendar
from .models import Employee, EmployeeDocument, EmployeeNote, EmployeeAttendance, User, LeaveRequest, Complaint, ComplaintReply, ComplaintAttachment, EmployeeDocument, Wallet, WalletTransaction, ReimbursementRequest, ReimbursementAttachment, Task, TaskReport, TaskComment
from utils.timezone_utils import system_now


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

    class Meta:
        model = EmployeeAttendance
        fields = ["id", "employee", "employee_name", "date", "check_in", "check_out", "status", "paid"]
        read_only_fields = ["employee"]

class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = ["id", "employee", "employee_name", "start_date", "end_date", "reason", "status", "created_at", "updated_at"]
        read_only_fields = ["status", "created_at", "updated_at", "employee"]

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

    class Meta:
        model = ReimbursementRequest
        fields = [
            "id", "employee", "employee_name", "amount", "description",
            "status", "admin_comment", "created_at", "updated_at",
            "attachments", "attachment_links"
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
        fields = ['id', 'comment', 'author', 'author_name', 'created_at', 'is_manager_note']
        read_only_fields = ['author', 'created_at']


class TaskCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tasks with role-based employee field handling"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority', 'date', 
            'start_date', 'end_date', 'estimated_minutes', 'notes'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        
        # Include employee field for admins, but make it optional if they have an employee profile
        if request and request.user.role == 'admin':
            # Check if admin has an employee profile
            has_employee_profile = hasattr(request.user, 'employee')
            self.fields['employee'] = serializers.PrimaryKeyRelatedField(
                queryset=Employee.objects.all(), 
                required=not has_employee_profile,  # Optional if admin has employee profile
                allow_null=True
            )
    
    def validate(self, data):
        """Custom validation that handles employee field based on user role"""
        request = self.context.get('request')
        if request and request.user.role == 'admin':
            # If admin doesn't have employee profile, employee field is required
            if not hasattr(request.user, 'employee'):
                if 'employee' not in data or data['employee'] is None:
                    raise serializers.ValidationError({
                        'employee': 'Employee field is required for admin task creation'
                    })
        # For employees and admins with employee profiles, employee field will be set by perform_create
        return data


class TaskSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    comments = TaskCommentSerializer(many=True, read_only=True)
    is_overdue = serializers.ReadOnlyField()
    is_paused = serializers.ReadOnlyField()
    time_spent = serializers.ReadOnlyField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'employee', 'employee_name', 'title', 'description', 'status', 
            'priority', 'date', 'start_date', 'end_date', 'created_by', 'created_by_name', 'assigned_by_manager',
            'estimated_minutes', 'actual_minutes', 'started_at', 'completed_at',
            'paused_at', 'total_pause_time', 'is_paused',
            'created_at', 'updated_at', 'notes', 'comments', 'is_overdue', 'time_spent'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'time_spent', 'is_overdue', 'is_paused', 'paused_at', 'total_pause_time']


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

