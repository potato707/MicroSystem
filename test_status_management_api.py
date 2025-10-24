#!/usr/bin/env python3
"""
Test script for the Custom Complaint Status Management System
Tests all CRUD operations for custom statuses and status updates
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/hr"
ADMIN_CREDENTIALS = {
    'username': 'mohammed',  # Replace with actual admin username
    'password': 'admin123'   # Replace with actual password
}

def get_auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/auth/login/", data=ADMIN_CREDENTIALS)
    if response.status_code == 200:
        return response.json().get('token') or response.cookies.get('sessionid')
    print(f"Authentication failed: {response.status_code}")
    return None

def test_custom_status_crud():
    """Test CRUD operations for custom statuses"""
    print("=== Testing Custom Status CRUD Operations ===")
    
    token = get_auth_token()
    if not token:
        print("Failed to authenticate")
        return
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    # 1. Test GET all custom statuses
    print("\n1. Getting all custom statuses...")
    response = requests.get(f"{BASE_URL}/client-complaint-statuses/", headers=headers)
    print(f"GET /client-complaint-statuses/ - Status: {response.status_code}")
    if response.status_code == 200:
        statuses = response.json()
        print(f"Found {len(statuses['results'] if 'results' in statuses else statuses)} custom statuses")
        for status in (statuses['results'] if 'results' in statuses else statuses):
            print(f"  - {status['name']} (Order: {status['display_order']}, Active: {status['is_active']})")
    
    # 2. Test GET active statuses
    print("\n2. Getting active custom statuses...")
    response = requests.get(f"{BASE_URL}/client-complaint-statuses/active/", headers=headers)
    print(f"GET /client-complaint-statuses/active/ - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Active statuses: {len(response.json())}")
    
    # 3. Test CREATE new custom status
    print("\n3. Creating new custom status...")
    new_status = {
        'name': 'Test Status',
        'description': 'This is a test status created by the API test',
        'display_order': 99,
        'is_active': True
    }
    response = requests.post(f"{BASE_URL}/client-complaint-statuses/", 
                           json=new_status, headers=headers)
    print(f"POST /client-complaint-statuses/ - Status: {response.status_code}")
    if response.status_code == 201:
        created_status = response.json()
        print(f"Created status: {created_status['name']} (ID: {created_status['id']})")
        
        # 4. Test UPDATE the created status
        print("\n4. Updating the created status...")
        update_data = {
            'name': 'Updated Test Status',
            'description': 'Updated description',
            'display_order': 50,
            'is_active': False
        }
        response = requests.put(f"{BASE_URL}/client-complaint-statuses/{created_status['id']}/", 
                              json=update_data, headers=headers)
        print(f"PUT /client-complaint-statuses/{created_status['id']}/ - Status: {response.status_code}")
        if response.status_code == 200:
            print("Status updated successfully")
        
        # 5. Test DELETE the created status
        print("\n5. Deleting the test status...")
        response = requests.delete(f"{BASE_URL}/client-complaint-statuses/{created_status['id']}/", 
                                 headers=headers)
        print(f"DELETE /client-complaint-statuses/{created_status['id']}/ - Status: {response.status_code}")
        if response.status_code == 204:
            print("Status deleted successfully")

def test_available_statuses_api():
    """Test the combined available statuses API"""
    print("\n\n=== Testing Available Statuses API ===")
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    # Test the combined endpoint that returns both default and custom statuses
    print("\n1. Getting all available statuses (default + custom)...")
    response = requests.get(f"{BASE_URL}/client-complaints/available-statuses/", headers=headers)
    print(f"GET /client-complaints/available-statuses/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Default statuses: {len(data['default_statuses'])}")
        for status in data['default_statuses']:
            print(f"  - {status['display_name']} ({status['name']})")
        
        print(f"Custom statuses: {len(data['custom_statuses'])}")
        for status in data['custom_statuses']:
            print(f"  - {status['display_name']} (Order: {status['display_order']})")
        
        print(f"All statuses combined: {len(data['all_statuses'])}")

def test_complaint_status_update():
    """Test updating complaint status"""
    print("\n\n=== Testing Complaint Status Update ===")
    
    token = get_auth_token()
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    # First, get a complaint to test with
    print("\n1. Getting existing complaints...")
    response = requests.get(f"{BASE_URL}/client-complaints/", headers=headers)
    print(f"GET /client-complaints/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        complaints = response.json()
        if (complaints['results'] if 'results' in complaints else complaints):
            complaint = (complaints['results'] if 'results' in complaints else complaints)[0]
            complaint_id = complaint['id']
            print(f"Testing with complaint ID: {complaint_id}")
            print(f"Current status: {complaint.get('status', 'N/A')}")
            
            # Test updating to a custom status
            print(f"\n2. Updating complaint {complaint_id} to custom status...")
            update_data = {
                'custom_status_id': 1  # ID of the first custom status we created
            }
            response = requests.post(f"{BASE_URL}/client-complaints/{complaint_id}/update-status/", 
                                   json=update_data, headers=headers)
            print(f"POST /client-complaints/{complaint_id}/update-status/ - Status: {response.status_code}")
            if response.status_code == 200:
                print("Status updated to custom status successfully")
                
                # Test updating back to a default status
                print(f"\n3. Updating complaint {complaint_id} back to default status...")
                update_data = {
                    'status': 2  # Approved status ID
                }
                response = requests.post(f"{BASE_URL}/client-complaints/{complaint_id}/update-status/", 
                                       json=update_data, headers=headers)
                print(f"POST /client-complaints/{complaint_id}/update-status/ - Status: {response.status_code}")
                if response.status_code == 200:
                    print("Status updated to default status successfully")
        else:
            print("No complaints found to test with")

if __name__ == "__main__":
    print("Custom Complaint Status Management System - API Test")
    print("=" * 60)
    
    try:
        test_custom_status_crud()
        test_available_statuses_api()
        test_complaint_status_update()
        print("\n" + "=" * 60)
        print("API Tests Completed!")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure Django server is running on localhost:8000")
    except Exception as e:
        print(f"Error during testing: {e}")