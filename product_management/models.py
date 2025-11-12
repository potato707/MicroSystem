import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from django.core.validators import MinValueValidator


class ProductCategory(models.Model):
    FIELD_TYPE_CHOICES = [
        ('text', 'نص'), ('number', 'رقم'), ('decimal', 'رقم عشري'),
        ('date', 'تاريخ'), ('select', 'قائمة منسدلة'), ('checkbox', 'خانة اختيار'),
        ('textarea', 'نص طويل'), ('email', 'بريد إلكتروني'), ('phone', 'هاتف'), ('url', 'رابط'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True, verbose_name="اسم التصنيف")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name="أيقونة")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="اللون")
    custom_fields = models.JSONField(default=list, blank=True, verbose_name="الحقول المخصصة")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="صورة التصنيف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='product_management_created_categories', verbose_name="أنشأه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "تصنيف المنتج"
        verbose_name_plural = "تصنيفات المنتجات"
        ordering = ['name']
        indexes = [models.Index(fields=['is_active']), models.Index(fields=['name'])]
    
    def __str__(self):
        return self.name
    
    @property
    def products_count(self):
        return self.products.count()
    
    @property
    def units_count(self):
        return self.category_units.count()


class ProductUnit(models.Model):
    FIELD_TYPE_CHOICES = [('text', 'نص'), ('number', 'رقم'), ('decimal', 'رقم عشري'), ('select', 'قائمة منسدلة')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name="اسم الوحدة")
    short_name = models.CharField(max_length=20, blank=True, null=True, verbose_name="اسم مختصر")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    custom_fields = models.JSONField(default=list, blank=True, verbose_name="الحقول المخصصة")
    is_countable = models.BooleanField(default=True, verbose_name="قابل للعد")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='product_management_created_units', verbose_name="أنشأه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "وحدة المنتج"
        verbose_name_plural = "وحدات المنتجات"
        ordering = ['name']
        indexes = [models.Index(fields=['is_active']), models.Index(fields=['name'])]
    
    def __str__(self):
        return self.short_name if self.short_name else self.name
    
    @property
    def products_count(self):
        return self.product_units.count()


class CategoryUnit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey('ProductCategory', on_delete=models.CASCADE, related_name='category_units', verbose_name="التصنيف")
    unit = models.ForeignKey('ProductUnit', on_delete=models.CASCADE, related_name='category_units', verbose_name="الوحدة")
    default_pieces_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=1,
                                                    validators=[MinValueValidator(Decimal('0.01'))],
                                                    verbose_name="عدد الحبات الافتراضي في الوحدة")
    is_primary = models.BooleanField(default=False, verbose_name="الوحدة الأساسية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "ربط تصنيف-وحدة"
        verbose_name_plural = "روابط التصنيفات-الوحدات"
        unique_together = ['category', 'unit']
        ordering = ['category', 'unit']
        indexes = [models.Index(fields=['category', 'unit']), models.Index(fields=['is_primary'])]
    
    def __str__(self):
        return f"{self.category.name} - {self.unit.name} ({self.default_pieces_per_unit} حبة)"


class AdvancedProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=300, verbose_name="اسم المنتج")
    category = models.ForeignKey('ProductCategory', on_delete=models.PROTECT, related_name='products', verbose_name="التصنيف", null=True)
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    custom_data = models.JSONField(default=dict, blank=True, verbose_name="البيانات المخصصة")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="صورة المنتج")
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                     validators=[MinValueValidator(Decimal('0'))], verbose_name="السعر الأساسي")
    total_stock_pieces = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                             validators=[MinValueValidator(Decimal('0'))],
                                             verbose_name="المخزون الكلي بالقطع")
    minimum_stock_pieces = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                               validators=[MinValueValidator(Decimal('0'))],
                                               verbose_name="الحد الأدنى للمخزون بالقطع")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                                    related_name='product_management_created_products', verbose_name="أنشأه")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "منتج متقدم"
        verbose_name_plural = "المنتجات المتقدمة"
        ordering = ['-created_at']
        indexes = [models.Index(fields=['category']), models.Index(fields=['name']), models.Index(fields=['-created_at'])]
    
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    @property
    def total_stock(self):
        return self.total_stock_pieces
    
    @property
    def is_low_stock(self):
        return self.total_stock_pieces <= self.minimum_stock_pieces
    
    @property
    def units_count(self):
        return self.product_units.count()


class ProductUnitStock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey('AdvancedProduct', on_delete=models.CASCADE, related_name='product_units', verbose_name="المنتج")
    unit = models.ForeignKey('ProductUnit', on_delete=models.PROTECT, related_name='product_units', verbose_name="الوحدة")
    pieces_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=1,
                                          validators=[MinValueValidator(Decimal('0.01'))],
                                          verbose_name="عدد القطع في الوحدة")
    quantity_in_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                            validators=[MinValueValidator(Decimal('0'))],
                                            verbose_name="الكمية بالوحدة")
    minimum_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                       validators=[MinValueValidator(Decimal('0'))],
                                       verbose_name="الحد الأدنى بالوحدة")
    custom_data = models.JSONField(default=dict, blank=True, verbose_name="بيانات الوحدة المخصصة")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                     validators=[MinValueValidator(Decimal('0'))], verbose_name="سعر الوحدة")
    is_primary = models.BooleanField(default=False, verbose_name="الوحدة الأساسية")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    class Meta:
        verbose_name = "وحدة عرض المنتج"
        verbose_name_plural = "وحدات عرض المنتجات"
        unique_together = ['product', 'unit']
        ordering = ['product', 'unit']
        indexes = [models.Index(fields=['product', 'unit']), models.Index(fields=['is_primary'])]
    
    def __str__(self):
        return f"{self.product.name} - {self.unit.name}"
    
    @property
    def total_pieces(self):
        return self.quantity_in_stock * self.pieces_per_unit
    
    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.minimum_stock
