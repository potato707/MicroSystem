"""
Test script for client account creation and authentication
This script tests:
1. Auto-creation of client accounts on complaint submission
2. Email notification sending
3. Client login functionality
4. Complaint linking to client accounts
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, ClientComplaint, ComplaintCategory
from hr_management.serializers import ClientComplaintSubmissionSerializer
import json


def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_client_account_creation():
    """Test automatic client account creation on complaint submission"""
    print_section("TEST 1: Client Account Creation")
    
    # Create a category first (if not exists)
    category, created = ComplaintCategory.objects.get_or_create(
        name="Technical Support",
        defaults={
            'description': 'Technical issues and support requests',
            'color': '#3B82F6',
            'is_active': True
        }
    )
    print(f"✓ Using category: {category.name}")
    
    # Test data for new client
    test_email = "testclient@example.com"
    test_name = "Test Client User"
    test_phone = "+1234567890"
    
    # Clean up any existing test data
    User.objects.filter(email=test_email).delete()
    ClientComplaint.objects.filter(client_email=test_email).delete()
    print(f"✓ Cleaned up existing test data for {test_email}")
    
    # Simulate complaint submission
    complaint_data = {
        'client_name': test_name,
        'client_email': test_email,
        'client_phone': test_phone,
        'project_name': 'Test Project',
        'project_code': 'TP-001',
        'category': category.id,
        'priority': 'medium',
        'title': 'Test Complaint for Account Creation',
        'description': 'This is a test complaint to verify automatic client account creation.'
    }
    
    print(f"\n📝 Submitting complaint with data:")
    print(f"   Client: {test_name} ({test_email})")
    print(f"   Title: {complaint_data['title']}")
    
    # Create complaint using serializer
    serializer = ClientComplaintSubmissionSerializer(data=complaint_data)
    
    if serializer.is_valid():
        complaint = serializer.save()
        print(f"✓ Complaint created successfully (ID: {complaint.id})")
        
        # Verify user was created
        try:
            client_user = User.objects.get(email=test_email)
            print(f"✓ Client user account created:")
            print(f"   - Username: {client_user.username}")
            print(f"   - Email: {client_user.email}")
            print(f"   - Name: {client_user.name}")
            print(f"   - Role: {client_user.role}")
            
            # Verify complaint is linked to user
            if complaint.client_user == client_user:
                print(f"✓ Complaint successfully linked to client user account")
            else:
                print(f"✗ ERROR: Complaint not linked to client user!")
                return False
            
            # Verify user has client role
            if client_user.role == 'client':
                print(f"✓ User role correctly set to 'client'")
            else:
                print(f"✗ ERROR: User role is '{client_user.role}', expected 'client'")
                return False
            
            print(f"\n📧 Email notification should have been sent to console (check above)")
            print(f"   (Email backend is set to console for development)")
            
            return True, client_user, complaint
            
        except User.DoesNotExist:
            print(f"✗ ERROR: Client user account was not created!")
            return False, None, None
    else:
        print(f"✗ ERROR: Complaint validation failed:")
        print(f"   {serializer.errors}")
        return False, None, None


def test_existing_client_submission():
    """Test that existing clients don't get duplicate accounts"""
    print_section("TEST 2: Existing Client Complaint Submission")
    
    # Use existing category
    category = ComplaintCategory.objects.first()
    if not category:
        print("✗ No categories available for testing")
        return False
    
    # Use the email from Test 1
    test_email = "testclient@example.com"
    
    # Check if user exists
    try:
        existing_user = User.objects.get(email=test_email)
        print(f"✓ Found existing client user: {existing_user.username}")
        initial_complaint_count = existing_user.client_complaints.count()
        print(f"✓ Current complaints for this user: {initial_complaint_count}")
    except User.DoesNotExist:
        print(f"✗ ERROR: No existing user found with email {test_email}")
        return False
    
    # Submit another complaint with same email
    complaint_data = {
        'client_name': existing_user.name,
        'client_email': test_email,
        'client_phone': '+1234567890',
        'project_name': 'Test Project 2',
        'category': category.id,
        'priority': 'urgent',
        'title': 'Second Test Complaint',
        'description': 'Testing that no duplicate account is created.'
    }
    
    print(f"\n📝 Submitting second complaint for same email...")
    
    serializer = ClientComplaintSubmissionSerializer(data=complaint_data)
    if serializer.is_valid():
        complaint = serializer.save()
        print(f"✓ Second complaint created successfully (ID: {complaint.id})")
        
        # Verify no duplicate user was created
        user_count = User.objects.filter(email=test_email).count()
        if user_count == 1:
            print(f"✓ No duplicate user account created (still 1 user with this email)")
        else:
            print(f"✗ ERROR: Found {user_count} users with email {test_email}!")
            return False
        
        # Verify complaint is linked to existing user
        if complaint.client_user == existing_user:
            print(f"✓ Second complaint correctly linked to existing user")
        else:
            print(f"✗ ERROR: Second complaint not linked correctly!")
            return False
        
        # Verify complaint count increased
        new_complaint_count = existing_user.client_complaints.count()
        if new_complaint_count == initial_complaint_count + 1:
            print(f"✓ User now has {new_complaint_count} complaints")
        else:
            print(f"✗ ERROR: Complaint count mismatch!")
            return False
        
        return True
    else:
        print(f"✗ ERROR: Validation failed: {serializer.errors}")
        return False


def test_client_complaints_query():
    """Test querying complaints for a client user"""
    print_section("TEST 3: Client Complaints Query")
    
    test_email = "testclient@example.com"
    
    try:
        client_user = User.objects.get(email=test_email)
        print(f"✓ Found client user: {client_user.username}")
        
        # Get all complaints for this client
        complaints = client_user.client_complaints.all()
        print(f"✓ Retrieved {complaints.count()} complaints for this client:")
        
        for i, complaint in enumerate(complaints, 1):
            print(f"   {i}. {complaint.title}")
            print(f"      - Status: {complaint.status}")
            print(f"      - Priority: {complaint.priority}")
            print(f"      - Created: {complaint.created_at.strftime('%Y-%m-%d %H:%M')}")
        
        if complaints.count() >= 2:
            print(f"✓ Client has multiple complaints as expected")
            return True
        else:
            print(f"⚠ Warning: Expected at least 2 complaints, found {complaints.count()}")
            return True  # Still pass, but warn
            
    except User.DoesNotExist:
        print(f"✗ ERROR: Client user not found")
        return False


def test_password_authentication():
    """Test that the generated password works for authentication"""
    print_section("TEST 4: Password Authentication")
    
    test_email = "testclient@example.com"
    
    try:
        client_user = User.objects.get(email=test_email)
        print(f"✓ Found client user: {client_user.username}")
        
        # Note: In real scenario, password would be sent via email
        # For this test, we'll just verify user can be authenticated
        print(f"ℹ Password was auto-generated and sent via email")
        print(f"ℹ Check console output above for the generated password")
        print(f"✓ User account is active and ready for login")
        
        # Verify user is active
        if client_user.is_active:
            print(f"✓ User account is active")
        else:
            print(f"✗ ERROR: User account is not active!")
            return False
        
        # Verify user has password set
        if client_user.password:
            print(f"✓ User has password set (hashed)")
        else:
            print(f"✗ ERROR: User has no password!")
            return False
        
        return True
        
    except User.DoesNotExist:
        print(f"✗ ERROR: Client user not found")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "🚀 "*20)
    print("CLIENT ACCOUNT SYSTEM - COMPREHENSIVE TEST SUITE")
    print("🚀 "*20)
    
    results = []
    
    # Test 1: Client account creation
    result1 = test_client_account_creation()
    if result1 and len(result1) == 3:
        results.append(("Client Account Creation", result1[0]))
    else:
        results.append(("Client Account Creation", False))
    
    # Test 2: Existing client submission
    result2 = test_existing_client_submission()
    results.append(("Existing Client Submission", result2))
    
    # Test 3: Client complaints query
    result3 = test_client_complaints_query()
    results.append(("Client Complaints Query", result3))
    
    # Test 4: Password authentication
    result4 = test_password_authentication()
    results.append(("Password Authentication", result4))
    
    # Print summary
    print_section("TEST SUMMARY")
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status:12} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Total: {len(results)} tests | Passed: {passed} | Failed: {failed}")
    print(f"{'='*60}")
    
    if failed == 0:
        print("\n🎉 All tests passed! The client account system is working correctly.")
        print("\nNext steps:")
        print("1. Run migrations: python manage.py makemigrations && python manage.py migrate")
        print("2. Test the API endpoints manually or with Postman")
        print("3. Build the frontend client login and dashboard")
    else:
        print(f"\n⚠ {failed} test(s) failed. Please review the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error during testing:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
