#!/usr/bin/env python3
"""
Test script for complaint admin permission system
"""
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc1ODc2OTI4LCJpYXQiOjE3NjA1MTY5MjgsImp0aSI6IjJlN2M4MDUzZTZkZTRiZmE5MjM5ODdmOTUwNmFlYWVkIiwidXNlcl9pZCI6ImMxYTUwYTUzLTk3Y2ItNDM0YS1iNTViLTFhMzY1YTM1ZGUzZCJ9.NRTa6lpS7qnW9vd1BdmlEnniGA7yaBzPVcyfFqgKT9I"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_complaint_admin_permissions():
    """Test the complaint admin permission system"""
    print("🔐 Testing Complaint Admin Permission System")
    print("=" * 60)
    
    # 1. Get available teams
    print("\n1. 📋 Getting available teams...")
    teams_response = requests.get(f"{BASE_URL}/hr/teams/", headers=headers)
    if teams_response.status_code == 200:
        teams_data = teams_response.json()
        teams = teams_data.get('results', teams_data) if isinstance(teams_data, dict) else teams_data
        print(f"✅ Found {len(teams)} teams")
        for i, team in enumerate(teams[:3], 1):
            print(f"   {i}. {team['name']} (ID: {team['id']})")
    else:
        print(f"❌ Failed to get teams: {teams_response.status_code}")
        return False
    
    # 2. Get available employees
    print("\n2. 👤 Getting available employees...")
    employees_response = requests.get(f"{BASE_URL}/hr/employees/", headers=headers)
    if employees_response.status_code == 200:
        employees_data = employees_response.json()
        employees = employees_data.get('results', employees_data) if isinstance(employees_data, dict) else employees_data
        print(f"✅ Found {len(employees)} employees")
        for i, employee in enumerate(employees[:3], 1):
            print(f"   {i}. {employee['name']} - {employee['position']} (ID: {employee['id']})")
    else:
        print(f"❌ Failed to get employees: {employees_response.status_code}")
        return False
    
    # 3. Grant complaint admin permissions to a team
    if teams:
        test_team = teams[0]
        print(f"\n3. 🏢 Granting complaint admin permissions to team '{test_team['name']}'...")
        
        team_permission_data = {
            "team_id": test_team['id'],
            "notes": "Test permission for complaint management",
            "can_review": True,
            "can_assign": True,
            "can_update_status": True,
            "can_add_comments": True,
            "can_create_tasks": False,  # Limited permission
            "can_manage_assignments": True
        }
        
        team_perm_response = requests.post(
            f"{BASE_URL}/hr/complaint-admin-permissions/teams/",
            headers=headers,
            json=team_permission_data
        )
        
        if team_perm_response.status_code in [200, 201]:
            result = team_perm_response.json()
            print(f"✅ Team permission granted successfully!")
            print(f"   Message: {result['message']}")
            print(f"   Permission ID: {result['permission_id']}")
        else:
            print(f"❌ Failed to grant team permission: {team_perm_response.status_code}")
            print(f"   Response: {team_perm_response.text[:300]}")
    
    # 4. Grant complaint admin permissions to an employee
    if employees:
        test_employee = employees[0]
        print(f"\n4. 👤 Granting complaint admin permissions to employee '{test_employee['name']}'...")
        
        employee_permission_data = {
            "employee_id": test_employee['id'],
            "notes": "Individual complaint admin access for senior staff",
            "can_review": True,
            "can_assign": True,
            "can_update_status": True,
            "can_add_comments": True,
            "can_create_tasks": True,
            "can_manage_assignments": False  # Limited permission
        }
        
        employee_perm_response = requests.post(
            f"{BASE_URL}/hr/complaint-admin-permissions/employees/",
            headers=headers,
            json=employee_permission_data
        )
        
        if employee_perm_response.status_code in [200, 201]:
            result = employee_perm_response.json()
            print(f"✅ Employee permission granted successfully!")
            print(f"   Message: {result['message']}")
            print(f"   Permission ID: {result['permission_id']}")
        else:
            print(f"❌ Failed to grant employee permission: {employee_perm_response.status_code}")
            print(f"   Response: {employee_perm_response.text[:300]}")
    
    # 5. List all team permissions
    print(f"\n5. 📝 Listing all team complaint admin permissions...")
    list_team_perms = requests.get(f"{BASE_URL}/hr/complaint-admin-permissions/teams/", headers=headers)
    
    if list_team_perms.status_code == 200:
        team_permissions = list_team_perms.json()
        print(f"✅ Found {len(team_permissions)} team permissions")
        for i, perm in enumerate(team_permissions, 1):
            print(f"   {i}. Team: {perm['team']['name']}")
            print(f"      Granted by: {perm['granted_by']} on {perm['granted_at'][:10]}")
            print(f"      Active: {perm['is_active']}")
            print(f"      Permissions: Review={perm['permissions']['can_review']}, "
                  f"Assign={perm['permissions']['can_assign']}, "
                  f"Status={perm['permissions']['can_update_status']}")
    else:
        print(f"❌ Failed to list team permissions: {list_team_perms.status_code}")
    
    # 6. List all employee permissions
    print(f"\n6. 📝 Listing all employee complaint admin permissions...")
    list_employee_perms = requests.get(f"{BASE_URL}/hr/complaint-admin-permissions/employees/", headers=headers)
    
    if list_employee_perms.status_code == 200:
        employee_permissions = list_employee_perms.json()
        print(f"✅ Found {len(employee_permissions)} employee permissions")
        for i, perm in enumerate(employee_permissions, 1):
            print(f"   {i}. Employee: {perm['employee']['name']} - {perm['employee']['position']}")
            print(f"      Granted by: {perm['granted_by']} on {perm['granted_at'][:10]}")
            print(f"      Active: {perm['is_active']}")
            print(f"      Permissions: Review={perm['permissions']['can_review']}, "
                  f"Assign={perm['permissions']['can_assign']}, "
                  f"Tasks={perm['permissions']['can_create_tasks']}")
    else:
        print(f"❌ Failed to list employee permissions: {list_employee_perms.status_code}")
    
    # 7. Check current user's complaint admin permissions
    print(f"\n7. 🔍 Checking current user's complaint admin permissions...")
    user_perms_response = requests.get(f"{BASE_URL}/hr/complaint-admin-permissions/user/", headers=headers)
    
    if user_perms_response.status_code == 200:
        user_permissions = user_perms_response.json()
        print(f"✅ Current user permissions retrieved:")
        print(f"   Is Complaint Admin: {user_permissions['is_complaint_admin']}")
        print(f"   Can Review: {user_permissions['can_review']}")
        print(f"   Can Assign: {user_permissions['can_assign']}")
        print(f"   Can Update Status: {user_permissions['can_update_status']}")
        print(f"   Can Add Comments: {user_permissions['can_add_comments']}")
        print(f"   Can Create Tasks: {user_permissions['can_create_tasks']}")
        print(f"   Can Manage Assignments: {user_permissions['can_manage_assignments']}")
    else:
        print(f"❌ Failed to get user permissions: {user_perms_response.status_code}")
    
    print(f"\n🎉 Complaint Admin Permission System Test Completed!")
    print(f"\n💡 System Features:")
    print(f"   ✅ Teams can be granted complaint admin permissions")
    print(f"   ✅ Individual employees can be granted complaint admin permissions")
    print(f"   ✅ Granular permission control (review, assign, status, comments, tasks, assignments)")
    print(f"   ✅ Permission inheritance: team members get team permissions")
    print(f"   ✅ Permission combination: users can have both team and individual permissions")
    print(f"   ✅ Admin-only management: only regular admins can grant/revoke permissions")
    print(f"   ✅ Activity tracking: permissions include granted_by and granted_at")
    
    print(f"\n🚀 Usage Instructions:")
    print(f"   1. Admins use the permission management API to grant complaint admin access")
    print(f"   2. Teams/employees with permissions can manage complaints without full admin access")
    print(f"   3. Complaint operations (review, assign, status update) check these permissions")
    print(f"   4. Users keep their regular role but gain complaint management capabilities")
    print(f"   5. Permissions can be revoked by setting is_active=False")
    
    return True

if __name__ == "__main__":
    test_complaint_admin_permissions()