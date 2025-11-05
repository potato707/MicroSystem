import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class ClientType(models.Model):
    """
    Dynamic client types with custom fields
    Admin can create different types (Branch, Website, Distributor, etc.)
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'نص'),
        ('number', 'رقم'),
        ('email', 'بريد إلكتروني'),
        ('phone', 'هاتف'),
        ('select', 'قائمة منسدلة'),
        ('textarea', 'نص طويل'),
        ('date', 'تاريخ'),
        ('url', 'رابط'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم نوع العميل")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="أيقونة")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="اللون")
    
    # Dynamic fields configuration stored as JSON
    # Example: [
    #   {"name": "address", "label": "العنوان", "type": "text", "required": true},
    #   {"name": "city", "label": "المدينة", "type": "select", "options": ["القاهرة", "الإسكندرية"], "required": true}
    # ]
    custom_fields = models.JSONField(default=list, verbose_name="الحقول المخصصة")
    
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_client_types',
        verbose_name="أنشأه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "نوع العميل"
        verbose_name_plural = "أنواع العملاء"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def clients_count(self):
        """Get number of clients of this type"""
        return self.clients.count()


class Client(models.Model):
    """
    Clients (Branches, Websites, Distributors, etc.)
    With dynamic fields based on client type
    """
    CLIENT_CATEGORY_CHOICES = [
        ('small', 'صغير'),
        ('medium', 'متوسط'),
        ('large', 'كبير'),
    ]
    
    CLIENT_STATUS_CHOICES = [
        ('potential', 'عميل محتمل'),
        ('active', 'عميل نشط'),
        ('inactive', 'غير نشط'),
        ('suspended', 'معلق'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="اسم العميل")
    client_type = models.ForeignKey(
        ClientType, 
        on_delete=models.PROTECT,
        related_name='clients',
        verbose_name="نوع العميل"
    )
    
    # Contact Information
    contact_person = models.CharField(max_length=200, blank=True, null=True, verbose_name="الشخص المسؤول")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="الهاتف")
    phone2 = models.CharField(max_length=20, blank=True, null=True, verbose_name="هاتف إضافي")
    
    # Classification
    category = models.CharField(
        max_length=20, 
        choices=CLIENT_CATEGORY_CHOICES, 
        blank=True, 
        null=True,
        verbose_name="الفئة"
    )
    status = models.CharField(
        max_length=20,
        choices=CLIENT_STATUS_CHOICES,
        default='potential',
        verbose_name="الحالة"
    )
    
    # Dynamic fields data stored as JSON
    # Example: {"address": "123 Main St", "city": "Cairo", "website_link": "https://example.com"}
    custom_data = models.JSONField(default=dict, blank=True, verbose_name="البيانات المخصصة")
    
    # Additional Information
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    description = models.TextField(blank=True, null=True, verbose_name="وصف")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_clients',
        verbose_name="أنشأه"
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        verbose_name="مسند إلى"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client_type']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def total_distributions(self):
        """Get total number of distributions for this client"""
        return self.distributions.count()
    
    @property
    def next_visit_date(self):
        """Get next scheduled visit date"""
        latest_distribution = self.distributions.order_by('-next_visit_date').first()
        return latest_distribution.next_visit_date if latest_distribution else None
    
    @property
    def upcoming_visit_days(self):
        """Get number of days until next visit"""
        if self.next_visit_date:
            delta = self.next_visit_date - timezone.now().date()
            return delta.days
        return None


class Product(models.Model):
    """
    Products/Services that can be distributed to clients
    """
    PRODUCT_TYPE_CHOICES = [
        ('product', 'منتج'),
        ('service', 'خدمة'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="اسم المنتج/الخدمة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPE_CHOICES,
        default='product',
        verbose_name="النوع"
    )
    
    # Base price (can be overridden per distribution)
    base_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="السعر الأساسي"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products',
        verbose_name="أنشأه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "منتج/خدمة"
        verbose_name_plural = "المنتجات والخدمات"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.base_price} {settings.CURRENCY if hasattr(settings, 'CURRENCY') else 'EGP'})"
    
    @property
    def total_distributed(self):
        """Get total quantity distributed"""
        from django.db.models import Sum
        total = self.distributions.aggregate(total=Sum('quantity'))['total']
        return total or 0


class Distribution(models.Model):
    """
    Distribution/Order records for clients
    """
    DISTRIBUTION_STATUS_CHOICES = [
        ('new', 'جديد'),
        ('waiting_visit', 'في انتظار الزيارة'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Client and Product
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='distributions',
        verbose_name="العميل"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='distributions',
        verbose_name="المنتج/الخدمة"
    )
    
    # Distribution Details
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الكمية")
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="السعر لكل وحدة"
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        verbose_name="المبلغ الإجمالي"
    )
    
    # Visit Management
    visit_interval_days = models.IntegerField(
        default=14,
        help_text="عدد الأيام بين كل زيارة",
        verbose_name="فترة الزيارة (بالأيام)"
    )
    last_visit_date = models.DateField(blank=True, null=True, verbose_name="تاريخ آخر زيارة")
    next_visit_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الزيارة الدورية")
    reminder_days_before = models.IntegerField(
        default=1,
        help_text="عدد الأيام قبل الموعد للتذكير",
        verbose_name="التذكير قبل الموعد بـ (أيام)"
    )
    
    # Status and Notes
    status = models.CharField(
        max_length=20,
        choices=DISTRIBUTION_STATUS_CHOICES,
        default='new',
        verbose_name="الحالة"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_distributions',
        verbose_name="أنشأه"
    )
    distributed_at = models.DateTimeField(default=timezone.now, verbose_name="تاريخ التوزيع")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "توزيع"
        verbose_name_plural = "التوزيعات"
        ordering = ['-distributed_at']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['next_visit_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.product.name} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total amount
        self.total_amount = self.quantity * self.price
        
        # Auto-calculate next visit date if last_visit_date is set
        if self.last_visit_date and not self.next_visit_date:
            self.next_visit_date = self.last_visit_date + timedelta(days=self.visit_interval_days)
        
        # If no last_visit_date but has next_visit_date, calculate it
        if not self.last_visit_date and self.next_visit_date:
            self.last_visit_date = self.next_visit_date - timedelta(days=self.visit_interval_days)
        
        # If neither is set, use today as last visit and calculate next
        if not self.last_visit_date and not self.next_visit_date:
            self.last_visit_date = timezone.now().date()
            self.next_visit_date = self.last_visit_date + timedelta(days=self.visit_interval_days)
        
        super().save(*args, **kwargs)
    
    @property
    def days_until_visit(self):
        """Get number of days until next visit"""
        if self.next_visit_date:
            delta = self.next_visit_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def is_visit_due(self):
        """Check if visit is due (within 3 days or overdue)"""
        if self.days_until_visit is not None:
            return self.days_until_visit <= 3
        return False
    
    @property
    def is_overdue(self):
        """Check if visit is overdue"""
        if self.days_until_visit is not None:
            return self.days_until_visit < 0
        return False
