from rest_framework import serializers
from .models import ClientType, Client, SimpleProduct, Distribution, ClientInventory
from django.contrib.auth import get_user_model

User = get_user_model()


class ClientTypeSerializer(serializers.ModelSerializer):
    """Serializer for ClientType model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    clients_count = serializers.ReadOnlyField()
    
    class Meta:
        model = ClientType
        fields = [
            'id', 'name', 'description', 'icon', 'color',
            'custom_fields', 'is_active', 'clients_count',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate_custom_fields(self, value):
        """Validate custom fields structure"""
        if not isinstance(value, list):
            raise serializers.ValidationError("custom_fields must be a list")
        
        for field in value:
            if not isinstance(field, dict):
                raise serializers.ValidationError("Each custom field must be a dictionary")
            
            required_keys = ['name', 'label', 'type']
            for key in required_keys:
                if key not in field:
                    raise serializers.ValidationError(f"Each custom field must have '{key}'")
            
            valid_types = ['text', 'number', 'email', 'phone', 'select', 'textarea', 'date', 'url']
            if field['type'] not in valid_types:
                raise serializers.ValidationError(f"Invalid field type: {field['type']}")
            
            if field['type'] == 'select' and 'options' not in field:
                raise serializers.ValidationError("Select fields must have 'options'")
        
        return value


class ClientSerializer(serializers.ModelSerializer):
    """Serializer for Client model"""
    client_type_name = serializers.CharField(source='client_type.name', read_only=True)
    client_type_color = serializers.CharField(source='client_type.color', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    # Computed fields
    total_distributions = serializers.ReadOnlyField()
    next_visit_date = serializers.ReadOnlyField()
    upcoming_visit_days = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = [
            'id', 'name', 'client_type', 'client_type_name', 'client_type_color',
            'contact_person', 'email', 'phone', 'phone2',
            'category', 'category_display', 'status', 'status_display',
            'custom_data', 'notes', 'description',
            'created_by', 'created_by_name', 'assigned_to', 'assigned_to_name',
            'total_distributions', 'next_visit_date', 'upcoming_visit_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def validate_custom_data(self, value):
        """Validate custom data against client type fields"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("custom_data must be a dictionary")
        
        # Get client type
        client_type_id = self.initial_data.get('client_type')
        if client_type_id:
            try:
                client_type = ClientType.objects.get(id=client_type_id)
                
                # Validate required fields
                for field in client_type.custom_fields:
                    if field.get('required', False):
                        field_name = field['name']
                        if field_name not in value or not value[field_name]:
                            raise serializers.ValidationError(
                                f"Required field '{field.get('label', field_name)}' is missing"
                            )
                
                # Validate field types
                for field_name, field_value in value.items():
                    # Find field definition
                    field_def = next((f for f in client_type.custom_fields if f['name'] == field_name), None)
                    if field_def:
                        field_type = field_def['type']
                        
                        # Basic type validation
                        if field_type == 'number':
                            try:
                                float(field_value)
                            except (ValueError, TypeError):
                                raise serializers.ValidationError(f"Field '{field_name}' must be a number")
                        
                        elif field_type == 'email':
                            from django.core.validators import validate_email
                            try:
                                validate_email(field_value)
                            except:
                                raise serializers.ValidationError(f"Field '{field_name}' must be a valid email")
                        
                        elif field_type == 'select' and 'options' in field_def:
                            if field_value not in field_def['options']:
                                raise serializers.ValidationError(
                                    f"Field '{field_name}' must be one of: {', '.join(field_def['options'])}"
                                )
            
            except ClientType.DoesNotExist:
                pass
        
        return value


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)
    total_distributed = serializers.ReadOnlyField()
    
    class Meta:
        model = SimpleProduct
        fields = [
            'id', 'name', 'description', 'product_type', 'product_type_display',
            'base_price', 'is_active', 'total_distributed',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class DistributionSerializer(serializers.ModelSerializer):
    """Serializer for Distribution model"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    client_status = serializers.CharField(source='client.status', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    # Computed fields
    days_until_visit = serializers.ReadOnlyField()
    is_visit_due = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Distribution
        fields = [
            'id', 'client', 'client_name', 'client_status',
            'product', 'product_name',
            'quantity', 'price', 'total_amount',
            'visit_interval_days', 'last_visit_date', 'next_visit_date',
            'reminder_days_before',
            'days_until_visit', 'is_visit_due', 'is_overdue',
            'status', 'status_display', 'notes',
            'created_by', 'created_by_name', 'distributed_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_amount', 'created_by', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Validate distribution data"""
        return data
    
    def create(self, validated_data):
        """Create distribution"""
        distribution = super().create(validated_data)
        return distribution
    
    def update(self, instance, validated_data):
        """Update distribution"""
        distribution = super().update(instance, validated_data)
        return distribution


class DistributionCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for creating distributions"""
    use_custom_price = serializers.BooleanField(write_only=True, required=False, default=False)
    
    class Meta:
        model = Distribution
        fields = [
            'client', 'product', 'quantity', 'price', 'use_custom_price',
            'visit_interval_days', 'reminder_days_before',
            'last_visit_date', 'status', 'notes'
        ]
    
    def validate(self, data):
        """Auto-fill price from product base price"""
        product = data.get('product')
        use_custom_price = data.pop('use_custom_price', False)
        
        # If price not provided, use product base price
        if 'price' not in data or data['price'] is None:
            data['price'] = product.base_price
        
        return data
    
    def create(self, validated_data):
        """Create distribution and auto-calculate next_visit_date"""
        from datetime import timedelta
        
        # Remove use_custom_price if it still exists
        validated_data.pop('use_custom_price', None)
        
        distribution = super().create(validated_data)
        
        # Auto-calculate next_visit_date based on distributed_at + visit_interval_days
        if distribution.distributed_at and distribution.visit_interval_days:
            distribution.next_visit_date = distribution.distributed_at.date() + timedelta(days=distribution.visit_interval_days)
            distribution.save(update_fields=['next_visit_date'])
        
        return distribution


# Statistics Serializers
class POSDashboardStatsSerializer(serializers.Serializer):
    """Serializer for POS dashboard statistics"""
    total_clients = serializers.IntegerField()
    active_clients = serializers.IntegerField()
    potential_clients = serializers.IntegerField()
    total_distributions = serializers.IntegerField()
    upcoming_visits = serializers.IntegerField()
    overdue_visits = serializers.IntegerField()
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Lists
    recent_distributions = DistributionSerializer(many=True)
    upcoming_visit_distributions = DistributionSerializer(many=True)


class ClientInventorySerializer(serializers.ModelSerializer):
    """Serializer for ClientInventory model"""
    client_name = serializers.CharField(source='client.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_type = serializers.CharField(source='product.product_type', read_only=True)
    last_updated_by_name = serializers.CharField(source='last_updated_by.username', read_only=True)
    
    # Computed fields
    inventory_status = serializers.ReadOnlyField()
    inventory_status_display = serializers.ReadOnlyField()
    inventory_percentage = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_out_of_stock = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    is_expiring_soon = serializers.ReadOnlyField()
    
    class Meta:
        model = ClientInventory
        fields = [
            'id', 'client', 'client_name', 'product', 'product_name', 'product_type',
            'current_quantity', 'minimum_quantity', 'maximum_quantity',
            'expiry_date', 'location', 'notes',
            'inventory_status', 'inventory_status_display', 'inventory_percentage',
            'is_low_stock', 'is_out_of_stock',
            'days_until_expiry', 'is_expired', 'is_expiring_soon',
            'last_updated_by', 'last_updated_by_name', 'last_distribution',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_updated_by', 'last_distribution', 'created_at', 'updated_at']
    
    def validate_expiry_date(self, value):
        """Allow empty string for optional expiry_date"""
        if value == '' or value is None:
            return None
        return value
    
    def validate_location(self, value):
        """Allow empty string for optional location"""
        if value == '' or value is None:
            return None
        return value
    
    def validate_notes(self, value):
        """Allow empty string for optional notes"""
        if value == '' or value is None:
            return None
        return value
    
    def validate(self, data):
        """Validate inventory data"""
        current_quantity = data.get('current_quantity', 0)
        minimum_quantity = data.get('minimum_quantity', 0)
        maximum_quantity = data.get('maximum_quantity', 100)
        
        if current_quantity < 0:
            raise serializers.ValidationError("Current quantity cannot be negative")
        
        if minimum_quantity < 0:
            raise serializers.ValidationError("Minimum quantity cannot be negative")
        
        if maximum_quantity <= 0:
            raise serializers.ValidationError("Maximum quantity must be greater than 0")
        
        if minimum_quantity > maximum_quantity:
            raise serializers.ValidationError("Minimum quantity cannot be greater than maximum quantity")
        
        # Duplicate check is handled in the viewset's create() method
        # to provide better error messages with existing inventory details
        
        return data


class ClientInventoryUpdateSerializer(serializers.Serializer):
    """Serializer for updating inventory quantities"""
    ACTION_CHOICES = [
        ('add', 'إضافة'),
        ('reduce', 'تقليل'),
        ('set', 'تعيين'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES, required=True)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value


class ClientInventoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing inventory"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    inventory_status = serializers.ReadOnlyField()
    inventory_percentage = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_expiring_soon = serializers.ReadOnlyField()
    
    class Meta:
        model = ClientInventory
        fields = [
            'id', 'product', 'product_name',
            'current_quantity', 'minimum_quantity', 'maximum_quantity',
            'expiry_date', 'location',
            'inventory_status', 'inventory_percentage',
            'is_low_stock', 'is_expiring_soon',
            'updated_at'
        ]

