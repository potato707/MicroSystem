"""
Helper functions for client authentication and verification
"""
from .models import GlobalClient


def is_global_client(user):
    """Check if user is a GlobalClient instance"""
    return isinstance(user, GlobalClient)


def verify_client_role(user):
    """
    Verify if user is a client (GlobalClient or legacy User with role='client')
    Returns True if user is a valid client, False otherwise
    """
    # Check if it's a GlobalClient (new system)
    if is_global_client(user):
        return True
    
    # Check if it's a legacy User with role='client' (old system)
    if hasattr(user, 'role') and user.role == 'client':
        return True
    
    return False


def get_client_email(user):
    """
    Get client email whether it's GlobalClient or legacy User
    """
    return user.email


def get_client_complaints(user):
    """
    Get all complaints for a client by their email
    Works for both GlobalClient and legacy User
    """
    from .models import ClientComplaint
    client_email = get_client_email(user)
    return ClientComplaint.objects.filter(client_email=client_email)
