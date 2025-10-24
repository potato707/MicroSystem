#!/usr/bin/env python3
"""
Quick test to check employee data structure for username display
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/hr"

def get_admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/token/",
        json={
            "username": "admin",
            "password": "admin123"
        }
    )
    if response.status_code == 200:
        return response.json()["access"]
    return None

def test_employee_structure():
    """Test employee data structure"""
    token = get_admin_token()
    if not token:
        print("❌ Failed to authenticate")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "="*70)
    print("  TESTING EMPLOYEE DATA STRUCTURE FOR USERNAME DISPLAY")
    print("="*70)
    
    # Get employees
    print("\nFetching employees...")
    response = requests.get(f"{API_URL}/employees/", headers=headers)
    
    if response.status_code == 200:
        employees = response.json()
        employees_list = employees.get('results', employees) if isinstance(employees, dict) else employees
        
        print(f"✓ Found {len(employees_list)} employees\n")
        
        # Show first 3 employees with all their data
        for i, emp in enumerate(employees_list[:3], 1):
            print(f"\n{i}. Employee Data Structure:")
            print(f"   ID: {emp.get('id', 'N/A')}")
            print(f"   First Name: {emp.get('first_name', 'N/A')}")
            print(f"   Last Name: {emp.get('last_name', 'N/A')}")
            print(f"   Email: {emp.get('email', 'N/A')}")
            
            # Check for username in different locations
            if 'username' in emp:
                print(f"   ✓ Username (direct): {emp['username']}")
            
            if 'user' in emp and isinstance(emp['user'], dict):
                print(f"   ✓ User object found:")
                if 'username' in emp['user']:
                    print(f"     - Username: {emp['user']['username']}")
                if 'first_name' in emp['user']:
                    print(f"     - First Name: {emp['user']['first_name']}")
                if 'last_name' in emp['user']:
                    print(f"     - Last Name: {emp['user']['last_name']}")
            
            # Determine display format
            username = emp.get('username') or (emp.get('user', {}).get('username') if isinstance(emp.get('user'), dict) else None) or emp.get('email', '').split('@')[0]
            
            if emp.get('first_name') or emp.get('last_name'):
                display_name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip()
            else:
                display_name = username
            
            print(f"\n   📋 Suggested Display Format:")
            print(f"   → {display_name} (@{username})")
            print("   " + "-"*60)
        
        print("\n" + "="*70)
        print("  RECOMMENDATION FOR DROPDOWN DISPLAY")
        print("="*70)
        print("\n  Format: [First Name] [Last Name] (@username)")
        print("  Example: John Doe (@johndoe)")
        print("\n  Fallback if no name: @username")
        print("\n" + "="*70 + "\n")
    else:
        print(f"❌ Failed to fetch employees: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_employee_structure()
