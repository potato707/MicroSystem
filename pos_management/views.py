from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import timedelta
from django_filters.rest_framework import DjangoFilterBackend

from .models import ClientType, Client, Product, Distribution
from .serializers import (
    ClientTypeSerializer, ClientSerializer, ProductSerializer,
    DistributionSerializer, DistributionCreateSerializer,
    POSDashboardStatsSerializer
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
    queryset = Product.objects.all()
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
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        
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
