#!/usr/bin/env python3
"""
Check client portal replies vs internal comments
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ClientComplaintComment, ClientComplaintReply

def check_replies_vs_comments():
    """Check the difference between client replies and internal comments"""
    print("🔍 Checking Client Replies vs Internal Comments")
    print("=" * 60)
    
    complaints = ClientComplaint.objects.all()
    print(f"📋 Found {complaints.count()} complaints in system")
    
    for complaint in complaints[:3]:  # Check first 3 complaints
        print(f"\n📄 Complaint: {complaint.title}")
        print(f"   ID: {complaint.id}")
        
        # Check internal comments
        internal_comments = ClientComplaintComment.objects.filter(complaint=complaint)
        print(f"   💬 Internal Comments: {internal_comments.count()}")
        for comment in internal_comments:
            print(f"      - {comment.author.name}: {comment.comment[:50]}... (Internal: {comment.is_internal})")
        
        # Check client replies
        client_replies = ClientComplaintReply.objects.filter(complaint=complaint)
        print(f"   📝 Client Replies: {client_replies.count()}")
        for reply in client_replies:
            print(f"      - {reply.client_name}: {reply.reply_text[:50]}... (Email: {reply.client_email})")
            if reply.admin_response:
                print(f"        └─ Admin Response: {reply.admin_response[:50]}...")
    
    print(f"\n📊 Summary:")
    total_comments = ClientComplaintComment.objects.count()
    total_replies = ClientComplaintReply.objects.count()
    print(f"   Total Internal Comments: {total_comments}")
    print(f"   Total Client Replies: {total_replies}")
    
    print(f"\n🔍 The Issue:")
    print(f"   - Internal comments are stored in ClientComplaintComment table")
    print(f"   - Client replies are stored in ClientComplaintReply table")
    print(f"   - Frontend only shows 'comments' field from complaint serializer")
    print(f"   - Client replies are NOT included in the comments field")
    
    print(f"\n💡 Solutions:")
    print(f"   1. Modify complaint serializer to include client replies as comments")
    print(f"   2. Create unified comment/reply view in frontend")
    print(f"   3. Add client replies to the comments array with proper formatting")

if __name__ == "__main__":
    check_replies_vs_comments()