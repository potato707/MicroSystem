from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers, status
from rest_framework.response import Response
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.db import connections
from .models import Employee
from .tenant_models import Tenant
from .tenant_db_router import set_current_tenant, clear_current_tenant, get_tenant_db_config
import logging
import os

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that authenticates users against tenant-specific databases
    """
    
    def validate(self, attrs):
        """
        Override validate to use tenant-specific database for authentication
        """
        # Get tenant from request context (set by middleware)
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None)
        
        if not tenant:
            logger.warning("No tenant in request context during authentication")
            raise serializers.ValidationError({
                'error': 'Tenant not specified',
                'detail': 'Please provide X-Tenant-Subdomain header or access via tenant subdomain'
            })
        
        # Set current tenant for DB routing
        set_current_tenant(tenant)
        
        try:
            username = attrs.get('username')
            password = attrs.get('password')
            
            if not username or not password:
                raise serializers.ValidationError('Username and password are required')
            
            # Get tenant database alias
            db_alias = f"tenant_{tenant.subdomain}"
            
            # Ensure database connection is registered
            if db_alias not in settings.DATABASES:
                logger.info(f"Database {db_alias} not registered, registering now...")
                db_config = get_tenant_db_config(tenant.subdomain)
                settings.DATABASES[db_alias] = db_config
                # Also register in connections.databases
                connections.databases[db_alias] = db_config
                
                # Close existing connection if any
                if hasattr(connections._connections, db_alias):
                    try:
                        conn = getattr(connections._connections, db_alias)
                        conn.close()
                    except:
                        pass
                    try:
                        delattr(connections._connections, db_alias)
                    except:
                        pass
            
            # For SQLite, check if database file exists
            if 'sqlite' in settings.DATABASES.get(db_alias, {}).get('ENGINE', ''):
                db_path = settings.DATABASES[db_alias]['NAME']
                if not os.path.isabs(db_path):
                    db_path = os.path.join(settings.BASE_DIR, db_path)
                
                if not os.path.exists(db_path):
                    logger.error(f"Database file does not exist: {db_path}")
                    raise serializers.ValidationError({
                        'error': 'Tenant database not initialized',
                        'detail': f'Please contact administrator to setup {tenant.name}'
                    })
            
            logger.info(f"Authenticating user '{username}' for tenant '{tenant.name}' (DB: {db_alias})")
            
            # Check if user exists in tenant database
            try:
                user = User.objects.using(db_alias).get(username=username)
            except User.DoesNotExist:
                logger.warning(f"User '{username}' not found in tenant '{tenant.name}' database")
                raise serializers.ValidationError({
                    'error': 'Invalid credentials',
                    'detail': f'User does not exist in {tenant.name}'
                })
            
            # Check password
            if not user.check_password(password):
                logger.warning(f"Invalid password for user '{username}' in tenant '{tenant.name}'")
                raise serializers.ValidationError({
                    'error': 'Invalid credentials',
                    'detail': 'Incorrect password'
                })
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user '{username}' attempted login in tenant '{tenant.name}'")
                raise serializers.ValidationError({
                    'error': 'Account disabled',
                    'detail': 'Your account has been disabled. Please contact your administrator.'
                })
            
            # Set the user for token generation
            self.user = user
            
            # Generate tokens using parent method
            refresh = self.get_token(user)
            
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            
            # Check if user has an associated employee record
            try:
                employee = Employee.objects.using(db_alias).get(user=user)
                
                # Check employee status
                if employee.status != 'active':
                    status_display = dict(Employee.EMPLOYMENT_STATUS).get(employee.status, employee.status)
                    logger.warning(f"Employee '{username}' has status '{employee.status}' in tenant '{tenant.name}'")
                    raise serializers.ValidationError({
                        'error': 'Account not active',
                        'detail': f"Current status: {status_display}. Please contact your administrator."
                    })
                
                # Add employee info to response
                data['employee_id'] = str(employee.id)
                data['employee_name'] = employee.name
                data['role'] = user.role  # Get role from User model, not Employee
                
            except Employee.DoesNotExist:
                logger.info(f"User '{username}' has no employee record in tenant '{tenant.name}' (admin user)")
                # User exists but no employee record (admin/superuser)
                data['role'] = user.role if hasattr(user, 'role') else ('admin' if user.is_superuser else 'staff')
            
            # Add tenant info to response
            data['tenant'] = tenant.subdomain
            data['tenant_name'] = tenant.name
            
            logger.info(f"✓ User '{username}' authenticated successfully for tenant '{tenant.name}'")
            
            return data
            
        finally:
            # Always clear tenant from thread-local
            clear_current_tenant()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            # Extract error details
            if isinstance(e.detail, dict):
                error_msg = e.detail.get('error', 'Authentication failed')
                error_detail = e.detail.get('detail', str(e.detail))
            else:
                error_msg = 'Authentication failed'
                error_detail = str(e.detail)
            
            logger.error(f"Authentication error: {error_msg} - {error_detail}")
            
            return Response(
                {
                    "error": error_msg,
                    "detail": error_detail
                }, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)