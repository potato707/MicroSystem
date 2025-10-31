#!/usr/bin/env python
"""
Test script to check if user is authenticated and is staff
"""
import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, '/home/ahmedyasser/lab/Saas/Second attempt/MicroSystem')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

User = get_user_model()

def check_session(session_key):
    """Check if session is valid and get user info"""
    try:
        session = Session.objects.get(session_key=session_key)
        
        if session.expire_date < timezone.now():
            print("❌ Session expired")
            return None
        
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        
        if not user_id:
            print("❌ No user in session")
            return None
        
        user = User.objects.get(pk=user_id)
        
        print(f"✓ User found: {user.username}")
        print(f"  - Email: {user.email}")
        print(f"  - Is staff: {user.is_staff}")
        print(f"  - Is superuser: {user.is_superuser}")
        print(f"  - Is active: {user.is_active}")
        
        if not user.is_staff:
            print("\n⚠️  User is NOT staff - will not have permission to update tenants")
        else:
            print("\n✓ User is staff - has permission to update tenants")
        
        return user
        
    except Session.DoesNotExist:
        print("❌ Session not found")
        return None
    except User.DoesNotExist:
        print("❌ User not found")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == '__main__':
    # Session key from the cookie
    session_key = 'fr2fdepumm1qezzvkgd6i6xfqzdyf1ui'
    
    print("Checking session...")
    print("-" * 50)
    user = check_session(session_key)
    
    if user and not user.is_staff:
        print("\n" + "=" * 50)
        print("TO FIX: Make user staff")
        print("=" * 50)
        print(f"\nIn Django shell:")
        print(f"  from django.contrib.auth import get_user_model")
        print(f"  User = get_user_model()")
        print(f"  user = User.objects.get(username='{user.username}')")
        print(f"  user.is_staff = True")
        print(f"  user.save()")
