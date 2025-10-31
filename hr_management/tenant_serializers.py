"""
Tenant Management Serializers
"""
from rest_framework import serializers
from .tenant_models import Tenant, TenantModule, ModuleDefinition, TenantAPIKey


class ModuleDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for module definitions"""
    
    class Meta:
        model = ModuleDefinition
        fields = [
            'id', 'module_key', 'module_name', 'description', 
            'icon', 'is_core', 'sort_order'
        ]


class TenantModuleSerializer(serializers.ModelSerializer):
    """Serializer for tenant modules"""
    
    class Meta:
        model = TenantModule
        fields = [
            'id', 'module_key', 'module_name', 'is_enabled',
            'enabled_at', 'disabled_at'
        ]
        read_only_fields = ['id', 'enabled_at', 'disabled_at']


class TenantListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing tenants"""
    module_count = serializers.SerializerMethodField()
    enabled_modules_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'subdomain', 'full_domain', 'is_active',
            'logo', 'primary_color', 'secondary_color',
            'created_at', 'module_count', 'enabled_modules_count'
        ]
        read_only_fields = ['id', 'full_domain', 'created_at']
    
    def get_module_count(self, obj):
        return obj.modules.count()
    
    def get_enabled_modules_count(self, obj):
        return obj.modules.filter(is_enabled=True).count()


class TenantDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for tenant with all information"""
    modules = TenantModuleSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(
        source='created_by.username', 
        read_only=True
    )
    config = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'subdomain', 'custom_domain', 'full_domain',
            'logo', 'primary_color', 'secondary_color',
            'is_active', 'contact_email', 'contact_phone',
            'created_at', 'updated_at', 'created_by_username',
            'modules', 'config'
        ]
        read_only_fields = [
            'id', 'full_domain', 'created_at', 'updated_at', 
            'created_by_username'
        ]
    
    def get_config(self, obj):
        """Returns the tenant's configuration"""
        return obj.generate_config_json()


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new tenant"""
    module_keys = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        help_text="List of module keys to enable for this tenant"
    )
    
    # Admin user fields
    admin_username = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Username for the tenant admin"
    )
    admin_email = serializers.EmailField(
        write_only=True,
        required=True,
        help_text="Email for the tenant admin"
    )
    admin_password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        help_text="Password for the tenant admin (minimum 6 characters)"
    )
    admin_name = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Full name for the tenant admin"
    )
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'subdomain', 'custom_domain',
            'logo', 'primary_color', 'secondary_color',
            'contact_email', 'contact_phone',
            'module_keys',
            'admin_username', 'admin_email', 'admin_password', 'admin_name'
        ]
    
    def validate_subdomain(self, value):
        """Ensure subdomain is lowercase and valid"""
        value = value.lower().strip()
        if not value.replace('-', '').isalnum():
            raise serializers.ValidationError(
                "Subdomain can only contain letters, numbers, and hyphens"
            )
        return value
    
    def create(self, validated_data):
        """Custom create method to handle module assignment and admin user creation"""
        from .tenant_service import TenantService
        from django.contrib.auth import get_user_model
        from django.conf import settings
        from django.db import connections
        import os
        
        User = get_user_model()
        
        # Extract module keys and admin data
        module_keys = validated_data.pop('module_keys', [])
        admin_username = validated_data.pop('admin_username')
        admin_email = validated_data.pop('admin_email')
        admin_password = validated_data.pop('admin_password')
        admin_name = validated_data.pop('admin_name', admin_username)
        
        # Get the user from the request context
        request = self.context.get('request')
        created_by = request.user if request and request.user.is_authenticated else None
        
        # Store admin credentials for the signal
        # We'll pass them via the tenant_data and then attach to instance
        admin_credentials = {
            'username': admin_username,
            'email': admin_email,
            'password': admin_password,
            'name': admin_name
        }
        
        # Pass credentials through tenant_data
        validated_data['_admin_credentials'] = admin_credentials
        
        # Use the tenant service to create tenant with modules
        # This will trigger the signal which will handle DB setup and user creation
        tenant, _ = TenantService.create_tenant_with_modules(
            tenant_data=validated_data,
            module_keys=module_keys,
            created_by=created_by
        )
        
        return tenant


class TenantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating tenant information"""
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'custom_domain', 'logo', 
            'primary_color', 'secondary_color',
            'contact_email', 'contact_phone', 'is_active'
        ]
    
    def update(self, instance, validated_data):
        """Custom update to regenerate config after changes"""
        from .tenant_service import TenantService
        
        # Update tenant basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Regenerate config.json
        TenantService.update_tenant_config(instance)
        
        return instance


class TenantModuleUpdateSerializer(serializers.Serializer):
    """Serializer for updating tenant modules"""
    module_key = serializers.CharField()
    is_enabled = serializers.BooleanField()
    
    def validate_module_key(self, value):
        """Ensure module key exists"""
        if not ModuleDefinition.objects.filter(module_key=value).exists():
            raise serializers.ValidationError(f"Module '{value}' does not exist")
        return value
    
    def update_module(self, tenant):
        """Update the module for the tenant"""
        from django.utils import timezone
        from .tenant_service import TenantService
        
        module_key = self.validated_data['module_key']
        is_enabled = self.validated_data['is_enabled']
        
        # Get or create the module
        module_def = ModuleDefinition.objects.get(module_key=module_key)
        tenant_module, created = TenantModule.objects.get_or_create(
            tenant=tenant,
            module_key=module_key,
            defaults={
                'module_name': module_def.module_name,
                'is_enabled': is_enabled
            }
        )
        
        # Update if not created
        if not created and tenant_module.is_enabled != is_enabled:
            tenant_module.is_enabled = is_enabled
            if is_enabled:
                tenant_module.enabled_at = timezone.now()
            else:
                tenant_module.disabled_at = timezone.now()
            tenant_module.save()
        
        # Regenerate config
        TenantService.update_tenant_config(tenant)
        
        return tenant_module


class TenantConfigSerializer(serializers.Serializer):
    """Serializer for tenant configuration (read-only)"""
    name = serializers.CharField()
    domain = serializers.CharField()
    subdomain = serializers.CharField()
    modules = serializers.DictField()
    theme = serializers.DictField()
    logo_url = serializers.CharField(allow_null=True)
    contact = serializers.DictField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
