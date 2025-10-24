#!/usr/bin/env python3
"""
Simple database-level test to verify team members can be fetched for subtask assignment
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


def test_team_members_data():
    """Check if we have proper team membership data for testing"""
    print("🔍 Checking Team Membership Data")
    print("=" * 40)
    
    # Get teams
    teams = Team.objects.all()
    print(f"✅ Found {teams.count()} teams:")
    
    for team in teams:
        memberships = TeamMembership.objects.filter(team=team, is_active=True)
        print(f"\n📋 Team: {team.name}")
        print(f"   Members: {memberships.count()}")
        
        for membership in memberships:
            print(f"   - {membership.employee.name} ({membership.employee.position})")
        
        if memberships.count() == 0:
            print("   ⚠️  No active members found")
    
    # Check if we have enough data for testing
    total_memberships = TeamMembership.objects.filter(is_active=True).count()
    if total_memberships == 0:
        print(f"\n❌ No team memberships found! This would cause empty assignment dropdowns.")
        return False
    
    print(f"\n✅ Total active team memberships: {total_memberships}")
    return True


def test_assignable_employees_logic():
    """Test the AssignableEmployeesView logic directly"""
    print(f"\n🧪 Testing Assignable Employees Logic")
    print("=" * 45)
    
    from hr_management.views import AssignableEmployeesView
    from django.test import RequestFactory
    
    # Get a team with members
    team = Team.objects.filter(
        memberships__is_active=True
    ).distinct().first()
    
    if not team:
        print("❌ No teams with active members found")
        return False
    
    print(f"✅ Testing with team: {team.name}")
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get(f'/api/teams/{team.id}/assignable-employees/')
    
    # Get admin user for request context
    admin_user = User.objects.get(username='admin')
    request.user = admin_user
    
    # Create view instance and test
    view = AssignableEmployeesView()
    view.request = request
    
    try:
        # Get queryset (this is what populates the dropdown)
        queryset = view.get_queryset()
        employees = list(queryset)
        
        print(f"✅ View returned {len(employees)} assignable employees:")
        for emp in employees:
            print(f"   - {emp.name} (ID: {emp.id})")
        
        if len(employees) == 0:
            print("❌ No employees returned - this would cause empty dropdown!")
            return False
        
        # Test serialization
        from hr_management.serializers import EmployeeSerializer
        serialized_data = EmployeeSerializer(employees, many=True).data
        
        print(f"✅ Serialization successful - {len(serialized_data)} employees serialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in view logic: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_frontend_integration():
    """Check what the frontend would receive"""
    print(f"\n📱 Frontend Integration Check")
    print("=" * 35)
    
    # Simulate what would happen in the frontend
    team = Team.objects.first()
    if not team:
        print("❌ No teams available")
        return False
    
    # Get team members (what fetchTeamMembers would return)
    memberships = TeamMembership.objects.filter(team=team, is_active=True)
    employees = [membership.employee for membership in memberships]
    
    print(f"✅ Team: {team.name}")
    print(f"✅ Team members available: {len(employees)}")
    
    if len(employees) == 0:
        print("❌ No team members - subtask assignment dropdown would be empty!")
        print("   Frontend fallback: Will use all employees instead")
        
        # Test fallback to all employees
        all_employees = Employee.objects.all()
        print(f"   Fallback employees available: {all_employees.count()}")
        return all_employees.count() > 0
    else:
        for emp in employees:
            print(f"   - {emp.name}")
        return True


if __name__ == "__main__":
    print("🔧 Debugging Subtask Assignment Dropdown Issue")
    print("=" * 55)
    
    test1 = test_team_members_data()
    test2 = test_assignable_employees_logic()
    test3 = check_frontend_integration()
    
    print(f"\n📊 Diagnosis Results:")
    print("=" * 25)
    print(f"✅ Team membership data: {'OK' if test1 else 'MISSING'}")
    print(f"✅ API view logic: {'OK' if test2 else 'BROKEN'}")
    print(f"✅ Frontend integration: {'OK' if test3 else 'BROKEN'}")
    
    if test1 and test2 and test3:
        print(f"\n🎯 DIAGNOSIS: All systems working correctly! ✅")
        print("   ✓ Team membership data is available")
        print("   ✓ API view returns team members correctly")
        print("   ✓ Frontend should receive assignment options")
        print(f"\n💡 The frontend fallback logic should now ensure assignment dropdown")
        print("   is never empty - either team members or all employees will show.")
    else:
        print(f"\n❌ DIAGNOSIS: Issues found in assignment system")
        
        if not test1:
            print("   ❌ Missing team membership data")
        if not test2:
            print("   ❌ API view logic issues")
        if not test3:
            print("   ❌ Frontend integration problems")
    
    sys.exit(0 if (test1 and test2 and test3) else 1)