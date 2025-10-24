#!/usr/bin/env python3
"""
Direct test of serializer changes without server
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ClientComplaintComment, ClientComplaintReply, User
from hr_management.serializers import ClientPortalComplaintSerializer

def test_serializer_directly():
    """Test the modified ClientPortalComplaintSerializer directly"""
    print("🔬 Direct Serializer Test - ClientPortalComplaintSerializer")
    print("=" * 65)
    
    complaint = ClientComplaint.objects.first()
    if not complaint:
        print("❌ No complaint found")
        return
    
    print(f"📋 Testing complaint: {complaint.title}")
    
    # Check existing data
    client_replies_count = complaint.client_replies.count()
    admin_comments_count = complaint.comments.count()
    admin_visible_comments = complaint.comments.filter(is_internal=False).count()
    
    print(f"📊 Current data:")
    print(f"   Client replies: {client_replies_count}")
    print(f"   Admin comments (total): {admin_comments_count}")
    print(f"   Admin comments (visible to client): {admin_visible_comments}")
    
    # Add a test admin comment visible to client if none exist
    if admin_visible_comments == 0:
        print(f"\n➕ Adding test admin comment visible to client...")
        admin_user = User.objects.filter(role='admin').first() or User.objects.first()
        
        test_comment = ClientComplaintComment.objects.create(
            complaint=complaint,
            comment="Test admin comment visible to client - from serializer test",
            author=admin_user,
            is_internal=False  # Visible to client
        )
        print(f"   ✅ Created admin comment: {test_comment.id}")
        admin_visible_comments = 1
    
    print(f"\n🧪 Testing ClientPortalComplaintSerializer...")
    
    try:
        # Test the serializer
        serializer = ClientPortalComplaintSerializer(complaint)
        data = serializer.data
        
        print(f"   ✅ Serializer executed successfully")
        
        # Check client_replies field
        client_replies = data.get('client_replies', [])
        print(f"   📝 Client replies field: {len(client_replies)} communications")
        
        if client_replies:
            # Count by type and author_type
            type_counts = {}
            author_type_counts = {}
            
            for comm in client_replies:
                comm_type = comm.get('type', 'unknown')
                author_type = comm.get('author_type', 'unknown')
                
                type_counts[comm_type] = type_counts.get(comm_type, 0) + 1
                author_type_counts[author_type] = author_type_counts.get(author_type, 0) + 1
            
            print(f"\n   📊 Communication breakdown:")
            for comm_type, count in type_counts.items():
                print(f"      - {comm_type}: {count}")
            
            print(f"\n   👥 Author type breakdown:")
            for author_type, count in author_type_counts.items():
                print(f"      - {author_type}: {count}")
            
            print(f"\n   📋 Recent communications (last 3):")
            for i, comm in enumerate(client_replies[-3:], 1):
                comm_type = comm.get('type', 'unknown')
                author_type = comm.get('author_type', 'unknown')
                content = comm.get('reply_text', '')[:50]
                created = comm.get('created_at', '')
                
                # Format date
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(str(created).replace('Z', '+00:00'))
                    formatted_date = dt.strftime('%b %d')
                except:
                    formatted_date = str(created)[:10] if created else 'Unknown'
                
                author_icon = "👨‍💼" if author_type == 'admin' else "👤"
                print(f"   {i}. {author_icon} [{comm_type}] {formatted_date}: {content}...")
            
            # Check if admin comments appear
            admin_comments_in_replies = [c for c in client_replies if c.get('author_type') == 'admin']
            
            if admin_comments_in_replies:
                print(f"\n   ✅ SUCCESS: Admin comments appear in client portal!")
                print(f"      Found {len(admin_comments_in_replies)} admin communications")
            else:
                print(f"\n   ❌ ISSUE: Admin comments not appearing in client portal")
        else:
            print(f"   ⚠️  No communications found in client_replies")
        
        print(f"\n🎯 Serializer Test Results:")
        print(f"✅ Serializer execution: Working")
        print(f"✅ Client replies included: {len([c for c in client_replies if c.get('author_type') == 'client'])}")
        print(f"✅ Admin comments included: {len([c for c in client_replies if c.get('author_type') == 'admin'])}")
        print(f"✅ Total communications: {len(client_replies)}")
        
        if any(c.get('author_type') == 'admin' for c in client_replies):
            print(f"\n🎉 BIDIRECTIONAL INTEGRATION: Admin comments now visible to client!")
        else:
            print(f"\n⚠️  PARTIAL: Need to verify admin comment creation")
            
    except Exception as e:
        print(f"   ❌ Serializer error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_serializer_directly()