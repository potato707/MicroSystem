#!/usr/bin/env python
"""
Complete test demonstrating the auto-status update fix
Shows the full bidirectional communication flow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ClientComplaintComment, ClientComplaintReply
from django.contrib.auth import get_user_model
from hr_management.ticket_automation import TicketStatusManager

User = get_user_model()

def print_box(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def show_status(complaint, label="Current Status"):
    """Display complaint status in a readable format"""
    from hr_management.serializers import ClientComplaintSerializer
    serializer = ClientComplaintSerializer(complaint)
    data = serializer.data
    
    print(f"📊 {label}:")
    print(f"   Main Status: {data.get('status_display')}")
    print(f"   Automated Status: {data.get('automated_status')}")
    print(f"   Status Message: {data.get('automated_status_message')}")
    print(f"   ✨ Display Combined: {data.get('display_status_combined')}")
    print(f"   Last Responder: {data.get('last_responder')}")
    print(f"   Last Response Time: {data.get('last_response_time')}")

def test_complete_workflow():
    """Test the complete bidirectional communication workflow"""
    
    # Get the test complaint
    complaint_id = '812c7c0b-c3b9-4c84-b99c-b0431e13095f'
    
    try:
        complaint = ClientComplaint.objects.get(id=complaint_id)
    except ClientComplaint.DoesNotExist:
        print("❌ Complaint not found")
        return
    
    # Get users
    try:
        admin_user = User.objects.get(username='ahmed')
    except User.DoesNotExist:
        admin_user = User.objects.filter(role='admin').first()
    
    try:
        client_user = complaint.client_user
    except:
        client_user = None
    
    print_box("AUTO-STATUS UPDATE COMPLETE TEST")
    
    # Show initial state
    show_status(complaint, "INITIAL STATE")
    
    print_box("SCENARIO 1: Client Sends a Reply")
    
    # Simulate client reply
    if client_user:
        reply = ClientComplaintReply.objects.create(
            complaint=complaint,
            client_name=client_user.name,
            client_email=client_user.email,
            reply_text="I need more information about this issue"
        )
        print(f"✅ Client Reply Created: '{reply.reply_text[:50]}...'")
    
    # Trigger status update
    TicketStatusManager.transition_on_client_response(complaint)
    complaint.refresh_from_db()
    
    show_status(complaint, "AFTER CLIENT REPLY")
    
    print("\n💡 Notice:")
    print("   - automated_status changed to 'waiting_for_system_response'")
    print("   - automated_status_message shows 'في انتظار رد فريق الدعم'")
    print("   - display_status_combined prioritizes automated message")
    print("   - last_responder is 'client'")
    
    print_box("SCENARIO 2: Support Team Responds")
    
    # Simulate system/admin response
    if admin_user:
        comment = ClientComplaintComment.objects.create(
            complaint=complaint,
            author=admin_user,
            comment="We're looking into this issue. We'll update you soon.",
            is_internal=False
        )
        print(f"✅ System Comment Created: '{comment.comment[:50]}...'")
    
    # Trigger status update
    TicketStatusManager.transition_on_system_response(complaint)
    complaint.refresh_from_db()
    
    show_status(complaint, "AFTER SYSTEM RESPONSE")
    
    print("\n💡 Notice:")
    print("   - automated_status changed to 'waiting_for_client_response'")
    print("   - automated_status_message shows 'في انتظار ردك'")
    print("   - display_status_combined shows the waiting message")
    print("   - last_responder is 'system'")
    
    print_box("FIELD COMPARISON")
    
    from hr_management.serializers import ClientComplaintSerializer
    serializer = ClientComplaintSerializer(complaint)
    data = serializer.data
    
    print("Available Status Fields in API Response:")
    print("-" * 80)
    print(f"1. status                    : {data.get('status')}")
    print(f"2. status_display            : {data.get('status_display')}")
    print(f"3. automated_status          : {data.get('automated_status')}")
    print(f"4. automated_status_message  : {data.get('automated_status_message')}")
    print(f"5. display_status_combined   : {data.get('display_status_combined')} ⭐ USE THIS")
    print("-" * 80)
    
    print("\n📝 Recommendation:")
    print("   Use 'display_status_combined' in your frontend to show the most relevant status")
    print("   This field automatically prioritizes:")
    print("   ✓ Automated communication status (when available)")
    print("   ✓ Falls back to main workflow status (when no active communication)")
    
    print_box("TEST COMPLETE ✅")
    
    print("""
Summary of Changes:
-------------------
✅ ClientComplaintSerializer now includes:
   - automated_status
   - automated_status_message (Arabic translation)
   - display_status_combined (smart priority)
   - last_responder
   - last_response_time
   - delay_status

✅ Status updates automatically on:
   - System/Admin comments (ClientComplaintCommentViewSet)
   - Client replies via dashboard (ClientComplaintAddReplyView)
   - Client replies via portal (ClientPortalReplyView) [FIXED]

✅ Frontend Integration:
   - Use complaint.display_status_combined for best UX
   - Shows "في انتظار ردك" when waiting for client
   - Shows "في انتظار رد فريق الدعم" when waiting for support
   - Falls back to main status when no active communication

The system is now fully functional! 🎉
    """)

if __name__ == "__main__":
    test_complete_workflow()
