#!/usr/bin/env python3
"""
Simple test to verify task creation with subtasks functionality using Django manage.py
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
from hr_management.serializers import TaskCreateSerializer
from django.test import RequestFactory
from django.contrib.auth import get_user_model


def test_task_serializer_with_subtasks():
    """Test TaskCreateSerializer directly with subtasks data"""
    print("🧪 Testing TaskCreateSerializer with subtasks...")
    
    # Get or create admin user
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin',
            name='Admin User'
        )
    
    # Get or create team
    team, created = Team.objects.get_or_create(
        name='Test Team',
        defaults={
            'description': 'Test Development Team',
            'created_by': admin_user
        }
    )
    
    # Get or create team members
    team_members = []
    for i in range(3):
        user, created = User.objects.get_or_create(
            username=f'dev{i+1}',
            defaults={
                'email': f'dev{i+1}@test.com',
                'password': 'password123',
                'role': 'employee',
                'name': f'Developer {i+1}'
            }
        )
        
        employee, created = Employee.objects.get_or_create(
            user=user,
            defaults={
                'name': f'Developer {i+1}',
                'position': 'Developer',
                'phone_number': f'12345678{i}',
                'salary': 50000.00
            }
        )
        team_members.append(employee)
    
    # Create request factory for context
    factory = RequestFactory()
    request = factory.post('/api/tasks/')
    request.user = admin_user
    
    # Test data with subtasks
    task_data = {
        "title": "Test Task with Subtasks",
        "description": "Testing subtask creation",
        "priority": "medium",
        "estimated_minutes": 120,
        "date": str(date.today()),
        "subtasks": [
            {
                "title": "First subtask",
                "description": "Test subtask 1",
                "assigned_employee": str(team_members[0].id),
                "priority": "high",
                "estimated_minutes": 60,
                "order": 1
            },
            {
                "title": "Second subtask", 
                "description": "Test subtask 2",
                "assigned_employee": str(team_members[1].id),
                "priority": "low",
                "estimated_minutes": 60,
                "order": 2
            }
        ]
    }
    
    print(f"📝 Task data: {task_data['title']}")
    print(f"   Subtasks: {len(task_data['subtasks'])}")
    
    # Test serializer
    serializer = TaskCreateSerializer(data=task_data, context={'request': request})
    
    if not serializer.is_valid():
        print(f"❌ Serializer validation failed: {serializer.errors}")
        return False
    
    print("✅ Serializer validation passed")
    
    # Save the task
    task = serializer.save(created_by=admin_user)
    
    print(f"✅ Task created: {task.title} (ID: {task.id})")
    
    # Check if subtasks were created
    subtasks = Subtask.objects.filter(parent_task=task)
    print(f"✅ Subtasks created: {subtasks.count()}")
    
    for subtask in subtasks:
        print(f"   - {subtask.title} → {subtask.assigned_employee.name if subtask.assigned_employee else 'Unassigned'}")
    
    return subtasks.count() == 2


def test_task_creation_no_subtasks():
    """Test regular task creation without subtasks"""
    print("\n🧪 Testing regular task creation...")
    
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return False
    
    factory = RequestFactory()
    request = factory.post('/api/tasks/')
    request.user = admin_user
    
    task_data = {
        "title": "Simple Task",
        "description": "No subtasks",
        "priority": "low",
        "estimated_minutes": 30,
        "date": str(date.today())
    }
    
    serializer = TaskCreateSerializer(data=task_data, context={'request': request})
    
    if not serializer.is_valid():
        print(f"❌ Serializer validation failed: {serializer.errors}")
        return False
    
    task = serializer.save(created_by=admin_user)
    subtasks_count = Subtask.objects.filter(parent_task=task).count()
    
    print(f"✅ Simple task created: {task.title}")
    print(f"   Subtasks: {subtasks_count}")
    
    return subtasks_count == 0


def run_tests():
    """Run all tests"""
    print("🚀 Testing Task Creation with Subtasks")
    print("=" * 50)
    
    try:
        test1 = test_task_serializer_with_subtasks()
        test2 = test_task_creation_no_subtasks()
        
        print("\n📊 Results:")
        print(f"✅ Task with subtasks: {'PASS' if test1 else 'FAIL'}")
        print(f"✅ Task without subtasks: {'PASS' if test2 else 'FAIL'}")
        
        if test1 and test2:
            print("\n🎯 All tests PASSED! ✅")
            print("   ✓ Tasks can be created with subtasks")
            print("   ✓ Regular task creation still works")
            return True
        else:
            print("\n❌ Some tests failed")
            return False
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)