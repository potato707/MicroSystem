#!/usr/bin/env python3
"""
Test script to manually create a ClientComplaintTask to verify the linking works
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, Task, Team, ClientComplaintTask, User

def test_complaint_task_linking():
    print("=== Testing Complaint-Task Linking ===")
    
    # Get a complaint that has team assignments
    complaint = ClientComplaint.objects.filter(assignments__is_active=True).first()
    if not complaint:
        print("ERROR: No complaints with active team assignments found")
        return
    
    print(f"Found complaint: {complaint.title}")
    
    # Get a task
    task = Task.objects.first()
    if not task:
        print("ERROR: No tasks found")
        return
        
    print(f"Found task: {task.title}")
    
    # Get the team from complaint assignment
    team_assignment = complaint.assignments.filter(is_active=True).first()
    team = team_assignment.team
    print(f"Found team: {team.name}")
    
    # Get a user (admin or member of the team)
    user = User.objects.filter(role='admin').first()
    if not user:
        user = User.objects.first()
    print(f"Using user: {user.username}")
    
    # Check if task is already linked
    if hasattr(task, 'client_complaint_task'):
        print(f"Task already linked to complaint: {task.client_complaint_task.complaint.title}")
        return
    
    # Create the link
    try:
        complaint_task = ClientComplaintTask.objects.create(
            complaint=complaint,
            task=task,
            team=team,
            created_by=user,
            notes="Manual test link"
        )
        
        print(f"SUCCESS: Created complaint-task link: {complaint_task.id}")
        print(f"  Complaint: {complaint_task.complaint.title}")
        print(f"  Task: {complaint_task.task.title}")
        print(f"  Team: {complaint_task.team.name}")
        
        # Verify the complaint now has tasks
        print(f"\nVerification:")
        print(f"  Complaint tasks count: {complaint.tasks.count()}")
        for ct in complaint.tasks.all():
            print(f"    - {ct.task.title} (Status: {ct.task.status})")
            
    except Exception as e:
        print(f"ERROR: Failed to create link: {e}")

if __name__ == "__main__":
    test_complaint_task_linking()