#!/usr/bin/env python3
"""
Test the actual JWT authentication API calls
"""
import os
import sys
import django
import requests
import json

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, User

def test_login_api():
    """Test the actual login API with active and inactive employees"""
    print("=== Testing Login API ===\n")
    
    base_url = "http://127.0.0.1:8000"  # Adjust if your server runs on different port
    login_url = f"{base_url}/api/token/"
    
    # Test 1: Login with active employee
    print("🔓 Test 1: Login with ACTIVE employee")
    active_employee = Employee.objects.filter(status='active', user__isnull=False).first()
    
    if active_employee:
        # Set a known password for testing
        active_employee.user.set_password('testpass123')
        active_employee.user.save()
        
        login_data = {
            "username": active_employee.user.username,
            "password": "testpass123"
        }
        
        try:
            response = requests.post(login_url, json=login_data)
            print(f"   Username: {login_data['username']}")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Login successful (as expected)")
                data = response.json()
                print(f"   🔑 Access token received: {data.get('access', '')[:50]}...")
            else:
                print(f"   ❌ Login failed: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("   ⚠️  Server not running. Start Django server with: python manage.py runserver")
    else:
        print("   ❌ No active employee found")
    
    print()
    
    # Test 2: Login with inactive employee  
    print("🔒 Test 2: Login with INACTIVE employee")
    inactive_employee = Employee.objects.filter(status='terminated', user__isnull=False).first()
    
    if inactive_employee:
        # Set a known password for testing
        inactive_employee.user.set_password('testpass123')
        inactive_employee.user.save()
        
        login_data = {
            "username": inactive_employee.user.username,
            "password": "testpass123"
        }
        
        try:
            response = requests.post(login_url, json=login_data)
            print(f"   Username: {login_data['username']}")
            print(f"   Employee Status: {inactive_employee.status}")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 403:
                print("   ✅ Login blocked (as expected)")
                data = response.json()
                print(f"   🚫 Error message: {data.get('error', 'No error message')}")
            elif response.status_code == 200:
                print("   ❌ Login succeeded (this should NOT happen!)")
            else:
                print(f"   ❓ Unexpected response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("   ⚠️  Server not running. Start Django server with: python manage.py runserver")
    else:
        print("   ❌ No inactive employee found")
    
    print()

def show_test_credentials():
    """Show test credentials for manual testing"""
    print("=== Test Credentials for Manual Testing ===\n")
    
    # Active employee
    active_employee = Employee.objects.filter(status='active', user__isnull=False).first()
    if active_employee:
        print("🔓 ACTIVE Employee (should be able to login):")
        print(f"   Username: {active_employee.user.username}")
        print(f"   Password: testpass123")
        print(f"   Status: {active_employee.status}")
        print()
    
    # Inactive employee
    inactive_employee = Employee.objects.filter(status='terminated', user__isnull=False).first()
    if inactive_employee:
        print("🔒 INACTIVE Employee (should be blocked):")
        print(f"   Username: {inactive_employee.user.username}")
        print(f"   Password: testpass123")
        print(f"   Status: {inactive_employee.status}")
        print()

if __name__ == "__main__":
    print("🧪 JWT AUTHENTICATION API TEST\n")
    print("=" * 50)
    
    show_test_credentials()
    test_login_api()
    
    print("=" * 50)
    print("✅ API TEST COMPLETE")
    print("\nTo run the Django server:")
    print("python manage.py runserver")
    print("\nThen test the login at: http://127.0.0.1:8000/api/token/")
    print("=" * 50)