#!/usr/bin/env python3
"""
Test the new team members endpoint for subtask assignment
"""

import os
import sys
import django

# Add the project root to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import User, Employee, Team, TeamMembership
from hr_management.views import TeamMembersView
from django.test import RequestFactory


def test_team_members_endpoint():
    """Test the new TeamMembersView endpoint"""
    print("🧪 Testing Team Members Endpoint")
    print("=" * 40)
    
    # Get a team with members
    team = Team.objects.filter(
        memberships__is_active=True
    ).distinct().first()
    
    if not team:
        print("❌ No teams with members found")
        return False
    
    print(f"✅ Testing with team: {team.name}")
    
    # Get admin user
    admin_user = User.objects.get(username='admin')
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get(f'/hr/teams/{team.id}/members/')
    request.user = admin_user
    
    # Test the view
    view = TeamMembersView()
    
    try:
        response = view.get(request, team.id)
        
        if response.status_code == 200:
            data = response.data
            employees = data.get('employees', [])
            
            print(f"✅ Endpoint returned {len(employees)} employees:")
            for emp in employees:
                print(f"   - {emp['name']} ({emp['position']}) - Role: {emp.get('team_role', 'N/A')}")
            
            return len(employees) > 0
        else:
            print(f"❌ Endpoint error: {response.status_code} - {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_teams():
    """Test endpoint with multiple teams"""
    print(f"\n🔄 Testing All Teams")
    print("=" * 25)
    
    admin_user = User.objects.get(username='admin')
    factory = RequestFactory()
    view = TeamMembersView()
    
    teams = Team.objects.all()
    successful_teams = 0
    
    for team in teams:
        request = factory.get(f'/hr/teams/{team.id}/members/')
        request.user = admin_user
        
        try:
            response = view.get(request, team.id)
            
            if response.status_code == 200:
                employees = response.data.get('employees', [])
                print(f"✅ {team.name}: {len(employees)} members")
                if len(employees) > 0:
                    successful_teams += 1
            else:
                print(f"❌ {team.name}: Error {response.status_code}")
                
        except Exception as e:
            print(f"❌ {team.name}: Exception - {e}")
    
    print(f"\n📊 Summary: {successful_teams}/{teams.count()} teams have members available")
    return successful_teams > 0


if __name__ == "__main__":
    print("🔧 Testing Team Members API Fix")
    print("=" * 45)
    
    test1 = test_team_members_endpoint()
    test2 = test_all_teams()
    
    print(f"\n📊 Results:")
    print(f"✅ Team members endpoint: {'PASS' if test1 else 'FAIL'}")
    print(f"✅ All teams test: {'PASS' if test2 else 'FAIL'}")
    
    if test1 and test2:
        print(f"\n🎯 SUCCESS: Team members endpoint is working! ✅")
        print("   ✓ New /teams/{team_id}/members/ endpoint added")
        print("   ✓ Frontend can now fetch team members for subtask assignment")
        print("   ✓ Assignment dropdown should no longer be empty")
        
        print(f"\n💡 Next steps:")
        print("   1. Test the frontend task creation with subtasks")
        print("   2. Select a team, then add subtasks")
        print("   3. Assignment dropdown should show team members")
    else:
        print(f"\n❌ Issues found with team members endpoint")
    
    sys.exit(0 if (test1 and test2) else 1)