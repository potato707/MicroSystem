from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q, Sum, Count
from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend

from .models import ClientType, Client, SimpleProduct, Distribution, ClientInventory
from .serializers import (
    ClientTypeSerializer, ClientSerializer, ProductSerializer,
    DistributionSerializer, DistributionCreateSerializer,
    POSDashboardStatsSerializer, ClientInventorySerializer,
    ClientInventoryUpdateSerializer, ClientInventoryListSerializer
)


class ClientTypeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Client Types
    Allows admins to create dynamic client types with custom fields
    """
    queryset = ClientType.objects.all()
    serializer_class = ClientTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'clients_count']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle active status of client type"""
        client_type = self.get_object()
        client_type.is_active = not client_type.is_active
        client_type.save()
        
        serializer = self.get_serializer(client_type)
        return Response(serializer.data)


class ClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Clients
    Supports filtering, searching, and bulk operations
    """
    queryset = Client.objects.select_related('client_type', 'created_by', 'assigned_to').all()
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client_type', 'status', 'category', 'assigned_to']
    search_fields = ['name', 'contact_person', 'email', 'phone', 'notes']
    ordering_fields = ['name', 'created_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by upcoming visits
        has_upcoming_visit = self.request.query_params.get('has_upcoming_visit')
        if has_upcoming_visit == 'true':
            queryset = queryset.filter(
                distributions__next_visit_date__isnull=False,
                distributions__next_visit_date__gte=timezone.now().date()
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change client status"""
        client = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Client.CLIENT_STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        client.status = new_status
        client.save(update_fields=['status'])
        
        serializer = self.get_serializer(client)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def distributions(self, request, pk=None):
        """Get all distributions for this client"""
        client = self.get_object()
        distributions = client.distributions.all().order_by('-distributed_at')
        
        # Pagination
        page = self.paginate_queryset(distributions)
        if page is not None:
            serializer = DistributionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DistributionSerializer(distributions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def upcoming_visits(self, request, pk=None):
        """Get upcoming visits for this client"""
        client = self.get_object()
        upcoming = client.distributions.filter(
            next_visit_date__gte=timezone.now().date(),
            status__in=['new', 'waiting_visit']
        ).order_by('next_visit_date')
        
        serializer = DistributionSerializer(upcoming, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_to(self, request, pk=None):
        """Assign client to a user"""
        client = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(id=user_id)
            client.assigned_to = user
            client.save(update_fields=['assigned_to'])
            
            serializer = self.get_serializer(client)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Products/Services
    """
    queryset = SimpleProduct.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'base_price', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset
    
    def perform_create(self, serializer):
        # Try to set created_by, but allow null if user doesn't exist in tenant DB
        try:
            serializer.save(created_by=self.request.user)
        except:
            serializer.save(created_by=None)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle active status of product"""
        product = self.get_object()
        product.is_active = not product.is_active
        product.save()
        
        serializer = self.get_serializer(product)
        return Response(serializer.data)


class DistributionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Distributions
    """
    queryset = Distribution.objects.select_related('client', 'product', 'created_by').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'product', 'status']
    search_fields = ['client__name', 'product__name', 'notes']
    ordering_fields = ['distributed_at', 'next_visit_date', 'total_amount']
    ordering = ['-distributed_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DistributionCreateSerializer
        return DistributionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by upcoming visits
        upcoming_visits = self.request.query_params.get('upcoming_visits')
        if upcoming_visits == 'true':
            date_threshold = timezone.now().date() + timedelta(days=7)
            queryset = queryset.filter(
                next_visit_date__lte=date_threshold,
                next_visit_date__gte=timezone.now().date(),
                status__in=['new', 'waiting_visit']
            )
        
        # Filter by overdue visits
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                next_visit_date__lt=timezone.now().date(),
                status__in=['new', 'waiting_visit']
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(distributed_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(distributed_at__date__lte=end_date)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_visited(self, request, pk=None):
        """Mark distribution as visited and calculate next visit date"""
        distribution = self.get_object()
        
        visit_date = request.data.get('visit_date')
        if visit_date:
            from datetime import datetime
            visit_date = datetime.strptime(visit_date, '%Y-%m-%d').date()
        else:
            visit_date = timezone.now().date()
        
        distribution.last_visit_date = visit_date
        distribution.next_visit_date = visit_date + timedelta(days=distribution.visit_interval_days)
        distribution.status = 'waiting_visit'
        distribution.save()
        
        serializer = self.get_serializer(distribution)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark distribution as completed"""
        distribution = self.get_object()
        distribution.status = 'completed'
        distribution.save(update_fields=['status'])
        
        serializer = self.get_serializer(distribution)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel distribution"""
        distribution = self.get_object()
        
        distribution.status = 'cancelled'
        distribution.save(update_fields=['status'])
        
        serializer = self.get_serializer(distribution)
        return Response(serializer.data)


class POSDashboardStatsView(APIView):
    """
    Get comprehensive POS dashboard statistics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Client statistics
        total_clients = Client.objects.count()
        active_clients = Client.objects.filter(status='active').count()
        potential_clients = Client.objects.filter(status='potential').count()
        
        # Distribution statistics
        total_distributions = Distribution.objects.count()
        
        # Upcoming visits (within 7 days)
        date_threshold = timezone.now().date() + timedelta(days=7)
        upcoming_visits = Distribution.objects.filter(
            next_visit_date__lte=date_threshold,
            next_visit_date__gte=timezone.now().date(),
            status__in=['new', 'waiting_visit']
        ).count()
        
        # Overdue visits
        overdue_visits = Distribution.objects.filter(
            next_visit_date__lt=timezone.now().date(),
            status__in=['new', 'waiting_visit']
        ).count()
        
        # Product statistics
        total_products = SimpleProduct.objects.count()
        active_products = SimpleProduct.objects.filter(is_active=True).count()
        
        # Revenue calculation
        total_revenue = Distribution.objects.filter(
            status__in=['completed', 'waiting_visit']
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Recent distributions (last 10)
        recent_distributions = Distribution.objects.select_related(
            'client', 'product'
        ).order_by('-distributed_at')[:10]
        
        # Upcoming visit distributions (next 10)
        upcoming_visit_distributions = Distribution.objects.filter(
            next_visit_date__gte=timezone.now().date(),
            status__in=['new', 'waiting_visit']
        ).select_related('client', 'product').order_by('next_visit_date')[:10]
        
        # Prepare response data
        data = {
            'total_clients': total_clients,
            'active_clients': active_clients,
            'potential_clients': potential_clients,
            'total_distributions': total_distributions,
            'upcoming_visits': upcoming_visits,
            'overdue_visits': overdue_visits,
            'total_products': total_products,
            'active_products': active_products,
            'total_revenue': total_revenue,
            'recent_distributions': DistributionSerializer(recent_distributions, many=True).data,
            'upcoming_visit_distributions': DistributionSerializer(upcoming_visit_distributions, many=True).data,
        }
        
        serializer = POSDashboardStatsSerializer(data)
        return Response(serializer.data)


class ClientInventoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Client Inventory
    Tracks product quantities at each client location
    """
    queryset = ClientInventory.objects.all()
    serializer_class = ClientInventorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'product']  # Only database fields, computed fields handled in get_queryset
    search_fields = ['client__name', 'product__name', 'location']
    ordering_fields = ['current_quantity', 'updated_at', 'expiry_date']
    ordering = ['client', 'product']
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('client', 'product', 'last_updated_by')
        
        # Filter by client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock is not None:
            if low_stock.lower() == 'true':
                queryset = [item for item in queryset if item.is_low_stock]
        
        # Filter by out of stock
        out_of_stock = self.request.query_params.get('out_of_stock')
        if out_of_stock is not None:
            if out_of_stock.lower() == 'true':
                queryset = [item for item in queryset if item.is_out_of_stock]
        
        # Filter by expiring soon
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon is not None:
            if expiring_soon.lower() == 'true':
                queryset = [item for item in queryset if item.is_expiring_soon]
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return ClientInventoryListSerializer
        return ClientInventorySerializer
    
    def perform_create(self, serializer):
        serializer.save(last_updated_by=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create to handle duplicate inventory gracefully"""
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            # Check if it's a duplicate client+product error
            if 'UNIQUE constraint' in str(e) or 'unique' in str(e).lower():
                client_id = request.data.get('client')
                product_id = request.data.get('product')
                
                if client_id and product_id:
                    try:
                        existing = ClientInventory.objects.get(client_id=client_id, product_id=product_id)
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
            
            # If not a duplicate error or can't find existing, return generic error
            return Response({
                'non_field_errors': ['حدث خطأ في إضافة المخزون. يرجى المحاولة مرة أخرى.']
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_update(self, serializer):
        serializer.save(last_updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        """
        Update inventory quantity
        POST /api/pos/inventory/{id}/update_quantity/
        Body: {
            "action": "add" | "reduce" | "set",
            "quantity": 10,
            "notes": "optional notes"
        }
        """
        inventory = self.get_object()
        serializer = ClientInventoryUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            quantity = serializer.validated_data['quantity']
            notes = serializer.validated_data.get('notes', '')
            
            if action == 'add':
                inventory.add_stock(quantity, user=request.user)
            elif action == 'reduce':
                inventory.reduce_stock(quantity, user=request.user)
            elif action == 'set':
                inventory.set_stock(quantity, user=request.user)
            
            # Update notes if provided
            if notes:
                inventory.notes = notes
                inventory.save(update_fields=['notes'])
            
            return Response({
                'success': True,
                'message': f'Inventory updated successfully',
                'inventory': ClientInventorySerializer(inventory).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def low_stock_alerts(self, request):
        """Get all low stock items across all clients"""
        low_stock_items = [item for item in self.get_queryset() if item.is_low_stock]
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get all items expiring soon"""
        expiring_items = [item for item in self.get_queryset() if item.is_expiring_soon]
        serializer = self.get_serializer(expiring_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_client(self, request):
        """Get inventory grouped by client"""
        client_id = request.query_params.get('client_id')
        if not client_id:
            return Response(
                {'error': 'client_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        inventory_items = self.get_queryset().filter(client_id=client_id)
        serializer = ClientInventoryListSerializer(inventory_items, many=True)
        
        # Calculate statistics
        total_items = len(inventory_items)
        low_stock_count = sum(1 for item in inventory_items if item.is_low_stock)
        out_of_stock_count = sum(1 for item in inventory_items if item.is_out_of_stock)
        expiring_soon_count = sum(1 for item in inventory_items if item.is_expiring_soon)
        
        return Response({
            'client_id': client_id,
            'total_items': total_items,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'expiring_soon_count': expiring_soon_count,
            'inventory': serializer.data
        })

