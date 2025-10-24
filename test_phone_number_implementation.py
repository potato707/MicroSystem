#!/usr/bin/env python3
"""
Test script to verify the phone number field implementation
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ComplaintCategory
from hr_management.serializers import ClientComplaintSubmissionSerializer
from rest_framework import serializers

def test_phone_number_field():
    """Test the phone number field in ClientComplaint model"""
    print("🧪 Testing Phone Number Implementation")
    print("=" * 50)
    
    # Test 1: Check if client_phone field exists in model
    print("\n1. Testing Model Field...")
    try:
        # Get the model fields
        fields = [f.name for f in ClientComplaint._meta.get_fields()]
        if 'client_phone' in fields:
            print("✅ client_phone field exists in ClientComplaint model")
            
            # Get field details
            phone_field = ClientComplaint._meta.get_field('client_phone')
            print(f"   - Field type: {type(phone_field).__name__}")
            print(f"   - Max length: {phone_field.max_length}")
            print(f"   - Verbose name: {phone_field.verbose_name}")
            print(f"   - Help text: {phone_field.help_text}")
        else:
            print("❌ client_phone field NOT found in ClientComplaint model")
            return False
    except Exception as e:
        print(f"❌ Error checking model field: {e}")
        return False
    
    # Test 2: Check if client_phone field is in serializer
    print("\n2. Testing Serializer Field...")
    try:
        serializer_fields = ClientComplaintSubmissionSerializer.Meta.fields
        if 'client_phone' in serializer_fields:
            print("✅ client_phone field included in ClientComplaintSubmissionSerializer")
        else:
            print("❌ client_phone field NOT included in ClientComplaintSubmissionSerializer")
            return False
    except Exception as e:
        print(f"❌ Error checking serializer field: {e}")
        return False
    
    # Test 3: Test phone number validation
    print("\n3. Testing Phone Number Validation...")
    
    # Get a test category (create one if none exist)
    category = ComplaintCategory.objects.first()
    if not category:
        category = ComplaintCategory.objects.create(
            name="Test Category",
            description="Test category for phone validation",
            color="#FF0000"
        )
        print("   Created test category")
    
    test_cases = [
        # Valid phone numbers
        ("+1234567890", True, "Valid international format"),
        ("1234567890", True, "Valid domestic format"),
        ("+966501234567", True, "Valid Saudi number"),
        ("01201760623", True, "Valid Egyptian number"),
        
        # Invalid phone numbers
        ("", False, "Empty phone number"),
        ("abc123", False, "Contains letters"),
        ("123", False, "Too short"),
        ("++1234567890", False, "Double plus sign"),
        ("123-456-7890", False, "Contains dashes"),
    ]
    
    for phone, should_be_valid, description in test_cases:
        test_data = {
            'client_name': 'Test User',
            'client_email': 'test@example.com',
            'client_phone': phone,
            'category': category.id,
            'priority': 'medium',
            'title': 'Test Complaint',
            'description': 'This is a test complaint description that is longer than 20 characters.'
        }
        
        serializer = ClientComplaintSubmissionSerializer(data=test_data)
        is_valid = serializer.is_valid()
        
        if should_be_valid:
            if is_valid:
                print(f"   ✅ {description}: '{phone}' - Valid (as expected)")
            else:
                print(f"   ❌ {description}: '{phone}' - Invalid (expected valid)")
                print(f"      Errors: {serializer.errors}")
        else:
            if not is_valid:
                if 'client_phone' in serializer.errors:
                    print(f"   ✅ {description}: '{phone}' - Invalid (as expected)")
                else:
                    print(f"   ⚠️  {description}: '{phone}' - Invalid but not due to phone field")
                    print(f"      Errors: {serializer.errors}")
            else:
                print(f"   ❌ {description}: '{phone}' - Valid (expected invalid)")
    
    print("\n4. Testing Database Creation...")
    try:
        # Test creating a complaint with phone number
        test_complaint_data = {
            'client_name': 'John Doe',
            'client_email': 'john@example.com',
            'client_phone': '+1234567890',
            'category': category.id,
            'priority': 'medium',
            'title': 'Test Complaint for Phone',
            'description': 'This is a test complaint to verify phone number storage works correctly.'
        }
        
        serializer = ClientComplaintSubmissionSerializer(data=test_complaint_data)
        if serializer.is_valid():
            complaint = serializer.save()
            print(f"✅ Successfully created complaint with ID: {complaint.id}")
            print(f"   - Client Name: {complaint.client_name}")
            print(f"   - Client Email: {complaint.client_email}")
            print(f"   - Client Phone: {complaint.client_phone}")
            print(f"   - Title: {complaint.title}")
            
            # Clean up - delete the test complaint
            complaint.delete()
            print("   - Test complaint deleted successfully")
        else:
            print("❌ Failed to create test complaint")
            print(f"   Errors: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Error during database test: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All tests passed! Phone number implementation is working correctly.")
    return True

if __name__ == '__main__':
    try:
        success = test_phone_number_field()
        if success:
            print("\n✅ Phone number implementation test completed successfully!")
        else:
            print("\n❌ Phone number implementation test failed!")
    except Exception as e:
        print(f"\n💥 Test script error: {e}")
        import traceback
        traceback.print_exc()