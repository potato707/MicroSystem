from django.contrib import admin
from .models import ClientType, Client, SimpleProduct, Distribution


@admin.register(ClientType)
class ClientTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'clients_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'clients_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon', 'color')
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'description': 'Define custom fields as JSON array'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'clients_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'client_type', 'status', 'category', 'contact_person', 'phone', 'created_at']
    list_filter = ['status', 'category', 'client_type', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone', 'notes']
    readonly_fields = ['created_at', 'updated_at', 'total_distributions', 'next_visit_date']
    raw_id_fields = ['client_type', 'created_by', 'assigned_to']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'client_type', 'status', 'category')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'email', 'phone', 'phone2')
        }),
        ('Custom Data', {
            'fields': ('custom_data',),
            'description': 'Custom fields based on client type'
        }),
        ('Additional Information', {
            'fields': ('notes', 'description')
        }),
        ('Assignment', {
            'fields': ('assigned_to',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'total_distributions', 'next_visit_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SimpleProduct)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_type', 'base_price', 'is_active', 'created_at']
    list_filter = ['product_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'total_distributed']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'product_type')
        }),
        ('Pricing', {
            'fields': ('base_price',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'total_distributed'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Distribution)
class DistributionAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'product', 'quantity', 'price', 'total_amount',
        'next_visit_date', 'days_until_visit', 'status', 'distributed_at'
    ]
    list_filter = ['status', 'distributed_at', 'next_visit_date']
    search_fields = ['client__name', 'product__name', 'notes']
    readonly_fields = ['total_amount', 'created_at', 'updated_at', 'days_until_visit', 'is_visit_due', 'is_overdue']
    raw_id_fields = ['client', 'product', 'created_by']
    date_hierarchy = 'distributed_at'
    
    fieldsets = (
        ('Distribution Details', {
            'fields': ('client', 'product', 'quantity', 'price', 'total_amount')
        }),
        ('Visit Schedule', {
            'fields': ('visit_interval_days', 'last_visit_date', 'next_visit_date', 'days_until_visit', 'is_visit_due', 'is_overdue')
        }),
        ('Status', {
            'fields': ('status', 'notes')
        }),
        ('Metadata', {
            'fields': ('created_by', 'distributed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
