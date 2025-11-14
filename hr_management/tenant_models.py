"""
Tenant/Client Management Models for Multi-Tenant SaaS System
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
import uuid
import json

User = get_user_model()


class Tenant(models.Model):
    """
    Represents a client/tenant in the SaaS system.
    Each tenant has their own configuration, modules, and branding.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Information
    name = models.CharField(max_length=200, verbose_name='Client Name', unique=True)
    subdomain = models.SlugField(
        max_length=100, 
        unique=True,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex='^[a-z0-9-]+$',
            message='Subdomain can only contain lowercase letters, numbers, and hyphens'
        )],
        verbose_name='Subdomain'
    )
    
    # Domain Configuration
    DOMAIN_TYPE_CHOICES = [
        ('subdomain', 'Subdomain'),
        ('custom', 'Custom Domain'),
    ]
    
    domain_type = models.CharField(
        max_length=20,
        choices=DOMAIN_TYPE_CHOICES,
        default='subdomain',
        verbose_name='Domain Type'
    )
    
    custom_domain = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        unique=True,
        verbose_name='Custom Domain',
        help_text='e.g., mycompany.com (only if domain_type is custom)'
    )
    
    # SSL Configuration
    ssl_enabled = models.BooleanField(
        default=False,
        verbose_name='SSL Enabled',
        help_text='Whether SSL certificate is installed for this domain'
    )
    ssl_issued_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='SSL Issued At',
        help_text='When the SSL certificate was issued'
    )
    
    # Branding
    logo = models.ImageField(
        upload_to='tenants/logos/', 
        blank=True, 
        null=True,
        verbose_name='Client Logo'
    )
    primary_color = models.CharField(
        max_length=7, 
        default='#3498db',
        validators=[RegexValidator(
            regex='^#[0-9A-Fa-f]{6}$',
            message='Enter a valid hex color code (e.g., #3498db)'
        )],
        verbose_name='Primary Color'
    )
    secondary_color = models.CharField(
        max_length=7, 
        default='#2ecc71',
        validators=[RegexValidator(
            regex='^#[0-9A-Fa-f]{6}$',
            message='Enter a valid hex color code (e.g., #2ecc71)'
        )],
        verbose_name='Secondary Color'
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Active')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_tenants'
    )
    
    # Contact Information
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.subdomain})"
    
    @property
    def full_domain(self):
        """Returns the full domain for this tenant"""
        if self.domain_type == 'custom' and self.custom_domain:
            return self.custom_domain
        # Default to subdomain
        from django.conf import settings
        base_domain = getattr(settings, 'BASE_DOMAIN', 'localhost:8000')
        return f"{self.subdomain}.{base_domain}"
    
    @property
    def folder_path(self):
        """Returns the filesystem path for tenant's frontend folder"""
        from django.conf import settings
        import os
        return os.path.join(settings.BASE_DIR, 'tenants', self.subdomain)
    
    @property
    def config_path(self):
        """Returns the path to tenant's config.json"""
        import os
        return os.path.join(self.folder_path, 'config.json')
    
    def get_enabled_modules(self):
        """Returns a dictionary of all modules and their status"""
        modules = {}
        for module in self.modules.all():
            modules[module.module_key] = module.is_enabled
        return modules
    
    def generate_config_json(self):
        """Generates the config.json content for this tenant"""
        config = {
            "name": self.name,
            "domain": self.full_domain,
            "subdomain": self.subdomain,
            "modules": self.get_enabled_modules(),
            "theme": {
                "primary": self.primary_color,
                "secondary": self.secondary_color
            },
            "logo_url": self.logo.url if self.logo else None,
            "contact": {
                "email": self.contact_email,
                "phone": self.contact_phone
            },
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        return config


class TenantModule(models.Model):
    """
    Represents a module/feature that can be enabled or disabled for a tenant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name='modules'
    )
    
    # Module Configuration
    module_key = models.CharField(
        max_length=50,
        verbose_name='Module Key',
        help_text='e.g., employees, attendance, wallet, tasks'
    )
    module_name = models.CharField(
        max_length=100,
        verbose_name='Module Display Name'
    )
    is_enabled = models.BooleanField(default=False, verbose_name='Enabled')
    
    # Timestamps
    enabled_at = models.DateTimeField(null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Tenant Module'
        verbose_name_plural = 'Tenant Modules'
        unique_together = [['tenant', 'module_key']]
        ordering = ['module_key']
    
    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{status} {self.module_name} - {self.tenant.name}"


class ModuleDefinition(models.Model):
    """
    Global definition of available modules in the system.
    This defines what modules can be assigned to tenants.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    module_key = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='Module Key'
    )
    module_name = models.CharField(
        max_length=100,
        verbose_name='Display Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Icon Class/Name'
    )
    is_core = models.BooleanField(
        default=False,
        verbose_name='Core Module',
        help_text='Core modules are always enabled and cannot be disabled'
    )
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Module Definition'
        verbose_name_plural = 'Module Definitions'
        ordering = ['sort_order', 'module_name']
    
    def __str__(self):
        return f"{self.module_name} ({self.module_key})"


class TenantAPIKey(models.Model):
    """
    API keys for tenant-specific access (optional, for future use)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='api_keys'
    )
    key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, help_text='Key name/description')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Tenant API Key'
        verbose_name_plural = 'Tenant API Keys'
    
    def __str__(self):
        return f"{self.tenant.name} - {self.name}"
