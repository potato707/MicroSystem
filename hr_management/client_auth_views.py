"""
Client Authentication Views
Handles login, logout, and user info for client accounts
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer


class ClientLoginView(APIView):
    """
    Client login endpoint using email and password
    Returns JWT tokens for authentication
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Validate input
        if not email or not password:
            return Response({
                'error': 'Both email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is a client
        if user.role != 'client':
            return Response({
                'error': 'This login is for clients only. Please use the appropriate login page.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Authenticate user
        user_auth = authenticate(username=user.username, password=password)
        if user_auth is None:
            return Response({
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is active
        if not user.is_active:
            return Response({
                'error': 'Your account has been deactivated. Please contact support.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        return Response({
            'message': 'Login successful',
            'user': user_serializer.data,
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }, status=status.HTTP_200_OK)


class ClientLogoutView(APIView):
    """
    Client logout endpoint
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Verify user is a client
        if request.user.role != 'client':
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Blacklist the refresh token if provided
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception as e:
                pass  # Token might already be blacklisted or invalid
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)


class ClientCurrentUserView(APIView):
    """
    Get current logged-in client user information
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Verify user is a client
        if request.user.role != 'client':
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Serialize and return user data
        user_serializer = UserSerializer(request.user)
        
        # Add additional client-specific stats
        total_complaints = request.user.client_complaints.count()
        pending_complaints = request.user.client_complaints.filter(
            status__in=['pending_review', 'in_progress']
        ).count()
        resolved_complaints = request.user.client_complaints.filter(
            status__in=['resolved', 'closed']
        ).count()
        
        return Response({
            'user': user_serializer.data,
            'stats': {
                'total_complaints': total_complaints,
                'pending_complaints': pending_complaints,
                'resolved_complaints': resolved_complaints
            }
        }, status=status.HTTP_200_OK)


class ClientChangePasswordView(APIView):
    """
    Allow clients to change their password
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Verify user is a client
        if request.user.role != 'client':
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            return Response({
                'error': 'All password fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if new passwords match
        if new_password != confirm_password:
            return Response({
                'error': 'New passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify current password
        if not request.user.check_password(current_password):
            return Response({
                'error': 'Current password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password strength (optional - add your own rules)
        if len(new_password) < 8:
            return Response({
                'error': 'New password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        request.user.set_password(new_password)
        request.user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class ClientProfileUpdateView(APIView):
    """
    Allow clients to update their profile information
    """
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        # Verify user is a client
        if request.user.role != 'client':
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = request.user
        
        # Update allowed fields
        if 'name' in request.data:
            user.name = request.data['name']
        
        if 'profile_picture' in request.data:
            user.profile_picture = request.data['profile_picture']
        
        user.save()
        
        # Return updated user data
        user_serializer = UserSerializer(user)
        return Response({
            'message': 'Profile updated successfully',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)
