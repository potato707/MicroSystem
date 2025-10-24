#!/usr/bin/env python
"""
Test notification targeting - verify complaint admins only get notified for assigned complaints
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, User, Notification, Team, ClientComplaintAssignment, Employee
from hr_management.notifications import NotificationService

print("\n=== Testing Targeted Notifications ===\n")

# Get user 'string' (has complaint admin permissions)
try:
    string_user = User.objects.get(username='string')
    string_employee = string_user.employee
    print(f"Found user: {string_user.username} (Employee: {string_employee.name})")
except:
    print("User 'string' not found!")
    exit(1)

# Get a complaint
complaint = ClientComplaint.objects.first()
if not complaint:
    print("No complaints found!")
    exit(1)

print(f"\nUsing complaint: {complaint.title} (ID: {complaint.id})")

# Clear existing assignments
complaint.assignments.all().delete()
complaint.employee_assignments.all().delete()
print("Cleared existing assignments")

# Scenario 1: Unassigned complaint
print("\n--- Scenario 1: Unassigned Complaint ---")
before_count = Notification.objects.filter(recipient=string_user).count()
print(f"String's notifications before: {before_count}")

NotificationService.notify_new_client_message(complaint)

after_count = Notification.objects.filter(recipient=string_user).count()
print(f"String's notifications after: {after_count}")
print(f"✅ String received notification: {after_count > before_count}" if after_count > before_count else "❌ String did NOT receive notification (CORRECT - not assigned)")

# Get latest notifications
latest_notifs = Notification.objects.order_by('-created_at')[:5]
print("\nRecent notification recipients:")
for notif in latest_notifs:
    print(f"  - {notif.recipient.username} ({notif.recipient.role})")

# Scenario 2: Assign string's team to the complaint
print("\n--- Scenario 2: Assign String's Team ---")

# Find a team that string is member of
string_teams = Team.objects.filter(memberships__employee=string_employee).first()
if string_teams:
    print(f"Assigning team: {string_teams.name}")
    ClientComplaintAssignment.objects.create(
        complaint=complaint,
        team=string_teams,
        assigned_by=User.objects.filter(role='admin').first(),
        is_active=True
    )
    
    before_count2 = Notification.objects.filter(recipient=string_user).count()
    NotificationService.notify_new_client_message(complaint)
    after_count2 = Notification.objects.filter(recipient=string_user).count()
    
    print(f"String's notifications before: {before_count2}")
    print(f"String's notifications after: {after_count2}")
    print(f"✅ String received notification: YES (CORRECT - assigned via team)" if after_count2 > before_count2 else "❌ String did NOT receive notification (WRONG)")
else:
    print("String is not in any team, skipping scenario 2")

print("\n=== Test Complete ===\n")
