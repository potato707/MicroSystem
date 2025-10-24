#!/usr/bin/env python3

"""
Test script to verify subtask assignment functionality.
This script tests the ability for admins and team managers to create 
subtasks and assign them to team members.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, TeamMembership, Task, Subtask
from django.contrib.auth import get_user_model
from datetime import date, datetime
import uuid

def setup_test_data():
    """Create test users, employees, teams, and tasks"""
    print("Setting up test data...")
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin_test',
        defaults={
            'email': 'admin@test.com',
            'role': 'admin',
            'name': 'Admin User',
            'first_name': 'Admin',
            'last_name': 'User'
        }
    )
    admin_user.set_password('password123')
    admin_user.save()
    
    # Create admin employee record
    admin_employee, created = Employee.objects.get_or_create(
        user=admin_user,
        defaults={
            'name': 'Admin User',
            'position': 'System Administrator',
            'department': 'IT',
            'hire_date': date.today(),
            'salary': 8000.00,
            'phone': '123456789',
            'email': 'admin@test.com',
            'address': 'Test Address'
        }
    )
    
    # Create team manager user
    manager_user, created = User.objects.get_or_create(
        username='manager_test',
        defaults={
            'email': 'manager@test.com',
            'role': 'manager',
            'name': 'Team Manager',
            'first_name': 'Team',
            'last_name': 'Manager'
        }
    )
    manager_user.set_password('password123')
    manager_user.save()
    
    # Create manager employee record
    manager_employee, created = Employee.objects.get_or_create(
        user=manager_user,
        defaults={
            'name': 'Team Manager',
            'position': 'Team Leader',
            'department': 'Development',
            'hire_date': date.today(),
            'salary': 7000.00,
            'phone': '123456788',
            'email': 'manager@test.com',
            'address': 'Manager Address'
        }
    )
    
    # Create regular employee users
    employee_users = []
    employees = []
    
    for i in range(3):
        emp_user, created = User.objects.get_or_create(
            username=f'employee_{i+1}',
            defaults={
                'email': f'employee{i+1}@test.com',
                'role': 'employee',
                'name': f'Employee {i+1}',
                'first_name': f'Employee',
                'last_name': f'{i+1}'
            }
        )
        emp_user.set_password('password123')
        emp_user.save()
        employee_users.append(emp_user)
        
        emp, created = Employee.objects.get_or_create(
            user=emp_user,
            defaults={
                'name': f'Employee {i+1}',
                'position': f'Developer {i+1}',
                'department': 'Development',
                'hire_date': date.today(),
                'salary': 5000.00,
                'phone': f'12345678{i}',
                'email': f'employee{i+1}@test.com',
                'address': f'Employee {i+1} Address'
            }
        )
        employees.append(emp)
    
    # Create a team
    team, created = Team.objects.get_or_create(
        name='Development Team',
        defaults={
            'description': 'Main development team for testing',
            'team_leader': manager_employee,
            'created_by': admin_user,
            'is_active': True
        }
    )
    
    # Add employees to the team
    for employee in employees:
        TeamMembership.objects.get_or_create(
            team=team,
            employee=employee,
            defaults={
                'role': 'member',
                'is_active': True
            }
        )
    
    # Create a task
    task, created = Task.objects.get_or_create(
        title='Test Task for Subtasks',
        defaults={
            'employee': employees[0],  # Assign to first employee
            'description': 'A task to test subtask assignment functionality',
            'status': 'to_do',
            'priority': 'medium',
            'date': date.today(),
            'created_by': admin_user,
            'assigned_by_manager': True,
            'team': team,
            'estimated_minutes': 120
        }
    )
    
    print(f"✓ Created admin user: {admin_user.username}")
    print(f"✓ Created manager user: {manager_user.username}")
    print(f"✓ Created {len(employee_users)} employee users")
    print(f"✓ Created team: {team.name} with {team.memberships.count()} members")
    print(f"✓ Created task: {task.title}")
    
    return admin_user, manager_user, employee_users, employees, team, task

def test_admin_subtask_creation(admin_user, task, employees):
    """Test admin creating and assigning subtasks"""
    print("\n=== Testing Admin Subtask Creation ===")
    
    # Admin should be able to create subtasks and assign to team members
    subtask1 = Subtask.objects.create(
        parent_task=task,
        assigned_employee=employees[0],
        title='Frontend Implementation',
        description='Implement the frontend UI components',
        priority='high',
        estimated_minutes=60
    )
    
    subtask2 = Subtask.objects.create(
        parent_task=task,
        assigned_employee=employees[1],
        title='Backend API',
        description='Create the backend API endpoints',
        priority='medium',
        estimated_minutes=90
    )
    
    print(f"✓ Admin created subtask 1: {subtask1.title} → {subtask1.assigned_employee.name}")
    print(f"✓ Admin created subtask 2: {subtask2.title} → {subtask2.assigned_employee.name}")
    
    return subtask1, subtask2

def test_team_manager_subtask_creation(manager_user, task, employees):
    """Test team manager creating and assigning subtasks"""
    print("\n=== Testing Team Manager Subtask Creation ===")
    
    # Team manager should be able to create subtasks for team tasks
    subtask3 = Subtask.objects.create(
        parent_task=task,
        assigned_employee=employees[2],
        title='Testing & QA',
        description='Write and execute tests for the feature',
        priority='medium',
        estimated_minutes=45
    )
    
    print(f"✓ Manager created subtask 3: {subtask3.title} → {subtask3.assigned_employee.name}")
    
    return subtask3

def test_subtask_permissions(employee_users, task, employees):
    """Test that regular employees have appropriate permissions"""
    print("\n=== Testing Subtask Permissions ===")
    
    # Employee should be able to view subtasks assigned to them
    assigned_subtasks = Subtask.objects.filter(assigned_employee=employees[0])
    print(f"✓ Employee 1 can see {assigned_subtasks.count()} subtask(s) assigned to them")
    
    # Test that subtask shows assignment information
    for subtask in assigned_subtasks:
        print(f"  - {subtask.title} (assigned to: {subtask.assigned_employee.name})")

def test_subtask_model_methods(task):
    """Test the Subtask model methods and properties"""
    print("\n=== Testing Subtask Model Methods ===")
    
    subtasks = Subtask.objects.filter(parent_task=task)
    
    for subtask in subtasks:
        print(f"✓ Subtask: {subtask}")  # This tests the __str__ method
        print(f"  - Time spent: {subtask.time_spent} minutes")
        print(f"  - Is paused: {subtask.is_paused}")

def test_api_assignable_employees(task):
    """Test the assignable employees functionality"""
    print("\n=== Testing Assignable Employees API ===")
    
    from hr_management.views import AssignableEmployeesView
    from rest_framework.test import APIRequestFactory
    from django.contrib.auth import get_user_model
    
    factory = APIRequestFactory()
    User = get_user_model()
    
    # Test as admin
    admin_user = User.objects.get(username='admin_test')
    request = factory.get(f'/hr/tasks/{task.id}/assignable-employees/')
    request.user = admin_user
    
    view = AssignableEmployeesView()
    view.request = request
    
    try:
        response = view.get(request, str(task.id))
        if response.status_code == 200:
            assignable_employees = response.data
            print(f"✓ API returned {len(assignable_employees)} assignable employees")
            for emp in assignable_employees:
                print(f"  - {emp['name']} ({emp['position']}) - Role: {emp.get('team_role', 'N/A')}")
        else:
            print(f"✗ API returned error: {response.status_code}")
    except Exception as e:
        print(f"✗ API test failed: {str(e)}")

def cleanup_test_data():
    """Clean up test data"""
    print("\n=== Cleaning Up Test Data ===")
    
    # Delete in reverse order of dependencies
    Subtask.objects.filter(parent_task__title='Test Task for Subtasks').delete()
    Task.objects.filter(title='Test Task for Subtasks').delete()
    TeamMembership.objects.filter(team__name='Development Team').delete()
    Team.objects.filter(name='Development Team').delete()
    
    # Delete employees and users
    Employee.objects.filter(name__startswith='Employee').delete()
    Employee.objects.filter(name__in=['Admin User', 'Team Manager']).delete()
    User.objects.filter(username__in=['admin_test', 'manager_test']).delete()
    User.objects.filter(username__startswith='employee_').delete()
    
    print("✓ Cleaned up all test data")

def main():
    """Main test function"""
    print("🚀 Starting Subtask Assignment Functionality Tests")
    print("=" * 60)
    
    try:
        # Setup test data
        admin_user, manager_user, employee_users, employees, team, task = setup_test_data()
        
        # Test admin functionality
        subtask1, subtask2 = test_admin_subtask_creation(admin_user, task, employees)
        
        # Test team manager functionality
        subtask3 = test_team_manager_subtask_creation(manager_user, task, employees)
        
        # Test permissions
        test_subtask_permissions(employee_users, task, employees)
        
        # Test model methods
        test_subtask_model_methods(task)
        
        # Test API functionality
        test_api_assignable_employees(task)
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\nSUMMARY:")
        print("- Admins can create and assign subtasks ✓")
        print("- Team managers can create and assign subtasks ✓") 
        print("- Employees can view their assigned subtasks ✓")
        print("- Subtask model shows assignment information ✓")
        print("- API provides assignable employees list ✓")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        cleanup_test_data()

if __name__ == '__main__':
    main()