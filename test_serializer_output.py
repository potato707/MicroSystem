#!/usr/bin/env python
import os
import sys
import django
import json

# Add the MicroSystem directory to the Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint
from hr_management.serializers import ClientComplaintSerializer

def test_serializer_output():
    print("=== Testing Serializer Comment Types ===")
    
    # Get the complaint 
    complaint = ClientComplaint.objects.get(id='29dd0634460d4c839fccd48f995c17e4')
    
    # Serialize it
    serializer = ClientComplaintSerializer(complaint)
    data = serializer.data
    
    # Check the comments
    comments = data.get('comments', [])
    print(f"Total comments returned: {len(comments)}")
    
    for comment in comments:  # Show all comments
        print(f"Comment ID: {comment['id']}")
        print(f"  Type: {comment['type']}")
        print(f"  Is Internal: {comment['is_internal']}")
        print(f"  Author ID: {comment.get('author_id', 'None')}")
        print(f"  Author Name: {comment.get('author_name', 'None')}")
        print(f"  Content: {comment['comment'][:50]}...")
        print()

if __name__ == "__main__":
    test_serializer_output()