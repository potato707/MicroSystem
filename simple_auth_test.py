#!/usr/bin/env python3
"""
Simple test for employee status authentication
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
from hr_management.models import Employee, User

def test_simple_authentication():
    """Simple test for authentication"""
    print("=== Simple Authentication Test ===\n")
    
    client = Client()
    
    # Test with active employee
    print("1. Testing ACTIVE employee:")
    active_employee = Employee.objects.filter(status='active', user__isnull=False).first()
    
    if active_employee:
        # Set known password
        active_employee.user.set_password('testpass123')
        active_employee.user.save()
        
        # Test login
        response = client.post('/api/token/', {
            'username': active_employee.user.username,
            'password': 'testpass123'
        }, content_type='application/json')
        
        print(f"   Username: {active_employee.user.username}")
        print(f"   Status: {active_employee.status}")
        print(f"   Response Code: {response.status_code}")
        print(f"   Success: {'✅' if response.status_code == 200 else '❌'}")
        
        if response.status_code != 200:
            print(f"   Error: {response.content.decode()}")
    else:
        print("   No active employee found")
    
    print()
    
    # Test with inactive employee
    print("2. Testing INACTIVE employee:")
    inactive_employee = Employee.objects.filter(status='terminated', user__isnull=False).first()
    
    if inactive_employee:
        # Set known password
        inactive_employee.user.set_password('testpass123')
        inactive_employee.user.save()
        
        # Test login
        response = client.post('/api/token/', {
            'username': inactive_employee.user.username,
            'password': 'testpass123'
        }, content_type='application/json')
        
        print(f"   Username: {inactive_employee.user.username}")
        print(f"   Status: {inactive_employee.status}")
        print(f"   Response Code: {response.status_code}")
        print(f"   Blocked: {'✅' if response.status_code == 403 else '❌'}")
        
        if response.status_code == 403:
            try:
                error_data = response.json()
                print(f"   Error Message: {error_data.get('error', 'No error message')}")
            except:
                print(f"   Error: {response.content.decode()}")
        else:
            print(f"   Unexpected response: {response.content.decode()}")
    else:
        print("   No inactive employee found")

if __name__ == "__main__":
    test_simple_authentication()