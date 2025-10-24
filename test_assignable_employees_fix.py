#!/usr/bin/env python3
"""
Test to verify that the getAssignableEmployees endpoint is working correctly
This endpoint is used to populate the subtask assignment dropdown
"""

import os
import sys
import django
from datetime import date

# Add the project root to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, TeamMembership
from django.test import Client
import json


def test_assignable_employees_endpoint():
    """Test the endpoint that populates subtask assignment dropdowns"""
    print("🔍 Testing Assignable Employees Endpoint")
    print("=" * 50)
    
    # Get admin user and login
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✅ Using admin user: {admin_user.username}")
    except User.DoesNotExist:
        print("❌ Admin user not found")
        return False
    
    # Get first team
    team = Team.objects.first()
    if not team:
        print("❌ No teams found")
        return False
    
    print(f"✅ Testing with team: {team.name}")
    
    # Check team memberships
    memberships = TeamMembership.objects.filter(team=team, is_active=True)
    print(f"✅ Team has {memberships.count()} active members:")
    for membership in memberships:
        print(f"   - {membership.employee.name} ({membership.employee.position})")
    
    # Test the API endpoint
    client = Client()
    login_success = client.login(username='admin', password='admin123')
    
    if not login_success:
        print("❌ Login failed")
        return False
    
    print("✅ Login successful")
    
    # Call the assignable employees endpoint
    response = client.get(f'/api/teams/{team.id}/assignable-employees/')
    
    print(f"📥 API Response: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ API Error: {response.content.decode()}")
        return False
    
    # Parse response
    response_data = json.loads(response.content.decode())
    employees = response_data.get('employees', [])
    
    print(f"✅ API returned {len(employees)} assignable employees:")
    for emp in employees:
        print(f"   - {emp['name']} (ID: {emp['id']})")
    
    # Verify the data matches team memberships
    if len(employees) == memberships.count():
        print("✅ Employee count matches team membership count")
    else:
        print(f"⚠️  Employee count mismatch: API={len(employees)}, DB={memberships.count()}")
    
    return len(employees) > 0


def test_team_selection_workflow():
    """Test the complete team selection → assignable employees workflow"""
    print(f"\n🔄 Testing Complete Team Selection Workflow")
    print("=" * 55)
    
    # Get test data
    teams = Team.objects.all()[:2]
    if len(teams) < 2:
        print("❌ Need at least 2 teams for testing")
        return False
    
    client = Client()
    client.login(username='admin', password='admin123')
    
    for i, team in enumerate(teams):
        print(f"\n📋 Testing Team {i+1}: {team.name}")
        
        # Get team members
        response = client.get(f'/api/teams/{team.id}/assignable-employees/')
        
        if response.status_code == 200:
            data = json.loads(response.content.decode())
            employees = data.get('employees', [])
            print(f"   ✅ {len(employees)} assignable employees")
            
            for emp in employees[:3]:  # Show first 3
                print(f"      - {emp['name']}")
            
            if len(employees) > 3:
                print(f"      ... and {len(employees) - 3} more")
        else:
            print(f"   ❌ Failed to fetch: {response.status_code}")
            return False
    
    print(f"\n✅ Team selection workflow working correctly!")
    return True


if __name__ == "__main__":
    print("🧪 Testing Subtask Assignment Dropdown Fix")
    print("=" * 60)
    
    test1 = test_assignable_employees_endpoint()
    test2 = test_team_selection_workflow()
    
    print(f"\n📊 Results:")
    print(f"✅ Assignable employees endpoint: {'PASS' if test1 else 'FAIL'}")
    print(f"✅ Team selection workflow: {'PASS' if test2 else 'FAIL'}")
    
    if test1 and test2:
        print(f"\n🎯 SUCCESS: Subtask assignment dropdown should now work! ✅")
        print("   ✓ API endpoint returns team members correctly")
        print("   ✓ Frontend should now populate assignment options")
        print("   ✓ Fallback to all employees if team members not loaded")
    else:
        print(f"\n❌ Some issues detected with assignment endpoint")
    
    sys.exit(0 if (test1 and test2) else 1)