
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as rest_status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

class ClientPortalReplyDeleteView(APIView):
    """Public endpoint for clients to delete their own replies"""

    def get_user_role(self, request):
        # If authenticated, get user role; else None
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return getattr(user, 'role', None)
        return None

    def delete(self, request, token, reply_id):
        try:
            access_token = ClientComplaintAccessToken.objects.select_related('complaint').get(
                token=token,
                is_active=True
            )
            if access_token.is_expired:
                return Response({'error': 'Access link has expired'}, status=rest_status.HTTP_410_GONE)
            complaint = access_token.complaint
            reply = ClientComplaintReply.objects.get(id=reply_id, complaint=complaint)

            # Check if authenticated admin
            user_role = self.get_user_role(request)
            if user_role == 'admin':
                reply.delete()
                return Response({'message': 'Reply deleted successfully'}, status=rest_status.HTTP_204_NO_CONTENT)

            # Employees cannot delete client replies
            if user_role == 'employee':
                return Response({'error': 'Permission denied'}, status=rest_status.HTTP_403_FORBIDDEN)

            # Only allow client to delete their own reply via token
            client_email = request.data.get('client_email') or reply.client_email
            if (
                reply.client_email.lower() == client_email.lower()
                and client_email.lower() == complaint.client_email.lower()
                and reply.author_type == 'client'
                and reply.type == 'client_reply'
            ):
                reply.delete()
                return Response({'message': 'Reply deleted successfully'}, status=rest_status.HTTP_204_NO_CONTENT)

            return Response({'error': 'Permission denied'}, status=rest_status.HTTP_403_FORBIDDEN)
        except (ClientComplaintAccessToken.DoesNotExist, ClientComplaintReply.DoesNotExist):
            return Response({'error': 'Reply not found'}, status=rest_status.HTTP_404_NOT_FOUND)
from .models import (
    ClientComplaint, ClientComplaintAccessToken, ClientComplaintReply, Team
)
from .serializers import (
    ClientPortalComplaintSerializer, ClientComplaintReplySerializer,
    ClientComplaintReplyCreateSerializer, ClientComplaintAccessTokenSerializer
)


class ClientPortalAccessView(APIView):
    """Public endpoint to access complaint details using secure token"""
    permission_classes = []  # No authentication required
    
    def get(self, request, token):
        try:
            # Find and validate the access token
            access_token = ClientComplaintAccessToken.objects.select_related('complaint').get(
                token=token,
                is_active=True
            )
            
            if access_token.is_expired:
                return Response(
                    {'error': 'Access link has expired'}, 
                    status=rest_status.HTTP_410_GONE
                )
            
            # Record the access
            access_token.record_access()
            
            # Return complaint details
            complaint = access_token.complaint
            serializer = ClientPortalComplaintSerializer(complaint)
            
            return Response({
                'complaint': serializer.data,
                'access_info': {
                    'expires_at': access_token.expires_at,
                    'access_count': access_token.access_count
                }
            })
            
        except ClientComplaintAccessToken.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired access link'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )


class ClientPortalReplyView(APIView):
    """Public endpoint for clients to reply to their complaints"""
    permission_classes = []  # No authentication required
    
    def post(self, request, token):
        try:
            # Validate access token
            access_token = ClientComplaintAccessToken.objects.select_related('complaint').get(
                token=token,
                is_active=True
            )
            
            if access_token.is_expired:
                return Response(
                    {'error': 'Access link has expired'}, 
                    status=rest_status.HTTP_410_GONE
                )
            
            complaint = access_token.complaint
            
            # Create the reply
            serializer = ClientComplaintReplyCreateSerializer(
                data=request.data,
                context={'complaint': complaint}
            )
            
            if serializer.is_valid():
                reply = serializer.save(complaint=complaint)
                
                # Automatic status transition - client replied
                from .ticket_automation import TicketStatusManager
                from .notifications import NotificationService
                TicketStatusManager.transition_on_client_response(complaint)
                
                # Send notification to admins
                try:
                    NotificationService.notify_new_client_message(complaint)
                except Exception as e:
                    # Log but don't fail if notification fails
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f'Failed to send client message notification: {e}')
                
                # Record token access
                access_token.record_access()
                
                # Return the created reply
                response_serializer = ClientComplaintReplySerializer(reply)
                return Response(
                    response_serializer.data, 
                    status=rest_status.HTTP_201_CREATED
                )
            
            return Response(
                serializer.errors, 
                status=rest_status.HTTP_400_BAD_REQUEST
            )
            
        except ClientComplaintAccessToken.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired access link'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )


class GenerateClientAccessLinkView(APIView):
    """Internal endpoint to generate secure access links for complaints"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, complaint_id):
        try:
            complaint = ClientComplaint.objects.get(id=complaint_id)
            
            # Check permissions
            if request.user.role not in ['admin', 'manager']:
                # Check if user's teams are assigned to this complaint
                user_teams = Team.objects.filter(memberships__employee__user=request.user)
                if not complaint.assignments.filter(team__in=user_teams, is_active=True).exists():
                    return Response(
                        {'error': 'Permission denied'}, 
                        status=rest_status.HTTP_403_FORBIDDEN
                    )
            
            # Get or create access token
            days_valid = request.data.get('days_valid', 30)
            access_token = ClientComplaintAccessToken.create_for_complaint(complaint, days_valid)
            
            # Generate the public URL
            base_url = request.build_absolute_uri('/').rstrip('/')
            client_portal_url = f"{base_url}/client-portal/{access_token.token}"
            
            serializer = ClientComplaintAccessTokenSerializer(access_token)
            
            return Response({
                'access_token': serializer.data,
                'portal_url': client_portal_url,
                'complaint_title': complaint.title,
                'client_email': complaint.client_email
            })
            
        except ClientComplaint.DoesNotExist:
            return Response(
                {'error': 'Complaint not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )


class AdminRespondToClientReplyView(APIView):
    """Internal endpoint for admins to respond to client replies"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, reply_id):
        try:
            reply = ClientComplaintReply.objects.select_related('complaint').get(id=reply_id)
            
            # Check permissions
            if request.user.role not in ['admin', 'manager']:
                return Response(
                    {'error': 'Permission denied'}, 
                    status=rest_status.HTTP_403_FORBIDDEN
                )
            
            admin_response = request.data.get('admin_response', '').strip()
            if not admin_response:
                return Response(
                    {'error': 'Admin response is required'}, 
                    status=rest_status.HTTP_400_BAD_REQUEST
                )
            
            # Update the reply with admin response
            reply.admin_response = admin_response
            reply.admin_responded_at = timezone.now()
            reply.admin_responded_by = request.user
            reply.is_read_by_admin = True
            reply.save()
            
            serializer = ClientComplaintReplySerializer(reply)
            return Response(serializer.data)
            
        except ClientComplaintReply.DoesNotExist:
            return Response(
                {'error': 'Reply not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )


class ClientRepliesListView(APIView):
    """Internal endpoint to list client replies for a complaint"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, complaint_id):
        try:
            complaint = ClientComplaint.objects.get(id=complaint_id)
            
            # Check permissions
            if request.user.role not in ['admin', 'manager']:
                user_teams = Team.objects.filter(memberships__employee__user=request.user)
                if not complaint.assignments.filter(team__in=user_teams, is_active=True).exists():
                    return Response(
                        {'error': 'Permission denied'}, 
                        status=rest_status.HTTP_403_FORBIDDEN
                    )
            
            replies = complaint.client_replies.all().order_by('-created_at')
            serializer = ClientComplaintReplySerializer(replies, many=True)
            
            return Response({
                'complaint_title': complaint.title,
                'client_name': complaint.client_name,
                'replies': serializer.data
            })
            
        except ClientComplaint.DoesNotExist:
            return Response(
                {'error': 'Complaint not found'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )


class ClientPortalTokenDeactivateView(APIView):
    """Endpoint to deactivate client portal access token"""
    permission_classes = []  # No authentication required - client can deactivate their own link
    
    def post(self, request, token):
        try:
            # Find the access token
            access_token = ClientComplaintAccessToken.objects.get(
                token=token,
                is_active=True
            )
            
            # Deactivate the token
            access_token.is_active = False
            access_token.save()
            
            return Response({
                'message': 'Access link has been deactivated successfully',
                'success': True
            })
            
        except ClientComplaintAccessToken.DoesNotExist:
            return Response(
                {'error': 'Invalid access link'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )