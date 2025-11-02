from django.db import models
import datetime
from django.conf import settings
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from utils.timezone_utils import system_now
import os
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import time, date, timedelta
from decimal import Decimal

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_picture = models.URLField(max_length=500, blank=True, null=True, verbose_name="الصورة الشخصية")

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('client', 'Client'),  # New role for complaint system clients
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    name = models.CharField(max_length=200, verbose_name="الاسم")

    REQUIRED_FIELDS = ['email', 'role', 'name']


class EmailVerificationCode(models.Model):
    """
    Store email verification codes for email change requests
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_verification_codes')
    new_email = models.EmailField(verbose_name="البريد الإلكتروني الجديد")
    verification_code = models.CharField(max_length=6, verbose_name="كود التحقق")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    expires_at = models.DateTimeField(verbose_name="تاريخ الانتهاء")
    is_verified = models.BooleanField(default=False, verbose_name="تم التحقق")
    
    class Meta:
        verbose_name = "كود تحقق البريد الإلكتروني"
        verbose_name_plural = "أكواد تحقق البريد الإلكتروني"
        ordering = ['-created_at']
    
    def is_valid(self):
        """Check if code is still valid and not expired"""
        return not self.is_verified and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"{self.user.email} -> {self.new_email} ({self.verification_code})"


class GlobalClient(models.Model):
    """
    Global client accounts that can access any tenant
    Stored in main database, accessible across all tenants
    This allows a single client account to work with multiple tenants
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, verbose_name="البريد الإلكتروني")
    password = models.CharField(max_length=128, verbose_name="كلمة المرور")
    name = models.CharField(max_length=200, verbose_name="الاسم")
    phone = models.CharField(max_length=20, blank=True, verbose_name="الهاتف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسجيل")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="آخر تسجيل دخول")
    
    class Meta:
        verbose_name = "عميل عام"
        verbose_name_plural = "عملاء عامون"
        db_table = 'hr_management_globalclient'
        ordering = ['-date_joined']
    
    def set_password(self, raw_password):
        """Hash and set password"""
        from django.contrib.auth.hashers import make_password
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Check if provided password matches"""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_password, self.password)
    
    # Django authentication compatibility properties
    @property
    def is_authenticated(self):
        """Always return True for active GlobalClient instances"""
        return True
    
    @property
    def is_anonymous(self):
        """GlobalClients are never anonymous"""
        return False
    
    @property
    def role(self):
        """Return 'client' role for compatibility with existing code"""
        return 'client'
    
    @property
    def username(self):
        """Return email as username for compatibility"""
        return self.email
    
    @property
    def is_staff(self):
        """GlobalClients are not staff"""
        return False
    
    @property
    def is_superuser(self):
        """GlobalClients are not superusers"""
        return False
    
    def get_username(self):
        """Return email as username"""
        return self.email
    
    @classmethod
    def get_email_field_name(cls):
        """Return the name of the email field for Django's PasswordResetTokenGenerator"""
        return 'email'
    
    def natural_key(self):
        """Return natural key for this model"""
        return (self.email,)
    
    def __str__(self):
        return f"{self.name} ({self.email})"


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
    
    # Client Complaint System - Categories this employee can handle
    complaint_categories = models.ManyToManyField('ComplaintCategory', blank=True, 
                                                related_name='handling_employees',
                                                verbose_name='فئات الشكاوى التي يمكن التعامل معها')

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
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
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
    total_pause_time = models.FloatField(default=0.0, verbose_name='Total Pause Time (minutes)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True, verbose_name='Task Notes')
    
    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-priority', 'created_at']
        # unique_together = ['employee', 'title', 'date']  # Prevent duplicate tasks on same day
    
    def __str__(self):
        assignee = self.employee.name if self.employee else (f"Team: {self.team.name}" if self.team else "Unassigned")
        return f"{assignee} - {self.title} ({self.date})"
    
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
    assigned_employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True, blank=True, related_name='assigned_subtasks', verbose_name='Assigned Employee')
    title = models.CharField(max_length=200, verbose_name='Subtask Title')
    description = models.TextField(blank=True, null=True, verbose_name='Subtask Description')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='to_do')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    estimated_minutes = models.IntegerField(default=15, verbose_name='Estimated Time (minutes)')
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True, verbose_name='Paused At')
    total_pause_time = models.FloatField(default=0.0, verbose_name='Total Pause Time (minutes)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True, verbose_name='Subtask Notes')
    order = models.IntegerField(default=0, verbose_name='Display Order')
    
    class Meta:
        verbose_name = 'Subtask'
        verbose_name_plural = 'Subtasks'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        assigned_to = f" (assigned to {self.assigned_employee.name})" if self.assigned_employee else ""
        return f"{self.parent_task.title} - {self.title}{assigned_to}"
    
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
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.name} on {self.task.title}"


class ShareableTaskLink(models.Model):
    """Shareable links for tasks - allows viewing task details without login"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='shared_links')
    token = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='Share Token')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_share_links')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Expiration Date')
    is_active = models.BooleanField(default=True, verbose_name='Active')
    view_count = models.IntegerField(default=0, verbose_name='View Count')
    last_viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='Last Viewed')
    allow_comments = models.BooleanField(default=False, verbose_name='Allow Comments')
    
    class Meta:
        verbose_name = 'Shareable Task Link'
        verbose_name_plural = 'Shareable Task Links'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Share link for {self.task.title} (Token: {self.token[:8]}...)"
    
    def is_expired(self):
        """Check if link has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if link is valid and active"""
        return self.is_active and not self.is_expired()
    
    def increment_view_count(self):
        """Increment view count and update last viewed time"""
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed_at'])
    
    @staticmethod
    def generate_token():
        """Generate a secure random token"""
        import secrets
        return secrets.token_urlsafe(48)


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
    
    # Client Complaint System - Categories this team can handle
    complaint_categories = models.ManyToManyField('ComplaintCategory', blank=True, 
                                                related_name='handling_teams',
                                                verbose_name='فئات الشكاوى التي يمكن للفريق التعامل معها')
    
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


# Client Complaint System Models

class ComplaintCategory(models.Model):
    """Categories for client complaints (e.g., Technical, Design, Support)"""
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الفئة")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الفئة")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="لون الفئة")  # Hex color
    is_active = models.BooleanField(default=True, verbose_name="فئة نشطة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Link categories to teams that can handle them
    assigned_teams = models.ManyToManyField(Team, blank=True, related_name='client_complaint_categories', verbose_name="الفرق المخصصة")
    
    class Meta:
        verbose_name = "فئة الشكوى"
        verbose_name_plural = "فئات الشكاوى"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ClientComplaintStatus(models.Model):
    """Custom statuses for client complaints that admins can create"""
    STATUS_TYPES = [
        ('default', 'Default Status'),
        ('custom', 'Custom Status'),
    ]
    
    name = models.CharField(max_length=50, unique=True, verbose_name="Status Name")
    label = models.CharField(max_length=100, verbose_name="Display Label")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="Badge Color")  # Hex color
    is_active = models.BooleanField(default=True, verbose_name="Active Status")
    status_type = models.CharField(max_length=10, choices=STATUS_TYPES, default='custom', verbose_name="Status Type")
    
    # Order for display in dropdowns
    display_order = models.PositiveIntegerField(default=0, verbose_name="Display Order")
    
    # Permissions and workflow
    can_be_set_by_admin = models.BooleanField(default=True, verbose_name="Can be set by admin")
    is_final_status = models.BooleanField(default=False, verbose_name="Is final status (cannot be changed)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='created_complaint_statuses', verbose_name="Created by")
    
    class Meta:
        verbose_name = "Client Complaint Status"
        verbose_name_plural = "Client Complaint Statuses"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.label or self.name


class TicketDelayThreshold(models.Model):
    """
    Defines delay thresholds for ticket response times
    Can be global default, priority-specific, or per-ticket custom
    """
    THRESHOLD_TYPE_CHOICES = [
        ('global', 'Global Default'),
        ('priority', 'Priority-Based'),
        ('custom', 'Per-Ticket Custom'),
    ]
    
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    threshold_type = models.CharField(max_length=20, choices=THRESHOLD_TYPE_CHOICES, default='global')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, null=True, blank=True,
                               help_text="Only for priority-based thresholds")
    
    # Threshold durations in hours
    system_response_hours = models.IntegerField(
        default=24,
        help_text="Hours allowed for system/support to respond before marked as delayed"
    )
    client_response_hours = models.IntegerField(
        default=48,
        help_text="Hours allowed for client to respond before marked as delayed"
    )
    auto_close_hours = models.IntegerField(
        default=48,
        help_text="Hours after resolution before auto-closing if no client confirmation"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Ticket Delay Threshold"
        verbose_name_plural = "Ticket Delay Thresholds"
        ordering = ['threshold_type', 'priority']
        unique_together = [['threshold_type', 'priority']]
    
    def __str__(self):
        if self.threshold_type == 'priority' and self.priority:
            return f"{self.priority.title()} Priority Thresholds"
        return f"{self.threshold_type.title()} Thresholds"


class ClientComplaint(models.Model):
    """Client complaints submitted through public interface"""
    STATUS_CHOICES = [
        ('pending_review', 'في انتظار المراجعة'),
        ('approved', 'معتمدة'),
        ('rejected', 'مرفوضة'),
        ('in_progress', 'قيد المعالجة'),
        ('resolved', 'محلولة'),
        ('closed', 'مغلقة'),
        ('custom', 'حالة مخصصة'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('urgent', 'عاجل'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Client Information (no login required)
    client_name = models.CharField(max_length=200, verbose_name="اسم العميل")
    client_email = models.EmailField(verbose_name="بريد العميل الإلكتروني")
    client_phone = models.CharField(max_length=20, verbose_name="رقم هاتف العميل", 
                                   help_text="رقم الهاتف مطلوب للتواصل")
    # Link to client user account (for dashboard/login)
    client_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="client_complaints", verbose_name="حساب العميل")  # New field for client login
    project_name = models.CharField(max_length=200, blank=True, null=True, verbose_name="اسم المشروع")
    project_code = models.CharField(max_length=50, blank=True, null=True, verbose_name="رمز المشروع")
    
    # Complaint Details
    category = models.ForeignKey(ComplaintCategory, on_delete=models.CASCADE, verbose_name="فئة الشكوى")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name="الأولوية")
    title = models.CharField(max_length=300, verbose_name="عنوان الشكوى")
    description = models.TextField(verbose_name="تفاصيل الشكوى")
    
    # Status and Workflow
    status = models.CharField(max_length=50, default='pending_review', verbose_name="حالة الشكوى")
    custom_status = models.ForeignKey(ClientComplaintStatus, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='complaints', verbose_name="Custom Status")
    
    # Review Information
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='reviewed_complaints', verbose_name="راجعها")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ المراجعة")
    review_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات المراجعة")
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="سبب الرفض")
    
    # Resolution Information
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='resolved_complaints', verbose_name="حلها")
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحل")
    resolution_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات الحل")
    
    # Automated Status Management (New fields for ticket automation)
    last_response_time = models.DateTimeField(null=True, blank=True, 
                                             help_text="Timestamp of last response (client or system)")
    last_responder = models.CharField(max_length=20, null=True, blank=True,
                                     choices=[('client', 'Client'), ('system', 'System')],
                                     help_text="Who responded last: client or system")
    automated_status = models.CharField(max_length=50, null=True, blank=True,
                                       help_text="Automated status based on response timing")
    delay_status = models.CharField(max_length=50, null=True, blank=True,
                                   help_text="Indicates if delayed by system or client")
    custom_threshold = models.ForeignKey('TicketDelayThreshold', on_delete=models.SET_NULL, 
                                        null=True, blank=True,
                                        related_name='complaints_with_custom_threshold',
                                        help_text="Custom thresholds for this specific ticket")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    class Meta:
        verbose_name = "شكوى عميل"
        verbose_name_plural = "شكاوى العملاء"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.client_name} - {self.title}"
    
    @property
    def is_overdue(self):
        """Check if complaint is overdue based on priority"""
        if self.status in ['resolved', 'closed']:
            return False
        
        now = timezone.now()
        days_since_creation = (now - self.created_at).days
        
        if self.priority == 'urgent':
            return days_since_creation > 1
        elif self.priority == 'medium':
            return days_since_creation > 3
        else:  # low priority
            return days_since_creation > 7

    @property
    def current_status_display(self):
        """Get display name for current status (custom or default)"""
        if self.custom_status:
            return self.custom_status.label
        else:
            # Return display name for default status
            status_dict = dict(self.STATUS_CHOICES)
            return status_dict.get(self.status, self.status)
    
    @property
    def current_status_color(self):
        """Get color for current status"""
        if self.custom_status:
            return self.custom_status.color
        else:
            # Default colors for default statuses
            status_colors = {
                'pending_review': '#fbbf24',  # yellow
                'approved': '#10b981',        # green  
                'rejected': '#ef4444',        # red
                'in_progress': '#3b82f6',     # blue
                'resolved': '#8b5cf6',        # purple
                'closed': '#6b7280',          # gray
            }
            return status_colors.get(self.status, '#6b7280')
    
    @property
    def effective_status(self):
        """Get the effective status (custom or default)"""
        return self.custom_status.name if self.custom_status else self.status
    
    def update_status(self, new_status, custom_status_id=None, updated_by=None):
        """Update complaint status (can be default or custom)"""
        old_status = self.effective_status
        
        if custom_status_id:
            try:
                custom_status = ClientComplaintStatus.objects.get(id=custom_status_id, is_active=True)
                self.custom_status = custom_status
                self.status = 'custom'  # Mark as using custom status
            except ClientComplaintStatus.DoesNotExist:
                raise ValueError("Invalid custom status ID")
        else:
            # Using default status
            self.custom_status = None
            self.status = new_status
        
        self.save()
        
        # Log status change in history
        from .models import ClientComplaintStatusHistory
        
        # Determine old and new status keys for history
        old_status_key = old_status if old_status in dict(self.STATUS_CHOICES) else 'custom'
        new_status_key = self.status  # This will be 'custom' for custom statuses
        
        reason_text = f"Status changed from {old_status} to {self.effective_status}"
        if updated_by:
            reason_text += f" by {updated_by.get_full_name() or updated_by.username}"
            
        ClientComplaintStatusHistory.objects.create(
            complaint=self,
            old_status=old_status_key,
            new_status=new_status_key,
            changed_by=updated_by,
            reason=reason_text
        )
        
        return self

    @classmethod
    def get_available_statuses(cls):
        """Get all available statuses (default + active custom)"""
        default_statuses = [
            {'type': 'default', 'name': key, 'label': value, 'color': '#6b7280'} 
            for key, value in cls.STATUS_CHOICES
        ]
        
        custom_statuses = [
            {
                'type': 'custom', 
                'name': status.name, 
                'label': status.label, 
                'color': status.color,
                'id': status.id
            }
            for status in ClientComplaintStatus.objects.filter(is_active=True).order_by('display_order', 'name')
        ]
        
        return default_statuses + custom_statuses

    @property
    def task_statistics(self):
        """Calculate task progress statistics for this complaint"""
        all_tasks = Task.objects.filter(client_complaint_task__complaint=self)
        
        total_tasks = all_tasks.count()
        completed_tasks = all_tasks.filter(status='done').count()
        in_progress_tasks = all_tasks.filter(status='doing').count()
        pending_tasks = all_tasks.filter(status='to_do').count()
        
        # Calculate completion percentage
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'in_progress_tasks': in_progress_tasks,
            'pending_tasks': pending_tasks,
            'completion_percentage': round(completion_percentage, 1)
        }

    def get_effective_status(self):
        """Get the effective status (custom status takes precedence over default status)"""
        if self.custom_status:
            return self.custom_status.name
        return self.status
    
    def is_using_custom_status(self):
        """Check if complaint is using a custom status"""
        return self.custom_status is not None
    
    def get_status_display_name(self):
        """Get the display name for the current status"""
        if self.custom_status:
            return self.custom_status.name
        
        # Return display name for default statuses
        status_display_names = {
            'pending_review': 'Pending Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed'
        }
        return status_display_names.get(self.status, self.status.title())
    
    def get_status_color(self):
        """Get the color for the current status"""
        if self.custom_status:
            return '#8B5CF6'  # Purple for custom statuses
        
        # Colors for default statuses
        status_colors = {
            'pending_review': '#FFA500',  # Orange
            'approved': '#22C55E',        # Green
            'rejected': '#EF4444',        # Red
            'in_progress': '#3B82F6',     # Blue
            'resolved': '#10B981',        # Emerald
            'closed': '#6B7280'           # Gray
        }
        return status_colors.get(self.status, '#6B7280')


class ClientComplaintAttachment(models.Model):
    """File attachments for client complaints"""
    complaint = models.ForeignKey(ClientComplaint, on_delete=models.CASCADE, related_name='attachments', verbose_name="الشكوى")
    file_url = models.URLField(verbose_name="رابط الملف")
    file_name = models.CharField(max_length=255, verbose_name="اسم الملف")
    file_size = models.PositiveIntegerField(null=True, blank=True, verbose_name="حجم الملف")  # in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")
    uploaded_by = models.CharField(max_length=20, choices=[('client', 'العميل'), ('admin', 'الإدارة')], 
                                 default='client', verbose_name="رفعه")
    
    class Meta:
        verbose_name = "مرفق شكوى عميل"
        verbose_name_plural = "مرفقات شكاوى العملاء"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.complaint.title} - {self.file_name}"


class ClientComplaintAssignment(models.Model):
    """Assignment of complaints to teams for handling"""
    complaint = models.ForeignKey(ClientComplaint, on_delete=models.CASCADE, related_name='assignments', verbose_name="الشكوى")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='client_complaint_assignments', verbose_name="الفريق")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="خصص بواسطة")
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التخصيص")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات التخصيص")
    is_active = models.BooleanField(default=True, verbose_name="تخصيص نشط")
    
    class Meta:
        verbose_name = "تخصيص شكوى عميل"
        verbose_name_plural = "تخصيصات شكاوى العملاء"
        unique_together = ['complaint', 'team']  # Each team can only be assigned once per complaint
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.complaint.title} → {self.team.name}"


class ClientComplaintEmployeeAssignment(models.Model):
    """Assignment of complaints to individual employees for handling"""
    complaint = models.ForeignKey(ClientComplaint, on_delete=models.CASCADE, related_name='employee_assignments', verbose_name="الشكوى")
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='client_complaint_assignments', verbose_name="الموظف")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="خصص بواسطة")
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التخصيص")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات التخصيص")
    is_active = models.BooleanField(default=True, verbose_name="تخصيص نشط")
    
    class Meta:
        verbose_name = "تخصيص شكوى عميل للموظف"
        verbose_name_plural = "تخصيصات شكاوى العملاء للموظفين"
        unique_together = ['complaint', 'employee']  # Each employee can only be assigned once per complaint
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.complaint.title} → {self.employee.name}"


class ClientComplaintTask(models.Model):
    """Tasks created by teams to handle complaints"""
    complaint = models.ForeignKey(ClientComplaint, on_delete=models.CASCADE, related_name='tasks', verbose_name="الشكوى")
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='client_complaint_task', verbose_name="المهمة")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, verbose_name="الفريق")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="أنشأه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    
    class Meta:
        verbose_name = "مهمة شكوى عميل"
        verbose_name_plural = "مهام شكاوى العملاء"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.complaint.title} - {self.task.title}"


class ClientComplaintComment(models.Model):
    """Internal comments on complaints for team collaboration"""
    complaint = models.ForeignKey(ClientComplaint, on_delete=models.CASCADE, related_name='comments', verbose_name="الشكوى")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="الكاتب")
    comment = models.TextField(verbose_name="التعليق")
    is_internal = models.BooleanField(default=True, verbose_name="تعليق داخلي")  # Internal vs client-visible
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    class Meta:
        verbose_name = "تعليق شكوى عميل"
        verbose_name_plural = "تعليقات شكاوى العملاء"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.author.name} على {self.complaint.title}"


class ClientComplaintStatusHistory(models.Model):
    """Track status changes of complaints for audit trail"""
    complaint = models.ForeignKey(ClientComplaint, on_delete=models.CASCADE, related_name='status_history', verbose_name="الشكوى")
    old_status = models.CharField(max_length=20, choices=ClientComplaint.STATUS_CHOICES, verbose_name="الحالة السابقة")
    new_status = models.CharField(max_length=20, choices=ClientComplaint.STATUS_CHOICES, verbose_name="الحالة الجديدة")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, verbose_name="غيرها")
    reason = models.TextField(blank=True, null=True, verbose_name="سبب التغيير")
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التغيير")
    
    class Meta:
        verbose_name = "تاريخ حالة شكوى عميل"
        verbose_name_plural = "تاريخ حالات شكاوى العملاء"
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.complaint.title}: {self.old_status} → {self.new_status}"


class ClientComplaintAccessToken(models.Model):
    """Secure access tokens for clients to view their complaints"""
    complaint = models.OneToOneField(ClientComplaint, on_delete=models.CASCADE, related_name='access_token', verbose_name="الشكوى")
    token = models.CharField(max_length=64, unique=True, verbose_name="رمز الوصول")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الانتهاء")  # Made optional for permanent links
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name="آخر وصول")
    access_count = models.PositiveIntegerField(default=0, verbose_name="عدد مرات الوصول")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    is_permanent = models.BooleanField(default=True, verbose_name="رابط دائم")  # New field for permanent links
    
    class Meta:
        verbose_name = "رمز وصول شكوى عميل"
        verbose_name_plural = "رموز وصول شكاوى العملاء"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Token for {self.complaint.title} - {self.complaint.client_name}"
    
    @property
    def is_expired(self):
        """Check if token has expired"""
        if self.is_permanent or self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid (active and not expired)"""
        return self.is_active and not self.is_expired
    
    def generate_token(self):
        """Generate a secure random token"""
        import secrets
        self.token = secrets.token_urlsafe(32)
        return self.token
    
    def record_access(self):
        """Record that the token was accessed"""
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])
    
    @classmethod
    def create_for_complaint(cls, complaint, days_valid=None, is_permanent=True):
        """Create or update access token for a complaint"""
        from datetime import timedelta
        
        # Check if token already exists
        try:
            token_obj = cls.objects.get(complaint=complaint)
            # Token exists, just reactivate it if needed
            if not token_obj.is_active:
                token_obj.is_active = True
                token_obj.save()
            return token_obj
        except cls.DoesNotExist:
            # Create new token
            expires_at = None
            if not is_permanent and days_valid:
                expires_at = timezone.now() + timedelta(days=days_valid)
            
            token_obj = cls.objects.create(
                complaint=complaint,
                expires_at=expires_at,
                is_active=True,
                is_permanent=is_permanent
            )
            
            token_obj.generate_token()
            token_obj.save()
            
            return token_obj


class ClientComplaintReply(models.Model):
    """Client replies to their complaints (public-facing)"""
    complaint = models.ForeignKey(ClientComplaint, on_delete=models.CASCADE, related_name='client_replies', verbose_name="الشكوى")
    reply_text = models.TextField(verbose_name="نص الرد")
    client_name = models.CharField(max_length=200, verbose_name="اسم العميل")
    client_email = models.EmailField(verbose_name="بريد العميل الإلكتروني")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    is_read_by_admin = models.BooleanField(default=False, verbose_name="مقروء من الإدارة")
    admin_response = models.TextField(blank=True, null=True, verbose_name="رد الإدارة")
    admin_responded_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ رد الإدارة")
    admin_responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="رد من")
    
    class Meta:
        verbose_name = "رد عميل على شكوى"
        verbose_name_plural = "ردود العملاء على الشكاوى"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reply from {self.client_name} on {self.complaint.title}"


# Complaint Admin Permission Models
class ComplaintAdminPermission(models.Model):
    """Base model for complaint admin permissions"""
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="منحت بواسطة")
    granted_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ المنح")
    is_active = models.BooleanField(default=True, verbose_name="صلاحية نشطة")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    
    # Specific permissions
    can_review = models.BooleanField(default=True, verbose_name="يمكن مراجعة الشكاوى")
    can_assign = models.BooleanField(default=True, verbose_name="يمكن تخصيص الشكاوى")
    can_update_status = models.BooleanField(default=True, verbose_name="يمكن تحديث حالة الشكاوى")
    can_change_status = models.BooleanField(default=True, verbose_name="يمكن تغيير حالة الشكاوى")  # Alias for can_update_status
    can_add_comments = models.BooleanField(default=True, verbose_name="يمكن إضافة تعليقات")
    can_create_tasks = models.BooleanField(default=True, verbose_name="يمكن إنشاء مهام")
    can_manage_assignments = models.BooleanField(default=True, verbose_name="يمكن إدارة التخصيصات")
    can_delete = models.BooleanField(default=False, verbose_name="يمكن حذف الشكاوى")
    can_manage_categories = models.BooleanField(default=False, verbose_name="يمكن إدارة الحالات المخصصة")
    
    class Meta:
        abstract = True


class TeamComplaintAdminPermission(ComplaintAdminPermission):
    """Grant complaint admin permissions to entire teams"""
    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name='complaint_admin_permission', verbose_name="الفريق")
    
    class Meta:
        verbose_name = "صلاحية إدارة شكاوى للفريق"
        verbose_name_plural = "صلاحيات إدارة الشكاوى للفرق"
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"Complaint Admin Permission: {self.team.name}"


class EmployeeComplaintAdminPermission(ComplaintAdminPermission):
    """Grant complaint admin permissions to individual employees"""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='complaint_admin_permission', verbose_name="الموظف")
    
    class Meta:
        verbose_name = "صلاحية إدارة شكاوى للموظف"
        verbose_name_plural = "صلاحيات إدارة الشكاوى للموظفين"
        ordering = ['-granted_at']
    
    def __str__(self):
        return f"Complaint Admin Permission: {self.employee.name}"


# Utility functions for complaint admin permissions
def has_complaint_admin_permission(user, permission_type='can_review'):
    """
    Check if a user has complaint admin permissions
    Args:
        user: The user to check
        permission_type: Specific permission to check (can_review, can_assign, etc.)
    Returns:
        bool: True if user has the permission
    """
    # Regular admins always have all permissions
    if user.role == 'admin':
        return True
    
    # Check if user has employee object
    if not hasattr(user, 'employee') or not user.employee:
        return False
    
    employee = user.employee
    
    # Check individual employee permission
    try:
        employee_permission = EmployeeComplaintAdminPermission.objects.get(
            employee=employee, 
            is_active=True
        )
        return getattr(employee_permission, permission_type, False)
    except EmployeeComplaintAdminPermission.DoesNotExist:
        pass
    
    # Check team permissions
    for team_membership in employee.team_memberships.filter(is_active=True):
        try:
            team_permission = TeamComplaintAdminPermission.objects.get(
                team=team_membership.team,
                is_active=True
            )
            if getattr(team_permission, permission_type, False):
                return True
        except TeamComplaintAdminPermission.DoesNotExist:
            continue
    
    return False


def get_complaint_admin_permissions(user):
    """
    Get all complaint admin permissions for a user
    Returns:
        dict: Dictionary with all permission flags
    """
    permissions = {
        'has_permission': False,
        'can_review': False,
        'can_assign': False,
        'can_update_status': False,
        'can_change_status': False,
        'can_add_comments': False,
        'can_create_tasks': False,
        'can_manage_assignments': False,
        'can_delete': False,
        'can_manage_categories': False,
        'is_complaint_admin': False
    }
    
    # Regular admins have all permissions
    if user.role == 'admin':
        for key in permissions:
            permissions[key] = True
        return permissions
    
    # Check if user has employee object
    if not hasattr(user, 'employee') or not user.employee:
        return permissions
    
    employee = user.employee
    
    # Check individual employee permission
    try:
        employee_permission = EmployeeComplaintAdminPermission.objects.get(
            employee=employee, 
            is_active=True
        )
        for key in permissions:
            if key not in ['is_complaint_admin', 'has_permission']:
                permissions[key] = getattr(employee_permission, key, False)
    except EmployeeComplaintAdminPermission.DoesNotExist:
        pass
    
    # Check team permissions (OR logic - if any team has permission, user gets it)
    for team_membership in employee.team_memberships.filter(is_active=True):
        try:
            team_permission = TeamComplaintAdminPermission.objects.get(
                team=team_membership.team,
                is_active=True
            )
            for key in permissions:
                if key != 'is_complaint_admin':
                    if getattr(team_permission, key, False):
                        permissions[key] = True
        except TeamComplaintAdminPermission.DoesNotExist:
            continue
    
    # Set is_complaint_admin if user has any complaint admin permissions
    permissions['is_complaint_admin'] = any(permissions[key] for key in permissions if key != 'is_complaint_admin')
    
    return permissions


class Notification(models.Model):
    """Model for storing in-app notifications"""
    NOTIFICATION_TYPES = [
        ('new_message', 'رسالة جديدة'),
        ('status_change', 'تغيير الحالة'),
        ('assignment', 'تعيين جديد'),
        ('comment', 'تعليق جديد'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='المستلم'
    )
    complaint = models.ForeignKey(
        'ClientComplaint',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='الشكوى',
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name='نوع الإشعار'
    )
    title = models.CharField(max_length=200, verbose_name='العنوان')
    message = models.TextField(verbose_name='الرسالة')
    is_read = models.BooleanField(default=False, verbose_name='مقروء')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ القراءة')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


# ========== Shift Scheduling System ==========

class WeeklyShiftSchedule(models.Model):
    """
    Permanent weekly schedule for employees - same hours repeat every week
    """
    DAYS_OF_WEEK = (
        (0, 'الأحد'),
        (1, 'الإثنين'),
        (2, 'الثلاثاء'),
        (3, 'الأربعاء'),
        (4, 'الخميس'),
        (5, 'الجمعة'),
        (6, 'السبت'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE, 
        related_name='weekly_shifts',
        verbose_name="الموظف"
    )
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        validators=[MinValueValidator(0), MaxValueValidator(6)],
        verbose_name="يوم الأسبوع"
    )
    start_time = models.TimeField(verbose_name="وقت البداية")
    end_time = models.TimeField(verbose_name="وقت النهاية")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "جدول دوام أسبوعي"
        verbose_name_plural = "جداول الدوام الأسبوعية"
        unique_together = ['employee', 'day_of_week']
        ordering = ['employee', 'day_of_week']
        indexes = [
            models.Index(fields=['employee', 'day_of_week']),
            models.Index(fields=['is_active']),
        ]
    
    def clean(self):
        """Validate shift times"""
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("وقت النهاية يجب أن يكون بعد وقت البداية")
    
    def calculate_hours(self):
        """Calculate total hours for this shift"""
        if not self.start_time or not self.end_time:
            return 0
        
        # Convert string to time object if needed
        start_time = self.start_time
        end_time = self.end_time
        
        if isinstance(start_time, str):
            start_time = datetime.datetime.strptime(start_time, '%H:%M:%S').time() if len(start_time) > 5 else datetime.datetime.strptime(start_time, '%H:%M').time()
        if isinstance(end_time, str):
            end_time = datetime.datetime.strptime(end_time, '%H:%M:%S').time() if len(end_time) > 5 else datetime.datetime.strptime(end_time, '%H:%M').time()
        
        # Convert to datetime for calculation
        start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
        end_dt = datetime.datetime.combine(datetime.date.today(), end_time)
        
        # Handle overnight shifts
        if end_dt < start_dt:
            end_dt += datetime.timedelta(days=1)
        
        hours = (end_dt - start_dt).total_seconds() / 3600
        
        # Deduct 1 hour break for shifts > 6 hours
        if hours > 6:
            hours -= 1
            
        return round(hours, 2)
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"


class ShiftOverride(models.Model):
    """
    Temporary changes to employee shifts for specific dates
    """
    OVERRIDE_TYPES = (
        ('custom', 'ساعات مخصصة'),
        ('day_off', 'يوم عطلة'),
        ('vacation', 'إجازة'),
        ('sick_leave', 'إجازة مرضية'),
        ('holiday', 'عطلة رسمية'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('approved', 'موافق عليه'),
        ('rejected', 'مرفوض'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='shift_overrides',
        verbose_name="الموظف"
    )
    date = models.DateField(verbose_name="التاريخ")
    override_type = models.CharField(
        max_length=20,
        choices=OVERRIDE_TYPES,
        verbose_name="نوع الاستثناء"
    )
    start_time = models.TimeField(null=True, blank=True, verbose_name="وقت البداية")
    end_time = models.TimeField(null=True, blank=True, verbose_name="وقت النهاية")
    reason = models.TextField(verbose_name="السبب")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="الحالة"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shift_override_requests',
        verbose_name="طلب بواسطة"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_shift_overrides',
        verbose_name="وافق عليه"
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الموافقة")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "استثناء دوام"
        verbose_name_plural = "استثناءات الدوام"
        unique_together = ['employee', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['status']),
        ]
    
    def clean(self):
        """Validate override"""
        if self.override_type == 'custom':
            if not self.start_time or not self.end_time:
                raise ValidationError("الدوامات المخصصة تتطلب أوقات البداية والنهاية")
            if self.start_time >= self.end_time:
                raise ValidationError("وقت النهاية يجب أن يكون بعد وقت البداية")
        elif self.override_type in ['day_off', 'vacation', 'sick_leave', 'holiday']:
            # These should not have times
            self.start_time = None
            self.end_time = None
    
    def approve(self, approved_by_user):
        """Approve this override"""
        self.status = 'approved'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
    
    def reject(self, approved_by_user):
        """Reject this override"""
        self.status = 'rejected'
        self.approved_by = approved_by_user
        self.approved_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.get_override_type_display()})"


class ShiftAttendance(models.Model):
    """
    Daily attendance tracking with automatic late/absent detection
    """
    STATUS_CHOICES = (
        ('scheduled', 'مجدول'),
        ('present', 'حاضر'),
        ('late', 'متأخر'),
        ('absent', 'غائب'),
        ('early_departure', 'مغادرة مبكرة'),
        ('overtime', 'وقت إضافي'),
        ('day_off', 'يوم عطلة'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='shift_attendances',
        verbose_name="الموظف"
    )
    date = models.DateField(verbose_name="التاريخ")
    
    # Expected times (from schedule or override)
    expected_start = models.TimeField(null=True, blank=True, verbose_name="وقت البداية المتوقع")
    expected_end = models.TimeField(null=True, blank=True, verbose_name="وقت النهاية المتوقع")
    
    # Actual times (clock in/out)
    actual_start = models.TimeField(null=True, blank=True, verbose_name="وقت البداية الفعلي")
    actual_end = models.TimeField(null=True, blank=True, verbose_name="وقت النهاية الفعلي")
    
    # Calculated fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name="الحالة"
    )
    late_minutes = models.IntegerField(default=0, verbose_name="دقائق التأخير")
    early_departure_minutes = models.IntegerField(default=0, verbose_name="دقائق المغادرة المبكرة")
    overtime_minutes = models.IntegerField(default=0, verbose_name="دقائق الوقت الإضافي")
    total_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="مجموع الساعات"
    )
    
    # System flags
    auto_marked_absent = models.BooleanField(default=False, verbose_name="تم وضع علامة غائب تلقائياً")
    requires_manager_approval = models.BooleanField(default=False, verbose_name="يتطلب موافقة المدير")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_attendances',
        verbose_name="وافق عليه"
    )
    
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "حضور دوام"
        verbose_name_plural = "سجل الحضور"
        unique_together = ['employee', 'date']
        ordering = ['-date', 'employee']
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['auto_marked_absent']),
        ]
    
    def clock_in(self, clock_in_time=None):
        """
        Record clock in and calculate if late
        """
        if clock_in_time is None:
            clock_in_time = timezone.now().time()
        
        self.actual_start = clock_in_time
        
        if self.expected_start:
            # Calculate late minutes
            expected_dt = datetime.datetime.combine(datetime.date.today(), self.expected_start)
            actual_dt = datetime.datetime.combine(datetime.date.today(), clock_in_time)
            
            grace_period = datetime.timedelta(minutes=15)  # 15 minute grace period
            
            if actual_dt > expected_dt + grace_period:
                self.late_minutes = int((actual_dt - expected_dt).total_seconds() / 60)
                self.status = 'late'
            else:
                self.late_minutes = 0
                self.status = 'present'
        else:
            self.status = 'present'
        
        self.auto_marked_absent = False
        self.save()
    
    def clock_out(self, clock_out_time=None):
        """
        Record clock out and calculate total hours, overtime, early departure
        """
        if clock_out_time is None:
            clock_out_time = timezone.now().time()
        
        self.actual_end = clock_out_time
        
        if self.actual_start:
            # Calculate total hours
            start_dt = datetime.datetime.combine(datetime.date.today(), self.actual_start)
            end_dt = datetime.datetime.combine(datetime.date.today(), clock_out_time)
            
            # Handle overnight shifts
            if end_dt < start_dt:
                end_dt += datetime.timedelta(days=1)
            
            hours = (end_dt - start_dt).total_seconds() / 3600
            
            # Deduct 1 hour break for shifts > 6 hours
            if hours > 6:
                hours -= 1
            
            self.total_hours = round(hours, 2)
            
            # Check for early departure or overtime
            if self.expected_end:
                expected_end_dt = datetime.datetime.combine(datetime.date.today(), self.expected_end)
                
                if end_dt < expected_end_dt - datetime.timedelta(minutes=15):
                    self.early_departure_minutes = int((expected_end_dt - end_dt).total_seconds() / 60)
                    if self.status == 'present':
                        self.status = 'early_departure'
                elif end_dt > expected_end_dt + datetime.timedelta(minutes=30):
                    self.overtime_minutes = int((end_dt - expected_end_dt).total_seconds() / 60)
                    if self.status == 'present':
                        self.status = 'overtime'
        
        self.save()
    
    def mark_absent(self, auto=False):
        """Mark employee as absent"""
        self.status = 'absent'
        self.auto_marked_absent = auto
        self.save()
    
    def __str__(self):
        return f"{self.employee.name} - {self.date} ({self.get_status_display()})"


# Helper functions for shift management

def get_employee_shift_for_date(employee_id, target_date):
    """
    Get the effective shift for an employee on a specific date
    Checks overrides first, then falls back to weekly schedule
    """
    # Check for approved override
    try:
        override = ShiftOverride.objects.get(
            employee_id=employee_id,
            date=target_date,
            status='approved'
        )
        
        if override.override_type in ['day_off', 'vacation', 'sick_leave', 'holiday']:
            return None  # No shift
        elif override.override_type == 'custom':
            return {
                'start_time': override.start_time,
                'end_time': override.end_time,
                'is_override': True,
                'override_type': override.get_override_type_display()
            }
    except ShiftOverride.DoesNotExist:
        pass
    
    # Check weekly schedule
    day_of_week = target_date.weekday()
    # Convert Python weekday (0=Monday) to our system (0=Sunday)
    if day_of_week == 6:
        day_of_week = 0
    else:
        day_of_week += 1
    
    try:
        schedule = WeeklyShiftSchedule.objects.get(
            employee_id=employee_id,
            day_of_week=day_of_week,
            is_active=True
        )
        return {
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'is_override': False
        }
    except WeeklyShiftSchedule.DoesNotExist:
        return None  # No shift scheduled


def get_employees_on_shift_now():
    """
    Get list of employees who should currently be on shift
    """
    now = timezone.now()
    current_date = now.date()
    current_time = now.time()
    
    on_shift = []
    
    for employee in Employee.objects.filter(status='active'):
        shift = get_employee_shift_for_date(employee.id, current_date)
        
        if shift and shift['start_time'] <= current_time <= shift['end_time']:
            on_shift.append({
                'employee': employee,
                'start_time': shift['start_time'],
                'end_time': shift['end_time'],
                'is_override': shift.get('is_override', False)
            })
    
    return on_shift


def calculate_weekly_hours(employee_id):
    """
    Calculate total weekly hours for an employee based on their schedule
    """
    schedules = WeeklyShiftSchedule.objects.filter(
        employee_id=employee_id,
        is_active=True
    )
    
    total_hours = sum(schedule.calculate_hours() for schedule in schedules)
    return round(total_hours, 2)


# Import Tenant models
from .tenant_models import Tenant, TenantModule, ModuleDefinition, TenantAPIKey
