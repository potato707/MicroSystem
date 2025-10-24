"""
Test serializer output for task progress statistics
"""
from hr_management.models import ClientComplaint
from hr_management.serializers import ClientComplaintSerializer
import json

print("Testing serializer output for task progress statistics...")
print("=" * 60)

# Get a complaint with tasks
complaint = ClientComplaint.objects.filter(tasks__isnull=False).first()

if complaint:
    print(f"Testing complaint: {complaint.title}")
    
    # Serialize the complaint
    serializer = ClientComplaintSerializer(complaint)
    data = serializer.data
    
    # Check if task_statistics is in the output
    if 'task_statistics' in data:
        stats = data['task_statistics']
        print(f"\n✅ task_statistics found in serializer output:")
        print(f"  Total tasks: {stats['total_tasks']}")
        print(f"  Completed tasks: {stats['completed_tasks']}")
        print(f"  In-progress tasks: {stats['in_progress_tasks']}")
        print(f"  Pending tasks: {stats['pending_tasks']}")
        print(f"  Completion percentage: {stats['completion_percentage']}%")
        
        print(f"\nFull task_statistics JSON:")
        print(json.dumps(stats, indent=2))
    else:
        print("❌ task_statistics NOT found in serializer output!")
        print("Available fields:", list(data.keys()))
else:
    print("No complaints with tasks found for testing.")

print("\n✅ Serializer test completed!")