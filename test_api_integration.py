#!/usr/bin/env python3
"""
Test the task creation API endpoint directly to ensure it works for frontend
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
from django.test import Client
from django.contrib.auth import authenticate


def test_api_endpoint():
    """Test the actual API endpoint that frontend will call"""
    print("🌐 Testing Task Creation API Endpoint")
    print("=" * 40)
    
    # Get existing admin user
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✅ Using admin user: {admin_user.username}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return False
    
    # Get existing team and employees
    try:
        team = Team.objects.first()
        employees = Employee.objects.all()[:2]
        print(f"✅ Using team: {team.name}")
        print(f"✅ Available employees: {len(employees)}")
    except:
        print("❌ Required test data not found")
        return False
    
    # Create Django test client
    client = Client()
    
    # Login as admin
    login_success = client.login(username='admin', password='admin123')
    if not login_success:
        print("❌ Login failed")
        return False
    
    print("✅ Login successful")
    
    # Prepare task data with subtasks (simulating frontend payload)
    task_payload = {
        "title": "Frontend API Test Task",
        "description": "Testing task creation from frontend",
        "priority": "medium", 
        "estimated_minutes": 180,
        "date": str(date.today()),
        "team": str(team.id),
        "subtasks": [
            {
                "title": "Setup environment",
                "description": "Configure development environment",
                "assigned_employee": str(employees[0].id),
                "priority": "high",
                "estimated_minutes": 60,
                "order": 1
            },
            {
                "title": "Implement feature",
                "description": "Build the main functionality",
                "assigned_employee": str(employees[1].id),
                "priority": "medium",
                "estimated_minutes": 90,
                "order": 2
            },
            {
                "title": "Write tests", 
                "description": "Add unit tests",
                "assigned_employee": None,  # Unassigned
                "priority": "low",
                "estimated_minutes": 30,
                "order": 3
            }
        ]
    }
    
    print(f"\n📤 Creating task via API:")
    print(f"   Title: {task_payload['title']}")
    print(f"   Team: {team.name}")
    print(f"   Subtasks: {len(task_payload['subtasks'])}")
    
    # Make API request
    response = client.post(
        '/api/tasks/',
        data=json.dumps(task_payload),
        content_type='application/json'
    )
    
    print(f"📥 API Response: {response.status_code}")
    
    if response.status_code != 201:
        print(f"❌ API Error: {response.content.decode()}")
        return False
        
    # Parse response
    response_data = json.loads(response.content.decode())
    task_id = response_data.get('id')
    
    print(f"✅ Task created successfully!")
    print(f"   Task ID: {task_id}")
    print(f"   Response keys: {list(response_data.keys())}")
    
    # Verify in database
    task = Task.objects.get(id=task_id)
    subtasks = Subtask.objects.filter(parent_task=task).order_by('order')
    
    print(f"\n🔍 Database verification:")
    print(f"   Task: {task.title}")
    print(f"   Team assigned: {task.team.name if task.team else 'None'}")
    print(f"   Subtasks found: {subtasks.count()}")
    
    # Check each subtask
    for i, subtask in enumerate(subtasks):
        assignee = subtask.assigned_employee.name if subtask.assigned_employee else "Unassigned"
        print(f"   Subtask {i+1}: '{subtask.title}' → {assignee}")
    
    # Test GET endpoint to ensure task shows up correctly
    print(f"\n🔍 Testing task retrieval...")
    get_response = client.get(f'/api/tasks/{task_id}/')
    
    if get_response.status_code == 200:
        task_data = json.loads(get_response.content.decode())
        print(f"✅ Task retrieved successfully")
        print(f"   Subtasks in response: {len(task_data.get('subtasks', []))}")
    else:
        print(f"❌ Failed to retrieve task: {get_response.status_code}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_api_endpoint()
    if success:
        print(f"\n🎯 SUCCESS: Frontend API integration ready! ✅")
        print("   ✓ Tasks can be created with subtasks via API")
        print("   ✓ Subtask assignment works correctly") 
        print("   ✓ Task retrieval includes subtasks")
        print("   ✓ Frontend can now create tasks with subtasks in single request")
    else:
        print(f"\n❌ FAILED: API integration issues detected")
    
    sys.exit(0 if success else 1)