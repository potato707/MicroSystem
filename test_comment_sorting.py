"""
Test script to verify comment/reply sorting by date and time
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
COMPLAINT_ID = "64915191-e191-46e7-8096-6e1bef730fe3"
CLIENT_PORTAL_TOKEN = "b_z9JfeRwMUZPp-uiUs5pfd6blonkydLyRlV08MOHuI"

# JWT Token for admin authentication
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoyMDc1NTM2NDUyLCJpYXQiOjE3NjAxNzY0NTIsImp0aSI6ImMzZTg3YTYyNjUyODRiOTU5YWZjODU0NzhkZjgzOWNmIiwidXNlcl9pZCI6ImMxYTUwYTUzLTk3Y2ItNDM0YS1iNTViLTFhMzY1YTM1ZGUzZCJ9.8bvrB19oqyRiIB8Tg-4go4OTpNzngoiOjY8DS8XhZww"

def test_comment_sorting():
    """Test that comments are sorted by date/time correctly"""
    print("=== Testing Comment/Reply Sorting by Date and Time ===")
    
    # Create multiple comments with slight delays to test sorting
    comments_to_create = [
        {"comment": "First comment - should appear LAST (oldest)", "is_internal": False},
        {"comment": "Second comment - should appear in middle", "is_internal": False},
        {"comment": "Third comment - should appear FIRST (newest)", "is_internal": False}
    ]
    
    created_comment_ids = []
    
    # Create comments with small delays
    for i, comment_data in enumerate(comments_to_create):
        print(f"\nCreating comment {i+1}: {comment_data['comment'][:30]}...")
        
        response = requests.post(
            f"{BASE_URL}/hr/client-complaints/{COMPLAINT_ID}/comments/",
            headers={
                "Authorization": AUTH_TOKEN,
                "Content-Type": "application/json"
            },
            json=comment_data
        )
        
        if response.status_code == 201:
            comment_id = response.json().get('id')
            created_comment_ids.append(comment_id)
            print(f"✅ Comment created with ID: {comment_id}")
        else:
            print(f"❌ Failed to create comment: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # Small delay to ensure different timestamps
        import time
        time.sleep(1)
    
    print(f"\nCreated {len(created_comment_ids)} comments")
    return created_comment_ids

def check_client_portal_sorting():
    """Check sorting in client portal"""
    print("\n=== Checking Client Portal Sorting ===")
    
    try:
        response = requests.get(f"{BASE_URL}/hr/client-portal/{CLIENT_PORTAL_TOKEN}/")
        
        if response.status_code == 200:
            data = response.json()
            replies = data.get('complaint', {}).get('client_replies', [])
            
            print(f"✅ Client portal accessed successfully")
            print(f"   Total messages: {len(replies)}")
            
            if len(replies) >= 2:
                print("\n📅 Message Sorting Analysis (First 5 messages):")
                print("   Expected: Newest messages first (descending by date)")
                
                for i, reply in enumerate(replies[:5]):
                    created_at = reply['created_at']
                    message_preview = reply['reply_text'][:50]
                    author = reply['author_type']
                    
                    print(f"   {i+1}. [{created_at}] ({author}) {message_preview}...")
                
                # Check if sorting is correct (newer dates should come first)
                if len(replies) >= 2:
                    first_date = replies[0]['created_at']
                    second_date = replies[1]['created_at']
                    
                    # Parse dates for comparison
                    try:
                        from dateutil import parser
                        first_dt = parser.parse(first_date)
                        second_dt = parser.parse(second_date)
                        
                        if first_dt >= second_dt:
                            print("\n✅ SORTING CORRECT: Messages are sorted newest first")
                        else:
                            print("\n❌ SORTING INCORRECT: Messages should be sorted newest first")
                    except Exception as e:
                        print(f"\n⚠️  Could not verify sorting due to date parsing error: {e}")
            else:
                print("   Not enough messages to verify sorting")
                
        else:
            print(f"❌ Failed to access client portal: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking client portal: {e}")

def check_admin_view_sorting():
    """Check sorting in admin complaint view"""
    print("\n=== Checking Admin View Sorting ===")
    
    try:
        response = requests.get(
            f"{BASE_URL}/hr/client-complaints/{COMPLAINT_ID}/",
            headers={"Authorization": AUTH_TOKEN}
        )
        
        if response.status_code == 200:
            data = response.json()
            comments = data.get('comments', [])
            
            print(f"✅ Admin complaint view accessed successfully")
            print(f"   Total comments: {len(comments)}")
            
            if len(comments) >= 2:
                print("\n📅 Admin Comments Sorting Analysis (First 5 comments):")
                print("   Expected: Newest comments first (descending by date)")
                
                for i, comment in enumerate(comments[:5]):
                    created_at = comment['created_at']
                    comment_preview = comment['comment'][:50]
                    author = comment.get('author_name', 'Unknown')
                    is_internal = comment.get('is_internal', False)
                    
                    print(f"   {i+1}. [{created_at}] {author} ({'Internal' if is_internal else 'Public'})")
                    print(f"       {comment_preview}...")
                
                # Check if sorting is correct
                if len(comments) >= 2:
                    first_date = comments[0]['created_at']
                    second_date = comments[1]['created_at']
                    
                    try:
                        from dateutil import parser
                        first_dt = parser.parse(first_date)
                        second_dt = parser.parse(second_date)
                        
                        if first_dt >= second_dt:
                            print("\n✅ ADMIN SORTING CORRECT: Comments are sorted newest first")
                        else:
                            print("\n❌ ADMIN SORTING INCORRECT: Comments should be sorted newest first")
                    except Exception as e:
                        print(f"\n⚠️  Could not verify admin sorting due to date parsing error: {e}")
            else:
                print("   Not enough comments to verify sorting")
                
        else:
            print(f"❌ Failed to access admin complaint view: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking admin view: {e}")

def main():
    """Run all sorting tests"""
    print("🚀 Testing Comment/Reply Sorting by Date and Time")
    print("=" * 60)
    
    # Create test comments
    created_ids = test_comment_sorting()
    
    # Check both client portal and admin view sorting
    check_client_portal_sorting()
    check_admin_view_sorting()
    
    print("\n" + "=" * 60)
    print("📋 Summary:")
    print("• Comments and replies should be sorted newest first")
    print("• Both client portal and admin views should show consistent sorting")
    print("• Model-level ordering has been updated to use '-created_at'")
    print("• Serializer sorting has been improved with better date parsing")
    
    if created_ids:
        print(f"\n💡 Test comments created with IDs: {created_ids}")
        print("   You can verify the sorting in your frontend interface")

if __name__ == "__main__":
    main()