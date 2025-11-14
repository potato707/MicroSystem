"""
Tenant Management URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .tenant_views import (
    TenantViewSet,
    ModuleDefinitionViewSet,
    get_tenant_config_by_subdomain,
    get_tenant_config_by_domain,
    check_module_access,
    tenant_statistics
)
from .tenant_creator_view import tenant_creator_view, tenant_management_view, dns_setup_guide_view

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'modules', ModuleDefinitionViewSet, basename='module')

urlpatterns = [
    # Tenant Creator - Custom page for easy tenant creation
    path('create-tenant/', tenant_creator_view, name='create-tenant'),
    
    # Tenant Management - View, edit, and delete tenants
    path('manage-tenants/', tenant_management_view, name='manage-tenants'),
    
    # DNS Setup Guide - Public guide for setting up custom domains
    path('dns-setup-guide/', dns_setup_guide_view, name='dns-setup-guide'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # Public tenant config endpoints
    path('public/tenant-config/<str:subdomain>/', 
         get_tenant_config_by_subdomain, 
         name='tenant-config-by-subdomain'),
    path('public/tenant-config/', 
         get_tenant_config_by_domain, 
         name='tenant-config-by-domain'),
    
    # Utility endpoints
    path('tenants/check-module-access/', 
         check_module_access, 
         name='check-module-access'),
    path('tenants/statistics/', 
         tenant_statistics, 
         name='tenant-statistics'),
]
