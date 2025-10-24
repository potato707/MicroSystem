#!/usr/bin/env python
"""
Quick test to see notification emails in action
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint
from hr_management.notifications import NotificationService

print("="*80)
print("📧 NOTIFICATION EMAIL TEST")
print("="*80)

# Get a test complaint
complaint_id = '812c7c0b-c3b9-4c84-b99c-b0431e13095f'

try:
    complaint = ClientComplaint.objects.get(id=complaint_id)
    print(f"\n✅ Found complaint: {complaint.title}")
    print(f"   Client: {complaint.client_name}")
    print(f"   Status: {complaint.automated_status}")
    
    # Get admin emails
    print("\n📧 Getting notification recipients...")
    emails = NotificationService._get_admin_emails(complaint)
    
    if emails:
        print(f"✅ Found {len(emails)} recipients:")
        for email in emails:
            print(f"   - {email}")
    else:
        print("⚠️  No assigned team members or employees found")
        print("   To receive notifications:")
        print("   1. Assign the complaint to a team, OR")
        print("   2. Assign employees directly, OR")  
        print("   3. Assign teams to the complaint's category")
    
    # Send test notification
    print("\n📤 Sending test notification...")
    print("   (Check your Django server console output)")
    print("-"*80)
    
    try:
        NotificationService.notify_new_client_message(complaint)
        print("\n✅ Notification sent successfully!")
        print("\n💡 The email should appear in your Django server console")
        print("   (Since you're using console email backend)")
    except Exception as e:
        print(f"\n⚠️  Notification error: {e}")
        print("   This is expected if no recipients are configured")
    
except ClientComplaint.DoesNotExist:
    print(f"\n❌ Complaint not found: {complaint_id}")

print("\n" + "="*80)
print("HOW TO CHECK NOTIFICATIONS:")
print("="*80)
print("""
1. CONSOLE OUTPUT (Current Setup):
   - Your Django server console will show email content
   - Look for lines starting with "Content-Type: text/plain"
   
2. SERVER LOGS:
   tail -f server.log | grep -i "email\\|notification"

3. ADD A COMMENT VIA API:
   The notification will trigger automatically and print to console

4. ASSIGN TEAMS/EMPLOYEES:
   - Go to http://localhost:3000/dashboard/client-complaints
   - Click on a complaint
   - Assign teams or employees
   - Then add comments to trigger notifications
""")

print("\n" + "="*80)
print("TO SEE EMAILS IN ACTION:")
print("="*80)
print("""
Run your Django server if not running:
  python manage.py runserver

Then in another terminal, add a comment:
  curl -X POST 'http://localhost:8000/hr/client-complaints/{id}/comments/' \\
    -H 'Authorization: Bearer {token}' \\
    -H 'Content-Type: application/json' \\
    --data-raw '{"comment":"Test notification","is_internal":false}'

Watch the Django console for the email output!
""")
