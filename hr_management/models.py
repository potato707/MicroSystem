from django.db import models
import datetime
from django.conf import settings
import uuid
from django.contrib.auth.models import AbstractUser
# from django.utils import timezone
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

class Wallet(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, verbose_name="الموظف", null=True, blank=True, related_name="wallet")
    balance = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ", default=0.0)

    def __str__(self):
        return f"Wallet of {self.employee.name} - Balance: {self.balance}"

class WalletTransaction(models.Model):
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
        return f"{self.transaction_type} {self.amount} for {self.wallet.employee.name}"

    class Meta:
        ordering = ["-created_at"]

class ReimbursementRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "تحت المراجعة"),
        ("approved", "موافقة"),
        ("rejected", "رفض"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="reimbursements")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    description = models.TextField(verbose_name="الوصف")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    admin_comment = models.TextField(blank=True, null=True, verbose_name="رد الأدمن")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ReimbursementAttachment(models.Model):
    reimbursement = models.ForeignKey(ReimbursementRequest, on_delete=models.CASCADE, related_name="attachments")
    file_url = models.URLField(verbose_name="رابط الملف")
    uploaded_at = models.DateTimeField(auto_now_add=True)
