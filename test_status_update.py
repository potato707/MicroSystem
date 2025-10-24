#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import ClientComplaint

# Check the complaint status
complaint_id = '812c7c0b-c3b9-4c84-b99c-b0431e13095f'
complaint = ClientComplaint.objects.get(id=complaint_id)

print(f"Complaint ID: {complaint.id}")
print(f"automated_status: {complaint.automated_status}")
print(f"last_responder: {complaint.last_responder}")
print(f"last_response_time: {complaint.last_response_time}")
print(f"delay_status: {complaint.delay_status}")
print(f"status: {complaint.status}")
print(f"custom_status: {complaint.custom_status}")
