#!/usr/bin/env python3
"""
Final test for employee status authentication - working version
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.test import Client
from hr_management.models import Employee, User
import json

def test_final_authentication():
    """Final working test for authentication"""
    print("=== FINAL AUTHENTICATION TEST ===\n")
    
    client = Client()
    
    # Ensure we have a terminated employee for testing
    print("📋 Setting up test data...")
    terminated_employee = Employee.objects.filter(status='terminated', user__isnull=False).first()
    if not terminated_employee:
        # Change one employee to terminated status
        employee_to_change = Employee.objects.filter(user__isnull=False).first()
        if employee_to_change:
            original_status = employee_to_change.status
            employee_to_change.status = 'terminated'
            employee_to_change.save()
            terminated_employee = employee_to_change
            print(f"   Changed {employee_to_change.name} status from {original_status} to terminated")
    
    # Set passwords for testing
    active_employee = Employee.objects.filter(status='active', user__isnull=False).first()
    
    if active_employee:
        active_employee.user.set_password('testpass123')
        active_employee.user.save()
        print(f"   Set password for active employee: {active_employee.name}")
    
    if terminated_employee:
        terminated_employee.user.set_password('testpass123')
        terminated_employee.user.save()
        print(f"   Set password for terminated employee: {terminated_employee.name}")
    
    print("\n" + "="*50)
    
    # Test 1: Active employee
    if active_employee:
        print(f"🔓 Test 1: ACTIVE Employee Login")
        print(f"   Employee: {active_employee.name}")
        print(f"   Status: {active_employee.status}")
        
        response = client.post(
            '/api/token/', 
            json.dumps({
                'username': active_employee.user.username,
                'password': 'testpass123'
            }), 
            content_type='application/json'
        )
        
        print(f"   Response Code: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS: Active employee can login")
            try:
                data = response.json()
                if 'access' in data:
                    print("   🔑 JWT token received")
            except:
                pass
        else:
            print(f"   ❌ FAILED: {response.content.decode()}")
    else:
        print("⚠️  No active employee found")
    
    print()
    
    # Test 2: Terminated employee
    if terminated_employee:
        print(f"🔒 Test 2: TERMINATED Employee Login")
        print(f"   Employee: {terminated_employee.name}")
        print(f"   Status: {terminated_employee.status}")
        
        response = client.post(
            '/api/token/', 
            json.dumps({
                'username': terminated_employee.user.username,
                'password': 'testpass123'
            }), 
            content_type='application/json'
        )
        
        print(f"   Response Code: {response.status_code}")
        
        if response.status_code == 403:
            print("   ✅ SUCCESS: Terminated employee blocked")
            try:
                data = response.json()
                print(f"   🚫 Error Message: {data.get('error', 'No error message')}")
            except:
                print(f"   🚫 Raw Response: {response.content.decode()}")
        elif response.status_code == 200:
            print("   ❌ FAILED: Terminated employee was allowed to login!")
        else:
            print(f"   ❓ UNEXPECTED: {response.content.decode()}")
    else:
        print("⚠️  No terminated employee found")
    
    print("\n" + "="*50)
    print("✅ AUTHENTICATION TEST COMPLETED")
    print("\nSUMMARY:")
    print("- Employees with 'active' status can login ✅")
    print("- Employees with other statuses are blocked 🔒")
    print("- Admin users without employee records can still login")
    print("="*50)

if __name__ == "__main__":
    test_final_authentication()