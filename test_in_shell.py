"""
Test script to check task progress statistics for client complaints
"""
from hr_management.models import ClientComplaint, Task, ClientComplaintTask
from hr_management.serializers import ClientComplaintSerializer

print("Testing task progress statistics for client complaints...")
print("=" * 60)

# Get all client complaints that have tasks
complaints_with_tasks = ClientComplaint.objects.filter(tasks__isnull=False).distinct()

if not complaints_with_tasks.exists():
    print("No complaints with tasks found in database.")
    # Let's check all complaints
    all_complaints = ClientComplaint.objects.all()
    print(f"Total complaints in database: {all_complaints.count()}")
    for complaint in all_complaints[:3]:  # Show first 3
        print(f"- {complaint.title} (ID: {complaint.id})")
        tasks_count = Task.objects.filter(client_complaint_task__complaint=complaint).count()
        print(f"  Tasks: {tasks_count}")
else:
    for complaint in complaints_with_tasks:
        print(f"\nComplaint: {complaint.title}")
        print(f"Client: {complaint.client_name}")
        print(f"Status: {complaint.status}")
        
        # Test the task_statistics property directly
        try:
            stats = complaint.task_statistics
            print(f"\nTask Statistics (from model property):")
            print(f"  Total tasks: {stats['total_tasks']}")
            print(f"  Completed tasks: {stats['completed_tasks']}")
            print(f"  In-progress tasks: {stats['in_progress_tasks']}")
            print(f"  Pending tasks: {stats['pending_tasks']}")
            print(f"  Completion percentage: {stats['completion_percentage']}%")
        except Exception as e:
            print(f"Error getting task statistics: {e}")
        
        # Show individual task details for verification
        tasks = Task.objects.filter(client_complaint_task__complaint=complaint)
        print(f"\nIndividual Task Details:")
        for i, task in enumerate(tasks, 1):
            print(f"  {i}. {task.title} - Status: {task.status} ({task.get_status_display()})")
        
        print("-" * 60)

# Check task status distribution
print("\nChecking task status mappings...")
all_tasks = Task.objects.filter(client_complaint_task__isnull=False)
status_counts = {}

for task in all_tasks:
    status = task.status
    status_counts[status] = status_counts.get(status, 0) + 1

print("Task status distribution:")
for status, count in status_counts.items():
    display_name = dict(Task.STATUS_CHOICES).get(status, status)
    print(f"  {status} ({display_name}): {count} tasks")

print("\n✅ Task progress statistics test completed!")