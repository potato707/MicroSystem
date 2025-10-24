#!/usr/bin/env python
import os
import sys
import django

# Add the MicroSystem directory to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint, ClientComplaintComment, User

def test_delete_logic():
    print("=== Testing Delete Button Logic ===")
    
    # Get the test user
    user = User.objects.get(username='string')
    print(f"User: {user.username} (ID: {user.id})")
    print(f"User role: {user.role}")
    
    # Get the complaint 
    complaint = ClientComplaint.objects.get(id='29dd0634460d4c839fccd48f995c17e4')
    print(f"Complaint ID: {complaint.id}")
    
    # Get user's comments
    user_comments = ClientComplaintComment.objects.filter(
        author=user, 
        complaint=complaint
    ).order_by('-id')[:5]
    
    print(f"\nUser's recent comments:")
    for comment in user_comments:
        print(f"  Comment ID {comment.id}: '{comment.comment[:30]}...' is_internal={comment.is_internal}")
    
    # Test the delete logic for each comment type
    print(f"\n=== Delete Permission Tests ===")
    print(f"User ID: {user.id}")
    print(f"User Role: {user.role}")
    
    for comment in user_comments:
        # This mimics the frontend logic
        userRole = user.role
        currentUserId = str(user.id)
        
        # Admin can delete any
        if userRole == 'admin':
            can_delete = True
            reason = "Admin role"
        # Employee/Manager can only delete their own internal comments
        elif userRole in ['employee', 'manager']:
            comment_type = 'internal_comment' if comment.is_internal else 'external_comment'
            author_matches = str(comment.author.id) == currentUserId
            can_delete = comment_type == 'internal_comment' and author_matches
            reason = f"Employee role: type={comment_type}, author_matches={author_matches}"
        else:
            can_delete = False
            reason = "Unknown role"
            
        print(f"  Comment {comment.id} ({comment.comment[:20]}...): CAN_DELETE={can_delete} ({reason})")

if __name__ == "__main__":
    test_delete_logic()