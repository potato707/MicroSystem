#!/usr/bin/env python
"""
Debug Client Reply Notification Issue
Check why admin isn't receiving notifications when client replies
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, User, Notification
from hr_management.notifications import NotificationService

print("="*80)
print("🔍 DEBUGGING CLIENT REPLY NOTIFICATION")
print("="*80)
print()

# Test 1: Find the complaint
complaint_id = "e8fdda46-ab31-4a20-9cc3-f8d9cdac18fd"
print(f"1️⃣  Checking complaint {complaint_id}...")
try:
    complaint = ClientComplaint.objects.get(id=complaint_id)
    print(f"✅ Found complaint: {complaint.title}")
    print(f"   Client: {complaint.client_name} ({complaint.client_email})")
    print()
except ClientComplaint.DoesNotExist:
    print("❌ Complaint not found")
    sys.exit(1)

# Test 2: Check team/employee assignments
print("2️⃣  Checking assignments...")
team_assignments = complaint.assignments.filter(is_active=True)
employee_assignments = complaint.employee_assignments.filter(is_active=True)
category_teams = complaint.category.assigned_teams.all() if complaint.category else []

print(f"   Team assignments: {team_assignments.count()}")
for assignment in team_assignments:
    print(f"      - Team: {assignment.team.name}")
    members = assignment.team.memberships.select_related('employee__user').all()
    print(f"        Members: {members.count()}")
    for member in members:
        if member.employee.user:
            print(f"          * {member.employee.user.username} ({member.employee.user.email})")

print(f"   Employee assignments: {employee_assignments.count()}")
for assignment in employee_assignments:
    if assignment.employee.user:
        print(f"      - {assignment.employee.user.username} ({assignment.employee.user.email})")

print(f"   Category teams: {category_teams.count()}")
for team in category_teams:
    print(f"      - Team: {team.name}")
    members = team.memberships.select_related('employee__user').all()
    print(f"        Members: {members.count()}")
    for member in members:
        if member.employee.user:
            print(f"          * {member.employee.user.username} ({member.employee.user.email})")

print()

# Test 3: Get admin users
print("3️⃣  Getting admin users...")
admin_users = NotificationService._get_admin_users(complaint)
print(f"   Found {len(admin_users)} admin users")
for user in admin_users:
    print(f"      - {user.username} ({user.email})")
print()

if not admin_users:
    print("⚠️  NO ADMIN USERS FOUND!")
    print("   This is why no notifications are being sent.")
    print()
    print("💡 SOLUTION:")
    print("   You need to either:")
    print("   1. Assign a team to this complaint, OR")
    print("   2. Assign employees directly to this complaint, OR")
    print("   3. Assign teams to the complaint's category")
    print()
    print("   To fix this:")
    print("   - Go to: http://localhost:3000/dashboard/client-complaints")
    print(f"   - Click on complaint: {complaint.title}")
    print("   - Look for 'Assignments' section")
    print("   - Add a team or employee assignment")
    print()
    sys.exit(0)

# Test 4: Manually trigger notification
print("4️⃣  Testing notification manually...")
try:
    result = NotificationService.notify_new_client_message(complaint)
    if result:
        print("✅ Notification function executed successfully")
    else:
        print("⚠️  Notification function returned False")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
print()

# Test 5: Check created notifications
print("5️⃣  Checking notification database...")
for user in admin_users:
    user_notifications = Notification.objects.filter(
        recipient=user,
        complaint=complaint
    ).order_by('-created_at')[:3]
    
    print(f"   Notifications for {user.username}: {user_notifications.count()}")
    for notif in user_notifications:
        status = "🔵 Unread" if not notif.is_read else "✓ Read"
        print(f"      {status} - {notif.title}")
        print(f"         Created: {notif.created_at}")
        print(f"         Message: {notif.message[:50]}...")

print()
print("="*80)
print("📊 DIAGNOSIS")
print("="*80)
print()

if not admin_users:
    print("❌ ISSUE: No admin users assigned to this complaint")
    print("   Notifications cannot be sent without recipients")
    print()
    print("   Fix: Assign teams or employees to the complaint")
else:
    print("✅ Admin users found - notifications should be created")
    print(f"   Recipients: {', '.join([u.username for u in admin_users])}")
    print()
    print("   If notifications still don't appear:")
    print("   1. Check Django console for errors")
    print("   2. Verify frontend is polling the API")
    print("   3. Check browser console for errors")

print()
print("="*80)
