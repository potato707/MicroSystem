"""
Custom JWT Authentication Backend for GlobalClient
Handles JWT tokens containing global_client information
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
from .models import GlobalClient
from django.utils import timezone


class GlobalClientJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication backend that retrieves GlobalClient
    from main database instead of User from tenant database
    """
    
    def get_user(self, validated_token):
        """
        Override to return GlobalClient instance from main database
        """
        try:
            # Check if this is a global client token
            role = validated_token.get('role')
            if role != 'global_client':
                # Not a global client token, let default auth handle it
                return super().get_user(validated_token)
            
            # Get client ID from token
            user_id = validated_token.get('user_id')
            if not user_id:
                raise InvalidToken('Token contained no recognizable user identification')
            
            # Retrieve GlobalClient from main database
            try:
                client = GlobalClient.objects.using('default').get(id=user_id)
            except GlobalClient.DoesNotExist:
                raise AuthenticationFailed('Global client not found')
            
            # Check if client is active
            if not client.is_active:
                raise AuthenticationFailed('Client account is inactive')
            
            return client
            
        except (KeyError, TokenError) as e:
            raise InvalidToken(str(e))


class GlobalClientUser:
    """
    Wrapper class to make GlobalClient compatible with Django's
    authentication system and request.user expectations
    """
    
    def __init__(self, global_client):
        self.global_client = global_client
        self.id = global_client.id
        self.email = global_client.email
        self.name = global_client.name
        self.phone = global_client.phone
        self.is_active = global_client.is_active
        self.date_joined = global_client.date_joined
        self.last_login = global_client.last_login
        self.role = 'client'  # For compatibility with existing code
        self.is_authenticated = True
        self.is_anonymous = False
    
    def __str__(self):
        return f"GlobalClient: {self.email}"
    
    def check_password(self, raw_password):
        """Check password using GlobalClient method"""
        return self.global_client.check_password(raw_password)
    
    def set_password(self, raw_password):
        """Set password using GlobalClient method"""
        self.global_client.set_password(raw_password)
        self.global_client.save(using='default')
    
    def save(self, *args, **kwargs):
        """Save changes to GlobalClient"""
        # Update global_client fields from self
        self.global_client.name = self.name
        self.global_client.email = self.email
        self.global_client.phone = self.phone
        self.global_client.is_active = self.is_active
        self.global_client.last_login = self.last_login
        self.global_client.save(using='default')
    
    @property
    def is_staff(self):
        """GlobalClients are not staff"""
        return False
    
    @property
    def is_superuser(self):
        """GlobalClients are not superusers"""
        return False
    
    def has_perm(self, perm, obj=None):
        """GlobalClients have no specific permissions"""
        return False
    
    def has_perms(self, perm_list, obj=None):
        """GlobalClients have no specific permissions"""
        return False
    
    def has_module_perms(self, app_label):
        """GlobalClients have no module permissions"""
        return False
    
    def get_username(self):
        """Return email as username"""
        return self.email
    
    @property
    def username(self):
        """Return email as username"""
        return self.email
