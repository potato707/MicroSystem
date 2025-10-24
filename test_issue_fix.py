"""
Test the specific issue: completed tasks should show in progress statistics
"""
from hr_management.models import ClientComplaint, Task
from hr_management.serializers import ClientComplaintSerializer
import json

print("Testing the specific issue reported by user...")
print("=" * 60)

# Find complaints that have completed tasks
complaints = ClientComplaint.objects.filter(tasks__task__status='done')

for complaint in complaints:
    print(f"\nComplaint: {complaint.title}")
    print(f"Client: {complaint.client_name}")
    print(f"Status: {complaint.status}")
    
    # Get task details
    tasks = Task.objects.filter(client_complaint_task__complaint=complaint)
    
    print(f"\nTask Details:")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. {task.title}")
        print(f"     Status: {task.status} ({task.get_status_display()})")
        if task.status == 'done':
            print("     ✅ This task is COMPLETED")
    
    # Get statistics
    stats = complaint.task_statistics
    print(f"\nTask Progress Statistics:")
    print(f"  📊 Total tasks: {stats['total_tasks']}")
    print(f"  ✅ Completed tasks: {stats['completed_tasks']}")
    print(f"  🔄 In-progress tasks: {stats['in_progress_tasks']}")
    print(f"  ⏳ Pending tasks: {stats['pending_tasks']}")
    print(f"  📈 Progress: {stats['completion_percentage']}%")
    
    # Test what user would see in the API
    serializer = ClientComplaintSerializer(complaint)
    api_stats = serializer.data['task_statistics']
    
    print(f"\nWhat user will see in the API:")
    print(f"  Total: {api_stats['total_tasks']}")
    print(f"  Completed: {api_stats['completed_tasks']} (was showing 0 before)")
    print(f"  In Progress: {api_stats['in_progress_tasks']}")
    print(f"  Progress: {api_stats['completion_percentage']}% (was showing 0% before)")
    
    # Verify the fix
    if api_stats['completed_tasks'] > 0:
        print(f"\n✅ FIX SUCCESSFUL: Completed tasks are now properly counted!")
    else:
        print(f"\n❌ Issue still exists: Completed tasks not being counted")
    
    print("-" * 60)

print("\n🎉 Issue resolution test completed!")