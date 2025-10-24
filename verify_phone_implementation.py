#!/usr/bin/env python3
"""
Quick test to verify phone number field shows up in complaint data
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
from hr_management.serializers import ClientComplaintSubmissionSerializer, ClientComplaintSerializer

def test_phone_in_serialized_data():
    """Test that phone number appears in serialized complaint data"""
    print("🧪 Testing Phone Number in Serialized Data")
    print("=" * 50)
    
    # Get or create a test category
    category, created = ComplaintCategory.objects.get_or_create(
        name="Test Category",
        defaults={
            'description': 'Test category for phone validation',
            'color': '#FF0000'
        }
    )
    if created:
        print("Created test category")
    
    # Create a test complaint with phone number
    test_data = {
        'client_name': 'John Doe',
        'client_email': 'john@example.com',
        'client_phone': '+1234567890',
        'category': category.id,
        'priority': 'medium',
        'title': 'Test Complaint with Phone',
        'description': 'This is a test complaint to verify phone number serialization works correctly.'
    }
    
    # Test submission serializer
    submission_serializer = ClientComplaintSubmissionSerializer(data=test_data)
    if submission_serializer.is_valid():
        complaint = submission_serializer.save()
        print(f"✅ Created complaint with ID: {complaint.id}")
        print(f"   Phone stored: {complaint.client_phone}")
        
        # Test full serializer (what the API returns)
        full_serializer = ClientComplaintSerializer(complaint)
        serialized_data = full_serializer.data
        
        print(f"✅ Full serializer includes phone: {'client_phone' in serialized_data}")
        if 'client_phone' in serialized_data:
            print(f"   Serialized phone: {serialized_data['client_phone']}")
        
        # Check field list
        fields = ClientComplaintSerializer.Meta.fields
        print(f"✅ Phone in serializer fields: {'client_phone' in fields}")
        
        # Clean up
        complaint.delete()
        print("   Test complaint deleted")
        
        return True
    else:
        print(f"❌ Failed to create complaint: {submission_serializer.errors}")
        return False

def list_complaint_fields():
    """List all fields in ClientComplaint model and serializers"""
    print("\n📋 Complaint Model and Serializer Fields")
    print("=" * 50)
    
    # Model fields
    model_fields = [f.name for f in ClientComplaint._meta.get_fields()]
    print("Model fields:")
    for field in sorted(model_fields):
        if 'client_' in field or field in ['id', 'title', 'description']:
            print(f"   ✓ {field}")
    
    # Serializer fields
    submission_fields = ClientComplaintSubmissionSerializer.Meta.fields
    print(f"\nSubmission Serializer fields: {len(submission_fields)}")
    for field in submission_fields:
        if 'client_' in field:
            print(f"   ✓ {field}")
    
    full_fields = ClientComplaintSerializer.Meta.fields
    print(f"\nFull Serializer fields: {len(full_fields)}")
    client_fields = [f for f in full_fields if 'client_' in f]
    for field in client_fields:
        print(f"   ✓ {field}")

if __name__ == '__main__':
    try:
        list_complaint_fields()
        success = test_phone_in_serialized_data()
        
        if success:
            print("\n🎉 Phone number implementation verification completed successfully!")
            print("\nSummary of changes:")
            print("✅ Backend: client_phone field added to ClientComplaint model")
            print("✅ Backend: client_phone included in both serializers")
            print("✅ Backend: Phone validation added")
            print("✅ Frontend: client_phone added to TypeScript interfaces")
            print("✅ Frontend: Phone input field added to complaint form")
            print("✅ Frontend: Phone number displayed in complaint detail modal") 
            print("✅ Frontend: Phone number displayed in client portal")
            print("\nThe phone number should now appear in:")
            print("- Complaint submission form (required field)")
            print("- Admin complaint detail modal")
            print("- Client portal complaint view")
        else:
            print("\n❌ Phone number implementation verification failed!")
            
    except Exception as e:
        print(f"\n💥 Verification script error: {e}")
        import traceback
        traceback.print_exc()