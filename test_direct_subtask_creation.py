#!/usr/bin/env python3
"""
Direct database test to verify task creation with subtasks works
"""

import os
import sys
import django
from datetime import date

# Add the project root to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, Task, Subtask


def test_database_directly():
    """Test creating task with subtasks directly in database"""
    print("🗄️  Testing Task + Subtask creation directly in database")
    print("=" * 60)
    
    # Get existing users
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✅ Found admin user: {admin_user.username}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return False
    
    # Get existing employees
    employees = Employee.objects.all()[:2]
    if len(employees) < 2:
        print("❌ Need at least 2 employees for testing")
        return False
    
    print(f"✅ Found {len(employees)} employees for testing")
    
    # Create a task
    task = Task.objects.create(
        title="Database Test Task with Subtasks",
        description="Testing direct database creation",
        priority="medium",
        estimated_minutes=120,
        date=date.today(),
        created_by=admin_user,
        employee=employees[0]  # Assign to first employee
    )
    
    print(f"✅ Task created: {task.title} (ID: {task.id})")
    
    # Create subtasks
    subtasks_data = [
        {
            "title": "Research phase",
            "description": "Initial research and planning",
            "assigned_employee": employees[0],
            "priority": "high",
            "estimated_minutes": 60,
            "order": 1
        },
        {
            "title": "Implementation phase",  
            "description": "Build the feature",
            "assigned_employee": employees[1],
            "priority": "medium",
            "estimated_minutes": 60,
            "order": 2
        }
    ]
    
    created_subtasks = []
    for subtask_data in subtasks_data:
        subtask = Subtask.objects.create(
            parent_task=task,
            **subtask_data
        )
        created_subtasks.append(subtask)
    
    print(f"✅ Created {len(created_subtasks)} subtasks:")
    for subtask in created_subtasks:
        assignee_name = subtask.assigned_employee.name if subtask.assigned_employee else "Unassigned"
        print(f"   - {subtask.title} → {assignee_name} ({subtask.priority} priority)")
    
    # Verify relationships
    task_subtasks = Subtask.objects.filter(parent_task=task)
    print(f"✅ Task has {task_subtasks.count()} subtasks in database")
    
    # Verify task details
    print(f"✅ Task details:")
    print(f"   Title: {task.title}")
    print(f"   Priority: {task.priority}")
    print(f"   Assigned to: {task.employee.name if task.employee else 'Unassigned'}")
    print(f"   Created by: {task.created_by.username}")
    print(f"   Date: {task.date}")
    
    return True


def test_serializer_integration():
    """Test the TaskCreateSerializer with subtasks"""
    print("\n🔧 Testing TaskCreateSerializer integration")
    print("=" * 50)
    
    from hr_management.serializers import TaskCreateSerializer
    from django.test import RequestFactory
    
    # Get admin user
    try:
        admin_user = User.objects.get(username='admin') 
        employees = Employee.objects.all()[:2]
    except:
        print("❌ Test data not available")
        return False
    
    # Create mock request
    factory = RequestFactory()
    request = factory.post('/api/tasks/')
    request.user = admin_user
    
    # Test data
    test_data = {
        "title": "Serializer Test Task", 
        "description": "Testing serializer with subtasks",
        "priority": "high",
        "estimated_minutes": 90,
        "date": str(date.today()),
        "subtasks": [
            {
                "title": "First subtask",
                "description": "Test subtask 1",
                "assigned_employee": str(employees[0].id),
                "priority": "medium",
                "estimated_minutes": 45,
                "order": 1
            },
            {
                "title": "Second subtask",
                "description": "Test subtask 2", 
                "assigned_employee": str(employees[1].id),
                "priority": "low",
                "estimated_minutes": 45,
                "order": 2
            }
        ]
    }
    
    print(f"📝 Testing serializer with:")
    print(f"   Task: {test_data['title']}")
    print(f"   Subtasks: {len(test_data['subtasks'])}")
    
    # Test serializer validation
    serializer = TaskCreateSerializer(data=test_data, context={'request': request})
    
    if not serializer.is_valid():
        print(f"❌ Validation failed: {serializer.errors}")
        return False
    
    print("✅ Serializer validation passed")
    
    # Test creation
    try:
        task = serializer.save(created_by=admin_user)
        print(f"✅ Task created via serializer: {task.title}")
        
        # Check subtasks
        subtasks = Subtask.objects.filter(parent_task=task)
        print(f"✅ Subtasks created: {subtasks.count()}")
        
        for subtask in subtasks:
            print(f"   - {subtask.title} → {subtask.assigned_employee.name}")
            
        return subtasks.count() == 2
        
    except Exception as e:
        print(f"❌ Creation failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Testing Subtask Creation Integration")
    print("=" * 70)
    
    # Run tests
    test1 = test_database_directly()
    test2 = test_serializer_integration()
    
    print(f"\n📊 Results:")
    print(f"✅ Database creation: {'PASS' if test1 else 'FAIL'}")
    print(f"✅ Serializer integration: {'PASS' if test2 else 'FAIL'}")
    
    if test1 and test2:
        print(f"\n🎯 SUCCESS: Task + Subtask creation is working! ✅")
        print("   ✓ Direct database creation works")
        print("   ✓ Serializer handles subtasks correctly")
        print("   ✓ Backend is ready for frontend integration")
    else:
        print(f"\n❌ Some tests failed")
    
    sys.exit(0 if (test1 and test2) else 1)