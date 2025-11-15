"""
Tenant Management API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
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


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF check for API calls
    """
    def enforce_csrf(self, request):
        return  # Skip CSRF check for API


class TenantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing tenants
    Requires admin privileges for most actions, but list is public
    """
    queryset = Tenant.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    authentication_classes = [JWTAuthentication, CsrfExemptSessionAuthentication, BasicAuthentication]
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
        For list action:
        - If user is authenticated and staff: return ALL tenants (active + inactive)
        - If user is not authenticated: return only active tenants
        For admin actions: return all tenants
        """
        if self.action == 'list':
            # If user is staff, show all tenants including inactive ones
            if self.request.user.is_authenticated and self.request.user.is_staff:
                return Tenant.objects.all().order_by('name')
            # For public/non-staff users, show only active tenants
            return Tenant.objects.filter(is_active=True).order_by('name')
        return Tenant.objects.all()
    
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
        tenant = serializer.save()
        
        # Debug: Print tenant info
        print(f"🔍 Tenant created: {tenant.name}")
        print(f"🔍 Domain type: {tenant.domain_type}")
        print(f"🔍 Custom domain: {tenant.custom_domain}")
        
        # If tenant has custom domain, setup SSL automatically
        if tenant.domain_type == 'custom' and tenant.custom_domain:
            print(f"✅ Condition met! Starting SSL setup for {tenant.custom_domain}")
            try:
                # Import here to avoid circular imports
                from .ssl_tasks import setup_ssl_certificate
                print(f"✅ SSL task imported successfully")
                
                # Trigger SSL setup as background task
                # This will wait for DNS propagation and then setup SSL
                result = setup_ssl_certificate.apply_async(
                    args=[str(tenant.id)],
                    kwargs={'email': 'admin@localhost'},
                    countdown=300  # Wait 5 minutes before starting
                )
                print(f"✅ SSL task scheduled! Task ID: {result.id}")

                
                print(f"✅ SSL task scheduled! Task ID: {result.id}")
                
                # Log the trigger
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f'🔒 SSL setup scheduled for {tenant.custom_domain} (Task ID: {result.id})')
            
            except Exception as e:
                # Don't fail tenant creation if SSL scheduling fails
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'❌ Failed to schedule SSL setup for {tenant.custom_domain}: {e}')
                print(f"❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"⚠️  SSL not scheduled - domain_type: {tenant.domain_type}, custom_domain: {tenant.custom_domain}")
        
        return tenant
    
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
    
    @action(detail=True, methods=['get'])
    def ssl_status(self, request, pk=None):
        """
        Check SSL status for a tenant
        GET /api/tenants/{id}/ssl_status/
        """
        tenant = self.get_object()
        
        if tenant.domain_type != 'custom' or not tenant.custom_domain:
            return Response({
                'ssl_enabled': False,
                'message': 'Tenant does not use custom domain'
            })
        
        return Response({
            'ssl_enabled': tenant.ssl_enabled,
            'ssl_issued_at': tenant.ssl_issued_at,
            'custom_domain': tenant.custom_domain,
            'https_url': f'https://{tenant.custom_domain}' if tenant.ssl_enabled else None
        })
    
    @action(detail=True, methods=['post'])
    def setup_ssl(self, request, pk=None):
        """
        Manually trigger SSL setup for a tenant
        POST /api/tenants/{id}/setup_ssl/
        Body (optional): {"email": "admin@example.com"}
        """
        tenant = self.get_object()
        
        if tenant.domain_type != 'custom' or not tenant.custom_domain:
            return Response(
                {'error': 'Tenant does not have a custom domain'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = request.data.get('email', 'admin@localhost')
        
        try:
            from .ssl_tasks import setup_ssl_certificate
            
            # Trigger SSL setup
            task = setup_ssl_certificate.apply_async(
                args=[str(tenant.id)],
                kwargs={'email': email},
                countdown=10  # Start in 10 seconds
            )
            
            return Response({
                'message': f'SSL setup initiated for {tenant.custom_domain}',
                'task_id': task.id,
                'domain': tenant.custom_domain
            })
        
        except Exception as e:
            return Response(
                {'error': f'Failed to initiate SSL setup: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def link_domain(self, request, pk=None):
        """
        Link a custom domain to tenant and setup SSL
        POST /api/tenants/{id}/link_domain/
        Body: {
            "custom_domain": "mycustomdomain.com",
            "email": "admin@example.com"  (optional)
        }
        
        Steps:
        1. Validates domain format
        2. Checks DNS is pointing to our server
        3. Updates tenant with custom_domain
        4. Triggers SSL automation
        """
        tenant = self.get_object()
        custom_domain = request.data.get('custom_domain', '').strip().lower()
        email = request.data.get('email', 'admin@localhost')
        
        # Validate domain format
        if not custom_domain:
            return Response(
                {'error': 'custom_domain is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not '.' in custom_domain or ' ' in custom_domain:
            return Response(
                {'error': 'Invalid domain format. Example: mycompany.com'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if domain is already used by another tenant
        existing = Tenant.objects.filter(custom_domain=custom_domain).exclude(id=tenant.id).first()
        if existing:
            return Response(
                {'error': f'Domain {custom_domain} is already linked to another tenant'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify DNS is pointing to our server
        from .ssl_tasks import verify_dns
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f'🔍 Verifying DNS for {custom_domain}...')
        
        if not verify_dns(custom_domain):
            return Response({
                'error': 'DNS verification failed',
                'message': f'Domain {custom_domain} is not pointing to our server. Please update your DNS records first.',
                'instructions': {
                    'step_1': f'Add an A record for {custom_domain}',
                    'step_2': 'Point it to our server IP',
                    'step_3': 'Wait 5-10 minutes for DNS propagation',
                    'step_4': 'Try again'
                },
                'dns_verified': False
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f'✅ DNS verified for {custom_domain}')
        
        # Update tenant
        tenant.custom_domain = custom_domain
        tenant.domain_type = 'custom'
        tenant.save()
        
        # Trigger SSL setup
        try:
            from .ssl_tasks import setup_ssl_certificate
            
            task = setup_ssl_certificate.apply_async(
                args=[str(tenant.id)],
                kwargs={'email': email},
                countdown=10  # Start in 10 seconds
            )
            
            logger.info(f'🔒 SSL setup scheduled for {custom_domain} (Task ID: {task.id})')
            
            return Response({
                'success': True,
                'message': f'Custom domain {custom_domain} linked successfully',
                'domain': custom_domain,
                'dns_verified': True,
                'ssl_status': 'pending',
                'ssl_task_id': task.id,
                'tenant': {
                    'id': str(tenant.id),
                    'name': tenant.name,
                    'subdomain': tenant.subdomain,
                    'custom_domain': tenant.custom_domain,
                    'domain_type': tenant.domain_type
                }
            })
        
        except Exception as e:
            logger.error(f'❌ Failed to schedule SSL: {e}')
            return Response(
                {'error': f'Domain linked but SSL setup failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def verify_domain(self, request, pk=None):
        """
        Verify DNS for a domain without linking it
        POST /api/tenants/{id}/verify_domain/
        Body: {"domain": "mycustomdomain.com"}
        
        Returns DNS verification status
        """
        domain = request.data.get('domain', '').strip().lower()
        
        if not domain:
            return Response(
                {'error': 'domain is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .ssl_tasks import verify_dns
        import socket
        import requests
        
        try:
            # Get domain IP
            domain_ip = socket.gethostbyname(domain)
            
            # Get server IP
            server_ip = requests.get('https://api.ipify.org', timeout=5).text
            
            dns_verified = (domain_ip == server_ip)
            
            return Response({
                'domain': domain,
                'domain_ip': domain_ip,
                'server_ip': server_ip,
                'dns_verified': dns_verified,
                'message': 'DNS is correctly configured' if dns_verified else 'DNS is not pointing to our server',
                'instructions': {
                    'step_1': f'Add an A record for {domain}',
                    'step_2': f'Point it to: {server_ip}',
                    'step_3': 'Wait 5-10 minutes for DNS propagation',
                    'current_ip': domain_ip
                } if not dns_verified else None
            })
        
        except socket.gaierror:
            return Response({
                'domain': domain,
                'dns_verified': False,
                'error': 'DNS lookup failed - domain not found',
                'message': 'Domain does not have DNS records yet'
            })
        except Exception as e:
            return Response(
                {'error': f'Verification failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def unlink_domain(self, request, pk=None):
        """
        Remove custom domain from tenant
        POST /api/tenants/{id}/unlink_domain/
        
        Reverts tenant back to subdomain-only access
        """
        tenant = self.get_object()
        
        if tenant.domain_type != 'custom':
            return Response(
                {'error': 'Tenant does not have a custom domain'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_domain = tenant.custom_domain
        
        # Revert to subdomain
        tenant.custom_domain = None
        tenant.domain_type = 'subdomain'
        tenant.ssl_enabled = False
        tenant.ssl_issued_at = None
        tenant.save()
        
        return Response({
            'success': True,
            'message': f'Custom domain {old_domain} unlinked successfully',
            'tenant': {
                'id': str(tenant.id),
                'name': tenant.name,
                'subdomain': tenant.subdomain,
                'domain_type': tenant.domain_type,
                'access_url': f'https://{tenant.subdomain}.client-radar.org'
            }
        })


class ModuleDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing available module definitions
    Read-only, available to authenticated users
    """
    queryset = ModuleDefinition.objects.all()
    serializer_class = ModuleDefinitionSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]


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
@authentication_classes([JWTAuthentication, SessionAuthentication])
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
@authentication_classes([JWTAuthentication, SessionAuthentication])
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


@api_view(['GET'])
@authentication_classes([JWTAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def get_current_tenant_info(request):
    """
    Get current tenant information from request
    
    GET /api/tenants/current/
    
    Returns tenant info based on the subdomain/custom domain in the request
    """
    # Get tenant from request (set by TenantMiddleware)
    tenant = getattr(request, 'tenant', None)
    
    if not tenant:
        return Response(
            {'error': 'No tenant found for this domain'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Return tenant details
    serializer = TenantDetailSerializer(tenant)
    return Response(serializer.data)
