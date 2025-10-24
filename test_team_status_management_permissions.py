#!/usr/bin/env python
"""
Test script to verify team complaint admin permissions for status management
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_project.settings')
django.setup()

from hr_management.models import (
    User, Team, TeamMembership, TeamComplaintAdminPermission,
    get_complaint_admin_permissions
)

def test_team_permissions():
    """Test that team members have correct permissions"""
    print("=" * 80)
    print("TEAM COMPLAINT ADMIN PERMISSIONS - STATUS MANAGEMENT TEST")
    print("=" * 80)
    
    # Test each team
    teams = Team.objects.filter(complaint_admin_permission__isnull=False)
    
    for team in teams:
        print(f"\n📋 Team: {team.name}")
        print("-" * 80)
        
        # Get team permission
        try:
            team_perm = TeamComplaintAdminPermission.objects.get(team=team)
            print(f"  Team Permissions:")
            print(f"    ✓ can_assign: {team_perm.can_assign}")
            print(f"    ✓ can_change_status: {team_perm.can_change_status}")
            print(f"    ✓ can_manage_categories: {team_perm.can_manage_categories}")
            print(f"    ✓ can_delete: {team_perm.can_delete}")
            print(f"    ✓ is_active: {team_perm.is_active}")
        except TeamComplaintAdminPermission.DoesNotExist:
            print("  ❌ No team permission found")
            continue
        
        # Test team members
        members = TeamMembership.objects.filter(team=team, is_active=True)
        print(f"\n  👥 Team Members ({members.count()}):")
        
        if not members.exists():
            print("    (No active members)")
            continue
        
        for membership in members:
            employee = membership.employee
            user = employee.user if hasattr(employee, 'user') else None
            
            if not user:
                print(f"    ❌ {employee.name} - No user account")
                continue
            
            # Get user's computed permissions
            user_perms = get_complaint_admin_permissions(user)
            
            print(f"\n    👤 {user.username} ({employee.name}):")
            print(f"       Role: {user.role}")
            print(f"       Permissions:")
            print(f"         • has_permission: {user_perms.get('has_permission')}")
            print(f"         • can_assign: {user_perms.get('can_assign')}")
            print(f"         • can_change_status: {user_perms.get('can_change_status')}")
            print(f"         • can_manage_categories: {user_perms.get('can_manage_categories')}")
            
            # Check if permissions are correct
            if user_perms.get('can_manage_categories'):
                print(f"       ✅ Can access Status Management section")
            else:
                print(f"       ❌ Cannot access Status Management section")
            
            if user_perms.get('can_change_status'):
                print(f"       ✅ Can change complaint status")
            else:
                print(f"       ❌ Cannot change complaint status")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    # Summary
    print("\n📊 SUMMARY:")
    total_teams = TeamComplaintAdminPermission.objects.filter(is_active=True).count()
    teams_with_manage = TeamComplaintAdminPermission.objects.filter(
        is_active=True, 
        can_manage_categories=True
    ).count()
    
    print(f"  • Total teams with complaint admin permissions: {total_teams}")
    print(f"  • Teams with status management access: {teams_with_manage}")
    
    # Count users with status management access
    users_with_access = []
    for team in teams:
        try:
            team_perm = TeamComplaintAdminPermission.objects.get(
                team=team, 
                is_active=True, 
                can_manage_categories=True
            )
            members = TeamMembership.objects.filter(team=team, is_active=True)
            for membership in members:
                if hasattr(membership.employee, 'user'):
                    users_with_access.append(membership.employee.user.username)
        except TeamComplaintAdminPermission.DoesNotExist:
            pass
    
    print(f"  • Users with status management access: {len(set(users_with_access))}")
    if users_with_access:
        print(f"    → {', '.join(sorted(set(users_with_access)))}")
    
    print("\n✅ All checks complete!")

if __name__ == '__main__':
    test_team_permissions()
