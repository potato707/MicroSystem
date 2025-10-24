"""
Test script for all three implemented features:
1. Comment system with is_internal flag
2. Sorted messages in client portal (newest first)
3. Permanent client portal links with management
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
COMPLAINT_ID = "64915191-e191-46e7-8096-6e1bef730fe3"
CLIENT_PORTAL_TOKEN = "b_z9JfeRwMUZPp-uiUs5pfd6blonkydLyRlV08MOHuI"

# JWT Token for admin authentication
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc1NTM2NDUyLCJpYXQiOjE3NjAxNzY0NTIsImp0aSI6ImMzZTg3YTYyNjUyODRiOTU5YWZjODU0NzhkZjgzOWNmIiwidXNlcl9pZCI6ImMxYTUwYTUzLTk3Y2ItNDM0YS1iNTViLTFhMzY1YTM1ZGUzZCJ9.8bvrB19oqyRiIB8Tg-4go4OTpNzngoiOjY8DS8XhZww"

def test_comment_with_is_internal_flag():
    """Test 1: Comment system with is_internal flag"""
    print("=== Testing Comment System with is_internal Flag ===")
    
    # Test internal comment (should not appear in client portal)
    internal_comment = {
        "comment": "This is an INTERNAL comment - should not be visible to client",
        "is_internal": True
    }
    
    response = requests.post(
        f"{BASE_URL}/hr/client-complaints/{COMPLAINT_ID}/comments/",
        headers={
            "Authorization": AUTH_TOKEN,
            "Content-Type": "application/json"
        },
        json=internal_comment
    )
    
    if response.status_code == 201:
        print("✅ Internal comment created successfully")
        print(f"   Comment ID: {response.json().get('id')}")
    else:
        print(f"❌ Failed to create internal comment: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test public comment (should appear in client portal)
    public_comment = {
        "comment": "This is a PUBLIC comment - should be visible to client",
        "is_internal": False
    }
    
    response = requests.post(
        f"{BASE_URL}/hr/client-complaints/{COMPLAINT_ID}/comments/",
        headers={
            "Authorization": AUTH_TOKEN,
            "Content-Type": "application/json"
        },
        json=public_comment
    )
    
    if response.status_code == 201:
        print("✅ Public comment created successfully")
        print(f"   Comment ID: {response.json().get('id')}")
    else:
        print(f"❌ Failed to create public comment: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print()

def test_client_portal_sorting():
    """Test 2: Check that messages are sorted with newest first"""
    print("=== Testing Client Portal Message Sorting ===")
    
    response = requests.get(f"{BASE_URL}/hr/client-portal/{CLIENT_PORTAL_TOKEN}/")
    
    if response.status_code == 200:
        data = response.json()
        replies = data.get('complaint', {}).get('client_replies', [])
        
        print(f"✅ Client portal accessed successfully")
        print(f"   Total messages: {len(replies)}")
        
        if len(replies) >= 2:
            # Check if messages are sorted by date (newest first)
            first_date = replies[0]['created_at']
            last_date = replies[-1]['created_at']
            
            print(f"   First message date: {first_date}")
            print(f"   Last message date: {last_date}")
            
            # Since we're sorting in reverse (newest first), first date should be >= last date
            if first_date >= last_date:
                print("✅ Messages are correctly sorted (newest first)")
            else:
                print("❌ Messages are NOT correctly sorted")
        
        # Show recent messages to verify sorting
        print("   Recent messages (showing first 3):")
        for i, reply in enumerate(replies[:3]):
            print(f"   {i+1}. [{reply['created_at']}] {reply['reply_text'][:50]}...")
            print(f"      Author: {reply['author_type']} | Internal: {reply.get('is_internal', 'N/A')}")
    else:
        print(f"❌ Failed to access client portal: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print()

def test_permanent_client_portal_links():
    """Test 3: Permanent client portal link management"""
    print("=== Testing Permanent Client Portal Links ===")
    
    # Test creating/managing portal token
    print("1. Creating/Managing Portal Token:")
    response = requests.post(
        f"{BASE_URL}/hr/client-complaints/{COMPLAINT_ID}/portal-token/",
        headers={
            "Authorization": AUTH_TOKEN,
            "Content-Type": "application/json"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Portal token managed successfully")
        print(f"   Token: {data.get('token')}")
        print(f"   Is Permanent: {data.get('is_permanent')}")
        print(f"   Access URL: {data.get('access_url')}")
        print(f"   Access Count: {data.get('access_count')}")
        
        token = data.get('token')
        
        # Test deactivating token from admin side
        print("\n2. Deactivating Portal Token (Admin):")
        response = requests.delete(
            f"{BASE_URL}/hr/client-complaints/{COMPLAINT_ID}/portal-token/",
            headers={
                "Authorization": AUTH_TOKEN,
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print("✅ Portal token deactivated successfully from admin")
            print(f"   Message: {response.json().get('message')}")
        else:
            print(f"❌ Failed to deactivate token from admin: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # Test client-side deactivation (if we had an active token)
        print("\n3. Testing Client-side Deactivation Endpoint:")
        if token:
            response = requests.post(
                f"{BASE_URL}/hr/client-portal/{token}/deactivate/",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 404]:  # 404 expected if already deactivated
                print("✅ Client-side deactivation endpoint works")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Client-side deactivation failed: {response.status_code}")
                print(f"   Error: {response.text}")
    else:
        print(f"❌ Failed to manage portal token: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print()

def main():
    """Run all tests"""
    print("🚀 Testing All Three Implemented Features")
    print("=" * 50)
    
    test_comment_with_is_internal_flag()
    test_client_portal_sorting()
    test_permanent_client_portal_links()
    
    print("=" * 50)
    print("📋 Frontend Implementation Notes:")
    print()
    print("1. COMMENT CHECKBOX (is_internal flag):")
    print("   - Add a checkbox in your comment form")
    print("   - Label: 'Internal Comment (Company Only)'")
    print("   - When checked: set is_internal: true")
    print("   - When unchecked: set is_internal: false")
    print("   - Default: false (public)")
    print()
    print("2. CLIENT PORTAL SORTING:")
    print("   - Messages are now automatically sorted newest first")
    print("   - No frontend changes needed")
    print()
    print("3. PERMANENT PORTAL LINKS:")
    print("   - Use POST /client-complaints/{id}/portal-token/ to create")
    print("   - Use DELETE /client-complaints/{id}/portal-token/ to deactivate (admin)")
    print("   - Use POST /client-portal/{token}/deactivate/ to deactivate (client)")
    print("   - Links no longer expire by default")
    print()
    
if __name__ == "__main__":
    main()