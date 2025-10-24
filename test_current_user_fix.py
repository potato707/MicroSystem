#!/usr/bin/env python
import os
import sys
import django

# Add the MicroSystem directory to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User
from hr_management.views import CurrentUserView
from django.http import HttpRequest
from django.contrib.auth import get_user_model

def test_current_user_api():
    print("=== Testing CurrentUserView API Response ===")
    
    # Get the string user
    User = get_user_model()
    user = User.objects.get(username='string')
    
    print(f"Database User ID: {user.id}")
    print(f"Database User Name: {user.name}")
    print(f"Database User Role: {user.role}")
    
    if hasattr(user, 'employee'):
        employee = user.employee
        print(f"Employee ID: {employee.id}")
        print(f"Employee Name: {employee.name}")
    
    # Simulate what CurrentUserView would return
    if hasattr(user, 'employee'):
        employee = user.employee
        data = {
            'id': str(user.id),  # This should now be correct
            'employee_id': str(employee.id),
            'name': employee.name,
            'role': user.role,
        }
    else:
        data = {
            'id': str(user.id),
            'name': user.name,
            'username': user.username,
            'role': user.role,
        }
    
    print(f"\nAPI Response would contain:")
    print(f"  id: {data['id']}")
    print(f"  employee_id: {data.get('employee_id', 'N/A')}")
    print(f"  name: {data['name']}")
    print(f"  role: {data['role']}")
    
    print(f"\nWith this fix:")
    print(f"  localStorage user_id will be: {data['id']}")
    print(f"  Comments are authored by: {user.id}")
    print(f"  Match: {str(user.id) == data['id']}")

if __name__ == "__main__":
    test_current_user_api()