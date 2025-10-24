#!/usr/bin/env python3
"""
Test script to verify username is included in employee permission responses
"""

import requests
import json

# Auth token
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc1ODc2OTI4LCJpYXQiOjE3NjA1MTY5MjgsImp0aSI6IjJlN2M4MDUzZTZkZTRiZmE5MjM5ODdmOTUwNmFlYWVkIiwidXNlcl9pZCI6ImMxYTUwYTUzLTk3Y2ItNDM0YS1iNTViLTFhMzY1YTM1ZGUzZCJ9.NRTa6lpS7qnW9vd1BdmlEnniGA7yaBzPVcyfFqgKT9I'
BASE_URL = 'http://localhost:8000'

headers = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json'
}

def test_get_employee_permissions():
    """Test GET /hr/complaint-admin-permissions/employees/"""
    print("=" * 80)
    print("TEST 1: GET Employee Permissions")
    print("=" * 80)
    
    response = requests.get(f'{BASE_URL}/hr/complaint-admin-permissions/employees/', headers=headers)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Found {len(data)} employee permission(s)\n")
        
        for i, perm in enumerate(data, 1):
            print(f"{i}. Permission ID: {perm['id']}")
            print(f"   Employee:")
            print(f"     - ID: {perm['employee']['id']}")
            print(f"     - Name: {perm['employee']['name']}")
            print(f"     - Username: {perm['employee'].get('username', 'NOT FOUND')}")
            print(f"     - Position: {perm['employee'].get('position', 'N/A')}")
            print(f"     - Department: {perm['employee'].get('department', 'N/A')}")
            print(f"   Granted By: {perm['granted_by']}")
            print(f"   Active: {perm['is_active']}")
            print(f"   Notes: {perm.get('notes', 'N/A')}")
            
            if 'permissions' in perm:
                print(f"   Capabilities:")
                print(f"     - Can Review: {perm['permissions'].get('can_review', False)}")
                print(f"     - Can Assign: {perm['permissions'].get('can_assign', False)}")
                print(f"     - Can Update Status: {perm['permissions'].get('can_update_status', False)}")
            print()
        
        # Verify username field exists
        if data:
            has_username = all('username' in p['employee'] for p in data)
            if has_username:
                print("✓ All employee permissions include username field")
            else:
                print("✗ Some employee permissions missing username field")
                return False
        
        return True
    else:
        print(f"✗ Request failed: {response.text}")
        return False

def test_grant_employee_permission():
    """Test POST /hr/complaint-admin-permissions/employees/"""
    print("\n" + "=" * 80)
    print("TEST 2: Grant/Update Employee Permission")
    print("=" * 80)
    
    # Get existing permission to update
    get_response = requests.get(f'{BASE_URL}/hr/complaint-admin-permissions/employees/', headers=headers)
    existing_perms = get_response.json()
    
    if not existing_perms:
        print("✗ No existing permissions to test with")
        return False
    
    first_perm = existing_perms[0]
    employee_id = first_perm['employee']['id']
    
    print(f"Testing with employee: {first_perm['employee']['name']} (@{first_perm['employee'].get('username', 'N/A')})")
    print(f"Employee ID: {employee_id}\n")
    
    # Update the permission
    grant_data = {
        'employee_id': employee_id,
        'can_assign': True,
        'can_review': True,
        'can_update_status': True,
        'notes': 'Test: Verifying username field in response'
    }
    
    response = requests.post(f'{BASE_URL}/hr/complaint-admin-permissions/employees/', 
                            headers=headers, json=grant_data)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code in [200, 201]:
        data = response.json()
        print("✓ Permission granted/updated successfully\n")
        
        print("Response structure:")
        print(json.dumps(data, indent=2))
        
        # Verify username field in response
        if 'employee' in data and 'username' in data['employee']:
            print(f"\n✓ Response includes username: @{data['employee']['username']}")
            return True
        else:
            print("\n✗ Response missing username field")
            return False
    else:
        print(f"✗ Request failed: {response.text}")
        return False

def main():
    print("\n" + "=" * 80)
    print("Testing Employee Permission Username Display Fix")
    print("=" * 80 + "\n")
    
    results = []
    
    # Test 1: GET employee permissions
    results.append(("GET employee permissions", test_get_employee_permissions()))
    
    # Test 2: POST grant/update permission
    results.append(("POST grant/update permission", test_grant_employee_permission()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    all_passed = all(result[1] for result in results)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + ("=" * 80))
    if all_passed:
        print("✓ ALL TESTS PASSED - Username field is properly included in responses")
        print("=" * 80)
        return 0
    else:
        print("✗ SOME TESTS FAILED - Username field may be missing")
        print("=" * 80)
        return 1

if __name__ == '__main__':
    exit(main())
