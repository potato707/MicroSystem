"""
Serializers for Advanced Product Management System
"""
from rest_framework import serializers
from .models import (
    ProductCategory,
    ProductUnit,
    CategoryUnit,
    AdvancedProduct,
    ProductUnitStock
)


class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for ProductCategory model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    products_count = serializers.ReadOnlyField()
    units_count = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'custom_fields', 'image', 'is_active',
            'products_count', 'units_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate_custom_fields(self, value):
        """Validate custom fields structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("يجب أن تكون custom_fields قائمة")
        
        for field in value:
            if not isinstance(field, dict):
                raise serializers.ValidationError("كل حقل مخصص يجب أن يكون قاموس")
            
            required_keys = ['name', 'label', 'type']
            for key in required_keys:
                if key not in field:
                    raise serializers.ValidationError(f"كل حقل مخصص يجب أن يحتوي على '{key}'")
            
            valid_types = ['text', 'number', 'decimal', 'date', 'select', 'checkbox', 'textarea', 'email', 'phone', 'url']
            if field['type'] not in valid_types:
                raise serializers.ValidationError(f"نوع الحقل غير صحيح: {field['type']}")
            
            if field['type'] == 'select' and 'options' not in field:
                raise serializers.ValidationError("حقول القائمة المنسدلة يجب أن تحتوي على 'options'")
        
        return value


class ProductUnitSerializer(serializers.ModelSerializer):
    """Serializer for ProductUnit model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    products_count = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductUnit
        fields = [
            'id', 'name', 'short_name', 'description',
            'custom_fields', 'is_countable', 'is_active',
            'products_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate_custom_fields(self, value):
        """Validate custom fields structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("يجب أن تكون custom_fields قائمة")
        
        for field in value:
            if not isinstance(field, dict):
                raise serializers.ValidationError("كل حقل مخصص يجب أن يكون قاموس")
            
            required_keys = ['name', 'label', 'type']
            for key in required_keys:
                if key not in field:
                    raise serializers.ValidationError(f"كل حقل مخصص يجب أن يحتوي على '{key}'")
        
        return value


class CategoryUnitSerializer(serializers.ModelSerializer):
    """Serializer for CategoryUnit model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_short_name = serializers.CharField(source='unit.short_name', read_only=True)
    
    class Meta:
        model = CategoryUnit
        fields = [
            'id', 'category', 'category_name',
            'unit', 'unit_name', 'unit_short_name',
            'default_pieces_per_unit', 'is_primary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CategoryUnitCreateSerializer(serializers.Serializer):
    """Simplified serializer for creating multiple category-unit links"""
    unit_id = serializers.UUIDField()
    default_pieces_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2, default=1)
    is_primary = serializers.BooleanField(default=False)


class ProductCategoryWithUnitsSerializer(ProductCategorySerializer):
    """Extended category serializer with units"""
    category_units = CategoryUnitSerializer(many=True, read_only=True)
    
    class Meta(ProductCategorySerializer.Meta):
        fields = ProductCategorySerializer.Meta.fields + ['category_units']


class ProductUnitStockSerializer(serializers.ModelSerializer):
    """Serializer for ProductUnitStock model - quantity_in_stock is calculated"""
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_short_name = serializers.CharField(source='unit.short_name', read_only=True)
    quantity_in_stock = serializers.ReadOnlyField()  # Calculated from total_stock_pieces
    total_pieces = serializers.ReadOnlyField()  # Always product's total_stock_pieces
    is_low_stock = serializers.ReadOnlyField()  # From product
    
    class Meta:
        model = ProductUnitStock
        fields = [
            'id', 'product', 'unit', 'unit_name', 'unit_short_name',
            'pieces_per_unit', 'quantity_in_stock',
            'custom_data', 'unit_price', 'is_primary',
            'total_pieces', 'is_low_stock',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'quantity_in_stock', 'total_pieces', 'is_low_stock', 'created_at', 'updated_at']
    
    def validate_custom_data(self, value):
        """Validate custom data against unit custom fields"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("يجب أن تكون custom_data قاموس")
        return value


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    total_stock = serializers.ReadOnlyField()  # Property that returns total_stock_pieces
    is_low_stock = serializers.ReadOnlyField()  # Property
    units_count = serializers.ReadOnlyField()
    
    class Meta:
        model = AdvancedProduct
        fields = [
            'id', 'name', 'category', 'category_name', 'category_color',
            'description', 'custom_data', 'image',
            'base_price',
            'total_stock_pieces', 'minimum_stock_pieces',
            'total_stock', 'is_low_stock', 'units_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate_custom_data(self, value):
        """Validate custom data against category custom fields"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("يجب أن تكون custom_data قاموس")
        
        # Get category
        category_id = self.initial_data.get('category')
        if category_id:
            try:
                category = ProductCategory.objects.get(id=category_id)
                
                # Validate required fields
                for field in category.custom_fields:
                    if field.get('required', False):
                        field_name = field['name']
                        if field_name not in value or not value[field_name]:
                            raise serializers.ValidationError(
                                f"الحقل الإلزامي '{field.get('label', field_name)}' مفقود"
                            )
                
            except ProductCategory.DoesNotExist:
                pass
        
        return value


class ProductWithUnitsSerializer(ProductSerializer):
    """Extended product serializer with units"""
    product_units = ProductUnitStockSerializer(many=True, read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['product_units']


class ProductUnitStockCreateSerializer(serializers.Serializer):
    """Simplified serializer for creating product unit stocks - no quantity_in_stock"""
    unit_id = serializers.UUIDField()
    pieces_per_unit = serializers.DecimalField(max_digits=10, decimal_places=2, default=1)
    custom_data = serializers.JSONField(default=dict)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_primary = serializers.BooleanField(default=False)


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products with units in one request"""
    units = ProductUnitStockCreateSerializer(many=True, write_only=True, required=False)
    total_stock_pieces = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    
    class Meta:
        model = AdvancedProduct
        fields = [
            'name', 'category', 'description', 'custom_data', 'image',
            'base_price', 'total_stock_pieces', 'minimum_stock_pieces', 'units'
        ]
    
    def create(self, validated_data):
        units_data = validated_data.pop('units', [])
        
        # Create product
        product = AdvancedProduct.objects.create(**validated_data)
        
        # Create product unit display entries (no stock data)
        for unit_data in units_data:
            unit_id = unit_data.pop('unit_id')
            ProductUnitStock.objects.create(
                product=product,
                unit_id=unit_id,
                **unit_data
            )
        
        return product


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating products"""
    units = serializers.ListField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = AdvancedProduct
        fields = [
            'name', 'description', 'custom_data', 'image',
            'base_price', 'total_stock_pieces', 'minimum_stock_pieces', 'units'
        ]
    
    def update(self, instance, validated_data):
        import json
        units_data = validated_data.pop('units', None)
        
        # Parse units_data if it's a JSON string (from FormData)
        if units_data is not None and isinstance(units_data, str):
            try:
                units_data = json.loads(units_data)
            except (json.JSONDecodeError, TypeError):
                units_data = None
        elif isinstance(units_data, list) and len(units_data) == 1 and isinstance(units_data[0], str):
            try:
                units_data = json.loads(units_data[0])
            except json.JSONDecodeError:
                units_data = None
        
        # Update basic product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update units if provided
        if units_data is not None and isinstance(units_data, list):
            # Delete existing units
            ProductUnitStock.objects.filter(product=instance).delete()
            
            # Create new units
            for unit_data in units_data:
                print(unit_data, units_data, ProductUnit.objects.get(id=unit_data['unit_id']))
                ProductUnitStock.objects.create(
                    product=instance,
                    unit=ProductUnit.objects.get(id=unit_data['unit_id']),
                    pieces_per_unit=unit_data.get('pieces_per_unit', 1),
                    # quantity_in_stock=unit_data.get('quantity_in_stock', 0),
                    # minimum_stock=unit_data.get('minimum_stock', 0),
                    custom_data=unit_data.get('custom_data', {}),
                    unit_price=unit_data.get('unit_price', 0),
                    is_primary=unit_data.get('is_primary', False),
                )
        
        return instance

class ProductStockUpdateSerializer(serializers.Serializer):
    """Serializer for updating product stock"""
    ACTION_CHOICES = [
        ('add', 'إضافة'),
        ('reduce', 'تقليل'),
        ('set', 'تعيين'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES, required=True)
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value < 0:
            raise serializers.ValidationError("الكمية لا يمكن أن تكون سالبة")
        return value
