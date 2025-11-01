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
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from .models import User, ClientComplaint, EmailVerificationCode, GlobalClient
from .serializers import UserSerializer
import secrets
import random
import string
from datetime import datetime, timedelta


class ClientRegisterView(APIView):
    """
    Register a new client in GlobalClient table (main database)
    This client can then login from any tenant
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name')
        phone = request.data.get('phone', '')
        
        # Validate input
        if not all([email, password, name]):
            return Response({
                'error': 'Email, password, and name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email already exists
        if GlobalClient.objects.using('default').filter(email=email).exists():
            return Response({
                'error': 'This email is already registered'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password strength
        if len(password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create new GlobalClient
        try:
            client = GlobalClient(
                email=email,
                name=name,
                phone=phone,
                is_active=True
            )
            client.set_password(password)
            client.save(using='default')
            
            # Generate JWT tokens
            refresh = RefreshToken()
            refresh['user_id'] = str(client.id)
            refresh['email'] = client.email
            refresh['name'] = client.name
            refresh['role'] = 'global_client'
            
            return Response({
                'message': 'Registration successful',
                'user': {
                    'id': str(client.id),
                    'email': client.email,
                    'name': client.name,
                    'phone': client.phone,
                    'is_active': client.is_active,
                    'role': 'client',
                    'date_joined': client.date_joined.isoformat() if client.date_joined else None
                },
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Registration failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ClientLoginView(APIView):
    """
    Client login endpoint using GlobalClient from main database
    Works across all tenants - one account for all tenants
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        from .models import GlobalClient
        
        email = request.data.get('email')
        password = request.data.get('password')
        
        # Validate input
        if not email or not password:
            return Response({
                'error': 'Both email and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find client in main database (not tenant-specific)
        try:
            client = GlobalClient.objects.using('default').get(email=email)
        except GlobalClient.DoesNotExist:
            return Response({
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check password
        if not client.check_password(password):
            return Response({
                'error': 'Invalid email or password'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if client is active
        if not client.is_active:
            return Response({
                'error': 'Your account has been deactivated. Please contact support.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update last login
        client.last_login = timezone.now()
        client.save(using='default')
        
        # Generate JWT tokens with client info
        refresh = RefreshToken()
        refresh['user_id'] = str(client.id)
        refresh['email'] = client.email
        refresh['name'] = client.name
        refresh['role'] = 'global_client'
        
        return Response({
            'message': 'Login successful',
            'user': {
                'id': str(client.id),
                'email': client.email,
                'name': client.name,
                'phone': client.phone,
                'is_active': client.is_active,
                'role': 'client',
                'date_joined': client.date_joined.isoformat() if client.date_joined else None,
                'last_login': client.last_login.isoformat() if client.last_login else None
            },
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
        
        # Merge user data with stats at the top level
        response_data = user_serializer.data.copy()
        response_data['total_complaints'] = total_complaints
        response_data['pending_complaints'] = pending_complaints
        response_data['resolved_complaints'] = resolved_complaints
        
        return Response(response_data, status=status.HTTP_200_OK)


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
            if not request.data['name'].strip():
                return Response({
                    'error': 'Name cannot be empty'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.name = request.data['name']
        
        if 'email' in request.data:
            new_email = request.data['email']
            # Check if email is already in use by another user
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                return Response({
                    'error': 'This email is already in use'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.email = new_email
        
        if 'profile_picture' in request.data:
            user.profile_picture = request.data['profile_picture']
        
        user.save()
        
        # Return updated user data
        user_serializer = UserSerializer(user)
        return Response({
            'message': 'Profile updated successfully',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)


class CheckPhoneExistsView(APIView):
    """
    Check if a phone number already exists in the system
    Used for complaint form validation
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        phone = request.data.get('phone')
        
        if not phone:
            return Response({
                'error': 'Phone number is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if any complaint has been submitted with this phone number
        existing_complaint = ClientComplaint.objects.filter(client_phone=phone).first()
        
        if existing_complaint:
            return Response({
                'exists': True,
                'message': 'رقم الهاتف مسجل من قبل، يرجى تسجيل الدخول'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'exists': False,
            'message': 'رقم الهاتف غير مسجل، يمكنك المتابعة'
        }, status=status.HTTP_200_OK)


class CheckEmailExistsView(APIView):
    """
    Check if an email already exists in the GlobalClient system
    Used for registration and complaint form validation
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email exists in GlobalClient table (main database)
        client_exists = GlobalClient.objects.using('default').filter(email=email).exists()
        
        if client_exists:
            return Response({
                'exists': True,
                'message': 'البريد الإلكتروني مسجل من قبل، يرجى تسجيل الدخول'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'exists': False,
            'message': 'البريد الإلكتروني غير مسجل، يمكنك المتابعة'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    Request a password reset via email
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email, role='client')
        except User.DoesNotExist:
            # Return success even if user doesn't exist for security reasons
            return Response({
                'message': 'If an account exists with this email, a password reset link has been sent.'
            }, status=status.HTTP_200_OK)
        
        # Generate password reset token
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build reset URL
        frontend_url = getattr(settings, 'CLIENT_FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/client/reset-password/{uid}/{token}"
        
        # Send email
        try:
            subject = "Password Reset Request - Complaint Management System"
            message = f"""
مرحباً {user.name},

لقد طلبت إعادة تعيين كلمة المرور الخاصة بك.

للمتابعة، يرجى النقر على الرابط التالي:
{reset_url}

إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذه الرسالة.

سينتهي هذا الرابط خلال 24 ساعة.

Hello {user.name},

You have requested to reset your password.

To proceed, please click on the following link:
{reset_url}

If you did not request a password reset, please ignore this message.

This link will expire in 24 hours.
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({
                'error': 'Failed to send reset email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'If an account exists with this email, a password reset link has been sent.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token and set new password
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate input
        if not all([uid, token, new_password, confirm_password]):
            return Response({
                'error': 'All fields are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if passwords match
        if new_password != confirm_password:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password strength
        if len(new_password) < 8:
            return Response({
                'error': 'Password must be at least 8 characters long'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Decode user ID
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, role='client')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({
                'error': 'Invalid reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify token
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({
                'error': 'Invalid or expired reset link'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password has been reset successfully. You can now login with your new password.'
        }, status=status.HTTP_200_OK)


class SendEmailVerificationCodeView(APIView):
    """
    Send verification code to new email for email change requests
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Verify user is a client
        if request.user.role != 'client':
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        new_email = request.data.get('new_email')
        
        if not new_email:
            return Response({
                'error': 'New email is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if new email is different from current
        if new_email == request.user.email:
            return Response({
                'error': 'New email must be different from current email'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email is already in use by another user
        if User.objects.filter(email=new_email).exclude(id=request.user.id).exists():
            return Response({
                'error': 'This email is already in use'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate 6-digit verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Delete old unverified codes for this user
        EmailVerificationCode.objects.filter(user=request.user, is_verified=False).delete()
        
        # Create new verification code (expires in 15 minutes)
        expires_at = timezone.now() + timedelta(minutes=15)
        EmailVerificationCode.objects.create(
            user=request.user,
            new_email=new_email,
            verification_code=verification_code,
            expires_at=expires_at
        )
        
        # Send verification email
        try:
            subject = "تأكيد تغيير البريد الإلكتروني - Verification Code"
            message = f"""
مرحباً {request.user.name},

لقد طلبت تغيير بريدك الإلكتروني إلى: {new_email}

كود التحقق الخاص بك هو: {verification_code}

هذا الكود صالح لمدة 15 دقيقة فقط.

إذا لم تطلب هذا التغيير، يرجى تجاهل هذه الرسالة.

---

Hello {request.user.name},

You have requested to change your email to: {new_email}

Your verification code is: {verification_code}

This code is valid for 15 minutes only.

If you did not request this change, please ignore this message.
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [new_email],
                fail_silently=False,
            )
        except Exception as e:
            return Response({
                'error': 'Failed to send verification email. Please try again later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'message': 'Verification code sent to your new email address'
        }, status=status.HTTP_200_OK)


class VerifyEmailCodeAndUpdateView(APIView):
    """
    Verify code and update email address
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Verify user is a client
        if request.user.role != 'client':
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        verification_code = request.data.get('verification_code')
        
        if not verification_code:
            return Response({
                'error': 'Verification code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find the verification code
        try:
            code_record = EmailVerificationCode.objects.get(
                user=request.user,
                verification_code=verification_code,
                is_verified=False
            )
        except EmailVerificationCode.DoesNotExist:
            return Response({
                'error': 'Invalid verification code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if code is expired
        if not code_record.is_valid():
            return Response({
                'error': 'Verification code has expired'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if email is still available
        if User.objects.filter(email=code_record.new_email).exclude(id=request.user.id).exists():
            return Response({
                'error': 'This email is now in use by another user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update email
        request.user.email = code_record.new_email
        request.user.save()
        
        # Mark code as verified
        code_record.is_verified = True
        code_record.save()
        
        # Return updated user data
        user_serializer = UserSerializer(request.user)
        return Response({
            'message': 'Email updated successfully',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)


class AllClientsFromAllTenantsView(APIView):
    """
    View to get all clients from all tenant databases
    This is a read-only view for administrative purposes
    Returns all clients with their tenant information
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from .tenant_models import Tenant
        from django.db import connections
        from .tenant_middleware import setup_tenant_database
        from django.conf import settings
        import os
        
        all_clients = []
        
        # Get all active tenants
        tenants = Tenant.objects.using('default').filter(is_active=True)
        
        for tenant in tenants:
            db_alias = f"tenant_{tenant.subdomain}"
            
            # Check if database file exists
            db_path = os.path.join(settings.BASE_DIR, f'tenant_{tenant.subdomain}.sqlite3')
            if not os.path.exists(db_path):
                print(f"Database file not found for tenant {tenant.subdomain}: {db_path}")
                continue
            
            try:
                # Setup database connection if not already configured
                if db_alias not in settings.DATABASES:
                    setup_tenant_database(tenant)
                
                # Get User model and query from tenant database
                with connections[db_alias].cursor() as cursor:
                    # Query to get all registered clients from this tenant's database
                    cursor.execute("""
                        SELECT id, email, first_name, last_name, '' as phone, is_active, 
                               date_joined, last_login, 'registered' as client_type
                        FROM hr_management_user
                        WHERE role = 'client'
                        
                        UNION ALL
                        
                        SELECT id, client_email as email, client_name as first_name, 
                               '' as last_name, client_phone as phone, 1 as is_active,
                               created_at as date_joined, NULL as last_login, 'complaint' as client_type
                        FROM hr_management_clientcomplaint
                        WHERE client_user_id IS NULL OR client_user_id = ''
                        
                        ORDER BY date_joined DESC
                    """)
                    
                    columns = [col[0] for col in cursor.description]
                    results = cursor.fetchall()
                    
                    for row in results:
                        client_data = dict(zip(columns, row))
                        client_data['tenant_name'] = tenant.name
                        client_data['tenant_subdomain'] = tenant.subdomain
                        client_data['tenant_id'] = str(tenant.id)
                        
                        # Format dates
                        if client_data.get('date_joined'):
                            client_data['date_joined'] = client_data['date_joined'].isoformat() if hasattr(client_data['date_joined'], 'isoformat') else str(client_data['date_joined'])
                        if client_data.get('last_login'):
                            client_data['last_login'] = client_data['last_login'].isoformat() if hasattr(client_data['last_login'], 'isoformat') else str(client_data['last_login'])
                        
                        all_clients.append(client_data)
                        
            except Exception as e:
                # If database doesn't exist or error occurs, skip this tenant
                print(f"Error accessing database for tenant {tenant.subdomain}: {str(e)}")
                continue
        
        return Response({
            'total_clients': len(all_clients),
            'total_tenants': tenants.count(),
            'clients': all_clients
        }, status=status.HTTP_200_OK)


# Django Template View (requires admin login)
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

@method_decorator(staff_member_required, name='dispatch')
class AllClientsDashboardView(View):
    """
    Django template view to display all clients from all tenant databases
    Requires Django admin login
    """
    
    def get(self, request):
        from .tenant_models import Tenant
        from django.db import connections
        from .tenant_middleware import setup_tenant_database
        from django.conf import settings
        import os
        
        all_clients = []
        
        # Get all active tenants
        tenants = Tenant.objects.using('default').filter(is_active=True)
        
        for tenant in tenants:
            db_alias = f"tenant_{tenant.subdomain}"
            
            # Check if database file exists
            db_path = os.path.join(settings.BASE_DIR, f'tenant_{tenant.subdomain}.sqlite3')
            if not os.path.exists(db_path):
                print(f"Database file not found for tenant {tenant.subdomain}: {db_path}")
                continue
            
            try:
                # Setup database connection if not already configured
                if db_alias not in settings.DATABASES:
                    setup_tenant_database(tenant)
                
                # Get User model and query from tenant database
                with connections[db_alias].cursor() as cursor:
                    # Query to get all clients from this tenant's database
                    cursor.execute("""
                        SELECT id, email, first_name, last_name, '' as phone, is_active, 
                               date_joined, last_login, 'registered' as client_type
                        FROM hr_management_user
                        WHERE role = 'client'
                        
                        UNION ALL
                        
                        SELECT id, client_email as email, client_name as first_name, 
                               '' as last_name, client_phone as phone, 1 as is_active,
                               created_at as date_joined, NULL as last_login, 'complaint' as client_type
                        FROM hr_management_clientcomplaint
                        WHERE client_user_id IS NULL OR client_user_id = ''
                        
                        ORDER BY date_joined DESC
                    """)
                    
                    columns = [col[0] for col in cursor.description]
                    results = cursor.fetchall()
                    
                    for row in results:
                        client_data = dict(zip(columns, row))
                        client_data['tenant_name'] = tenant.name
                        client_data['tenant_subdomain'] = tenant.subdomain
                        client_data['tenant_id'] = str(tenant.id)
                        all_clients.append(client_data)
                        
            except Exception as e:
                # If database doesn't exist or error occurs, skip this tenant
                print(f"Error accessing database for tenant {tenant.subdomain}: {str(e)}")
                continue
        
        context = {
            'clients': all_clients,
            'total_clients': len(all_clients),
            'total_tenants': tenants.count(),
            'tenants': tenants,
            'user': request.user
        }
        
        return render(request, 'admin_dashboard/all_clients.html', context)

