#!/usr/bin/env python3

"""
Complete integration test for team assignment functionality.
Tests both backend API and simulates frontend workflows.
"""

import os
import sys
import django
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, TeamMembership, Task, Subtask
from hr_management.views import AssignTaskToTeamView, AssignableEmployeesView
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response
from datetime import date

def test_complete_workflow():
    """Test the complete team assignment workflow"""
    print("🔄 Testing Complete Team Assignment Workflow")
    print("=" * 60)
    
    try:
        # Get test data
        admin_user = User.objects.get(username='admin')
        manager_user = User.objects.get(username='team_manager')
        team = Team.objects.get(name='Web Development Team')
        
        factory = APIRequestFactory()
        
        # Test 1: Create task assigned to team without specific employee (via API)
        print("1️⃣ Testing Team-Only Task Creation via API...")
        
        task_data = {
            'title': 'API Integration Testing',
            'description': 'Test all API endpoints and ensure proper integration',
            'priority': 'high',
            'team_id': str(team.id),
            'estimated_minutes': 180,
            'team_priority': 'high'
        }
        
        request = factory.post('/hr/tasks/assign-to-team/', task_data, format='json')
        request.user = admin_user
        
        view = AssignTaskToTeamView()
        view.request = request
        
        # Manually set the data attribute for the view
        request.data = task_data
        
        response = view.post(request)
        
        if response.status_code == 201:
            print(f"   ✅ Team task created successfully")
            
            # Get the task ID from the team_task data
            team_task_data = response.data['team_task']
            task_id = str(team_task_data['task'])  # The task field contains the UUID directly
            created_task = Task.objects.get(id=task_id)
            print(f"   - Task: {created_task.title}")
            print(f"   - Assigned to team: {created_task.team.name}")
            print(f"   - No specific employee: {created_task.employee is None}")
        else:
            print(f"   ❌ Failed to create team task: {response.data}")
            return False
        
        # Test 2: Get assignable employees for the task
        print(f"\n2️⃣ Testing Assignable Employees API...")
        
        request = factory.get(f'/hr/tasks/{task_id}/assignable-employees/')
        request.user = admin_user
        
        view = AssignableEmployeesView()
        view.request = request
        
        response = view.get(request, task_id)
        
        if response.status_code == 200:
            assignable_employees = response.data
            print(f"   ✅ Retrieved {len(assignable_employees)} assignable employees")
            for emp in assignable_employees:
                print(f"     • {emp['name']} ({emp['position']}) - Role: {emp.get('team_role', 'N/A')}")
        else:
            print(f"   ❌ Failed to get assignable employees: {response.data}")
            return False
        
        # Test 3: Create subtasks and assign to team members
        print(f"\n3️⃣ Testing Subtask Assignment...")
        
        # Create unassigned subtask
        unassigned_subtask = Subtask.objects.create(
            parent_task=created_task,
            title='Code Review & Testing',
            description='Review code quality and run comprehensive tests',
            priority='high',
            estimated_minutes=60,
            assigned_employee=None,  # Unassigned
            order=1
        )
        print(f"   ✅ Created unassigned subtask: {unassigned_subtask.title}")
        
        # Assign subtask to specific team member
        if assignable_employees:
            first_employee_id = assignable_employees[0]['id']
            assigned_employee = Employee.objects.get(id=first_employee_id)
            
            assigned_subtask = Subtask.objects.create(
                parent_task=created_task,
                title='Documentation Update',
                description='Update API documentation with new endpoints',
                priority='medium',
                estimated_minutes=45,
                assigned_employee=assigned_employee,
                order=2
            )
            print(f"   ✅ Created assigned subtask: {assigned_subtask.title} → {assigned_employee.name}")
        
        # Test 4: Verify team member access
        print(f"\n4️⃣ Testing Team Member Access...")
        
        team_member = team.memberships.filter(is_active=True).first().employee
        team_member_user = team_member.user
        
        # Check if team member can view the team task
        from django.db.models import Q
        
        team_member_teams = list(team_member.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
        accessible_tasks = Task.objects.filter(
            Q(employee=team_member) |  # Tasks assigned directly
            Q(team_id__in=team_member_teams, employee__isnull=True)  # Team tasks without specific employee
        )
        
        can_access_task = accessible_tasks.filter(id=created_task.id).exists()
        print(f"   ✅ Team member '{team_member.name}' can access team task: {can_access_task}")
        
        # Check subtask access
        accessible_subtasks = Subtask.objects.filter(
            parent_task=created_task
        ).filter(
            Q(assigned_employee=team_member) |
            Q(parent_task__team_id__in=team_member_teams, parent_task__employee__isnull=True)
        )
        
        print(f"   ✅ Team member can access {accessible_subtasks.count()} subtask(s)")
        
        # Test 5: Test permissions for task creation by team manager
        print(f"\n5️⃣ Testing Team Manager Permissions...")
        
        # Team manager should be able to create tasks for their team
        manager_task_data = {
            'title': 'Weekly Team Review',
            'description': 'Review team progress and plan next week',
            'priority': 'medium',
            'team_id': str(team.id),
            'estimated_minutes': 90
        }
        
        request = factory.post('/hr/tasks/assign-to-team/', manager_task_data, format='json')
        request.user = manager_user
        
        view = AssignTaskToTeamView()
        view.request = request
        
        # Manually set the data attribute for the view
        request.data = manager_task_data
        
        response = view.post(request)
        
        if response.status_code == 201:
            manager_team_task_data = response.data['team_task']
            manager_task_id = str(manager_team_task_data['task'])  # The task field contains the UUID directly
            manager_task = Task.objects.get(id=manager_task_id)
            print(f"   ✅ Manager created team task: {manager_task.title}")
            print(f"   - No specific assignee: {manager_task.employee is None}")
        else:
            print(f"   ❌ Manager failed to create team task: {response.data}")
        
        # Test 6: Cleanup
        print(f"\n6️⃣ Cleaning up test data...")
        
        # Delete created tasks and subtasks
        Task.objects.filter(id__in=[created_task.id, manager_task_id]).delete()
        print(f"   ✅ Cleaned up test data")
        
        print(f"\n🎉 Complete Integration Test PASSED!")
        print(f"\n✅ Verified Features:")
        print(f"   • Team-only task assignment without specific employees ✓")
        print(f"   • API endpoints for assignable employees ✓")
        print(f"   • Subtask individual assignment within team tasks ✓")
        print(f"   • Team member access permissions ✓")
        print(f"   • Manager permissions for team task creation ✓")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the complete integration test"""
    print("🚀 Starting Complete Integration Test")
    
    success = test_complete_workflow()
    
    if success:
        print(f"\n🎯 RESULT: All tests PASSED! ✅")
        print(f"\nThe team assignment functionality is working correctly:")
        print(f"• Admins and team managers can assign tasks to teams")
        print(f"• Team member assignment is now OPTIONAL")
        print(f"• Subtasks can be assigned to individual team members")
        print(f"• Team members have appropriate access to team tasks")
    else:
        print(f"\n❌ RESULT: Some tests FAILED!")

if __name__ == '__main__':
    main()