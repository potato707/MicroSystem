#!/usr/bin/env python3
"""
Test the comment system without using Django test client to bypass ALLOWED_HOSTS issue
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ClientComplaintComment, User
from rest_framework_simplejwt.tokens import RefreshToken

def test_comment_system_with_real_server():
    """Test using actual running Django server"""
    print("🔍 Testing Comment System with Real Server")
    print("=" * 60)
    
    try:
        # Get test data
        complaints = ClientComplaint.objects.all()
        if not complaints.exists():
            print("❌ No complaints found in system")
            return
        
        complaint = complaints.first()
        print(f"📋 Testing with complaint: {complaint.title} (ID: {complaint.id})")
        
        # Get existing comments
        existing_comments = ClientComplaintComment.objects.filter(complaint=complaint)
        print(f"💬 Existing comments in database: {existing_comments.count()}")
        
        for comment in existing_comments[:3]:
            print(f"   - {comment.author.name}: {comment.comment[:50]}...")
        
        # Test with real server (assuming it's running on 8000)
        base_url = "http://localhost:8000"
        
        # Get admin user for authentication
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            admin_user = User.objects.first()
        
        if not admin_user:
            print("❌ No users found in system")
            return
        
        # Generate JWT token
        refresh = RefreshToken.for_user(admin_user)
        access_token = str(refresh.access_token)
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"\n🔑 Using user: {admin_user.name} ({admin_user.role})")
        
        # Test GET comments endpoint
        comments_url = f"{base_url}/hr/client-complaints/{complaint.id}/comments/"
        print(f"\n📥 Testing GET {comments_url}")
        
        try:
            response = requests.get(comments_url, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Retrieved {len(data)} comments from API")
                if data:
                    print("   Sample comment from API:")
                    comment_data = data[0]
                    print(f"   - Author: {comment_data.get('author_name')}")
                    print(f"   - Content: {comment_data.get('comment', '')[:50]}...")
                    print(f"   - Internal: {comment_data.get('is_internal')}")
            elif response.status_code == 404:
                print("   ❌ Comments endpoint not found (404)")
            elif response.status_code == 401:
                print("   ❌ Authentication failed (401)")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:200]}")
        
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection failed - Django server not running")
            print("   ℹ️  To test with real server, run: python manage.py runserver")
            return
        except requests.exceptions.Timeout:
            print("   ❌ Request timed out")
            return
        
        # Test POST comment endpoint
        print(f"\n📤 Testing POST {comments_url}")
        comment_data = {
            'comment': 'Test comment from API validation script',
            'is_internal': True
        }
        
        try:
            response = requests.post(comments_url, json=comment_data, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                print("   ✅ Comment created successfully via API")
                print(f"   - New comment ID: {data.get('id')}")
                print(f"   - Content: {data.get('comment')}")
                print(f"   - Author: {data.get('author_name')}")
            else:
                print(f"   ❌ Failed to create comment: {response.status_code}")
                if response.text:
                    print(f"   Error: {response.text[:200]}")
        
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection failed - Django server not running")
        
        # Final database check
        print(f"\n🗄️  Final database check...")
        final_count = ClientComplaintComment.objects.filter(complaint=complaint).count()
        print(f"   Total comments in database: {final_count}")
        
        print(f"\n🎯 Summary:")
        print(f"   - Database models: ✅ Working")
        print(f"   - Comment data exists: {'✅' if existing_comments.count() > 0 else '❌'}")
        print(f"   - API endpoint accessible: {'✅ Check server logs' if response.status_code in [200, 404] else '❌'}")
        
        print(f"\n💡 Next steps to debug frontend issue:")
        print(f"   1. Check browser Network tab when adding comments")
        print(f"   2. Check Django server logs for API errors")
        print(f"   3. Verify frontend is calling correct endpoint: {comments_url}")
        print(f"   4. Check JWT token is being sent in frontend requests")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comment_system_with_real_server()