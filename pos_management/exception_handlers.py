"""
Custom exception handlers for POS Management
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from .models import ClientInventory


def custom_exception_handler(exc, context):
    """
    Custom exception handler to provide better error messages
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Handle IntegrityError for ClientInventory unique constraint
    if isinstance(exc, IntegrityError):
        if 'UNIQUE constraint' in str(exc) or 'unique' in str(exc).lower():
            # Try to extract client and product from request data
            request = context.get('request')
            if request and hasattr(request, 'data'):
                client_id = request.data.get('client')
                product_id = request.data.get('product')
                
                if client_id and product_id:
                    try:
                        existing = ClientInventory.objects.get(
                            client_id=client_id,
                            product_id=product_id
                        )
                        return Response({
                            'non_field_errors': [
                                f'يوجد مخزون بالفعل لهذا المنتج عند هذا العميل. '
                                f'الكمية الحالية: {existing.current_quantity}. '
                                f'يمكنك تعديله بدلاً من إضافة مخزون جديد.'
                            ],
                            'existing_inventory_id': str(existing.id),
                            'current_quantity': str(existing.current_quantity)
                        }, status=status.HTTP_400_BAD_REQUEST)
                    except ClientInventory.DoesNotExist:
                        pass
            
            # Fallback to generic message
            return Response({
                'non_field_errors': ['هذا السجل موجود بالفعل. يرجى التحقق من البيانات.']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    # Return the default response for other exceptions
    return response
