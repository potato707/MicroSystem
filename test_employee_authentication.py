#!/usr/bin/env python3
"""
Test script for employee status-based authentication
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, User
from django.contrib.auth import authenticate

def show_employee_statuses():
    """Show all employees and their current statuses"""
    print("=== Current Employee Statuses ===\n")
    
    employees = Employee.objects.all()
    
    for employee in employees:
        user_info = f" (User: {employee.user.username})" if employee.user else " (No User Account)"
        status_display = dict(Employee.EMPLOYMENT_STATUS).get(employee.status, employee.status)
        
        print(f"👤 {employee.name}{user_info}")
        print(f"   📍 Status: {employee.status} ({status_display})")
        print(f"   🏢 Position: {employee.position}")
        print(f"   📅 Hire Date: {employee.hire_date}")
        print()

def create_test_inactive_employee():
    """Create a test employee with inactive status for testing"""
    print("=== Creating Test Inactive Employee ===\n")
    
    # Create a user for the inactive employee
    try:
        test_user = User.objects.create_user(
            username='test_inactive',
            email='test_inactive@company.com',
            password='testpass123',
            name='Test Inactive Employee',
            role='employee'
        )
        
        # Create employee with 'terminated' status
        test_employee = Employee.objects.create(
            user=test_user,
            name='Test Inactive Employee',
            position='Test Position',
            department='Test Department',
            hire_date='2025-01-01',
            salary=1000.00,
            status='terminated',  # Non-active status
            phone='123-456-7890',
            email='test_inactive@company.com',
            address='Test Address',
            emergency_contact='Test Contact'
        )
        
        print(f"✅ Created test inactive employee:")
        print(f"   Username: test_inactive")
        print(f"   Password: testpass123")
        print(f"   Status: {test_employee.status} (terminated)")
        print()
        
        return test_user, test_employee
        
    except Exception as e:
        print(f"❌ Error creating test employee: {e}")
        # If user already exists, get it
        try:
            test_user = User.objects.get(username='test_inactive')
            test_employee = test_user.employee
            print(f"📋 Test inactive employee already exists:")
            print(f"   Username: test_inactive")
            print(f"   Status: {test_employee.status}")
            return test_user, test_employee
        except:
            return None, None

def test_authentication():
    """Test authentication with active and inactive employees"""
    print("=== Testing Authentication ===\n")
    
    # Test with active employee (if any)
    active_employees = Employee.objects.filter(status='active')
    if active_employees.exists():
        active_emp = active_employees.first()
        if active_emp.user:
            print(f"🔓 Testing ACTIVE employee: {active_emp.name}")
            auth_result = authenticate(username=active_emp.user.username, password='password123')  # You may need to set a known password
            print(f"   Authentication result: {'Success' if auth_result else 'Failed (wrong password or other issue)'}")
            print()
    
    # Test with inactive employee
    inactive_employees = Employee.objects.exclude(status='active')
    if inactive_employees.exists():
        inactive_emp = inactive_employees.first()
        if inactive_emp.user:
            print(f"🔒 Testing INACTIVE employee: {inactive_emp.name}")
            print(f"   Status: {inactive_emp.status}")
            print(f"   This should be blocked by our custom authentication")
            print()

def change_employee_status_for_testing():
    """Change an existing employee's status for testing"""
    print("=== Changing Employee Status for Testing ===\n")
    
    # Find an employee to change status
    employees = Employee.objects.filter(user__isnull=False)
    
    if employees.exists():
        employee = employees.first()
        original_status = employee.status
        
        print(f"👤 Employee: {employee.name}")
        print(f"   Original Status: {original_status}")
        
        # Change to terminated status
        employee.status = 'terminated'
        employee.save()
        
        print(f"   ✅ Changed Status to: {employee.status}")
        print(f"   🔒 This employee should now be unable to login")
        print()
        
        return employee, original_status
    
    return None, None

if __name__ == "__main__":
    print("🧪 EMPLOYEE STATUS AUTHENTICATION TEST\n")
    print("=" * 50)
    
    show_employee_statuses()
    create_test_inactive_employee()
    test_authentication()
    
    # Optionally change an employee's status for testing
    changed_employee, original_status = change_employee_status_for_testing()
    
    print("=" * 50)
    print("✅ TEST SETUP COMPLETE")
    print("\nTo test the authentication:")
    print("1. Try logging in with an active employee - should work")
    print("2. Try logging in with an inactive employee - should be blocked")
    print("3. Check the frontend login response for proper error messages")
    print("=" * 50)
    
    if changed_employee:
        print(f"\n⚠️  Remember to restore {changed_employee.name}'s status to '{original_status}' after testing!")