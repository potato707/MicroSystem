#!/usr/bin/env python
"""
Test Notification API for Admin User
Simulates checking unread count and listing notifications
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Notification
from hr_management.serializers import NotificationSerializer

print("="*80)
print("📱 TESTING NOTIFICATION API FOR ADMIN")
print("="*80)
print()

# Find an admin user
print("1️⃣  Finding admin user...")
admin_user = User.objects.filter(role='admin').first()
if not admin_user:
    print("❌ No admin users found")
    sys.exit(1)

print(f"✅ Testing with user: {admin_user.username} ({admin_user.email})")
print()

# Test 2: Get unread count
print("2️⃣  Testing GET /hr/notifications/unread_count/")
unread_count = Notification.objects.filter(recipient=admin_user, is_read=False).count()
print(f"✅ Response: {{'unread_count': {unread_count}}}")
print()

# Test 3: Get all notifications
print("3️⃣  Testing GET /hr/notifications/")
all_notifications = Notification.objects.filter(recipient=admin_user).order_by('-created_at')[:10]
print(f"✅ Found {all_notifications.count()} notifications")
print()

if all_notifications:
    print("   Latest notifications:")
    serializer = NotificationSerializer(all_notifications, many=True)
    for notif_data in serializer.data:
        status_icon = "🔵" if not notif_data['is_read'] else "✓"
        print(f"   {status_icon} {notif_data['title']}")
        print(f"      Message: {notif_data['message']}")
        print(f"      Time: {notif_data['time_ago']}")
        print(f"      Complaint: {notif_data.get('complaint_title', 'N/A')}")
        print()

# Test 4: Get only unread
print("4️⃣  Testing GET /hr/notifications/unread/")
unread_notifications = Notification.objects.filter(recipient=admin_user, is_read=False).order_by('-created_at')
print(f"✅ Found {unread_notifications.count()} unread notifications")
if unread_notifications:
    for notif in unread_notifications:
        print(f"   🔵 {notif.title}")
        print(f"      Created: {notif.created_at}")
print()

# Test 5: Frontend polling simulation
print("5️⃣  Simulating frontend polling...")
print("   Frontend should poll every 30 seconds:")
print(f"   GET /hr/notifications/unread_count/ → {{'unread_count': {unread_count}}}")
print()
if unread_count > 0:
    print(f"   ✅ Red badge should show: {unread_count}")
    print("   ✅ User can click bell to see dropdown")
else:
    print("   ℹ️  No unread notifications - bell shows no badge")
print()

print("="*80)
print("📊 SUMMARY")
print("="*80)
print()
print(f"User: {admin_user.username}")
print(f"Total notifications: {all_notifications.count()}")
print(f"Unread notifications: {unread_count}")
print()
if unread_count > 0:
    print("✅ Admin should see notification bell with badge!")
    print()
    print("To test in frontend:")
    print("1. Login as admin: http://localhost:3000/login")
    print(f"   Username: {admin_user.username}")
    print("2. Look for 🔔 bell icon in top right")
    print(f"3. Badge should show: {unread_count}")
    print("4. Click bell to see dropdown with notifications")
else:
    print("ℹ️  No unread notifications")
    print("   Add a client reply to create new notification:")
    print("   - Login as client")
    print("   - Add a reply to a complaint")
    print("   - Admin will receive notification")

print()
print("="*80)
