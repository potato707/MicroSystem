import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.core.validators import MinValueValidator


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


class SimpleProduct(models.Model):
    """
    Simple Products/Services for distributions (Legacy - kept for backward compatibility)
    For advanced product management, use DynamicProduct from product_models
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
        related_name='created_simple_products',
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
        SimpleProduct,
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


class ClientInventory(models.Model):
    """
    Track product inventory at each client location
    Shows what products and quantities are currently at the client
    """
    INVENTORY_STATUS_CHOICES = [
        ('low', 'ناقص مخزون'),
        ('warning', 'على الحد'),
        ('good', 'كافي'),
        ('excellent', 'ممتاز'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Client and Product
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='inventory_items',
        verbose_name="العميل"
    )
    product = models.ForeignKey(
        SimpleProduct,
        on_delete=models.PROTECT,
        related_name='client_inventory',
        verbose_name="المنتج"
    )
    
    # Inventory Details
    current_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="الكمية الحالية"
    )
    minimum_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="الحد الأدنى للكمية",
        help_text="عند الوصول لهذه الكمية، يظهر تحذير"
    )
    maximum_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=100,
        verbose_name="الحد الأقصى للكمية",
        help_text="السعة التخزينية القصوى"
    )
    
    # Expiry tracking (optional for products with expiration dates)
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ انتهاء الصلاحية"
    )
    
    # Location within client site (optional)
    location = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="موقع التخزين",
        help_text="مثل: مخزن رئيسي، ثلاجة، رف 3"
    )
    
    # Notes
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    
    # Last update tracking
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_updates',
        verbose_name="آخر تحديث بواسطة"
    )
    last_distribution = models.ForeignKey(
        Distribution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_updates',
        verbose_name="آخر توزيعة"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")
    
    class Meta:
        verbose_name = "مخزون عميل"
        verbose_name_plural = "مخزون العملاء"
        unique_together = ['client', 'product']  # One inventory record per client-product
        ordering = ['client', 'product']
        indexes = [
            models.Index(fields=['client', 'product']),
            models.Index(fields=['current_quantity']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.client.name} - {self.product.name} ({self.current_quantity})"
    
    @property
    def inventory_status(self):
        """Calculate inventory status based on current quantity"""
        if self.current_quantity <= 0:
            return 'low'
        elif self.current_quantity <= self.minimum_quantity:
            return 'warning'
        elif self.current_quantity >= self.maximum_quantity * Decimal('0.8'):  # 80% or more
            return 'excellent'
        else:
            return 'good'
    
    @property
    def inventory_status_display(self):
        """Get display name for inventory status"""
        status_dict = dict(self.INVENTORY_STATUS_CHOICES)
        return status_dict.get(self.inventory_status, 'غير معروف')
    
    @property
    def inventory_percentage(self):
        """Calculate percentage of inventory (0-100)"""
        if self.maximum_quantity > 0:
            percentage = (float(self.current_quantity) / float(self.maximum_quantity)) * 100
            return min(100, max(0, percentage))  # Clamp between 0 and 100
        return 0
    
    @property
    def is_low_stock(self):
        """Check if stock is low"""
        return self.current_quantity <= self.minimum_quantity
    
    @property
    def is_out_of_stock(self):
        """Check if out of stock"""
        return self.current_quantity <= 0
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None
    
    @property
    def is_expired(self):
        """Check if product is expired"""
        if self.days_until_expiry is not None:
            return self.days_until_expiry < 0
        return False
    
    @property
    def is_expiring_soon(self):
        """Check if product is expiring soon (within 7 days)"""
        if self.days_until_expiry is not None:
            return 0 <= self.days_until_expiry <= 7
        return False
    
    def add_stock(self, quantity, distribution=None, user=None):
        """Add quantity to inventory"""
        self.current_quantity += quantity
        self.last_distribution = distribution
        self.last_updated_by = user
        self.save()
    
    def reduce_stock(self, quantity, user=None):
        """Reduce quantity from inventory"""
        self.current_quantity = max(0, self.current_quantity - quantity)
        self.last_updated_by = user
        self.save()
    
    def set_stock(self, quantity, user=None):
        """Set inventory to specific quantity"""
        self.current_quantity = quantity
        self.last_updated_by = user
        self.save()
"""
Advanced Dynamic Product Management System
Models for Categories, Units, and Products with Custom Fields
"""
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class ProductCategory(models.Model):
    """
    Dynamic Product Categories with Custom Fields
    Each category can have custom fields that appear when adding products
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'نص'),
        ('number', 'رقم'),
        ('decimal', 'رقم عشري'),
        ('date', 'تاريخ'),
        ('select', 'قائمة منسدلة'),
        ('checkbox', 'خانة اختيار'),
        ('textarea', 'نص طويل'),
        ('email', 'بريد إلكتروني'),
        ('phone', 'هاتف'),
        ('url', 'رابط'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم التصنيف")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="أيقونة")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="اللون")
    
    # Custom fields configuration stored as JSON
    # Example: [
    #   {"name": "brand", "label": "الماركة", "type": "text", "required": true},
    #   {"name": "expiry_type", "label": "نوع الصلاحية", "type": "select", 
    #    "options": ["يومي", "شهري", "سنوي"], "required": true}
    # ]
    custom_fields = models.JSONField(default=list, blank=True, verbose_name="الحقول المخصصة")
    
    # Image upload
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name="صورة التصنيف"
    )
    
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_product_categories',
        verbose_name="أنشأه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "تصنيف المنتج"
        verbose_name_plural = "تصنيفات المنتجات"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def products_count(self):
        """Get number of products in this category"""
        return self.products.count()
    
    @property
    def units_count(self):
        """Get number of units linked to this category"""
        return self.category_units.count()


class ProductUnit(models.Model):
    """
    Product Units (e.g., Box, Carton, Piece, Meter, Liter)
    Each unit can have custom fields (dimensions, weight, etc.)
    """
    FIELD_TYPE_CHOICES = [
        ('text', 'نص'),
        ('number', 'رقم'),
        ('decimal', 'رقم عشري'),
        ('select', 'قائمة منسدلة'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الوحدة")
    short_name = models.CharField(max_length=20, blank=True, null=True, verbose_name="اسم مختصر")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    
    # Custom fields for this unit
    # Example: [
    #   {"name": "length", "label": "الطول", "type": "decimal", "unit": "cm"},
    #   {"name": "width", "label": "العرض", "type": "decimal", "unit": "cm"},
    #   {"name": "height", "label": "الارتفاع", "type": "decimal", "unit": "cm"},
    #   {"name": "weight", "label": "الوزن", "type": "decimal", "unit": "kg"}
    # ]
    custom_fields = models.JSONField(default=list, blank=True, verbose_name="الحقول المخصصة")
    
    # Whether this unit is countable (has pieces inside)
    is_countable = models.BooleanField(default=True, verbose_name="قابل للعد")
    
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_product_units',
        verbose_name="أنشأه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "وحدة المنتج"
        verbose_name_plural = "وحدات المنتجات"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.short_name if self.short_name else self.name
    
    @property
    def products_count(self):
        """Get number of products using this unit"""
        return self.product_units.count()


class CategoryUnit(models.Model):
    """
    Link between Category and Unit with pieces_per_unit
    Example: Pepsi category + Carton unit = 10 pieces per carton
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.CASCADE,
        related_name='category_units',
        verbose_name="التصنيف"
    )
    unit = models.ForeignKey(
        ProductUnit,
        on_delete=models.CASCADE,
        related_name='category_units',
        verbose_name="الوحدة"
    )
    
    # Default pieces per unit for this category-unit combination
    default_pieces_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="عدد الحبات الافتراضي في الوحدة"
    )
    
    # Whether this is the primary unit for this category
    is_primary = models.BooleanField(default=False, verbose_name="الوحدة الأساسية")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "ربط تصنيف-وحدة"
        verbose_name_plural = "روابط التصنيفات-الوحدات"
        unique_together = ['category', 'unit']
        ordering = ['category', 'unit']
        indexes = [
            models.Index(fields=['category', 'unit']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.category.name} - {self.unit.name} ({self.default_pieces_per_unit} حبة)"


class AdvancedProduct(models.Model):
    """
    Advanced Dynamic Products with category-specific custom fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(max_length=300, verbose_name="اسم المنتج")
    
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name="التصنيف",
        null=True
    )
    
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    
    # Custom data specific to category (filled from category.custom_fields)
    custom_data = models.JSONField(default=dict, blank=True, verbose_name="البيانات المخصصة")
    
    # Product image
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name="صورة المنتج"
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="السعر الأساسي"
    )
    
    # Total Stock in pieces (the single source of truth)
    total_stock_pieces = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="المخزون الكلي بالقطع",
        help_text="المخزون الكلي بالقطع - الوحدات تحسب منه تلقائياً"
    )
    
    minimum_stock_pieces = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="الحد الأدنى للمخزون بالقطع"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_advanced_products',
        verbose_name="أنشأه"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "منتج متقدم"
        verbose_name_plural = "المنتجات المتقدمة"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['name']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    @property
    def total_stock(self):
        """Return total stock in pieces"""
        return self.total_stock_pieces
    
    @property
    def is_low_stock(self):
        """Check if stock is below minimum"""
        return self.total_stock_pieces <= self.minimum_stock_pieces
    
    @property
    def units_count(self):
        """Get number of units for this product"""
        return self.product_units.count()


class ProductUnitStock(models.Model):
    """
    Display unit for product - calculates quantity from total_stock_pieces
    Does NOT store stock - only pieces_per_unit and unit-specific data
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    product = models.ForeignKey(
        AdvancedProduct,
        on_delete=models.CASCADE,
        related_name='product_units',
        verbose_name="المنتج"
    )
    unit = models.ForeignKey(
        ProductUnit,
        on_delete=models.PROTECT,
        related_name='product_units',
        verbose_name="الوحدة"
    )
    
    # Pieces per unit (can be customized per product, defaults from CategoryUnit)
    pieces_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="عدد القطع في الوحدة",
        help_text="كم قطعة في هذه الوحدة؟ مثال: 24 قطعة في الكرتون"
    )
    
    # Custom data specific to this unit (filled from unit.custom_fields)
    # Example: {"length": "30", "width": "20", "height": "15", "weight": "5.5"}
    custom_data = models.JSONField(default=dict, blank=True, verbose_name="بيانات الوحدة المخصصة")
    
    # Unit-specific pricing
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="سعر الوحدة"
    )
    
    # Whether this is the primary unit for this product
    is_primary = models.BooleanField(default=False, verbose_name="الوحدة الأساسية")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "وحدة عرض المنتج"
        verbose_name_plural = "وحدات عرض المنتجات"
        unique_together = ['product', 'unit']
        ordering = ['product', 'unit']
        indexes = [
            models.Index(fields=['product', 'unit']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.unit.name}"
    
    @property
    def quantity_in_stock(self):
        """Calculate quantity in this unit from total pieces"""
        if self.pieces_per_unit > 0:
            return self.product.total_stock_pieces / self.pieces_per_unit
        return 0
    
    @property
    def total_pieces(self):
        """Total pieces is always the product's total stock"""
        return self.product.total_stock_pieces
    
    @property
    def is_low_stock(self):
        """Check if product stock is below minimum"""
        return self.product.is_low_stock

