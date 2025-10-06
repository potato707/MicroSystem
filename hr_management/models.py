from django.db import models
import datetime
from django.conf import settings
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from utils.timezone_utils import system_now
import os

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_picture = models.URLField(max_length=500, blank=True, null=True, verbose_name="الصورة الشخصية")

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('manager', 'Manager'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    name = models.CharField(max_length=200, verbose_name="الاسم")

    REQUIRED_FIELDS = ['email', 'role', 'name']

class Employee(models.Model):
    EMPLOYMENT_STATUS = [
        ('active', 'نشط'),
        ('vacation', 'في إجازة'),
        ('resigned', 'استقالة'),
        ('terminated', 'مفصول'),
        ('probation', 'فترة تجريبية'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    profile_picture = models.URLField(max_length=500, blank=True, null=True, verbose_name="الصورة الشخصية")
    name = models.CharField(max_length=200, verbose_name='الاسم')
    position = models.CharField(max_length=100, verbose_name='الوظيفة')
    department = models.CharField(max_length=100, verbose_name='القسم')
    hire_date = models.DateField(verbose_name='تاريخ التعيين')
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='الراتب الأساسي')
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='المعدل المتوسط للوقت الإضافي', default=0.0)
    status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS, default='active', verbose_name='الحالة الوظيفية')
    phone = models.CharField(max_length=15, verbose_name='رقم الهاتف')
    email = models.EmailField(verbose_name='البريد الإلكتروني')
    address = models.TextField(verbose_name='العنوان')
    emergency_contact = models.CharField(max_length=200, verbose_name='جهة الاتصال في حالات الطوارئ')
    shift_start_time = models.TimeField(verbose_name='وقت التبديل', default=datetime.time(9, 0))
    shift_end_time = models.TimeField(verbose_name='وقت الانتهاء التبديل', default=datetime.time(17, 0))

    class Meta:
        verbose_name = 'موظف'
        verbose_name_plural = 'الموظفين'
    
    def __str__(self):
        return f"{self.name} - {self.position}"

class EmployeeDocument(models.Model):
    DOCUMENT_TYPES = [
        ('certificate', 'شهادة'),
        ('contract', 'عقد'),
        ('cv', 'السيرة الذاتية'),
        ('id', 'بطاقة هوية'),
        ('other', 'أخرى'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='الموظف', related_name="attachments")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name='نوع المستند')
    title = models.CharField(max_length=200, verbose_name='عنوان المستند')
    file_url = models.URLField(verbose_name='رابط الملف')
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الرفع')
    description = models.TextField(blank=True, verbose_name='وصف')
    
    class Meta:
        verbose_name = 'مستند الموظف'
        verbose_name_plural = 'مستندات الموظفين'
    
    def __str__(self):
        return f"{self.employee.name} - {self.title}"

class EmployeeNote(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='الموظف')
    note = models.TextField(verbose_name='الملاحظة')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='كتب بواسطة')
    created_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    
    class Meta:
        verbose_name = 'ملاحظة الموظف'
        verbose_name_plural = 'ملاحظات الموظفين'
    
    def __str__(self):
        return f"ملاحظة لـ {self.employee.name}"

class EmployeeAttendance(models.Model):
    ATTENDANCE_STATUS = [
        ('present', 'حاضر'),
        ('absent', 'غائب'),
        ('late', 'متأخر'),
        ('on_leave', 'إجازة'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="الموظف")
    date = models.DateField(default=system_now(), verbose_name="التاريخ")
    check_in = models.TimeField(null=True, blank=True, verbose_name="وقت الحضور")
    check_out = models.TimeField(null=True, blank=True, verbose_name="وقت الانصراف")
    status = models.CharField(max_length=20, choices=ATTENDANCE_STATUS, default="present", verbose_name="الحالة")
    paid = models.BooleanField(default=True, verbose_name="المدفوعة")

    class Meta:
        verbose_name = "الحضور والانصراف"
        verbose_name_plural = "الحضور والانصراف"
        unique_together = ("employee", "date") # Each employee has only one attendance record for each day

    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.status})"


class WorkShift(models.Model):
    """Individual work shifts within a day - supports multiple shifts per day"""
    SHIFT_TYPE_CHOICES = [
        ('regular', 'Regular Shift'),
        ('overtime', 'Overtime Shift'),
        ('emergency', 'Emergency Shift'),
        ('meeting', 'Meeting/Training'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='work_shifts', verbose_name="الموظف")
    attendance = models.ForeignKey(EmployeeAttendance, on_delete=models.CASCADE, related_name='shifts', verbose_name="سجل الحضور")
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPE_CHOICES, default='regular', verbose_name="نوع الوردية")
    check_in = models.DateTimeField(verbose_name="وقت بداية الوردية")
    check_out = models.DateTimeField(null=True, blank=True, verbose_name="وقت نهاية الوردية")
    break_start = models.DateTimeField(null=True, blank=True, verbose_name="بداية الاستراحة")
    break_end = models.DateTimeField(null=True, blank=True, verbose_name="نهاية الاستراحة")
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name="موقع العمل")
    # GPS coordinates for location tracking
    checkin_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="خط عرض الدخول")
    checkin_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, verbose_name="خط طول الدخول")
    checkout_latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True, verbose_name="خط عرض الخروج")
    checkout_longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True, verbose_name="خط طول الخروج")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    is_active = models.BooleanField(default=True, verbose_name="الوردية نشطة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "وردية عمل"
        verbose_name_plural = "ورديات العمل"
        ordering = ['check_in']
    
    def __str__(self):
        status = "Active" if self.is_active and not self.check_out else "Completed"
        return f"{self.employee.name} - {self.shift_type} ({self.check_in.date()}) - {status}"
    
    @property
    def duration_minutes(self):
        """Calculate shift duration in minutes (excluding breaks)"""
        if not self.check_out:
            return 0
        
        total_duration = (self.check_out - self.check_in).total_seconds() / 60
        
        # Subtract break time if applicable
        if self.break_start and self.break_end:
            break_duration = (self.break_end - self.break_start).total_seconds() / 60
            total_duration -= break_duration
            
        return max(0, total_duration)
    
    # Add new fields for salary calculation support
    date = models.DateField(verbose_name="التاريخ", null=True, blank=True)
    check_in_time = models.TimeField(null=True, blank=True, verbose_name="وقت الدخول")
    check_out_time = models.TimeField(null=True, blank=True, verbose_name="وقت الخروج")
    total_break_time = models.IntegerField(default=0, verbose_name="إجمالي وقت الاستراحة (دقائق)")
    status = models.CharField(max_length=20, choices=[
        ('present', 'حاضر'),
        ('late', 'متأخر'),
        ('absent', 'غائب'),
        ('on_leave', 'في إجازة'),
    ], default='present', verbose_name="الحالة")
    is_paid_leave = models.BooleanField(default=True, verbose_name="إجازة مدفوعة")
    
    @property
    def is_on_break(self):
        """Check if currently on break"""
        if not self.break_start or self.break_end:
            return False  
        return self.break_start <= system_now() and not self.break_end


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافقة'),
        ('rejected', 'رفض'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, verbose_name="الموظف")
    start_date = models.DateField(verbose_name="تاريخ البداية")
    end_date = models.DateField(verbose_name="تاريخ النهاية")
    reason = models.TextField(verbose_name="سبب الإجازة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    is_paid = models.BooleanField(null=True, blank=True, verbose_name="إجازة مدفوعة الأجر")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="تعليق الأدمن")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="تمت المراجعة بواسطة")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المراجعة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "طلب إجازة"
        verbose_name_plural = "طلبات الإجازة"

    def __str__(self):
        return f"{self.employee.name} - {self.start_date} إلى {self.end_date}"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ("open", "مفتوحة"),
        ("in_review", "تحت المراجعة"),
        ("answered", "تم الرد"),
        ("closed", "مغلقة"),
    ]
    URGENCY_CHOICES = [
        ("low", "منخفض"),
        ("medium", "متوسط"),
        ("high", "عال"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, verbose_name="الموظف")
    title = models.CharField(max_length=200, verbose_name="عنوان الشكوى")
    description = models.TextField(verbose_name="تفاصيل الشكوى")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open", verbose_name="الحالة")
    attachment_url = models.URLField(max_length=500, blank=True, null=True, verbose_name="رابط مرفق")
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES, default="low", verbose_name="الاهمية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "شكوى"
        verbose_name_plural = "الشكاوى"

    def __str__(self):
        return f"{self.title} - {self.employee.name}"

class ComplaintReply(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="replies", verbose_name="الشكوى")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="المستخدم")
    message = models.TextField(verbose_name="الرد")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرد")

    class Meta:
        verbose_name = "رد على الشكوى"
        verbose_name_plural = "ردود الشكاوى"

    def __str__(self):
        return f"Reply by {self.user.username} on {self.complaint.title}"


class ComplaintAttachment(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True)
    reply = models.ForeignKey(ComplaintReply, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True)
    file_url = models.URLField(verbose_name="رابط الملف")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مرفق شكوى/رد"
        verbose_name_plural = "مرفقات الشكاوى/الردود"

    def __str__(self):
        target = self.complaint or self.reply
        return f"Attachment for {target}"

# Multi-Wallet System Models
class EmployeeWalletSystem(models.Model):
    """Container for all employee wallets"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, verbose_name="الموظف", related_name="wallet_system")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet System for {self.employee.name}"

class MainWallet(models.Model):
    """Employee's main wallet - total available balance (money they currently own)"""
    wallet_system = models.OneToOneField(EmployeeWalletSystem, on_delete=models.CASCADE, related_name="main_wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الرصيد الأساسي", default=0.0)

    def __str__(self):
        return f"Main Wallet: {self.wallet_system.employee.name} - ${self.balance}"

class ReimbursementWallet(models.Model):
    """Tracks pending/approved reimbursement amounts (money owed to employee by company)"""
    wallet_system = models.OneToOneField(EmployeeWalletSystem, on_delete=models.CASCADE, related_name="reimbursement_wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="رصيد المبالغ المستردة", default=0.0)

    def __str__(self):
        return f"Reimbursement Wallet: {self.wallet_system.employee.name} - ${self.balance}"

class AdvanceWallet(models.Model):
    """Tracks amounts employee owes to company (loans/salary advances)"""
    wallet_system = models.OneToOneField(EmployeeWalletSystem, on_delete=models.CASCADE, related_name="advance_wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="رصيد السلف", default=0.0)

    def __str__(self):
        return f"Advance Wallet: {self.wallet_system.employee.name} - ${self.balance}"

class MultiWalletTransaction(models.Model):
    """New wallet transactions with specific wallet targeting"""
    WALLET_TYPES = [
        ('main', 'Main Wallet'),
        ('reimbursement', 'Reimbursement Wallet'), 
        ('advance', 'Advance Wallet'),
    ]
    
    TRANSACTION_TYPES = [
        # Main Wallet transactions
        ('salary_credit', 'Salary Credit'),
        ('bonus_credit', 'Bonus Credit'),
        ('advance_withdrawal', 'Advance Withdrawal'),
        ('manual_withdrawal', 'Manual Withdrawal'),
        ('manual_deposit', 'Manual Deposit'),
        ('advance_deduction', 'Advance Deduction'),
        ('reimbursement_payment', 'Reimbursement Payment'),
        
        # Reimbursement Wallet transactions
        ('reimbursement_approved', 'Reimbursement Approved'),
        ('reimbursement_paid', 'Reimbursement Paid'),
        
        # Advance Wallet transactions
        ('advance_taken', 'Advance Taken'),
        ('advance_repaid', 'Advance Repaid'),
    ]

    wallet_system = models.ForeignKey(EmployeeWalletSystem, on_delete=models.CASCADE, related_name="multi_transactions")
    wallet_type = models.CharField(max_length=20, choices=WALLET_TYPES, verbose_name="نوع المحفظة")
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES, verbose_name="نوع المعاملة")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    description = models.TextField(verbose_name="الوصف")
    
    # Optional references for tracking related entities
    reimbursement_request = models.ForeignKey('ReimbursementRequest', on_delete=models.SET_NULL, null=True, blank=True)
    related_transaction = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المعاملة المرتبطة")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="أنشأ بواسطة")

    def __str__(self):
        return f"{self.transaction_type} ${self.amount} - {self.wallet_system.employee.name} ({self.wallet_type})"

    class Meta:
        ordering = ["-created_at"]

# Legacy models for backward compatibility - will be deprecated
class Wallet(models.Model):
    """DEPRECATED: Legacy single wallet model - kept for migration purposes"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, verbose_name="الموظف", null=True, blank=True, related_name="legacy_wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ", default=0.0)

    def __str__(self):
        return f"Legacy Wallet of {self.employee.name} - Balance: {self.balance}"

    class Meta:
        verbose_name = "Legacy Wallet (Deprecated)"

# Keep the old WalletTransaction for legacy data
class WalletTransaction(models.Model):
    """DEPRECATED: Legacy wallet transaction model"""
    TRANSACTION_TYPES = [
        ('deposit', 'إيداع'),
        ('withdrawal', 'سحب'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, verbose_name="المحصول")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, verbose_name="نوع المعاملة")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    description = models.TextField(verbose_name="الوصف")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    def __str__(self):
        return f"{self.transaction_type} {self.amount} for {self.wallet.employee.name if self.wallet.employee else 'N/A'}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Legacy Wallet Transaction (Deprecated)"

class WalletTransfer(models.Model):
    """Records transfers between different wallet types for the same employee"""
    TRANSFER_TYPES = [
        ('reimbursement_to_main', 'Reimbursement Payment'),
        ('main_to_advance', 'Advance Deduction'),
    ]
    
    wallet_system = models.ForeignKey(EmployeeWalletSystem, on_delete=models.CASCADE, related_name="transfers")
    transfer_type = models.CharField(max_length=30, choices=TRANSFER_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    
    from_wallet_type = models.CharField(max_length=20, choices=MultiWalletTransaction.WALLET_TYPES)
    to_wallet_type = models.CharField(max_length=20, choices=MultiWalletTransaction.WALLET_TYPES)
    
    # Link to the paired transactions this transfer creates
    from_transaction = models.OneToOneField(MultiWalletTransaction, on_delete=models.CASCADE, related_name="transfer_from")
    to_transaction = models.OneToOneField(MultiWalletTransaction, on_delete=models.CASCADE, related_name="transfer_to")
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Transfer: ${self.amount} from {self.from_wallet_type} to {self.to_wallet_type} - {self.wallet_system.employee.name}"

    class Meta:
        ordering = ["-created_at"]

class ReimbursementRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "تحت المراجعة"),
        ("approved", "موافقة"), 
        ("paid", "تم الدفع"),
        ("rejected", "رفض"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="reimbursements")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    description = models.TextField(verbose_name="الوصف")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="رد الأدمن")
    
    # New fields for multi-wallet integration
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الدفع")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_reimbursements")
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="paid_reimbursements")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ReimbursementAttachment(models.Model):
    reimbursement = models.ForeignKey(ReimbursementRequest, on_delete=models.CASCADE, related_name="attachments")
    file_url = models.URLField(verbose_name="رابط الملف")
    uploaded_at = models.DateTimeField(auto_now_add=True)


class Task(models.Model):
    """Daily TO-DO tasks for employees"""
    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('doing', 'Doing'),
        ('done', 'Done'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200, verbose_name='Task Title')
    description = models.TextField(blank=True, null=True, verbose_name='Task Description')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='to_do')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    date = models.DateField(default=datetime.date.today, verbose_name='Task Date')
    start_date = models.DateField(null=True, blank=True, verbose_name='Start Date')
    end_date = models.DateField(null=True, blank=True, verbose_name='Deadline')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    assigned_by_manager = models.BooleanField(default=False, verbose_name='Assigned by Manager')
    team = models.ForeignKey('Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks', verbose_name='Assigned Team')
    estimated_minutes = models.IntegerField(default=30, verbose_name='Estimated Time (minutes)')
    actual_minutes = models.IntegerField(null=True, blank=True, verbose_name='Actual Time (minutes)')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True, verbose_name='Paused At')
    total_pause_time = models.IntegerField(default=0, verbose_name='Total Pause Time (minutes)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True, verbose_name='Task Notes')
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-priority', 'created_at']
        # unique_together = ['employee', 'title', 'date']  # Prevent duplicate tasks on same day
    
    def __str__(self):
        return f"{self.employee.name} - {self.title} ({self.date})"
    
    @property
    def is_overdue(self):
        """Check if task is overdue (not completed by end of day)"""
        from datetime import time
        if self.status == 'done' or self.date > system_now().date():
            return False
        
        # Only consider tasks overdue if they're from previous days
        # or if they were created before 6 PM on the task date and it's now past 6 PM
        current_time = system_now()
        task_date = self.date
        
        # If task is from a previous day and not completed, it's overdue
        if task_date < current_time.date():
            return True
            
        # If task is from today, only overdue if created before 6 PM and it's now past 6 PM
        if task_date == current_time.date():
            # Create timezone-aware end_of_day datetime
            naive_end_of_day = datetime.datetime.combine(task_date, time(18, 0))
            end_of_day = timezone.make_aware(naive_end_of_day) if timezone.is_naive(naive_end_of_day) else naive_end_of_day
            # Only overdue if task was created before 6 PM and it's now past 6 PM
            return self.created_at < end_of_day and current_time > end_of_day
            
        return False
    
    @property
    def time_spent(self):
        """Calculate time spent on task (excluding pause time)"""
        if not self.started_at:
            return 0
        
        end_time = self.completed_at or system_now()
        total_time = (end_time - self.started_at).total_seconds() / 60
        
        # Subtract total pause time
        active_time = total_time - self.total_pause_time
        
        # If currently paused, subtract current pause duration
        if self.paused_at:
            current_pause = (system_now() - self.paused_at).total_seconds() / 60
            active_time -= current_pause
            
        return max(0, active_time)  # Ensure non-negative
    
    @property
    def is_paused(self):
        """Check if task is currently paused"""
        return self.paused_at is not None and self.status == 'doing'


class Subtask(models.Model):
    """Subtasks within main tasks - each can have its own timer and status"""
    STATUS_CHOICES = [
        ('to_do', 'To Do'),
        ('doing', 'Doing'),
        ('done', 'Done'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=200, verbose_name='Subtask Title')
    description = models.TextField(blank=True, null=True, verbose_name='Subtask Description')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='to_do')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    estimated_minutes = models.IntegerField(default=15, verbose_name='Estimated Time (minutes)')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True, verbose_name='Paused At')
    total_pause_time = models.IntegerField(default=0, verbose_name='Total Pause Time (minutes)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True, verbose_name='Subtask Notes')
    order = models.IntegerField(default=0, verbose_name='Display Order')
    
    class Meta:
        verbose_name = 'Subtask'
        verbose_name_plural = 'Subtasks'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.parent_task.title} - {self.title}"
    
    @property
    def time_spent(self):
        """Calculate time spent on subtask (excluding pause time)"""
        if not self.started_at:
            return 0
        
        end_time = self.completed_at or system_now()
        total_time = (end_time - self.started_at).total_seconds() / 60
        
        # Subtract total pause time
        active_time = total_time - self.total_pause_time
        
        # If currently paused, subtract current pause duration
        if self.paused_at:
            current_pause = (system_now() - self.paused_at).total_seconds() / 60
            active_time -= current_pause
            
        return max(0, active_time)  # Ensure non-negative
    
    @property
    def is_paused(self):
        """Check if subtask is currently paused"""
        return self.paused_at is not None and self.status == 'doing'


class TaskReport(models.Model):
    """Daily task report submitted by employees"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='task_reports')
    date = models.DateField(default=datetime.date.today)
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    in_progress_tasks = models.IntegerField(default=0)
    not_completed_tasks = models.IntegerField(default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Percentage
    summary_notes = models.TextField(blank=True, null=True, verbose_name='Daily Summary')
    challenges_faced = models.TextField(blank=True, null=True, verbose_name='Challenges/Issues')
    achievements = models.TextField(blank=True, null=True, verbose_name='Key Achievements')
    tomorrow_priorities = models.TextField(blank=True, null=True, verbose_name='Tomorrow\'s Priorities')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by_manager = models.BooleanField(default=False)
    manager_feedback = models.TextField(blank=True, null=True, verbose_name='Manager Feedback')
    manager_rating = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])  # 1-5 rating
    
    class Meta:
        verbose_name = 'Task Report'
        verbose_name_plural = 'Task Reports'
        unique_together = ['employee', 'date']  # One report per employee per day
        ordering = ['-date', 'employee__name']
    
    def __str__(self):
        return f"{self.employee.name} - Report for {self.date}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate completion rate
        if self.total_tasks > 0:
            self.completion_rate = (self.completed_tasks / self.total_tasks) * 100
        super().save(*args, **kwargs)


class TaskComment(models.Model):
    """Comments on tasks for collaboration"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_manager_note = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.name} on {self.task.title}"


class Team(models.Model):
    """Teams for organizing employees and task assignments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="اسم الفريق")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الفريق")
    team_leader = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='led_teams', verbose_name="قائد الفريق")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                 related_name='created_teams', verbose_name="منشئ الفريق")
    is_active = models.BooleanField(default=True, verbose_name="فريق نشط")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "فريق"
        verbose_name_plural = "فرق"
        ordering = ['name']
    
    def __str__(self):
        leader_name = self.team_leader.name if self.team_leader else "No Leader"
        return f"{self.name} - Leader: {leader_name}"
    
    @property
    def member_count(self):
        """Get total number of team members"""
        return self.members.count()
    
    @property
    def active_tasks_count(self):
        """Get count of active tasks assigned to this team"""
        from django.db.models import Q
        return Task.objects.filter(
            team=self,
            status__in=['to_do', 'doing']
        ).count()


class TeamMembership(models.Model):
    """Team membership with roles"""
    ROLE_CHOICES = [
        ('member', 'عضو'),
        ('senior_member', 'عضو أقدم'),
        ('assistant_leader', 'مساعد قائد'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships', verbose_name="الفريق")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='team_memberships', verbose_name="الموظف")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member', verbose_name="الدور")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الانضمام")
    is_active = models.BooleanField(default=True, verbose_name="عضوية نشطة")
    
    class Meta:
        verbose_name = "عضوية فريق"
        verbose_name_plural = "عضويات الفرق"
        unique_together = ['team', 'employee']  # Employee can only be in a team once
        ordering = ['team__name', 'role', 'employee__name']
    
    def __str__(self):
        return f"{self.employee.name} - {self.team.name} ({self.get_role_display()})"


class TeamTask(models.Model):
    """Tasks assigned to teams with team-specific metadata"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='team_assignment', verbose_name="المهمة")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='assigned_tasks', verbose_name="الفريق")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                                  related_name='team_task_assignments', verbose_name="تم التكليف بواسطة")
    can_reassign = models.BooleanField(default=True, verbose_name="يمكن إعادة التكليف")
    team_priority = models.CharField(max_length=10, choices=Task.PRIORITY_CHOICES, 
                                   default='medium', verbose_name="أولوية الفريق")
    team_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات الفريق")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "مهمة فريق"
        verbose_name_plural = "مهام الفرق"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.task.title} - {self.team.name}"


class OfficeLocation(models.Model):
    """Office location settings for GPS-based check-in validation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, default="Main Office", verbose_name="اسم المكتب")
    latitude = models.DecimalField(max_digits=10, decimal_places=8, verbose_name="خط العرض")
    longitude = models.DecimalField(max_digits=11, decimal_places=8, verbose_name="خط الطول")
    radius_meters = models.PositiveIntegerField(default=100, verbose_name="نطاق المسموح (متر)")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    set_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="تم تعيينه بواسطة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "موقع المكتب"
        verbose_name_plural = "مواقع المكاتب"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.latitude}, {self.longitude})"
    
    @classmethod
    def get_active_location(cls):
        """Get the currently active office location"""
        return cls.objects.filter(is_active=True).first()
