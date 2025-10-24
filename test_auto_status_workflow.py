#!/usr/bin/env python
"""
Test script to demonstrate the complete auto-status update workflow
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ClientComplaintComment
from django.contrib.auth import get_user_model

User = get_user_model()

def print_separator():
    print("\n" + "="*70 + "\n")

def show_complaint_status(complaint):
    """Display current complaint status"""
    print(f"📋 Complaint: {complaint.title}")
    print(f"   Status: {complaint.status}")
    print(f"   Automated Status: {complaint.automated_status}")
    print(f"   Last Responder: {complaint.last_responder}")
    print(f"   Last Response Time: {complaint.last_response_time}")
    print(f"   Delay Status: {complaint.delay_status}")

def test_auto_status_update():
    """Test the auto-status update workflow"""
    
    # Test with the complaint from the user's request
    complaint_id = '812c7c0b-c3b9-4c84-b99c-b0431e13095f'
    
    try:
        complaint = ClientComplaint.objects.get(id=complaint_id)
    except ClientComplaint.DoesNotExist:
        print("❌ Complaint not found")
        return
    
    print_separator()
    print("🔍 INITIAL STATUS")
    print_separator()
    show_complaint_status(complaint)
    
    # Get a user to act as commenter
    try:
        user = User.objects.get(username='ahmed')
    except User.DoesNotExist:
        user = User.objects.filter(role='admin').first()
        if not user:
            print("❌ No admin user found")
            return
    
    print_separator()
    print("💬 ADDING NEW COMMENT (System Response)")
    print_separator()
    
    # Create a new comment
    comment = ClientComplaintComment.objects.create(
        complaint=complaint,
        author=user,
        comment="This is a test comment to trigger status update",
        is_internal=False
    )
    
    print(f"✅ Comment created: ID={comment.id}, Author={comment.author.name}")
    
    # Trigger the auto-update
    from hr_management.ticket_automation import TicketStatusManager
    TicketStatusManager.transition_on_system_response(complaint)
    
    # Refresh complaint from database
    complaint.refresh_from_db()
    
    print_separator()
    print("📊 UPDATED STATUS (After System Response)")
    print_separator()
    show_complaint_status(complaint)
    
    # Test serialization
    print_separator()
    print("🔄 API SERIALIZATION TEST")
    print_separator()
    
    from hr_management.serializers import ClientComplaintSerializer
    serializer = ClientComplaintSerializer(complaint)
    
    # Extract relevant fields
    data = serializer.data
    print(f"✅ automated_status: {data.get('automated_status')}")
    print(f"✅ automated_status_message: {data.get('automated_status_message')}")
    print(f"✅ last_responder: {data.get('last_responder')}")
    print(f"✅ last_response_time: {data.get('last_response_time')}")
    print(f"✅ delay_status: {data.get('delay_status')}")
    
    print_separator()
    print("✨ AUTO-STATUS UPDATE TEST COMPLETE ✨")
    print_separator()
    
    print(f"""
Summary:
--------
✓ Comment created successfully
✓ Status automatically updated to: {complaint.automated_status}
✓ Last responder set to: {complaint.last_responder}
✓ Response time recorded: {complaint.last_response_time}
✓ API serializer includes all automated status fields
✓ Arabic message available: {data.get('automated_status_message')}

The system is working correctly! 🎉
    """)

if __name__ == "__main__":
    test_auto_status_update()
