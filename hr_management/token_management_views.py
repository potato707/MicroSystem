
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as rest_status
from rest_framework.permissions import IsAuthenticated
from .models import ClientComplaint, ClientComplaintAccessToken, Team


class ClientPortalTokenManagementView(APIView):
    """Admin endpoint to manage client portal access tokens"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, complaint_id):
        """Create or reactivate client portal access token"""
        try:
            complaint = ClientComplaint.objects.get(pk=complaint_id)
            
            # Check if user has permission (admin or assigned team member)
            if request.user.role != 'admin':
                user_teams = Team.objects.filter(memberships__employee__user=request.user)
                if not complaint.assignments.filter(team__in=user_teams, is_active=True).exists():
                    return Response(
                        {'error': 'ليس لديك صلاحية إدارة هذه الشكوى'}, 
                        status=rest_status.HTTP_403_FORBIDDEN
                    )
            
            # Create or get existing token
            access_token = ClientComplaintAccessToken.create_for_complaint(complaint)
            
            return Response({
                'message': 'تم إنشاء/تفعيل رابط البوابة بنجاح',
                'token': access_token.token,
                'access_url': f'/client-portal/{access_token.token}/',
                'is_permanent': access_token.is_permanent,
                'created_at': access_token.created_at,
                'access_count': access_token.access_count
            })
            
        except ClientComplaint.DoesNotExist:
            return Response(
                {'error': 'الشكوى غير موجودة'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, complaint_id):
        """Deactivate client portal access token"""
        try:
            complaint = ClientComplaint.objects.get(pk=complaint_id)
            
            # Check if user has permission (admin or assigned team member)
            if request.user.role != 'admin':
                user_teams = Team.objects.filter(memberships__employee__user=request.user)
                if not complaint.assignments.filter(team__in=user_teams, is_active=True).exists():
                    return Response(
                        {'error': 'ليس لديك صلاحية إدارة هذه الشكوى'}, 
                        status=rest_status.HTTP_403_FORBIDDEN
                    )
            
            try:
                access_token = complaint.access_token
                access_token.is_active = False
                access_token.save()
                
                return Response({
                    'message': 'تم إلغاء تفعيل رابط البوابة بنجاح',
                    'success': True
                })
                
            except ClientComplaintAccessToken.DoesNotExist:
                return Response(
                    {'error': 'لا يوجد رابط بوابة لهذه الشكوى'}, 
                    status=rest_status.HTTP_404_NOT_FOUND
                )
            
        except ClientComplaint.DoesNotExist:
            return Response(
                {'error': 'الشكوى غير موجودة'}, 
                status=rest_status.HTTP_404_NOT_FOUND
            )