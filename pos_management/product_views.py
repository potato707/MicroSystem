"""
Views for Advanced Product Management System
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db import models

from .models import (
    ProductCategory,
    ProductUnit,
    CategoryUnit,
    AdvancedProduct,
    ProductUnitStock
)
from .product_serializers import (
    ProductCategorySerializer,
    ProductCategoryWithUnitsSerializer,
    ProductUnitSerializer,
    CategoryUnitSerializer,
    CategoryUnitCreateSerializer,
    ProductSerializer,
    ProductWithUnitsSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    ProductUnitStockSerializer,
    ProductStockUpdateSerializer,
)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Product Categories
    Supports custom fields and units linking
    """
    queryset = ProductCategory.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action in ['retrieve', 'list']:
            return ProductCategoryWithUnitsSerializer
        return ProductCategorySerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle active status"""
        category = self.get_object()
        category.is_active = not category.is_active
        category.save(update_fields=['is_active'])
        
        serializer = self.get_serializer(category)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def link_units(self, request, pk=None):
        """Link multiple units to category"""
        category = self.get_object()
        units_data = request.data.get('units', [])
        
        if not units_data:
            return Response(
                {'error': 'يجب تحديد وحدة واحدة على الأقل'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_links = []
        errors = []
        
        with transaction.atomic():
            for unit_data in units_data:
                serializer = CategoryUnitCreateSerializer(data=unit_data)
                if serializer.is_valid():
                    try:
                        link, created = CategoryUnit.objects.get_or_create(
                            category=category,
                            unit_id=serializer.validated_data['unit_id'],
                            defaults={
                                'default_pieces_per_unit': serializer.validated_data.get('default_pieces_per_unit', 1),
                                'is_primary': serializer.validated_data.get('is_primary', False),
                            }
                        )
                        
                        if not created:
                            # Update existing link
                            link.default_pieces_per_unit = serializer.validated_data.get('default_pieces_per_unit', link.default_pieces_per_unit)
                            link.is_primary = serializer.validated_data.get('is_primary', link.is_primary)
                            link.save()
                        
                        created_links.append(CategoryUnitSerializer(link).data)
                    except Exception as e:
                        errors.append(str(e))
                else:
                    errors.append(serializer.errors)
        
        return Response({
            'success': True,
            'created_links': created_links,
            'errors': errors
        })
    
    @action(detail=True, methods=['post'])
    def unlink_unit(self, request, pk=None):
        """Unlink a unit from category"""
        category = self.get_object()
        unit_id = request.data.get('unit_id')
        
        if not unit_id:
            return Response(
                {'error': 'يجب تحديد معرف الوحدة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            link = CategoryUnit.objects.get(category=category, unit_id=unit_id)
            link.delete()
            return Response({'success': True, 'message': 'تم فك الربط بنجاح'})
        except CategoryUnit.DoesNotExist:
            return Response(
                {'error': 'الربط غير موجود'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def with_units(self, request):
        """Get all categories with their linked units"""
        categories = self.get_queryset().filter(is_active=True)
        serializer = ProductCategoryWithUnitsSerializer(categories, many=True)
        return Response(serializer.data)


class ProductUnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Product Units
    Supports custom fields
    """
    queryset = ProductUnit.objects.all()
    serializer_class = ProductUnitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['is_active', 'is_countable']
    search_fields = ['name', 'short_name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_destroy(self, instance):
        """
        Override destroy to delete all ProductUnitStock instances first
        This prevents ProtectedError from on_delete=models.PROTECT
        """
        # Delete all ProductUnitStock instances referencing this unit
        from pos_management.models import ProductUnitStock
        ProductUnitStock.objects.filter(unit=instance).delete()
        
        # Now safe to delete the ProductUnit
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle active status"""
        unit = self.get_object()
        unit.is_active = not unit.is_active
        unit.save(update_fields=['is_active'])
        
        serializer = self.get_serializer(unit)
        return Response(serializer.data)


class CategoryUnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Category-Unit links
    """
    queryset = CategoryUnit.objects.all()
    serializer_class = CategoryUnitSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'unit', 'is_primary']
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get all units for a specific category"""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {'error': 'يجب تحديد معرف التصنيف'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        links = self.get_queryset().filter(category_id=category_id)
        serializer = self.get_serializer(links, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Products
    Supports dynamic custom fields based on category
    """
    queryset = AdvancedProduct.objects.select_related('category', 'created_by').prefetch_related('product_units__unit').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'base_price']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProductCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProductUpdateSerializer
        elif self.action in ['retrieve', 'list']:
            return ProductWithUnitsSerializer
        return ProductSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by low stock
        low_stock = self.request.query_params.get('low_stock')
        if low_stock == 'true':
            # Get products with at least one unit below minimum stock
            queryset = queryset.filter(
                product_units__quantity_in_stock__lte=models.F('product_units__minimum_stock')
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def units(self, request, pk=None):
        """Get all units for this product"""
        product = self.get_object()
        units = product.product_units.all()
        serializer = ProductUnitStockSerializer(units, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_unit(self, request, pk=None):
        """Add a unit to product"""
        product = self.get_object()
        
        serializer = ProductUnitStockSerializer(data={
            **request.data,
            'product': product.id
        })
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_unit(self, request, pk=None):
        """Remove a unit from product"""
        product = self.get_object()
        unit_id = request.data.get('unit_id')
        
        if not unit_id:
            return Response(
                {'error': 'يجب تحديد معرف الوحدة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            unit_stock = ProductUnitStock.objects.get(product=product, unit_id=unit_id)
            unit_stock.delete()
            return Response({'success': True, 'message': 'تم حذف الوحدة بنجاح'})
        except ProductUnitStock.DoesNotExist:
            return Response(
                {'error': 'الوحدة غير موجودة'},
                status=status.HTTP_404_NOT_FOUND
            )


class ProductUnitStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Product Unit Stocks
    """
    queryset = ProductUnitStock.objects.select_related('product', 'unit').all()
    serializer_class = ProductUnitStockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'unit', 'is_primary']
    
    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        """Update stock quantity (add/reduce/set)"""
        unit_stock = self.get_object()
        serializer = ProductStockUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            action = serializer.validated_data['action']
            quantity = serializer.validated_data['quantity']
            
            if action == 'add':
                unit_stock.add_stock(quantity)
            elif action == 'reduce':
                if not unit_stock.reduce_stock(quantity):
                    return Response(
                        {'error': 'الكمية المطلوبة أكبر من المخزون المتاح'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif action == 'set':
                unit_stock.set_stock(quantity)
            
            return Response({
                'success': True,
                'message': 'تم تحديث المخزون بنجاح',
                'stock': ProductUnitStockSerializer(unit_stock).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock items"""
        low_stock_items = [item for item in self.get_queryset() if item.is_low_stock]
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """Get all unit stocks for a specific product"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'error': 'يجب تحديد معرف المنتج'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stocks = self.get_queryset().filter(product_id=product_id)
        serializer = self.get_serializer(stocks, many=True)
        
        # Calculate statistics
        total_stock = sum(s.total_pieces for s in stocks)
        low_stock_count = sum(1 for s in stocks if s.is_low_stock)
        
        return Response({
            'product_id': product_id,
            'total_stock': total_stock,
            'low_stock_count': low_stock_count,
            'stocks': serializer.data
        })
