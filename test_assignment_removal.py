#!/usr/bin/env python3
"""
Test script for assignment removal functionality
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

def test_assignment_removal():
    """Test removing assignments from a complaint"""
    # Use the complaint we know has assignments
    complaint_id = "ce89d8e1-3695-4d5e-ac45-d4472ed230cc"
    
    print("🧪 Testing Assignment Removal Functionality")
    print("=" * 50)
    
    # 1. Get current assignments
    print(f"\n1. 📋 Getting current assignments for complaint {complaint_id}...")
    response = requests.get(f"{BASE_URL}/hr/client-complaints/{complaint_id}/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get complaint: {response.status_code}")
        return False
        
    complaint = response.json()
    print(f"✅ Complaint: {complaint['title']}")
    
    # Check current team assignments
    team_assignments = complaint.get('assignments', [])
    active_team_assignments = [a for a in team_assignments if a['is_active']]
    print(f"🏢 Active Team Assignments: {len(active_team_assignments)}")
    for i, assignment in enumerate(active_team_assignments, 1):
        print(f"   {i}. {assignment['team_name']} (ID: {assignment['id']})")
    
    # Check current employee assignments
    employee_assignments = complaint.get('employee_assignments', [])
    active_employee_assignments = [a for a in employee_assignments if a['is_active']]
    print(f"👤 Active Employee Assignments: {len(active_employee_assignments)}")
    for i, assignment in enumerate(active_employee_assignments, 1):
        print(f"   {i}. {assignment['employee_name']} (ID: {assignment['id']})")
    
    if not active_team_assignments and not active_employee_assignments:
        print("⚠️ No active assignments found to remove")
        return True
    
    # 2. Test removing a team assignment if available
    if active_team_assignments:
        assignment_to_remove = active_team_assignments[0]
        print(f"\n2. 🗑️ Testing team assignment removal...")
        print(f"   Removing: {assignment_to_remove['team_name']} (ID: {assignment_to_remove['id']})")
        
        remove_response = requests.delete(
            f"{BASE_URL}/hr/client-complaints/{complaint_id}/remove-team/{assignment_to_remove['id']}/",
            headers=headers
        )
        
        if remove_response.status_code == 200:
            result = remove_response.json()
            print(f"✅ Team assignment removed successfully!")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Failed to remove team assignment: {remove_response.status_code}")
            print(f"   Response: {remove_response.text[:300]}")
    
    # 3. Test removing an employee assignment if available
    if active_employee_assignments:
        assignment_to_remove = active_employee_assignments[0]
        print(f"\n3. 🗑️ Testing employee assignment removal...")
        print(f"   Removing: {assignment_to_remove['employee_name']} (ID: {assignment_to_remove['id']})")
        
        remove_response = requests.delete(
            f"{BASE_URL}/hr/client-complaints/{complaint_id}/remove-employee/{assignment_to_remove['id']}/",
            headers=headers
        )
        
        if remove_response.status_code == 200:
            result = remove_response.json()
            print(f"✅ Employee assignment removed successfully!")
            print(f"   Message: {result['message']}")
        else:
            print(f"❌ Failed to remove employee assignment: {remove_response.status_code}")
            print(f"   Response: {remove_response.text[:300]}")
    
    # 4. Verify assignments were removed
    print(f"\n4. 🔍 Verifying assignments after removal...")
    verify_response = requests.get(f"{BASE_URL}/hr/client-complaints/{complaint_id}/", headers=headers)
    
    if verify_response.status_code == 200:
        updated_complaint = verify_response.json()
        
        # Check updated team assignments
        updated_team_assignments = updated_complaint.get('assignments', [])
        updated_active_team_assignments = [a for a in updated_team_assignments if a['is_active']]
        print(f"🏢 Active Team Assignments After Removal: {len(updated_active_team_assignments)}")
        for i, assignment in enumerate(updated_active_team_assignments, 1):
            print(f"   {i}. {assignment['team_name']} (ID: {assignment['id']})")
        
        # Check updated employee assignments
        updated_employee_assignments = updated_complaint.get('employee_assignments', [])
        updated_active_employee_assignments = [a for a in updated_employee_assignments if a['is_active']]
        print(f"👤 Active Employee Assignments After Removal: {len(updated_active_employee_assignments)}")
        for i, assignment in enumerate(updated_active_employee_assignments, 1):
            print(f"   {i}. {assignment['employee_name']} (ID: {assignment['id']})")
        
        # Show inactive assignments too
        inactive_team_assignments = [a for a in updated_team_assignments if not a['is_active']]
        inactive_employee_assignments = [a for a in updated_employee_assignments if not a['is_active']]
        
        if inactive_team_assignments or inactive_employee_assignments:
            print(f"\n📜 Inactive Assignments (Removed):")
            if inactive_team_assignments:
                print(f"🏢 Inactive Teams: {len(inactive_team_assignments)}")
                for i, assignment in enumerate(inactive_team_assignments, 1):
                    print(f"   {i}. {assignment['team_name']} (Inactive)")
            
            if inactive_employee_assignments:
                print(f"👤 Inactive Employees: {len(inactive_employee_assignments)}")
                for i, assignment in enumerate(inactive_employee_assignments, 1):
                    print(f"   {i}. {assignment['employee_name']} (Inactive)")
        
        print(f"\n🎉 Assignment removal test completed!")
        print(f"\n💡 UI Usage:")
        print(f"   1. Open complaint detail modal")
        print(f"   2. Look for 'Team Assignments' and 'Individual Employee Assignments' cards")
        print(f"   3. Click 'Remove' button next to active assignments")
        print(f"   4. Confirm removal in dialog")
        print(f"   5. Assignment will be marked as inactive (not deleted)")
        
        return True
    else:
        print(f"❌ Failed to verify assignments: {verify_response.status_code}")
        return False

if __name__ == "__main__":
    test_assignment_removal()