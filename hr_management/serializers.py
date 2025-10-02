from rest_framework import serializers
import datetime
import calendar
from .models import Employee, EmployeeDocument, EmployeeNote, EmployeeAttendance, User, LeaveRequest, Complaint, ComplaintReply, ComplaintAttachment, EmployeeDocument, Wallet, WalletTransaction, ReimbursementRequest, ReimbursementAttachment
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

    class Meta:
        model = ReimbursementRequest
        fields = [
            "id", "employee", "amount", "description",
            "status", "admin_comment", "created_at", "updated_at",
            "attachments", "attachment_links"
        ]
        read_only_fields = ["status", "admin_comment", "created_at", "updated_at", "employee"]

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

