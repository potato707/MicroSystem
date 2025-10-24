#!/usr/bin/env python
import os
import sys
import django

# Add the MicroSystem directory to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint

def test_client_name_fix():
    print("=== Testing Client Name Fix ===")
    
    # Get the complaint 
    complaint = ClientComplaint.objects.get(id='24629837bb8347e182d7a98cb090c7c2')
    
    # Test the updated serializer logic manually
    admin_comments = complaint.comments.filter(is_internal=False).order_by('created_at')
    
    print("Admin comments (non-internal):")
    for comment in admin_comments:
        # Apply the same logic as the updated serializer
        if comment.author:
            author_name = comment.author.name.strip() if comment.author.name else ''
            if not author_name:
                author_name = comment.author.username or 'Admin'
        else:
            author_name = 'Admin'
            
        print(f"  Comment ID {comment.id}:")
        print(f"    Original name: '{comment.author.name if comment.author else 'None'}'")
        print(f"    Username: '{comment.author.username if comment.author else 'None'}'")
        print(f"    Final author_name: '{author_name}'")
        print(f"    Comment: '{comment.comment}'")
        print()

if __name__ == "__main__":
    test_client_name_fix()