#!/usr/bin/env python3
"""
Test what the complaint detail API actually returns
"""
import os
import sys
import django
import requests
import json

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, User
from rest_framework_simplejwt.tokens import RefreshToken

def test_complaint_api_response():
    """Test what the complaint API actually returns for comments"""
    print("🔍 Testing Complaint API Response for Comments")
    print("=" * 60)
    
    try:
        complaint = ClientComplaint.objects.first()
        if not complaint:
            print("❌ No complaints found")
            return
        
        print(f"📋 Testing complaint: {complaint.title}")
        print(f"   ID: {complaint.id}")
        
        # Get user for auth
        admin_user = User.objects.filter(role='admin').first()
        if not admin_user:
            admin_user = User.objects.first()
        
        # Generate JWT token
        refresh = RefreshToken.for_user(admin_user)
        access_token = str(refresh.access_token)
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test complaint detail API
        base_url = "http://localhost:8000"
        complaint_url = f"{base_url}/hr/client-complaints/{complaint.id}/"
        
        print(f"\n📥 Testing GET {complaint_url}")
        
        try:
            response = requests.get(complaint_url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ Successfully retrieved complaint data")
                
                # Check if comments are included
                if 'comments' in data:
                    comments = data['comments']
                    print(f"   💬 Comments in response: {len(comments)}")
                    
                    if comments:
                        print("   📝 Sample comment:")
                        comment = comments[0]
                        for key, value in comment.items():
                            print(f"      {key}: {value}")
                    else:
                        print("   ℹ️  No comments in response (empty array)")
                else:
                    print("   ❌ 'comments' field missing from API response!")
                    print("   Available fields:", list(data.keys()))
                
                # Also check other related fields
                related_fields = ['attachments', 'assignments', 'tasks', 'status_history']
                for field in related_fields:
                    if field in data:
                        count = len(data[field]) if isinstance(data[field], list) else 'N/A'
                        print(f"   📊 {field}: {count}")
                    else:
                        print(f"   ❌ {field}: Missing")
            
            elif response.status_code == 404:
                print("   ❌ Complaint not found (404)")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text[:300]}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection failed - Django server not running")
            print("   💡 Start server: python manage.py runserver")
            return
        
        # Test comments endpoint separately
        comments_url = f"{base_url}/hr/client-complaints/{complaint.id}/comments/"
        print(f"\n📥 Testing GET {comments_url}")
        
        try:
            response = requests.get(comments_url, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                comments_data = response.json()
                print(f"   ✅ Comments endpoint working: {len(comments_data)} comments")
                
                if comments_data:
                    print("   📝 Sample comment from comments endpoint:")
                    comment = comments_data[0]
                    for key, value in comment.items():
                        print(f"      {key}: {value}")
            else:
                print(f"   ❌ Comments endpoint failed: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("   ❌ Connection failed for comments endpoint")
        
        print(f"\n🎯 Analysis:")
        print(f"   - If complaint API includes comments: Frontend should see them")
        print(f"   - If complaint API missing comments: Backend serializer issue")
        print(f"   - If comments endpoint works separately: Frontend reload issue")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complaint_api_response()