from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers, status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import Employee


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # First call the parent validate method to handle basic authentication
        data = super().validate(attrs)
        
        # Get the authenticated user
        user = self.user
        
        # Check if user has an associated employee record
        try:
            employee = user.employee
            # Check employee status - only allow 'active' employees to login
            if employee.status != 'active':
                status_display = dict(Employee.EMPLOYMENT_STATUS).get(employee.status, employee.status)
                raise serializers.ValidationError(
                    f"Account is not active. Current status: {status_display}. Please contact your administrator."
                )
        except Employee.DoesNotExist:
            # If user doesn't have employee record, allow login (for admin users)
            pass
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            # Check if this is our custom employee status error
            error_detail = str(e.detail)
            if "Account is not active" in error_detail:
                return Response(
                    {"error": error_detail.replace("['", "").replace("']", "")}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            # Re-raise other validation errors
            raise e
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)