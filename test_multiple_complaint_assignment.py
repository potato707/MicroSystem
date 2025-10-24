#!/usr/bin/env python3
"""
Test script for multiple complaint assignment functionality
"""
import requests
import json
import sys

# Test configuration
BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc1ODc2OTI4LCJpYXQiOjE3NjA1MTY5MjgsImp0aSI6IjJlN2M4MDUzZTZkZTRiZmE5MjM5ODdmOTUwNmFlYWVkIiwidXNlcl9pZCI6ImMxYTUwYTUzLTk3Y2ItNDM0YS1iNTViLTFhMzY1YTM1ZGUzZCJ9.NRTa6lpS7qnW9vd1BdmlEnniGA7yaBzPVcyfFqgKT9I"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_complaints():
    """Test getting complaints to find one for testing"""
    print("🔍 Getting complaints...")
    response = requests.get(f"{BASE_URL}/hr/client-complaints/", headers=headers)
    
    if response.status_code == 200:
        complaints = response.json()
        results = complaints.get('results', [])
        if results:
            print(f"✅ Found {len(results)} complaints")
            # Return first approved/in_progress complaint for testing
            for complaint in results:
                if complaint['status'] in ['approved', 'in_progress']:
                    print(f"📋 Using complaint: {complaint['title']} (ID: {complaint['id']})")
                    return complaint['id']
            print("⚠️ No approved/in_progress complaints found")
            return results[0]['id'] if results else None
        else:
            print("❌ No complaints found")
            return None
    else:
        print(f"❌ Failed to get complaints: {response.status_code}")
        print(response.text)
        return None

def test_get_teams_and_employees():
    """Get teams and employees for assignment testing"""
    print("👥 Getting teams and employees...")
    
    # Get teams
    teams_response = requests.get(f"{BASE_URL}/hr/teams/", headers=headers)
    employees_response = requests.get(f"{BASE_URL}/hr/employees/", headers=headers)
    
    teams = []
    employees = []
    
    if teams_response.status_code == 200:
        teams_data = teams_response.json()
        teams = teams_data.get('results', [])[:2]  # Take first 2 teams
        print(f"✅ Found {len(teams)} teams for testing")
    
    if employees_response.status_code == 200:
        employees_data = employees_response.json()
        employees = employees_data.get('results', [])[:2]  # Take first 2 employees
        print(f"✅ Found {len(employees)} employees for testing")
    
    return teams, employees

def test_multiple_assignment(complaint_id, teams, employees):
    """Test multiple assignment functionality"""
    print(f"\n🎯 Testing multiple assignment for complaint {complaint_id}...")
    
    # Prepare assignment data
    assignment_data = {
        "team_ids": [team['id'] for team in teams],
        "employee_ids": [employee['id'] for employee in employees],
        "notes": "Test assignment via multiple assignment API"
    }
    
    print(f"📤 Assigning to {len(teams)} teams and {len(employees)} employees")
    
    response = requests.post(
        f"{BASE_URL}/hr/client-complaints/{complaint_id}/assign-multiple/",
        headers=headers,
        data=json.dumps(assignment_data)
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Multiple assignment successful!")
        print(f"   - Created assignments: {result['success_count']}")
        print(f"   - Errors: {len(result['errors'])}")
        if result['errors']:
            for error in result['errors']:
                print(f"     ⚠️ {error}")
        
        # Print assignment details
        for assignment in result['created_assignments']:
            print(f"   - {assignment['type'].title()}: {assignment['name']}")
        
        return True
    else:
        print(f"❌ Multiple assignment failed: {response.status_code}")
        print(response.text)
        return False

def test_single_employee_assignment(complaint_id, employees):
    """Test single employee assignment"""
    if not employees:
        print("⚠️ No employees available for single assignment test")
        return True
    
    print(f"\n👤 Testing single employee assignment...")
    
    employee = employees[0]
    assignment_data = {
        "employee_id": employee['id'],
        "notes": "Test assignment via single employee API"
    }
    
    response = requests.post(
        f"{BASE_URL}/hr/client-complaints/{complaint_id}/assign-employee/",
        headers=headers,
        data=json.dumps(assignment_data)
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Employee assignment successful!")
        print(f"   - Assigned to: {result['employee_name']}")
        return True
    else:
        # This might fail if already assigned, which is expected
        print(f"⚠️ Employee assignment response: {response.status_code}")
        if response.status_code == 400:
            error_data = response.json()
            if 'already assigned' in error_data.get('error', '').lower():
                print("   (Expected - employee already assigned)")
                return True
        return False

def test_get_complaint_with_assignments(complaint_id):
    """Test getting complaint with assignments to verify they're included"""
    print(f"\n📋 Getting complaint {complaint_id} with assignments...")
    
    response = requests.get(f"{BASE_URL}/hr/client-complaints/{complaint_id}/", headers=headers)
    
    if response.status_code == 200:
        complaint = response.json()
        
        team_assignments = complaint.get('assignments', [])
        employee_assignments = complaint.get('employee_assignments', [])
        
        print(f"✅ Complaint retrieved successfully!")
        print(f"   - Team assignments: {len(team_assignments)}")
        print(f"   - Employee assignments: {len(employee_assignments)}")
        
        # Show assignment details
        for assignment in team_assignments:
            print(f"     🏢 Team: {assignment['team_name']} (Active: {assignment['is_active']})")
        
        for assignment in employee_assignments:
            print(f"     👤 Employee: {assignment['employee_name']} - {assignment['employee_position']} (Active: {assignment['is_active']})")
        
        return True
    else:
        print(f"❌ Failed to get complaint: {response.status_code}")
        return False

def main():
    print("🚀 Testing Multiple Complaint Assignment System\n")
    
    # Test 1: Get a complaint to work with
    complaint_id = test_get_complaints()
    if not complaint_id:
        print("❌ Cannot proceed without a complaint to test")
        return False
    
    # Test 2: Get teams and employees
    teams, employees = test_get_teams_and_employees()
    if not teams and not employees:
        print("❌ Cannot proceed without teams or employees")
        return False
    
    # Test 3: Test multiple assignment
    if teams or employees:
        success = test_multiple_assignment(complaint_id, teams, employees)
        if not success:
            return False
    
    # Test 4: Test single employee assignment (might fail if already assigned)
    test_single_employee_assignment(complaint_id, employees)
    
    # Test 5: Verify assignments are properly retrieved
    success = test_get_complaint_with_assignments(complaint_id)
    
    if success:
        print(f"\n🎉 All tests completed! Multiple assignment system is working.")
        print(f"\n💡 Frontend Usage:")
        print(f"   1. Open complaint detail modal")
        print(f"   2. Go to 'Assignment Actions' card")  
        print(f"   3. Use 'Multiple Assignment' tab to select teams and employees")
        print(f"   4. Add notes and click assign")
        return True
    else:
        print(f"\n❌ Tests failed. Check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)