#!/usr/bin/env python
"""
Test script to trigger a new client complaint message and verify all complaint admins receive notifications
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, User, Notification
from hr_management.notifications import NotificationService

print("\n=== Testing New Notification to Complaint Admins ===\n")

# Get a client complaint
complaint = ClientComplaint.objects.first()
if not complaint:
    print("❌ No client complaints found!")
    exit(1)

print(f"Using complaint: {complaint.title} (ID: {complaint.id})")
print(f"Client: {complaint.client_user.username if complaint.client_user else 'No client'}")

# Get notification count before
before_count = Notification.objects.count()
print(f"\nNotifications before: {before_count}")

# Trigger notification
print("\nTriggering new client message notification...")
NotificationService.notify_new_client_message(complaint)

# Check notifications after
after_count = Notification.objects.count()
new_notifications = Notification.objects.order_by('-created_at')[:10]

print(f"\nNotifications after: {after_count}")
print(f"New notifications created: {after_count - before_count}")

print("\nRecipients of new notifications:")
for notif in new_notifications[:after_count - before_count]:
    print(f"   - {notif.recipient.username} ({notif.recipient.role})")
    print(f"     Title: {notif.title}")

# Check specific users
print("\n=== Checking Specific Users ===")
test_users = ['potato', 'string', 'sting', 'ahmed', 'mohammed']
for username in test_users:
    try:
        user = User.objects.get(username=username)
        count = Notification.objects.filter(recipient=user, is_read=False).count()
        latest = Notification.objects.filter(recipient=user).order_by('-created_at').first()
        print(f"\n{username} ({user.role}):")
        print(f"   Unread: {count}")
        if latest:
            print(f"   Latest: {latest.title[:50]}... ({latest.created_at.strftime('%H:%M:%S')})")
    except User.DoesNotExist:
        print(f"\n{username}: User not found")

print("\n=== Test Complete ===\n")
