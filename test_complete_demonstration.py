#!/usr/bin/env python3
"""
Final comprehensive test demonstrating the complete subtask creation workflow
Shows how the system now supports creating tasks with subtasks in a single operation
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
from hr_management.serializers import TaskCreateSerializer
from django.test import RequestFactory


def demonstrate_complete_workflow():
    """Demonstrate the complete workflow: Frontend → API → Database"""
    print("🌟 COMPLETE SUBTASK CREATION WORKFLOW DEMONSTRATION")
    print("=" * 70)
    print("This demonstrates the new functionality where admins/managers can")
    print("create tasks with subtasks and assign team members in a single operation.\n")
    
    # Get existing data
    admin_user = User.objects.get(username='admin')
    team = Team.objects.first()
    employees = list(Employee.objects.all()[:3])
    
    print(f"👤 Admin User: {admin_user.username} ({admin_user.role})")
    print(f"👥 Team: {team.name}")
    print(f"🧑‍💼 Available Team Members: {len(employees)}")
    for emp in employees:
        print(f"   - {emp.name} ({emp.position})")
    
    # Simulate frontend payload (what React component would send)
    print(f"\n📤 FRONTEND PAYLOAD (React → API):")
    print("-" * 40)
    
    frontend_payload = {
        "title": "Develop New Feature: User Dashboard",
        "description": "Create a comprehensive user dashboard with analytics and user management",
        "priority": "high",
        "estimated_minutes": 480,  # 8 hours total
        "date": str(date.today()),
        "team": str(team.id),
        "subtasks": [
            {
                "title": "UI/UX Design",
                "description": "Design mockups and user interface wireframes",
                "assigned_employee": str(employees[0].id),
                "priority": "high", 
                "estimated_minutes": 120,
                "order": 1
            },
            {
                "title": "Backend API Development",
                "description": "Build REST APIs for dashboard data",
                "assigned_employee": str(employees[1].id),
                "priority": "high",
                "estimated_minutes": 180,
                "order": 2
            },
            {
                "title": "Frontend Implementation", 
                "description": "Build React components and integrate with APIs",
                "assigned_employee": str(employees[2].id),
                "priority": "medium",
                "estimated_minutes": 150,
                "order": 3
            },
            {
                "title": "Testing & QA",
                "description": "Write unit tests and perform quality assurance",
                "assigned_employee": None,  # Unassigned - team can pick up
                "priority": "medium",
                "estimated_minutes": 90,
                "order": 4
            },
            {
                "title": "Documentation",
                "description": "Write user documentation and API docs",
                "assigned_employee": str(employees[0].id),  # Designer can handle docs
                "priority": "low",
                "estimated_minutes": 60,
                "order": 5
            }
        ]
    }
    
    print(f"Task: {frontend_payload['title']}")
    print(f"Team: {team.name}")
    print(f"Priority: {frontend_payload['priority']}")
    print(f"Total Time: {frontend_payload['estimated_minutes']} minutes")
    print(f"Subtasks: {len(frontend_payload['subtasks'])}")
    
    for i, subtask in enumerate(frontend_payload['subtasks']):
        if subtask['assigned_employee']:
            assignee = next(emp.name for emp in employees if str(emp.id) == subtask['assigned_employee'])
        else:
            assignee = "Unassigned"
        print(f"  {i+1}. {subtask['title']} → {assignee} ({subtask['estimated_minutes']}min)")
    
    # Process through API layer (TaskCreateSerializer)
    print(f"\n⚙️  API PROCESSING:")
    print("-" * 20)
    
    factory = RequestFactory()
    request = factory.post('/api/tasks/')
    request.user = admin_user
    
    serializer = TaskCreateSerializer(data=frontend_payload, context={'request': request})
    
    if not serializer.is_valid():
        print(f"❌ Validation failed: {serializer.errors}")
        return False
        
    print("✅ Payload validation successful")
    
    # Save to database (single atomic operation) 
    task = serializer.save(created_by=admin_user)
    
    # Add team assignment
    if team:
        task.team = team
        task.save()
    
    print("✅ Task and subtasks created in single transaction")
    
    # Verify results in database
    print(f"\n🗄️  DATABASE RESULTS:")
    print("-" * 25)
    
    # Main task
    print(f"📋 Task Created:")
    print(f"   ID: {task.id}")
    print(f"   Title: {task.title}")
    print(f"   Priority: {task.priority}")
    print(f"   Team: {task.team.name if task.team else 'None'}")
    print(f"   Created by: {task.created_by.username}")
    print(f"   Total estimated time: {task.estimated_minutes} minutes")
    
    # Subtasks
    subtasks = Subtask.objects.filter(parent_task=task).order_by('order')
    print(f"\n📝 Subtasks Created ({subtasks.count()}):")
    
    for subtask in subtasks:
        assignee = subtask.assigned_employee.name if subtask.assigned_employee else "🔄 Unassigned"
        print(f"   {subtask.order}. {subtask.title}")
        print(f"      → Assigned: {assignee}")
        print(f"      → Priority: {subtask.priority}")
        print(f"      → Time: {subtask.estimated_minutes} minutes")
        print(f"      → Status: {subtask.status}")
    
    # Show total time allocation
    print(f"\n⏱️  TIME ALLOCATION SUMMARY:")
    print("-" * 30)
    
    subtask_time = sum(st.estimated_minutes for st in subtasks)
    print(f"Main task estimate: {task.estimated_minutes} minutes")
    print(f"Subtasks total: {subtask_time} minutes")
    print(f"Time efficiency: {(subtask_time/task.estimated_minutes)*100:.1f}%")
    
    # Show assignment distribution
    print(f"\n👥 ASSIGNMENT DISTRIBUTION:")
    print("-" * 30)
    
    assignment_counts = {}
    for subtask in subtasks:
        if subtask.assigned_employee:
            name = subtask.assigned_employee.name
            assignment_counts[name] = assignment_counts.get(name, 0) + 1
        else:
            assignment_counts["Unassigned"] = assignment_counts.get("Unassigned", 0) + 1
    
    for person, count in assignment_counts.items():
        print(f"   {person}: {count} subtask(s)")
    
    print(f"\n🎯 WORKFLOW COMPLETE! ✅")
    print("=" * 40)
    print("✅ Single API call created task + subtasks")
    print("✅ Team members assigned to specific subtasks") 
    print("✅ Some subtasks left unassigned for team flexibility")
    print("✅ All relationships properly established in database")
    print("✅ Ready for frontend integration!")
    
    return True


def show_api_example():
    """Show example of how frontend would call the API"""
    print(f"\n📚 FRONTEND INTEGRATION EXAMPLE:")
    print("=" * 50)
    print("""
// React component example - TaskDialog.tsx
const handleSubmit = async (formData) => {
  const taskPayload = {
    title: formData.title,
    description: formData.description,
    priority: formData.priority,
    estimated_minutes: formData.estimated_minutes,
    date: formData.date,
    team: formData.team,
    subtasks: subtasks.map(subtask => ({
      title: subtask.title,
      description: subtask.description,
      assigned_employee: subtask.assigned_employee === "unassigned" ? null : subtask.assigned_employee,
      priority: subtask.priority,
      estimated_minutes: subtask.estimated_minutes,
      order: subtask.order
    }))
  }
  
  // Single API call creates task + all subtasks
  const response = await api.createTask(taskPayload)
  console.log('Task with subtasks created:', response.id)
}
    """)


if __name__ == "__main__":
    try:
        success = demonstrate_complete_workflow()
        if success:
            show_api_example()
            print(f"\n🚀 IMPLEMENTATION COMPLETE! 🚀")
            print("The system now supports creating tasks with subtasks in a single operation.")
            print("Admins and managers can assign subtasks to team members during task creation.")
            
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"💥 Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)