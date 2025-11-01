"""
Client Dashboard Views
API endpoints for clients to manage their complaints
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from .models import ClientComplaint, ComplaintCategory, ClientComplaintStatusHistory, ClientComplaintReply
from .serializers import (
    ClientComplaintSerializer, ClientComplaintSubmissionSerializer,
    ComplaintCategorySerializer
)
from .client_helpers import verify_client_role, get_client_complaints, get_client_email


class ClientComplaintsPagination(PageNumberPagination):
    """Custom pagination for client complaints"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ClientDashboardStatsView(APIView):
    """
    Get dashboard statistics for the logged-in client
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get all complaints for this client
        complaints = get_client_complaints(request.user)
        
        # Calculate statistics
        total_complaints = complaints.count()
        pending_review = complaints.filter(status='pending_review').count()
        approved = complaints.filter(status='approved').count()
        in_progress = complaints.filter(status='in_progress').count()
        resolved = complaints.filter(status='resolved').count()
        closed = complaints.filter(status='closed').count()
        rejected = complaints.filter(status='rejected').count()
        
        # Priority breakdown
        urgent = complaints.filter(priority='urgent').count()
        medium = complaints.filter(priority='medium').count()
        low = complaints.filter(priority='low').count()
        
        # Recent activity
        recent_complaints = complaints.order_by('-created_at')[:5]
        recent_serializer = ClientComplaintSerializer(recent_complaints, many=True)
        
        return Response({
            'stats': {
                'total_complaints': total_complaints,
                'by_status': {
                    'pending_review': pending_review,
                    'approved': approved,
                    'in_progress': in_progress,
                    'resolved': resolved,
                    'closed': closed,
                    'rejected': rejected
                },
                'by_priority': {
                    'urgent': urgent,
                    'medium': medium,
                    'low': low
                }
            },
            'recent_complaints': recent_serializer.data
        }, status=status.HTTP_200_OK)


class ClientComplaintsListView(APIView):
    """
    List all complaints for the logged-in client with filtering and pagination
    """
    permission_classes = [IsAuthenticated]
    pagination_class = ClientComplaintsPagination
    
    def get(self, request):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get complaints for this client
        complaints = get_client_complaints(request.user).select_related(
            'category', 'reviewed_by', 'resolved_by'
        ).prefetch_related(
            'attachments', 'tasks__task', 'comments', 'status_history'
        )
        
        # Apply filters from query parameters
        status_filter = request.query_params.get('status')
        if status_filter:
            complaints = complaints.filter(status=status_filter)
        
        priority_filter = request.query_params.get('priority')
        if priority_filter:
            complaints = complaints.filter(priority=priority_filter)
        
        category_filter = request.query_params.get('category')
        if category_filter:
            complaints = complaints.filter(category_id=category_filter)
        
        # Search by title or description
        search = request.query_params.get('search')
        if search:
            complaints = complaints.filter(
                title__icontains=search
            ) | complaints.filter(
                description__icontains=search
            )
        
        # Order by creation date (newest first)
        complaints = complaints.order_by('-created_at')
        
        # Paginate results
        paginator = ClientComplaintsPagination()
        paginated_complaints = paginator.paginate_queryset(complaints, request)
        
        # Serialize data
        serializer = ClientComplaintSerializer(paginated_complaints, many=True)
        
        return paginator.get_paginated_response(serializer.data)


class ClientComplaintDetailView(APIView):
    """
    Get detailed information about a specific complaint
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, complaint_id):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get complaint and verify ownership
        complaint = get_object_or_404(
            ClientComplaint.objects.select_related(
                'category', 'reviewed_by', 'resolved_by'
            ).prefetch_related(
                'attachments', 'assignments__team', 'tasks__task', 
                'comments', 'status_history'
            ),
            id=complaint_id,
            client_email=get_client_email(request.user)  # Ensure client owns this complaint
        )
        
        # Serialize and return
        serializer = ClientComplaintSerializer(complaint)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClientSubmitComplaintView(APIView):
    """
    Allow logged-in clients to submit new complaints
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Pre-fill client information from authenticated user
        data = request.data.copy()
        data['client_name'] = request.user.name
        data['client_email'] = request.user.email
        
        # Use existing serializer
        serializer = ClientComplaintSubmissionSerializer(data=data)
        
        if serializer.is_valid():
            # Create complaint and link to current user
            complaint = serializer.save()
            complaint.client_user = request.user
            
            # Initialize automated status tracking
            from .ticket_automation import TicketStatusManager
            from django.utils import timezone
            complaint.last_responder = TicketStatusManager.RESPONDER_CLIENT
            complaint.last_response_time = timezone.now()
            complaint.automated_status = TicketStatusManager.STATUS_WAITING_SYSTEM
            complaint.save()
            
            # Create status history entry
            ClientComplaintStatusHistory.objects.create(
                complaint=complaint,
                old_status='pending_review',
                new_status='pending_review',
                changed_by=None,
                reason="شكوى جديدة من العميل (تم تسجيل الدخول)"
            )
            
            # Return created complaint details
            response_serializer = ClientComplaintSerializer(complaint)
            return Response({
                'message': 'Complaint submitted successfully',
                'complaint': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientAvailableCategoriesView(APIView):
    """
    Get list of available complaint categories for clients
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get active categories
        categories = ComplaintCategory.objects.filter(is_active=True).order_by('name')
        serializer = ComplaintCategorySerializer(categories, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClientComplaintStatusHistoryView(APIView):
    """
    Get status change history for a specific complaint
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, complaint_id):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get complaint and verify ownership
        complaint = get_object_or_404(
            ClientComplaint,
            id=complaint_id,
            client_email=get_client_email(request.user)
        )
        
        # Get status history
        history = complaint.status_history.select_related('changed_by').order_by('-changed_at')
        
        # Format history data
        history_data = [{
            'id': entry.id,
            'old_status': entry.old_status,
            'new_status': entry.new_status,
            'changed_by': entry.changed_by.name if entry.changed_by else 'System',
            'reason': entry.reason,
            'changed_at': entry.changed_at
        } for entry in history]
        
        return Response(history_data, status=status.HTTP_200_OK)


class ClientComplaintRepliesView(APIView):
    """
    Get all replies (client replies + admin responses + internal comments) for a complaint
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, complaint_id):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get complaint and verify ownership
        complaint = get_object_or_404(
            ClientComplaint,
            id=complaint_id,
            client_email=get_client_email(request.user)
        )
        
        # Get all communication
        replies = []
        
        # Get client replies
        for reply in complaint.client_replies.all():
            replies.append({
                'id': reply.id,
                'type': 'client_reply',
                'text': reply.reply_text,
                'author_name': reply.client_name,
                'author_email': reply.client_email,
                'created_at': reply.created_at,
                'is_read_by_admin': reply.is_read_by_admin,
                'can_delete': True,  # Client can delete their own replies
                'admin_response': reply.admin_response,
                'admin_responded_at': reply.admin_responded_at,
                'admin_responded_by': reply.admin_responded_by.name if reply.admin_responded_by else None,
            })
        
        # Get external comments (non-internal)
        for comment in complaint.comments.filter(is_internal=False):
            replies.append({
                'id': comment.id,
                'type': 'admin_comment',
                'text': comment.comment,
                'author_name': comment.author.name if comment.author else 'System',
                'created_at': comment.created_at,
                'updated_at': comment.updated_at,
                'can_delete': False,  # Client cannot delete admin comments
            })
        
        # Sort by creation date (newest first)
        replies.sort(key=lambda x: x['created_at'], reverse=True)
        
        return Response(replies, status=status.HTTP_200_OK)


class ClientComplaintAddReplyView(APIView):
    """
    Allow logged-in clients to add replies to their complaints
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, complaint_id):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get complaint and verify ownership
        complaint = get_object_or_404(
            ClientComplaint,
            id=complaint_id,
            client_email=get_client_email(request.user)
        )
        
        reply_text = request.data.get('reply_text')
        if not reply_text:
            return Response({
                'error': 'Reply text is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create reply
        reply = ClientComplaintReply.objects.create(
            complaint=complaint,
            reply_text=reply_text,
            client_name=request.user.name,
            client_email=request.user.email
        )
        
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
        
        # Create status history entry if needed
        from .models import ClientComplaintStatusHistory
        ClientComplaintStatusHistory.objects.create(
            complaint=complaint,
            old_status=complaint.status,
            new_status=complaint.status,
            changed_by=None,
            reason=f"رد جديد من العميل: {request.user.name}"
        )
        
        return Response({
            'message': 'Reply added successfully',
            'reply': {
                'id': reply.id,
                'type': 'client_reply',
                'text': reply.reply_text,
                'author_name': reply.client_name,
                'author_email': reply.client_email,
                'created_at': reply.created_at,
                'is_read_by_admin': reply.is_read_by_admin,
                'can_delete': True,
            }
        }, status=status.HTTP_201_CREATED)


class ClientComplaintDeleteReplyView(APIView):
    """
    Allow logged-in clients to delete their own replies
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, complaint_id, reply_id):
        # Verify user is a client
        if not verify_client_role(request.user):
            return Response({
                'error': 'This endpoint is for clients only'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get complaint and verify ownership
        complaint = get_object_or_404(
            ClientComplaint,
            id=complaint_id,
            client_email=get_client_email(request.user)
        )
        
        # Get reply and verify it belongs to this complaint and client
        reply = get_object_or_404(
            ClientComplaintReply,
            id=reply_id,
            complaint=complaint,
            client_email=request.user.email
        )
        
        # Delete the reply
        reply.delete()
        
        return Response({
            'message': 'Reply deleted successfully'
        }, status=status.HTTP_200_OK)
