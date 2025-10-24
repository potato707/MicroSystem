#!/usr/bin/env python
"""
Test script to verify the fixed API endpoints are working correctly.
This script tests the main endpoints that were causing 404/500 errors.
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, Team, TeamMembership, User

def test_api_endpoints():
    """Test the fixed API endpoints"""
    print("🔧 Testing Fixed API Endpoints")
    print("=" * 50)
    
    client = Client()
    
    try:
        # Get or create admin user
        User = get_user_model()
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            print("❌ No admin user found - creating test admin")
            admin_user = User.objects.create_user(
                username='test_admin',
                password='testpass123',
                role='admin',
                first_name='Test',
                last_name='Admin'
            )
        
        # Login as admin
        login_success = client.login(username=admin_user.username, password='testpass123')
        if not login_success:
            print("❌ Failed to login as admin")
            return
        
        print(f"✅ Successfully logged in as admin: {admin_user.username}")
        
        # Test 1: Team complaints dashboard endpoint
        print("\n📊 Testing Team Complaints Dashboard...")
        response = client.get('/hr/team-complaints/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Team complaints dashboard working")
        else:
            print(f"   ❌ Team complaints dashboard failed: {response.content}")
        
        # Test 2: Check if we have any complaints to test comments on
        complaints = ClientComplaint.objects.all()[:1]
        if complaints:
            complaint = complaints[0]
            print(f"\n💬 Testing Comments on Complaint {complaint.id}...")
            
            # Test comments list endpoint
            response = client.get(f'/hr/client-complaints/{complaint.id}/comments/')
            print(f"   Comments list status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ Comments list endpoint working")
            else:
                print(f"   ❌ Comments list failed: {response.content}")
            
            # Test creating a comment
            comment_data = {
                'content': 'Test comment from API test',
                'comment_type': 'internal'
            }
            response = client.post(f'/hr/client-complaints/{complaint.id}/comments/', comment_data)
            print(f"   Create comment status: {response.status_code}")
            if response.status_code in [200, 201]:
                print("   ✅ Create comment endpoint working")
            else:
                print(f"   ❌ Create comment failed: {response.content}")
        else:
            print("\n💬 No complaints found to test comments")
        
        # Test 3: General complaints list endpoint
        print("\n📋 Testing General Complaints List...")
        response = client.get('/hr/client-complaints/')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Complaints list working")
        else:
            print(f"   ❌ Complaints list failed: {response.content}")
            
        print("\n" + "=" * 50)
        print("✅ API Endpoint Testing Complete!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_endpoints()