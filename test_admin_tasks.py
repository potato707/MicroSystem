#!/usr/bin/env python3
"""
Test admin personal tasks functionality
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.test import Client
from hr_management.models import Employee, User, Task
from datetime import date

def test_admin_personal_tasks():
    """Test that admins can have personal tasks"""
    print("🧪 TESTING ADMIN PERSONAL TASKS FUNCTIONALITY\n")
    print("=" * 60)
    
    # Create or get an admin user with an employee profile
    admin_user, created = User.objects.get_or_create(
        username='admin_test_tasks',
        defaults={
            'email': 'admin@test.com',
            'name': 'Admin Test User',
            'role': 'admin'
        }
    )
    
    if created or not admin_user.check_password('adminpass123'):
        admin_user.set_password('adminpass123')
        admin_user.save()
    
    # Create employee profile for admin if it doesn't exist
    admin_employee, emp_created = Employee.objects.get_or_create(
        user=admin_user,
        defaults={
            'name': 'Admin Test User',
            'position': 'System Administrator',
            'department': 'IT',
            'hire_date': date.today(),
            'salary': 5000.00,
            'phone': '1234567890',
            'email': 'admin@test.com',
            'address': 'Test Address',
            'emergency_contact': 'Emergency Contact',
            'status': 'active'
        }
    )
    
    client = Client()
    
    # Login as admin
    print("🔓 Test 1: Admin Login")
    login_data = {
        "username": "admin_test_tasks",
        "password": "adminpass123"
    }
    
    login_response = client.post('/api/token/', 
                               data=json.dumps(login_data), 
                               content_type='application/json')
    
    print(f"   Login Status: {login_response.status_code}")
    
    if login_response.status_code == 200:
        print("   ✅ Admin login successful")
        
        login_data = login_response.json()
        token = login_data.get('access')
        
        # Test 2: Fetch today's tasks for admin
        print("\\n📋 Test 2: Fetch Admin's Today Tasks")
        
        tasks_response = client.get('/hr/tasks/today/', 
                                  HTTP_AUTHORIZATION=f'Bearer {token}')
        
        print(f"   Tasks Response Status: {tasks_response.status_code}")
        
        if tasks_response.status_code == 200:
            print("   ✅ Successfully fetched admin's tasks")
            tasks_data = tasks_response.json()
            print(f"   📊 Current tasks count: {len(tasks_data.get('tasks', []))}")
            print(f"   📈 Task summary: {tasks_data.get('summary', {})}")
            
            # Test 3: Create a personal task for admin
            print("\\n➕ Test 3: Create Personal Task for Admin")
            
            task_data = {
                "title": "Admin Personal Task - System Maintenance",
                "description": "Review system logs and update security patches",
                "priority": "high",
                "date": date.today().strftime('%Y-%m-%d')
            }
            
            create_response = client.post('/hr/tasks/', 
                                        data=json.dumps(task_data),
                                        content_type='application/json',
                                        HTTP_AUTHORIZATION=f'Bearer {token}')
            
            print(f"   Create Task Status: {create_response.status_code}")
            
            if create_response.status_code == 201:
                print("   ✅ Successfully created personal task for admin")
                created_task = create_response.json()
                print(f"   📝 Task ID: {created_task.get('id')}")
                print(f"   📝 Task Title: {created_task.get('title')}")
                print(f"   👤 Assigned to: {created_task.get('employee_name')}")
                
                # Test 4: Fetch tasks again to verify
                print("\\n🔄 Test 4: Verify Task Creation")
                
                verify_response = client.get('/hr/tasks/today/', 
                                           HTTP_AUTHORIZATION=f'Bearer {token}')
                
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    new_tasks_count = len(verify_data.get('tasks', []))
                    print(f"   📊 Updated tasks count: {new_tasks_count}")
                    
                    if new_tasks_count > 0:
                        print("   ✅ Task creation verified - admin has personal tasks!")
                        
                        # Show task details
                        for task in verify_data.get('tasks', []):
                            print(f"   📋 Task: {task.get('title')} ({task.get('status')})")
                    else:
                        print("   ❌ Task not found in admin's task list")
                else:
                    print(f"   ❌ Failed to verify task creation: {verify_response.status_code}")
                    
            else:
                print(f"   ❌ Failed to create task: {create_response.content.decode()}")
                
        else:
            print(f"   ❌ Failed to fetch tasks: {tasks_response.content.decode()}")
    else:
        print(f"   ❌ Admin login failed: {login_response.content.decode()}")
    
    print("\\n" + "=" * 60)
    print("✅ ADMIN PERSONAL TASKS TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_admin_personal_tasks()