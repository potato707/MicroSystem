from django.contrib import admin
from .models import ProductCategory, ProductUnit, CategoryUnit, AdvancedProduct, ProductUnitStock


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active', 'products_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by when creating
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'is_countable', 'is_active', 'products_count', 'created_at']
    list_filter = ['is_countable', 'is_active', 'created_at']
    search_fields = ['name', 'short_name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CategoryUnit)
class CategoryUnitAdmin(admin.ModelAdmin):
    list_display = ['category', 'unit', 'default_pieces_per_unit', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'category', 'created_at']
    search_fields = ['category__name', 'unit__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdvancedProduct)
class AdvancedProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'base_price', 'total_stock_pieces', 'is_low_stock', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'total_stock', 'is_low_stock', 'units_count']
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ProductUnitStock)
class ProductUnitStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'unit', 'quantity_in_stock', 'pieces_per_unit', 'total_pieces', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'unit', 'created_at']
    search_fields = ['product__name', 'unit__name']
    readonly_fields = ['created_at', 'updated_at', 'total_pieces', 'is_low_stock']
