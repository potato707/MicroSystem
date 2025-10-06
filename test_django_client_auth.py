#!/usr/bin/env python3
"""
Test authentication using Django test client
"""
import os
import sys
import django
import json

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from hr_management.models import Employee, User

def test_authentication_with_client():
    """Test authentication using Django test client"""
    print("=== Testing Authentication with Django Client ===\n")
    
    client = Client()
    
    # Test 1: Active employee login
    print("🔓 Test 1: ACTIVE Employee Login")
    active_employee = Employee.objects.filter(status='active', user__isnull=False).first()
    
    if active_employee:
        # Set known password
        active_employee.user.set_password('testpass123')
        active_employee.user.save()
        
        login_data = {
            "username": active_employee.user.username,
            "password": "testpass123"
        }
        
        response = client.post('/api/token/', data=json.dumps(login_data), content_type='application/json')
        
        print(f"   Username: {login_data['username']}")
        print(f"   Employee Status: {active_employee.status}")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Login successful (as expected)")
            data = response.json()
            print(f"   🔑 Access token received: {'Yes' if 'access' in data else 'No'}")
        else:
            print(f"   ❌ Login failed: {response.content.decode()}")
    else:
        print("   ❌ No active employee found")
    
    print()
    
    # Test 2: Inactive employee login
    print("🔒 Test 2: INACTIVE Employee Login")
    inactive_employee = Employee.objects.filter(status='terminated', user__isnull=False).first()
    
    if inactive_employee:
        # Set known password
        inactive_employee.user.set_password('testpass123')
        inactive_employee.user.save()
        
        login_data = {
            "username": inactive_employee.user.username,
            "password": "testpass123"
        }
        
        response = client.post('/api/token/', data=json.dumps(login_data), content_type='application/json')
        
        print(f"   Username: {login_data['username']}")
        print(f"   Employee Status: {inactive_employee.status}")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 403:
            print("   ✅ Login blocked (as expected)")
            data = response.json()
            print(f"   🚫 Error message: {data.get('error', 'No error message')}")
        elif response.status_code == 200:
            print("   ❌ Login succeeded (this should NOT happen!)")
            print("   🐛 Bug: Inactive employee was allowed to login")
        else:
            print(f"   ❓ Unexpected response: {response.content.decode()}")
    else:
        print("   ❌ No inactive employee found")
    
    print()
    
    # Test 3: User without employee record (admin)
    print("🔧 Test 3: Admin User (No Employee Record)")
    
    # Create or get admin user
    admin_user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@company.com',
            'name': 'Admin User',
            'role': 'admin'
        }
    )
    
    if created or not admin_user.check_password('adminpass123'):
        admin_user.set_password('adminpass123')
        admin_user.save()
    
    login_data = {
        "username": "admin_test",
        "password": "adminpass123"
    }
    
    response = client.post('/api/token/', data=json.dumps(login_data), content_type='application/json')
    
    print(f"   Username: {login_data['username']}")
    print(f"   User Role: {admin_user.role}")
    print(f"   Has Employee Record: {hasattr(admin_user, 'employee')}")
    print(f"   Response Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Admin login successful (as expected)")
    else:
        print(f"   ❌ Admin login failed: {response.content.decode()}")

def test_different_employee_statuses():
    """Test different employee statuses"""
    print("=== Testing Different Employee Statuses ===\n")
    
    client = Client()
    
    # Create employees with different statuses for testing
    statuses_to_test = ['vacation', 'resigned', 'probation']
    
    for status_code in statuses_to_test:
        status_display = dict(Employee.EMPLOYMENT_STATUS).get(status_code, status_code)
        print(f"🧪 Testing status: {status_code} ({status_display})")
        
        # Try to find existing employee with this status or create new one
        test_employee = Employee.objects.filter(status=status_code, user__isnull=False).first()
        
        if not test_employee:
            # Create test employee with this status
            try:
                test_user = User.objects.create_user(
                    username=f'test_{status_code}',
                    email=f'test_{status_code}@company.com',
                    password='testpass123',
                    name=f'Test {status_display} Employee',
                    role='employee'
                )
                
                test_employee = Employee.objects.create(
                    user=test_user,
                    name=f'Test {status_display} Employee',
                    position='Test Position',
                    department='Test Department',
                    hire_date='2025-01-01',
                    salary=1000.00,
                    status=status_code,
                    phone='123-456-7890',
                    email=f'test_{status_code}@company.com',
                    address='Test Address',
                    emergency_contact='Test Contact'
                )
                print(f"   ✅ Created test employee with {status_code} status")
            except Exception as e:
                print(f"   ⚠️  Could not create test employee: {e}")
                continue
        
        # Test login
        test_employee.user.set_password('testpass123')
        test_employee.user.save()
        
        login_data = {
            "username": test_employee.user.username,
            "password": "testpass123"
        }
        
        response = client.post('/api/token/', data=json.dumps(login_data), content_type='application/json')
        
        print(f"   Username: {login_data['username']}")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 403:
            print(f"   ✅ Login blocked for {status_code} status (correct)")
        elif response.status_code == 200:
            print(f"   ❌ Login allowed for {status_code} status (should be blocked)")
        else:
            print(f"   ❓ Unexpected response: {response.content.decode()}")
        
        print()

if __name__ == "__main__":
    print("🧪 DJANGO CLIENT AUTHENTICATION TEST\n")
    print("=" * 60)
    
    test_authentication_with_client()
    test_different_employee_statuses()
    
    print("=" * 60)
    print("✅ AUTHENTICATION TEST COMPLETE")
    print("=" * 60)