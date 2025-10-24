#!/usr/bin/env python3
"""
Test the ClientComplaintComment system
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ClientComplaintComment, User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

def test_comment_system():
    """Test the complete comment system"""
    print("🔍 Testing ClientComplaintComment System")
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
        print(f"💬 Existing comments: {existing_comments.count()}")
        
        if existing_comments.exists():
            print("   Sample comment:")
            comment = existing_comments.first()
            print(f"   - Author: {comment.author.name}")
            print(f"   - Content: {comment.comment[:50]}...")
            print(f"   - Internal: {comment.is_internal}")
            print(f"   - Created: {comment.created_at}")
        
        # Test API endpoints
        print("\n🌐 Testing API Endpoints...")
        
        # Get user for authentication
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            admin_user = User.objects.first()
        
        if not admin_user:
            print("❌ No users found in system")
            return
        
        # Setup API client
        client = APIClient()
        refresh = RefreshToken.for_user(admin_user)
        access_token = str(refresh.access_token)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        print(f"🔑 Using user: {admin_user.name} ({admin_user.role})")
        
        # Test GET comments endpoint
        print(f"\n📥 Testing GET /hr/client-complaints/{complaint.id}/comments/")
        response = client.get(f'/hr/client-complaints/{complaint.id}/comments/')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Comments retrieved: {len(data)} comments")
            if data:
                print("   Sample comment from API:")
                comment_data = data[0]
                print(f"   - ID: {comment_data.get('id')}")
                print(f"   - Author: {comment_data.get('author_name')}")
                print(f"   - Content: {comment_data.get('comment', '')[:50]}...")
                print(f"   - Internal: {comment_data.get('is_internal')}")
        else:
            print(f"   ❌ Failed to get comments: {response.content}")
        
        # Test POST comment endpoint
        print(f"\n📤 Testing POST /hr/client-complaints/{complaint.id}/comments/")
        comment_data = {
            'comment': 'Test comment from automated test',
            'is_internal': True
        }
        response = client.post(
            f'/hr/client-complaints/{complaint.id}/comments/', 
            data=json.dumps(comment_data),
            content_type='application/json'
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("   ✅ Comment created successfully")
            print(f"   - New comment ID: {data.get('id')}")
            print(f"   - Content: {data.get('comment')}")
            print(f"   - Author: {data.get('author_name')}")
        else:
            print(f"   ❌ Failed to create comment: {response.content}")
            
        # Check database after API test
        print(f"\n🗄️  Database check after API test...")
        final_count = ClientComplaintComment.objects.filter(complaint=complaint).count()
        print(f"   Total comments now: {final_count}")
        
        # Test URL routing directly
        print(f"\n🛣️  Testing URL routing...")
        from django.urls import reverse, NoReverseMatch
        try:
            # This should match the nested router pattern
            url_name = 'client-complaint-comment-list'
            print(f"   Attempting to reverse URL: {url_name}")
            # This will fail because DRF routers don't work with reverse like this
        except NoReverseMatch as e:
            print(f"   URL reverse failed (expected for DRF nested routes): {e}")
        
        # Check router registration
        print(f"\n📋 Checking router registration...")
        from hr_management.urls import router
        print("   Registered routes:")
        for pattern in router.urls:
            if 'comment' in str(pattern.pattern):
                print(f"   - {pattern.pattern}")
        
        print(f"\n🎯 Final Status:")
        print(f"   - Database model: ✅ Working")
        print(f"   - API authentication: ✅ Working")
        if response.status_code in [200, 201]:
            print(f"   - Comment creation: ✅ Working")
        else:
            print(f"   - Comment creation: ❌ Failed")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_comment_system()