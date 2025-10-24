#!/usr/bin/env python3
"""
Test the unified comments system
"""
import os
import sys
import django
import requests

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, User
from rest_framework_simplejwt.tokens import RefreshToken

def test_unified_comments():
    """Test the new unified comments system"""
    print("🔍 Testing Unified Comments System")
    print("=" * 60)
    
    # Get complaint with both comments and replies
    complaint = ClientComplaint.objects.filter(
        client_replies__isnull=False
    ).first()
    
    if not complaint:
        print("❌ No complaint found with client replies")
        return
    
    print(f"📋 Testing complaint: {complaint.title}")
    print(f"   ID: {complaint.id}")
    
    # Count what we expect to see
    internal_comments = complaint.comments.count()
    client_replies = complaint.client_replies.count()
    admin_responses = complaint.client_replies.filter(admin_response__isnull=False).count()
    
    expected_total = internal_comments + client_replies + admin_responses
    
    print(f"\n📊 Expected in unified comments:")
    print(f"   - Internal comments: {internal_comments}")
    print(f"   - Client replies: {client_replies}")
    print(f"   - Admin responses: {admin_responses}")
    print(f"   - Total expected: {expected_total}")
    
    # Test the API
    admin_user = User.objects.filter(role='admin').first()
    if not admin_user:
        admin_user = User.objects.first()
    
    refresh = RefreshToken.for_user(admin_user)
    access_token = str(refresh.access_token)
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    base_url = "http://localhost:8000"
    complaint_url = f"{base_url}/hr/client-complaints/{complaint.id}/"
    
    print(f"\n📥 Testing GET {complaint_url}")
    
    try:
        response = requests.get(complaint_url, headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'comments' in data:
                comments = data['comments']
                print(f"   ✅ Found {len(comments)} unified comments")
                
                print(f"\n📝 Comments breakdown:")
                internal_count = len([c for c in comments if c.get('type') == 'internal_comment'])
                reply_count = len([c for c in comments if c.get('type') == 'client_reply'])
                response_count = len([c for c in comments if c.get('type') == 'admin_response'])
                
                print(f"   - Internal comments: {internal_count}")
                print(f"   - Client replies: {reply_count}")
                print(f"   - Admin responses: {response_count}")
                print(f"   - Total: {len(comments)}")
                
                print(f"\n📋 Sample comments (chronological order):")
                for i, comment in enumerate(comments[:5]):  # Show first 5
                    comment_type = comment.get('type', 'unknown')
                    author = comment.get('author_name', 'Unknown')
                    content = comment.get('comment', '')[:50]
                    
                    print(f"   {i+1}. [{comment_type}] {author}: {content}...")
                    
                if len(comments) != expected_total:
                    print(f"\n⚠️  Count mismatch: Expected {expected_total}, got {len(comments)}")
                else:
                    print(f"\n✅ Perfect! Comment count matches expected total.")
            
            else:
                print("   ❌ No 'comments' field found in response")
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            
    except requests.ConnectionError:
        print("   ❌ Connection failed - Django server not running")
        print("   💡 Start server: python manage.py runserver")
    
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_unified_comments()