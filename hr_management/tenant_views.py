"""
Tenant Management API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os
import json

from .tenant_models import Tenant, TenantModule, ModuleDefinition
from .tenant_serializers import (
    TenantListSerializer,
    TenantDetailSerializer,
    TenantCreateSerializer,
    TenantUpdateSerializer,
    TenantModuleSerializer,
    TenantModuleUpdateSerializer,
    ModuleDefinitionSerializer,
    TenantConfigSerializer
)
from .tenant_service import TenantService


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants
    Requires admin privileges for most actions, but list is public
    """
    queryset = Tenant.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_permissions(self):
        """
        Allow public access to list and create actions
        Require admin for all other actions
        """
        if self.action in ['list', 'create']:
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]
    
    def get_queryset(self):
        """
        For list action, only return active tenants
        For admin actions, return all tenants
        """
        if self.action == 'list':
            return Tenant.objects.filter(is_active=True).order_by('name')
        return Tenant.objects.all()
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """Exempt create action from CSRF protection"""
        return super().dispatch(*args, **kwargs)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return TenantListSerializer
        elif self.action == 'create':
            return TenantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TenantUpdateSerializer
        return TenantDetailSerializer
    
    def perform_create(self, serializer):
        """Create tenant with current user as creator"""
        serializer.save()
    
    @action(detail=True, methods=['get'])
    def config(self, request, pk=None):
        """
        Get the tenant's configuration
        GET /api/tenants/{id}/config/
        """
        tenant = self.get_object()
        config_data = tenant.generate_config_json()
        serializer = TenantConfigSerializer(config_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """
        Get all modules for a tenant
        GET /api/tenants/{id}/modules/
        """
        tenant = self.get_object()
        modules = tenant.modules.all()
        serializer = TenantModuleSerializer(modules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_module(self, request, pk=None):
        """
        Update a specific module for a tenant
        POST /api/tenants/{id}/update_module/
        Body: {"module_key": "employees", "is_enabled": true}
        """
        tenant = self.get_object()
        serializer = TenantModuleUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            tenant_module = serializer.update_module(tenant)
            return Response(
                TenantModuleSerializer(tenant_module).data,
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def regenerate_config(self, request, pk=None):
        """
        Regenerate the config.json file for a tenant
        POST /api/tenants/{id}/regenerate_config/
        """
        tenant = self.get_object()
        success = TenantService.update_tenant_config(tenant)
        
        if success:
            return Response({
                'message': 'Configuration regenerated successfully',
                'config_path': tenant.config_path
            })
        
        return Response(
            {'error': 'Failed to regenerate configuration'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=True, methods=['post'])
    def copy_frontend(self, request, pk=None):
        """
        Copy frontend template to tenant folder
        POST /api/tenants/{id}/copy_frontend/
        """
        tenant = self.get_object()
        success = TenantService.copy_frontend_template(tenant)
        
        if success:
            return Response({
                'message': 'Frontend template copied successfully',
                'folder_path': tenant.folder_path
            })
        
        return Response(
            {'error': 'Failed to copy frontend template'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    @action(detail=False, methods=['post'])
    def initialize_modules(self, request):
        """
        Initialize default module definitions
        POST /api/tenants/initialize_modules/
        """
        count = TenantService.initialize_module_definitions()
        return Response({
            'message': f'Initialized {count} module definitions',
            'count': count
        })


class ModuleDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing available module definitions
    Read-only, available to authenticated users
    """
    queryset = ModuleDefinition.objects.all()
    serializer_class = ModuleDefinitionSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([])  # Public endpoint
def get_tenant_config_by_subdomain(request, subdomain):
    """
    Public endpoint to get tenant configuration by subdomain
    This is used by the frontend to load tenant-specific settings
    
    GET /api/public/tenant-config/{subdomain}/
    """
    try:
        tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
        config_data = tenant.generate_config_json()
        serializer = TenantConfigSerializer(config_data)
        return Response(serializer.data)
    
    except Tenant.DoesNotExist:
        return Response(
            {'error': 'Tenant not found or inactive'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([])  # Public endpoint
def get_tenant_config_by_domain(request):
    """
    Public endpoint to get tenant configuration by domain from request
    Useful for subdomain-based routing
    
    GET /api/public/tenant-config/
    """
    # Get domain from request
    host = request.get_host()
    
    # Try to find tenant by custom domain or subdomain
    try:
        # Try custom domain first
        tenant = Tenant.objects.filter(
            custom_domain=host,
            is_active=True
        ).first()
        
        # If not found, try to extract subdomain
        if not tenant:
            subdomain = host.split('.')[0]
            tenant = Tenant.objects.get(
                subdomain=subdomain,
                is_active=True
            )
        
        if tenant:
            config_data = tenant.generate_config_json()
            serializer = TenantConfigSerializer(config_data)
            return Response(serializer.data)
    
    except (Tenant.DoesNotExist, IndexError):
        pass
    
    return Response(
        {'error': 'Tenant not found for this domain'},
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def check_module_access(request):
    """
    Check if a tenant has access to a specific module
    
    POST /api/tenants/check-module-access/
    Body: {"subdomain": "client1", "module_key": "employees"}
    """
    subdomain = request.data.get('subdomain')
    module_key = request.data.get('module_key')
    
    if not subdomain or not module_key:
        return Response(
            {'error': 'subdomain and module_key are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
        tenant_module = TenantModule.objects.get(
            tenant=tenant,
            module_key=module_key
        )
        
        return Response({
            'has_access': tenant_module.is_enabled,
            'module_name': tenant_module.module_name,
            'tenant_name': tenant.name
        })
    
    except Tenant.DoesNotExist:
        return Response(
            {'error': 'Tenant not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    except TenantModule.DoesNotExist:
        return Response(
            {'error': 'Module not found for this tenant'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def tenant_statistics(request):
    """
    Get statistics about tenants (admin only)
    
    GET /api/tenants/statistics/
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return Response(
            {'error': 'Admin access required'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()
    inactive_tenants = total_tenants - active_tenants
    
    # Module usage statistics
    module_stats = {}
    for module in ModuleDefinition.objects.all():
        enabled_count = TenantModule.objects.filter(
            module_key=module.module_key,
            is_enabled=True
        ).count()
        module_stats[module.module_key] = {
            'name': module.module_name,
            'enabled_count': enabled_count,
            'total_tenants': total_tenants,
            'percentage': round((enabled_count / total_tenants * 100), 2) if total_tenants > 0 else 0
        }
    
    return Response({
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'inactive_tenants': inactive_tenants,
        'module_statistics': module_stats
    })
