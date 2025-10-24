#!/usr/bin/env python3
"""
Test script to check if complaint data includes assignments after assignment
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

def test_complaint_data_after_assignment():
    """Test what data is returned for a complaint with assignments"""
    # Get a complaint that we know has assignments
    complaint_id = "ce89d8e1-3695-4d5e-ac45-d4472ed230cc"
    
    print(f"🔍 Getting complaint {complaint_id} to check assignment data...")
    response = requests.get(f"{BASE_URL}/hr/client-complaints/{complaint_id}/", headers=headers)
    
    if response.status_code == 200:
        complaint = response.json()
        
        print(f"✅ Complaint retrieved: {complaint['title']}")
        print(f"📋 Status: {complaint['status']}")
        
        # Check team assignments
        if 'assignments' in complaint and complaint['assignments']:
            print(f"\n🏢 Team Assignments ({len(complaint['assignments'])}):")
            for i, assignment in enumerate(complaint['assignments'], 1):
                print(f"  {i}. {assignment['team_name']} (Active: {assignment['is_active']})")
                print(f"     Assigned by: {assignment['assigned_by_name']}")
                print(f"     Notes: {assignment.get('notes', 'No notes')}")
        else:
            print("\n⚠️  No team assignments found in complaint data")
            
        # Check employee assignments
        if 'employee_assignments' in complaint and complaint['employee_assignments']:
            print(f"\n👤 Employee Assignments ({len(complaint['employee_assignments'])}):")
            for i, assignment in enumerate(complaint['employee_assignments'], 1):
                print(f"  {i}. {assignment['employee_name']} (Active: {assignment['is_active']})")
                print(f"     Position: {assignment['employee_position']}")
                print(f"     Department: {assignment['employee_department']}")
                print(f"     Assigned by: {assignment['assigned_by_name']}")
                print(f"     Notes: {assignment.get('notes', 'No notes')}")
        else:
            print("\n⚠️  No employee assignments found in complaint data")
            
        # Print available fields for debugging
        print(f"\n🔧 Available fields in complaint data:")
        for key in sorted(complaint.keys()):
            if key in ['assignments', 'employee_assignments']:
                print(f"  ✅ {key}: {len(complaint[key])} items")
            else:
                print(f"     {key}")
                
    else:
        print(f"❌ Failed to get complaint: {response.status_code}")
        print(f"Response: {response.text[:500]}")

if __name__ == "__main__":
    test_complaint_data_after_assignment()