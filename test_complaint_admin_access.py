#!/usr/bin/env python3
"""
Test script to verify complaint admin permissions work correctly for non-admin users
"""

import requests
import json

# Token for "string" user who has complaint admin permissions
STRING_USER_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc1ODk2NzgyLCJpYXQiOjE3NjA1MzY3ODIsImp0aSI6ImFmMTNhNmU2MDU0ZTQ2Yzk4ZDcwNWUyOWY3MTdiYjY0IiwidXNlcl9pZCI6IjIyMWMzYTQ5LThiZTktNGI0MS1iNjkwLWZlZmQwYjFjMzE3NiJ9.Q-1C2tfacLQ9MvP5KkNUOVKwG-_g-FcPtk4kWe0NTeM'

BASE_URL = 'http://localhost:8000'

def test_endpoint(name, url, token, method='GET', data=None, expected_status=200):
    """Test an API endpoint"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        else:
            return False, f"Unknown method: {method}"
        
        success = response.status_code == expected_status
        
        if success:
            return True, f"✓ {name} - Status: {response.status_code}"
        else:
            error_msg = f"✗ {name} - Expected: {expected_status}, Got: {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f"\n  Error: {error_data.get('detail', error_data)}"
            except:
                error_msg += f"\n  Response: {response.text[:200]}"
            return False, error_msg
            
    except Exception as e:
        return False, f"✗ {name} - Exception: {str(e)}"

def main():
    print("=" * 80)
    print("Testing Complaint Admin Permissions for Non-Admin User")
    print("=" * 80)
    print(f"\nTesting with 'string' user token\n")
    
    tests = []
    
    # Test 1: Get user's complaint admin permissions
    print("1. Testing User Permissions Endpoint")
    success, msg = test_endpoint(
        "GET user permissions",
        f"{BASE_URL}/hr/complaint-admin-permissions/user/",
        STRING_USER_TOKEN
    )
    tests.append(("User Permissions", success))
    print(f"   {msg}\n")
    
    # Test 2: Get complaint statuses (the one that was failing)
    print("2. Testing Complaint Statuses Endpoint")
    success, msg = test_endpoint(
        "GET complaint statuses",
        f"{BASE_URL}/hr/client-complaint-statuses/",
        STRING_USER_TOKEN
    )
    tests.append(("Complaint Statuses", success))
    print(f"   {msg}\n")
    
    # Test 3: Get complaint categories
    print("3. Testing Complaint Categories Endpoint")
    success, msg = test_endpoint(
        "GET complaint categories",
        f"{BASE_URL}/hr/complaint-categories/",
        STRING_USER_TOKEN
    )
    tests.append(("Complaint Categories", success))
    print(f"   {msg}\n")
    
    # Test 4: Get client complaints
    print("4. Testing Client Complaints Endpoint")
    success, msg = test_endpoint(
        "GET client complaints",
        f"{BASE_URL}/hr/client-complaints/",
        STRING_USER_TOKEN
    )
    tests.append(("Client Complaints", success))
    print(f"   {msg}\n")
    
    # Test 5: Get active statuses
    print("5. Testing Active Statuses Endpoint")
    success, msg = test_endpoint(
        "GET active statuses",
        f"{BASE_URL}/hr/client-complaint-statuses/active/",
        STRING_USER_TOKEN
    )
    tests.append(("Active Statuses", success))
    print(f"   {msg}\n")
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in tests if success)
    total = len(tests)
    
    for test_name, success in tests:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 80)
    if passed == total:
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        print("Complaint admin permissions are working correctly!")
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total} passed)")
        print("Some endpoints may still have permission issues.")
    print("=" * 80)
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    exit(main())
