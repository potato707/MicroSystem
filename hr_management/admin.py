from django.contrib import admin
from django import forms
from .models import *
from .tenant_models import Tenant, TenantModule, ModuleDefinition, TenantAPIKey

class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0
    fields = ['title', 'status', 'priority', 'estimated_minutes', 'order']
    readonly_fields = ['time_spent', 'is_paused']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'department', 'status', 'hire_date']
    list_filter = ['status', 'department', 'hire_date', 'complaint_categories']
    search_fields = ['name', 'english_name']
    ordering = ['name']
    filter_horizontal = ['complaint_categories']  # Nice UI for many-to-many fields

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'document_type', 'title', 'upload_date']
    list_filter = ['document_type', 'upload_date']
    search_fields = ['employee__name', 'title']

@admin.register(EmployeeNote)
class EmployeeNoteAdmin(admin.ModelAdmin):
    list_display = ['employee', 'created_by', 'created_date']
    list_filter = ['created_date']
    search_fields = ['employee__name', 'note']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'status', 'priority', 'date', 'created_at']
    list_filter = ['status', 'priority', 'date', 'assigned_by_manager']
    search_fields = ['title', 'employee__name', 'description']
    ordering = ['-date', 'priority']
    readonly_fields = ['time_spent', 'is_overdue', 'is_paused']
    inlines = [SubtaskInline]

@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent_task', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['title', 'parent_task__title', 'parent_task__employee__name']
    ordering = ['parent_task', 'order', 'created_at']
    readonly_fields = ['time_spent', 'is_paused']


# Team Admin
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_leader', 'is_active', 'member_count', 'created_at']
    list_filter = ['is_active', 'created_at', 'complaint_categories']
    search_fields = ['name', 'description', 'team_leader__name']
    ordering = ['name']
    filter_horizontal = ['complaint_categories']  # Nice UI for many-to-many fields
    readonly_fields = ['member_count', 'active_tasks_count']


# Client Complaint System Admin
@admin.register(ComplaintCategory)
class ComplaintCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']

class ClientComplaintAttachmentInline(admin.TabularInline):
    model = ClientComplaintAttachment
    extra = 0
    fields = ['file', 'file_name', 'file_size', 'uploaded_at']
    readonly_fields = ['uploaded_at', 'file_size']

class ClientComplaintCommentInline(admin.TabularInline):
    model = ClientComplaintComment
    extra = 0
    fields = ['comment', 'created_by', 'is_internal', 'created_at']
    readonly_fields = ['created_at']

@admin.register(ClientComplaint)
class ClientComplaintAdmin(admin.ModelAdmin):
    list_display = ['client_name', 'title', 'category', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority', 'category', 'created_at']
    search_fields = ['client_name', 'client_email', 'title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ClientComplaintAttachmentInline, ClientComplaintCommentInline]
    
    fieldsets = (
        ('Client Information', {
            'fields': ('client_name', 'client_email', 'project_name', 'project_code')
        }),
        ('Complaint Details', {
            'fields': ('category', 'title', 'description', 'priority')
        }),
        ('Status & Review', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'review_notes', 'rejection_reason')
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolved_at', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ClientComplaintAssignment)
class ClientComplaintAssignmentAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'team', 'assigned_by', 'assigned_at']
    list_filter = ['assigned_at', 'team']
    search_fields = ['complaint__title', 'team__name', 'assigned_by__username']
    ordering = ['-assigned_at']

@admin.register(ClientComplaintTask)
class ClientComplaintTaskAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'task', 'team', 'created_by', 'created_at']
    list_filter = ['created_at', 'team']
    search_fields = ['complaint__title', 'task__title', 'notes']
    ordering = ['-created_at']

@admin.register(ClientComplaintComment)
class ClientComplaintCommentAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['complaint__title', 'comment', 'author__username']
    ordering = ['-created_at']

@admin.register(ClientComplaintStatusHistory)
class ClientComplaintStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['complaint', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['old_status', 'new_status', 'changed_at']
    search_fields = ['complaint__complaint_id', 'changed_by__username', 'notes']
    ordering = ['-changed_at']


# Tenant Management Admin
class TenantModuleInline(admin.TabularInline):
    model = TenantModule
    extra = 0
    fields = ['module_key', 'module_name', 'is_enabled', 'enabled_at']
    readonly_fields = ['module_key', 'module_name', 'enabled_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        # Don't allow manual addition - modules are auto-created
        return False


class TenantAdminForm(forms.ModelForm):
    """Custom form for tenant creation with admin user fields"""
    
    # Admin user fields (only shown when creating new tenant)
    admin_username = forms.CharField(
        max_length=150,
        required=False,
        help_text="Username for the tenant admin (required for new tenants)"
    )
    admin_email = forms.EmailField(
        required=False,
        help_text="Email for the tenant admin"
    )
    admin_password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        min_length=6,
        help_text="Password for the tenant admin (minimum 6 characters)"
    )
    admin_name = forms.CharField(
        max_length=200,
        required=False,
        help_text="Full name for the tenant admin"
    )
    
    class Meta:
        model = Tenant
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only require admin fields for new tenants
        if not self.instance.pk:
            self.fields['admin_username'].required = True
            self.fields['admin_email'].required = True
            self.fields['admin_password'].required = True
    
    def save(self, commit=True):
        # Check if this is a new tenant BEFORE saving
        is_new_tenant = self.instance.pk is None
        
        print(f"\n{'*'*60}", flush=True)
        print(f"FORM SAVE CALLED - is_new: {is_new_tenant}, subdomain: {self.instance.subdomain}", flush=True)
        
        # If new tenant, store admin credentials in the instance temporarily
        if is_new_tenant:
            admin_username = self.cleaned_data.get('admin_username')
            admin_email = self.cleaned_data.get('admin_email')
            admin_password = self.cleaned_data.get('admin_password')
            admin_name = self.cleaned_data.get('admin_name', admin_username)
            
            print(f"Admin credentials from form:", flush=True)
            print(f"  - Username: {admin_username}", flush=True)
            print(f"  - Email: {admin_email}", flush=True)
            print(f"  - Has password: {bool(admin_password)}", flush=True)
            print(f"  - Name: {admin_name}", flush=True)
            
            if admin_username and admin_email and admin_password:
                # Store credentials in instance for signal to pick up
                self.instance._admin_credentials = {
                    'username': admin_username,
                    'email': admin_email,
                    'password': admin_password,
                    'name': admin_name
                }
                print(f"✅ Credentials stored in instance._admin_credentials", flush=True)
            else:
                print(f"❌ Incomplete credentials - NOT storing", flush=True)
        
        print(f"{'*'*60}\n", flush=True)
        
        # Save the tenant - post_save signal will handle database initialization
        tenant = super().save(commit=commit)
        return tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    form = TenantAdminForm
    list_display = ['name', 'subdomain', 'is_active', 'created_at', 'created_by']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'subdomain', 'custom_domain']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'full_domain']
    inlines = [TenantModuleInline]
    
    def get_fieldsets(self, request, obj=None):
        """Dynamic fieldsets based on whether creating new or editing existing tenant"""
        base_fieldsets = [
            ('Basic Information', {
                'fields': ('name', 'subdomain', 'custom_domain', 'full_domain', 'is_active')
            }),
            ('Branding', {
                'fields': ('logo', 'primary_color', 'secondary_color')
            }),
            ('Contact Information', {
                'fields': ('contact_email', 'contact_phone')
            }),
        ]
        
        # Add admin user fields only for new tenants
        if obj is None:
            base_fieldsets.insert(1, (
                'Admin User (Required for New Tenant)', {
                    'fields': ('admin_username', 'admin_email', 'admin_password', 'admin_name'),
                    'description': 'These credentials will be used to create the initial admin user for this tenant.'
                }
            ))
        
        # Add metadata fieldset
        base_fieldsets.append((
            'Metadata', {
                'fields': ('created_by', 'created_at', 'updated_at'),
                'classes': ('collapse',)
            }
        ))
        
        return base_fieldsets

@admin.register(TenantModule)
class TenantModuleAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'module_name', 'module_key', 'is_enabled']
    list_filter = ['is_enabled', 'module_key']
    search_fields = ['tenant__name', 'module_key', 'module_name']
    ordering = ['tenant', 'module_key']

@admin.register(ModuleDefinition)
class ModuleDefinitionAdmin(admin.ModelAdmin):
    list_display = ['module_name', 'module_key', 'is_core', 'sort_order']
    list_filter = ['is_core']
    search_fields = ['module_key', 'module_name', 'description']
    ordering = ['sort_order', 'module_name']

@admin.register(TenantAPIKey)
class TenantAPIKeyAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'name', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['tenant__name', 'name', 'key']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'last_used']

