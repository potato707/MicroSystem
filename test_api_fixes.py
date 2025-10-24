#!/usr/bin/env python3
"""
Test script to verify the API fixes for task assignment and complaint task creation
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/hr"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc1Mzc3OTM2LCJpYXQiOjE3NjAwMTc5MzYsImp0aSI6ImJhMDUyNWM1YjY1ZDQzOGFiYjRjZDZiYjhiOGI1MDVjIiwidXNlcl9pZCI6IjIyMWMzYTQ5LThiZTktNGI0MS1iNjkwLWZlZmQwYjFjMzE3NiJ9.zF7upDNarFa6CrL7-TQroXdEsNlpczDts-WkrqqpI4M"

headers = {
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.8',
    'Authorization': f'Bearer {TOKEN}',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'http://localhost:3000',
    'Referer': 'http://localhost:3000/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'Sec-GPC': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Brave";v="138"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"'
}

def test_task_assignment():
    """Test the task assignment endpoint"""
    print("Testing task assignment endpoint...")
    
    url = f"{BASE_URL}/tasks/assign-to-team/"
    
    # Test with the exact same data that the React app is sending (causing the error)
    data = {
        "team_id": "fc2b0783-9238-470a-b112-938a05c81396",
        "team_priority": "medium",
        "can_reassign": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Task assignment endpoint working correctly!")
            return True
        else:
            print("❌ Task assignment endpoint failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error testing task assignment: {e}")
        return False

def test_complaint_task_creation():
    """Test the complaint task creation endpoint"""
    print("\nTesting complaint task creation endpoint...")
    
    url = f"{BASE_URL}/client-complaints/tasks/create/"
    
    # Test with the exact same data that the React app is sending (causing the error)
    data = {
        "complaint_id": "20b24e5e-d0af-4a74-85b9-ec16eafdb107",
        "team_id": "fc2b0783-9238-470a-b112-938a05c81396",
        "notes": ""
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Complaint task creation endpoint working correctly!")
            return True
        else:
            print("❌ Complaint task creation endpoint failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure Django server is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error testing complaint task creation: {e}")
        return False

def main():
    print("=" * 60)
    print("API FIX VALIDATION TEST")
    print("=" * 60)
    
    # Test both endpoints
    task_assignment_ok = test_task_assignment()
    complaint_task_ok = test_complaint_task_creation()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Task Assignment API: {'✅ FIXED' if task_assignment_ok else '❌ FAILED'}")
    print(f"Complaint Task Creation API: {'✅ FIXED' if complaint_task_ok else '❌ FAILED'}")
    
    if task_assignment_ok and complaint_task_ok:
        print("\n🎉 All API fixes are working correctly!")
    else:
        print("\n⚠️ Some API fixes need attention.")
    print("=" * 60)

if __name__ == "__main__":
    main()