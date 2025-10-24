#!/usr/bin/env python3
"""
Test script to verify task creation with subtasks functionality
Tests the new integrated task+subtask creation workflow
"""

import os
import sys
import django
import json
from datetime import date

# Add the project root to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, Task, Subtask
from rest_framework.test import APIClient
from rest_framework import status


def setup_test_data():
    """Set up test users, teams, and employees"""
    print("🔧 Setting up test data...")
    
    # Create admin user
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@company.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
    admin_user.role = 'admin'
    admin_user.save()
    
    # Create admin employee
    admin_employee = Employee.objects.filter(user=admin_user).first()
    if not admin_employee:
        admin_employee = Employee.objects.create(
            user=admin_user,
            name="Admin User",
            position="System Administrator",
            phone_number="1234567890",
            salary=80000.00
        )
    
    # Create team
    dev_team = Team.objects.filter(name='Development Team').first()
    if not dev_team:
        dev_team = Team.objects.create(
            name='Development Team',
            description='Software Development Team',
            created_by=admin_user
        )
    
    # Create team members
    members = []
    for i, (username, name, position) in enumerate([
        ('dev1', 'John Developer', 'Senior Developer'),
        ('dev2', 'Jane Coder', 'Junior Developer'),
        ('dev3', 'Bob Tester', 'QA Engineer')
    ]):
        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@company.com',
                password='password123',
                first_name=name.split()[0],
                last_name=' '.join(name.split()[1:])
            )
        user.role = 'employee'
        user.save()
        
        employee = Employee.objects.filter(user=user).first()
        if not employee:
            employee = Employee.objects.create(
                user=user,
                name=name,
                position=position,
                phone_number=f"555000{i+1:03d}",
                salary=60000.00 + (i * 10000)
            )
        members.append(employee)
        
        # Add to team
        from hr_management.models import TeamMembership
        TeamMembership.objects.get_or_create(
            team=dev_team,
            employee=employee,
            defaults={'is_active': True}
        )
    
    return admin_user, admin_employee, dev_team, members


def test_task_creation_with_subtasks():
    """Test creating a task with multiple subtasks in single API call"""
    print("\n🧪 Testing task creation with subtasks...")
    
    admin_user, admin_employee, dev_team, team_members = setup_test_data()
    
    # Set up API client
    client = APIClient()
    client.force_authenticate(user=admin_user)
    
    # Prepare task data with subtasks
    task_data = {
        "title": "Implement User Authentication System",
        "description": "Build complete authentication system with login, registration, and password reset",
        "priority": "high",
        "estimated_minutes": 480,  # 8 hours total
        "date": str(date.today()),
        "team": str(dev_team.id),
        "subtasks": [
            {
                "title": "Design database schema",
                "description": "Create user tables and relationships",
                "assigned_employee": str(team_members[0].id),  # John Developer
                "priority": "high",
                "estimated_minutes": 120,
                "order": 1
            },
            {
                "title": "Implement login API",
                "description": "Build REST API for user authentication",
                "assigned_employee": str(team_members[1].id),  # Jane Coder  
                "priority": "medium", 
                "estimated_minutes": 180,
                "order": 2
            },
            {
                "title": "Create frontend login form",
                "description": "Build React login component",
                "assigned_employee": str(team_members[1].id),  # Jane Coder
                "priority": "medium",
                "estimated_minutes": 90,
                "order": 3
            },
            {
                "title": "Write unit tests",
                "description": "Test authentication flows",
                "assigned_employee": str(team_members[2].id),  # Bob Tester
                "priority": "low",
                "estimated_minutes": 90,
                "order": 4
            }
        ]
    }
    
    print(f"📤 Sending task creation request with {len(task_data['subtasks'])} subtasks...")
    print(f"   Main task: '{task_data['title']}'")
    for i, subtask in enumerate(task_data['subtasks']):
        assigned_name = next(m.name for m in team_members if str(m.id) == subtask['assigned_employee'])
        print(f"   Subtask {i+1}: '{subtask['title']}' → {assigned_name}")
    
    # Make API request
    response = client.post('/api/tasks/', task_data, format='json')
    
    print(f"📥 Response status: {response.status_code}")
    if response.status_code != status.HTTP_201_CREATED:
        print(f"❌ Error: {response.data}")
        return False
        
    task_response = response.data
    task_id = task_response['id']
    print(f"✅ Task created successfully! ID: {task_id}")
    
    # Verify task was created
    task = Task.objects.get(id=task_id)
    print(f"   Task title: {task.title}")
    print(f"   Task team: {task.team.name if task.team else 'None'}")
    print(f"   Task priority: {task.priority}")
    
    # Verify subtasks were created
    subtasks = Subtask.objects.filter(parent_task=task).order_by('order')
    print(f"   Subtasks created: {subtasks.count()}")
    
    if subtasks.count() != len(task_data['subtasks']):
        print(f"❌ Expected {len(task_data['subtasks'])} subtasks, got {subtasks.count()}")
        return False
    
    # Verify each subtask
    for i, subtask in enumerate(subtasks):
        expected = task_data['subtasks'][i]
        print(f"   Subtask {i+1}: '{subtask.title}' → {subtask.assigned_employee.name if subtask.assigned_employee else 'Unassigned'}")
        
        if subtask.title != expected['title']:
            print(f"❌ Subtask title mismatch: expected '{expected['title']}', got '{subtask.title}'")
            return False
            
        if str(subtask.assigned_employee.id) != expected['assigned_employee']:
            print(f"❌ Assignment mismatch for subtask '{subtask.title}'")
            return False
            
        if subtask.priority != expected['priority']:
            print(f"❌ Priority mismatch for subtask '{subtask.title}'")
            return False
    
    print("✅ All subtasks verified successfully!")
    return True


def test_task_creation_with_unassigned_subtasks():
    """Test creating task with some unassigned subtasks"""
    print("\n🧪 Testing task creation with unassigned subtasks...")
    
    admin_user, admin_employee, dev_team, team_members = setup_test_data()
    
    client = APIClient()
    client.force_authenticate(user=admin_user)
    
    task_data = {
        "title": "Plan Sprint Activities",
        "description": "Organize next sprint planning",
        "priority": "medium",
        "estimated_minutes": 120,
        "date": str(date.today()),
        "team": str(dev_team.id),
        "subtasks": [
            {
                "title": "Review backlog items",
                "description": "Go through product backlog",
                "assigned_employee": str(team_members[0].id),
                "priority": "high",
                "estimated_minutes": 60,
                "order": 1
            },
            {
                "title": "Estimate story points",
                "description": "Team estimation session",
                "assigned_employee": None,  # Unassigned
                "priority": "medium",
                "estimated_minutes": 60,
                "order": 2
            }
        ]
    }
    
    print(f"📤 Creating task with mixed assignment...")
    
    response = client.post('/api/tasks/', task_data, format='json')
    
    if response.status_code != status.HTTP_201_CREATED:
        print(f"❌ Error: {response.data}")
        return False
        
    task = Task.objects.get(id=response.data['id'])
    subtasks = Subtask.objects.filter(parent_task=task).order_by('order')
    
    print(f"✅ Task created with {subtasks.count()} subtasks")
    print(f"   Subtask 1: '{subtasks[0].title}' → {subtasks[0].assigned_employee.name}")
    print(f"   Subtask 2: '{subtasks[1].title}' → {'Unassigned' if not subtasks[1].assigned_employee else subtasks[1].assigned_employee.name}")
    
    return True


def test_task_creation_without_subtasks():
    """Test that regular task creation still works"""
    print("\n🧪 Testing regular task creation (no subtasks)...")
    
    admin_user, admin_employee, dev_team, team_members = setup_test_data()
    
    client = APIClient()
    client.force_authenticate(user=admin_user)
    
    task_data = {
        "title": "Quick Bug Fix",
        "description": "Fix minor UI issue",
        "priority": "low",
        "estimated_minutes": 30,
        "date": str(date.today()),
        "employee": str(team_members[0].id)
    }
    
    print(f"📤 Creating regular task without subtasks...")
    
    response = client.post('/api/tasks/', task_data, format='json')
    
    if response.status_code != status.HTTP_201_CREATED:
        print(f"❌ Error: {response.data}")
        return False
        
    task = Task.objects.get(id=response.data['id'])
    subtask_count = Subtask.objects.filter(parent_task=task).count()
    
    print(f"✅ Regular task created: '{task.title}'")
    print(f"   Assigned to: {task.employee.name}")
    print(f"   Subtasks: {subtask_count}")
    
    return subtask_count == 0


def run_all_tests():
    """Run comprehensive test suite"""
    print("🚀 Testing Integrated Task + Subtask Creation")
    print("=" * 60)
    
    try:
        # Test 1: Task with assigned subtasks
        test1_result = test_task_creation_with_subtasks()
        
        # Test 2: Task with mixed assignment
        test2_result = test_task_creation_with_unassigned_subtasks()
        
        # Test 3: Regular task (backward compatibility)
        test3_result = test_task_creation_without_subtasks()
        
        print("\n📊 Test Results:")
        print("=" * 40)
        print(f"✅ Task with assigned subtasks: {'PASS' if test1_result else 'FAIL'}")
        print(f"✅ Task with unassigned subtasks: {'PASS' if test2_result else 'FAIL'}")
        print(f"✅ Regular task creation: {'PASS' if test3_result else 'FAIL'}")
        
        if all([test1_result, test2_result, test3_result]):
            print("\n🎯 RESULT: All tests PASSED! ✅")
            print("   ✓ Tasks can be created with subtasks in single API call")
            print("   ✓ Subtasks can be assigned to specific team members") 
            print("   ✓ Subtasks can be left unassigned")
            print("   ✓ Regular task creation still works")
            return True
        else:
            print("\n❌ RESULT: Some tests FAILED!")
            return False
            
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)