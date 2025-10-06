#!/usr/bin/env python3
"""
Test authentication redirect functionality
This script demonstrates how the authentication flow should work
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.test import Client
from hr_management.models import Employee, User

def test_authentication_redirect_flow():
    """Test that unauthenticated users are redirected properly"""
    print("🧪 TESTING AUTHENTICATION REDIRECT FLOW\n")
    print("=" * 60)
    
    client = Client()
    
    # Test 1: Try to access dashboard without login (should fail)
    print("🔒 Test 1: Access dashboard without authentication")
    
    # Try to make an API call that requires authentication
    response = client.get('/hr/employee-dashboard-stats/')
    print(f"   Response Status: {response.status_code}")
    
    if response.status_code == 401:
        print("   ✅ Correctly returns 401 Unauthorized")
    elif response.status_code == 403:
        print("   ✅ Correctly returns 403 Forbidden")
    else:
        print(f"   ❓ Unexpected response: {response.status_code}")
    
    print()
    
    # Test 2: Login and then access dashboard
    print("🔓 Test 2: Login and access dashboard")
    
    # Get an active employee
    active_employee = Employee.objects.filter(status='active', user__isnull=False).first()
    
    if active_employee:
        # Set a known password
        active_employee.user.set_password('testpass123')
        active_employee.user.save()
        
        # Login
        login_data = {
            "username": active_employee.user.username,
            "password": "testpass123"
        }
        
        login_response = client.post('/api/token/', 
                                   data=json.dumps(login_data), 
                                   content_type='application/json')
        
        print(f"   Login Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            print("   ✅ Login successful")
            
            # Extract token and make authenticated request
            login_data = login_response.json()
            token = login_data.get('access')
            
            # Make authenticated API call
            auth_response = client.get('/hr/employee-dashboard-stats/', 
                                     HTTP_AUTHORIZATION=f'Bearer {token}')
            
            print(f"   Dashboard Access Status: {auth_response.status_code}")
            
            if auth_response.status_code == 200:
                print("   ✅ Successfully accessed dashboard with authentication")
                data = auth_response.json()
                print(f"   📊 Dashboard data received: {list(data.keys())}")
            else:
                print(f"   ❌ Failed to access dashboard: {auth_response.content.decode()}")
                
        else:
            print(f"   ❌ Login failed: {login_response.content.decode()}")
    else:
        print("   ❌ No active employee found for testing")
    
    print()
    
    # Test 3: Test with inactive employee (should fail after login check)
    print("🚫 Test 3: Login with inactive employee")
    
    inactive_employee = Employee.objects.filter(status='terminated', user__isnull=False).first()
    
    if inactive_employee:
        # Set a known password
        inactive_employee.user.set_password('testpass123')
        inactive_employee.user.save()
        
        # Try to login
        login_data = {
            "username": inactive_employee.user.username,
            "password": "testpass123"
        }
        
        login_response = client.post('/api/token/', 
                                   data=json.dumps(login_data), 
                                   content_type='application/json')
        
        print(f"   Login Status: {login_response.status_code}")
        print(f"   Employee Status: {inactive_employee.status}")
        
        if login_response.status_code == 403:
            print("   ✅ Correctly blocked inactive employee from logging in")
        elif login_response.status_code == 200:
            print("   ❌ Inactive employee was allowed to login (this should not happen)")
        else:
            print(f"   ❓ Unexpected response: {login_response.content.decode()}")
    else:
        print("   ❌ No inactive employee found for testing")
    
    print()
    print("=" * 60)
    print("✅ AUTHENTICATION REDIRECT FLOW TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_authentication_redirect_flow()