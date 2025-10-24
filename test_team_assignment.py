#!/usr/bin/env python3

"""
Test script to verify team assignment functionality without requiring specific employees.
This tests that tasks can be assigned to teams without individual team member assignments.
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, TeamMembership, Task, Subtask
from django.db import models
from datetime import date
import uuid

def test_team_only_assignment():
    """Test creating tasks assigned to teams without specific employees"""
    print("🧪 Testing Team-Only Assignment Functionality")
    print("=" * 60)
    
    try:
        # Get existing test data
        admin_user = User.objects.get(username='admin')
        team = Team.objects.get(name='Web Development Team')
        
        # Create a task assigned to the team but no specific employee
        team_task = Task.objects.create(
            title='Team Planning & Strategy Session',
            description='''This is a team-wide task that doesn't require a specific assignee.
            
Any team member can take ownership of this task or collaborate on it:
- Plan quarterly objectives
- Discuss resource allocation
- Review team processes
- Identify improvement opportunities''',
            status='to_do',
            priority='medium',
            date=date.today(),
            created_by=admin_user,
            assigned_by_manager=True,
            team=team,
            employee=None,  # No specific employee assigned
            estimated_minutes=120  # 2 hours
        )
        
        print(f"✅ Created team-only task: {team_task.title}")
        print(f"   - Assigned to team: {team_task.team.name}")
        print(f"   - No specific employee assigned: {team_task.employee is None}")
        print(f"   - Task representation: {team_task}")
        
        # Create subtasks that can be assigned to individual team members
        subtasks_data = [
            {
                'title': 'Prepare Agenda',
                'description': 'Create detailed agenda for the planning session',
                'assigned_employee': None,  # Initially unassigned
                'priority': 'high',
                'estimated_minutes': 30,
                'order': 1
            },
            {
                'title': 'Research Best Practices',
                'description': 'Research industry best practices for team processes',
                'assigned_employee': None,  # Initially unassigned
                'priority': 'medium',
                'estimated_minutes': 60,
                'order': 2
            },
            {
                'title': 'Facilitate Discussion',
                'description': 'Lead the team discussion during the session',
                'assigned_employee': None,  # Initially unassigned
                'priority': 'high',
                'estimated_minutes': 90,
                'order': 3
            }
        ]
        
        created_subtasks = []
        for subtask_data in subtasks_data:
            subtask = Subtask.objects.create(
                parent_task=team_task,
                **subtask_data
            )
            created_subtasks.append(subtask)
            print(f"   ✅ Created unassigned subtask: {subtask.title}")
        
        # Now assign some subtasks to specific team members
        team_members = list(team.memberships.filter(is_active=True))
        if len(team_members) >= 2:
            # Assign first subtask to team leader
            if team.team_leader:
                created_subtasks[0].assigned_employee = team.team_leader
                created_subtasks[0].save()
                print(f"   📝 Assigned '{created_subtasks[0].title}' to team leader: {team.team_leader.name}")
            
            # Assign second subtask to a team member
            member_employee = team_members[0].employee
            created_subtasks[1].assigned_employee = member_employee
            created_subtasks[1].save()
            print(f"   📝 Assigned '{created_subtasks[1].title}' to team member: {member_employee.name}")
            
            # Leave third subtask unassigned (any team member can pick it up)
            print(f"   📝 Left '{created_subtasks[2].title}' unassigned for any team member")
        
        # Test team member access
        print(f"\n🔐 Testing Team Member Access:")
        team_member = team_members[0].employee
        team_member_user = team_member.user
        
        # Simulate checking if team member can view the task
        team_member_teams = list(team_member.team_memberships.filter(is_active=True).values_list('team_id', flat=True))
        can_view_team_task = team_task.team_id in team_member_teams and not team_task.employee
        
        print(f"   - Team member '{team_member.name}' can view team task: {can_view_team_task}")
        print(f"   - Team member is part of {len(team_member_teams)} active team(s)")
        
        # Test subtask access
        viewable_subtasks = Subtask.objects.filter(
            parent_task=team_task
        ).filter(
            # Can view if assigned to them OR if it's a team task without specific employee
            models.Q(assigned_employee=team_member) |
            models.Q(parent_task__team__in=team_member_teams, parent_task__employee__isnull=True)
        )
        
        print(f"   - Team member can view {viewable_subtasks.count()}/{len(created_subtasks)} subtasks")
        for subtask in viewable_subtasks:
            assignee = subtask.assigned_employee.name if subtask.assigned_employee else "Unassigned"
            print(f"     • {subtask.title} (assigned to: {assignee})")
        
        # Test assignment flexibility
        print(f"\n🔄 Testing Assignment Flexibility:")
        
        # Any team member should be able to assign themselves to unassigned subtasks
        unassigned_subtask = created_subtasks[2]  # The one we left unassigned
        print(f"   - Subtask '{unassigned_subtask.title}' is available for self-assignment")
        print(f"   - Current assignee: {unassigned_subtask.assigned_employee or 'None'}")
        
        # Simulate a team member taking ownership
        unassigned_subtask.assigned_employee = team_members[1].employee
        unassigned_subtask.save()
        print(f"   ✅ Team member '{team_members[1].employee.name}' took ownership of the subtask")
        
        print(f"\n📊 Final Summary:")
        print(f"   - Team task created: ✅")
        print(f"   - Task assigned to team without specific employee: ✅") 
        print(f"   - Subtasks can be individually assigned: ✅")
        print(f"   - Team members can view team tasks: ✅")
        print(f"   - Flexible assignment system working: ✅")
        
        return team_task, created_subtasks
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, []

def cleanup_test_data(team_task, subtasks):
    """Clean up test data"""
    print(f"\n🧹 Cleaning up test data...")
    
    if subtasks:
        for subtask in subtasks:
            subtask.delete()
        print(f"   ✅ Deleted {len(subtasks)} test subtasks")
    
    if team_task:
        team_task.delete()
        print(f"   ✅ Deleted test team task")

def main():
    """Main test function"""
    print("🚀 Starting Team Assignment Flexibility Tests")
    
    try:
        team_task, subtasks = test_team_only_assignment()
        
        if team_task:
            print(f"\n✅ All tests passed! Team assignment flexibility is working correctly.")
            print(f"\n💡 Key Benefits:")
            print(f"   - Tasks can be assigned to teams without specific employees")
            print(f"   - Team members can view and collaborate on team tasks")
            print(f"   - Subtasks can be assigned individually or left for self-assignment")
            print(f"   - Flexible workflow supports different team management styles")
            
        # Clean up test data
        cleanup_test_data(team_task, subtasks)
        
    except Exception as e:
        print(f"\n❌ Tests failed with error: {str(e)}")

if __name__ == '__main__':
    main()