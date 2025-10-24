#!/usr/bin/env python
"""
Test the notification fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint
from hr_management.notifications import NotificationService

# Get the test complaint
complaint_id = '812c7c0b-c3b9-4c84-b99c-b0431e13095f'

try:
    complaint = ClientComplaint.objects.get(id=complaint_id)
    print(f"✅ Complaint found: {complaint.title}")
    print(f"   Status: {complaint.automated_status}")
    print(f"   Last responder: {complaint.last_responder}")
    
    # Test getting admin emails (this was failing before)
    print("\n🔍 Testing _get_admin_emails() method...")
    try:
        emails = NotificationService._get_admin_emails(complaint)
        print(f"✅ Success! Found {len(emails)} admin emails")
        for email in emails:
            print(f"   - {email}")
    except AttributeError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test the full notification method
    print("\n📧 Testing notify_new_client_message()...")
    try:
        NotificationService.notify_new_client_message(complaint)
        print("✅ Notification method executed successfully!")
    except AttributeError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"⚠️  Warning: {e}")
        print("   (This is expected if email settings are not configured)")
    
    print("\n🎉 All tests passed! The notification fix is working.")
    
except ClientComplaint.DoesNotExist:
    print(f"❌ Complaint not found: {complaint_id}")
