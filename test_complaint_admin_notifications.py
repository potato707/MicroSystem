#!/usr/bin/env python
"""
Test script to verify complaint admin permissions users receive notifications
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import EmployeeComplaintAdminPermission, TeamComplaintAdminPermission, Employee, User, Notification
from django.db.models import Q

print("\n=== Testing Complaint Admin Notifications ===\n")

# 1. Check users with complaint admin permissions
print("1. Users with individual complaint admin permissions:")
employee_permissions = EmployeeComplaintAdminPermission.objects.filter(is_active=True).select_related('employee__user')
print(f"   Found {employee_permissions.count()} active employee complaint admin permissions")
for perm in employee_permissions:
    if perm.employee.user:
        print(f"   - {perm.employee.user.username} ({perm.employee.user.role})")
        print(f"     Can assign: {perm.can_assign}, Can change status: {perm.can_change_status}")

print("\n2. Teams with complaint admin permissions:")
team_permissions = TeamComplaintAdminPermission.objects.filter(is_active=True).select_related('team')
print(f"   Found {team_permissions.count()} teams with complaint admin permissions")
for perm in team_permissions:
    print(f"   - Team: {perm.team.name}")
    team_members = perm.team.memberships.select_related('employee__user').all()
    for membership in team_members:
        if membership.employee.user:
            print(f"     * {membership.employee.user.username} ({membership.employee.user.role})")

# 2. Check admin users
print("\n3. Admin users:")
admins = User.objects.filter(role='admin')
print(f"   Found {admins.count()} admins")
for admin in admins:
    print(f"   - {admin.username}")

# 3. Check recent notifications
print("\n4. Recent notifications (last 5):")
notifications = Notification.objects.select_related('recipient').order_by('-created_at')[:5]
for notif in notifications:
    print(f"   - To: {notif.recipient.username} ({notif.recipient.role})")
    print(f"     Title: {notif.title}")
    print(f"     Type: {notif.notification_type}")
    print(f"     Read: {notif.is_read}")
    print()

# 4. Count unread notifications per user
print("\n5. Unread notification counts:")
users_with_perms = set()

# Add individual employee permissions
for perm in employee_permissions:
    if perm.employee.user:
        users_with_perms.add(perm.employee.user.id)

# Add team member permissions
for perm in team_permissions:
    team_members = perm.team.memberships.select_related('employee__user').all()
    for membership in team_members:
        if membership.employee.user:
            users_with_perms.add(membership.employee.user.id)

# Add admins
for admin in admins:
    users_with_perms.add(admin.id)

for user_id in users_with_perms:
    user = User.objects.get(id=user_id)
    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
    print(f"   {user.username} ({user.role}): {unread_count} unread")

print("\n=== Test Complete ===\n")
