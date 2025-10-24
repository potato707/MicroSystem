#!/usr/bin/env python
"""
Test script to verify the task progress statistics fix for client complaints.
"""
import os
import sys
import django
from django.conf import settings

# Add the project root to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, Task, ClientComplaintTask
from hr_management.serializers import ClientComplaintSerializer

def test_task_progress_statistics():
    """Test the task progress statistics calculation"""
    
    print("Testing task progress statistics for client complaints...")
    print("=" * 60)
    
    # Get all client complaints that have tasks
    complaints_with_tasks = ClientComplaint.objects.filter(tasks__isnull=False).distinct()
    
    if not complaints_with_tasks.exists():
        print("No complaints with tasks found in database.")
        return
    
    for complaint in complaints_with_tasks:
        print(f"\nComplaint: {complaint.title}")
        print(f"Client: {complaint.client_name}")
        print(f"Status: {complaint.status}")
        
        # Test the task_statistics property directly
        stats = complaint.task_statistics
        print(f"\nTask Statistics (from model property):")
        print(f"  Total tasks: {stats['total_tasks']}")
        print(f"  Completed tasks: {stats['completed_tasks']}")
        print(f"  In-progress tasks: {stats['in_progress_tasks']}")
        print(f"  Pending tasks: {stats['pending_tasks']}")
        print(f"  Completion percentage: {stats['completion_percentage']}%")
        
        # Test the serializer output
        serializer = ClientComplaintSerializer(complaint)
        serialized_stats = serializer.data.get('task_statistics')
        print(f"\nTask Statistics (from serializer):")
        if serialized_stats:
            print(f"  Total tasks: {serialized_stats['total_tasks']}")
            print(f"  Completed tasks: {serialized_stats['completed_tasks']}")
            print(f"  In-progress tasks: {serialized_stats['in_progress_tasks']}")
            print(f"  Pending tasks: {serialized_stats['pending_tasks']}")
            print(f"  Completion percentage: {serialized_stats['completion_percentage']}%")
        else:
            print("  ERROR: task_statistics not found in serializer output!")
        
        # Show individual task details for verification
        tasks = Task.objects.filter(client_complaint_task__complaint=complaint)
        print(f"\nIndividual Task Details:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task.title} - Status: {task.status} ({task.get_status_display()})")
        
        print("-" * 60)

def check_task_status_mapping():
    """Verify task status values match our calculations"""
    print("\nChecking task status mappings...")
    print("=" * 40)
    
    # Check all task statuses in database
    all_tasks = Task.objects.filter(client_complaint_task__isnull=False)
    status_counts = {}
    
    for task in all_tasks:
        status = task.status
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts[status] = 1
    
    print("Task status distribution:")
    for status, count in status_counts.items():
        display_name = dict(Task.STATUS_CHOICES).get(status, status)
        print(f"  {status} ({display_name}): {count} tasks")
    
    # Check for any tasks with unexpected status values
    expected_statuses = ['to_do', 'doing', 'done']
    unexpected = [status for status in status_counts.keys() if status not in expected_statuses]
    if unexpected:
        print(f"\nWARNING: Found unexpected task statuses: {unexpected}")
    else:
        print("\nAll task statuses are as expected.")

if __name__ == "__main__":
    try:
        test_task_progress_statistics()
        check_task_status_mapping()
        print("\n✅ Task progress statistics test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()