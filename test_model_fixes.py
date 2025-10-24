#!/usr/bin/env python
"""
Test script to verify the Django model relationship fixes are working.
This tests the model queries directly without HTTP host issues.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')

# Add testserver to ALLOWED_HOSTS temporarily for testing
if hasattr(settings, 'ALLOWED_HOSTS'):
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')
else:
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1', '[::1]']

django.setup()

from hr_management.models import Team, TeamMembership, User, ClientComplaint

def test_model_relationships():
    """Test that our model relationship fixes work correctly"""
    print("🔧 Testing Model Relationship Fixes")
    print("=" * 50)
    
    try:
        # Test 1: Basic model access
        print("📊 Testing basic model access...")
        users = User.objects.all()
        teams = Team.objects.all()
        complaints = ClientComplaint.objects.all()
        
        print(f"   Users in database: {users.count()}")
        print(f"   Teams in database: {teams.count()}")
        print(f"   Complaints in database: {complaints.count()}")
        
        # Test 2: Test the fixed query pattern
        print("\n🔍 Testing fixed Team.objects.filter(memberships__employee__user=user) pattern...")
        if users.exists():
            test_user = users.first()
            print(f"   Testing with user: {test_user.username}")
            
            try:
                # This should work with our fix
                user_teams = Team.objects.filter(memberships__employee__user=test_user)
                print(f"   ✅ Query successful - User is in {user_teams.count()} teams")
                
                # Test the old broken pattern to confirm it would fail
                try:
                    broken_teams = Team.objects.filter(members__user=test_user)
                    print(f"   ❌ Old broken pattern still works - this shouldn't happen!")
                except Exception as e:
                    print(f"   ✅ Old broken pattern properly fails: {str(e)[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Fixed pattern failed: {str(e)}")
        else:
            print("   ⚠️  No users found to test with")
        
        # Test 3: Test TeamMembership relationships
        print("\n👥 Testing TeamMembership relationships...")
        memberships = TeamMembership.objects.all()
        print(f"   TeamMemberships in database: {memberships.count()}")
        
        if memberships.exists():
            membership = memberships.first()
            print(f"   Sample membership: Team '{membership.team.name}' - Employee '{membership.employee.name}'")
        
        # Test 4: Test complaint assignments
        print("\n📋 Testing complaint assignments...")
        if complaints.exists():
            complaint = complaints.first()
            assignments = complaint.assignments.all()
            print(f"   Sample complaint has {assignments.count()} team assignments")
        
        print("\n" + "=" * 50)
        print("✅ Model Relationship Testing Complete!")
        print("The fixed queries using 'memberships__employee' should work correctly.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_model_relationships()