"""
Email notification utilities for client portal
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from .models import ClientComplaint, ClientComplaintAccessToken


def send_client_portal_access_email(complaint, portal_url, access_token):
    """
    Send email to client with secure portal access link
    """
    subject = f"Access Your Complaint Status - {complaint.title}"
    
    # Plain text message
    message = f"""
Hello {complaint.client_name},

You can now track the status of your complaint and communicate with our team using the secure link below:

Complaint: {complaint.title}
Reference ID: {complaint.id}
Priority: {complaint.get_priority_display()}
Status: {complaint.get_status_display()}

Secure Access Link:
{portal_url}

This link will allow you to:
- View your complaint status and progress
- See task completion statistics
- Reply with additional information
- Track resolution progress

Link Details:
- Valid until: {access_token.expires_at.strftime('%B %d, %Y')}
- Secure token: This link is unique to your complaint

If you have any questions or need assistance, please don't hesitate to contact us.

Best regards,
The Support Team
    """
    
    # HTML message (optional - could create an HTML template)
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">Your Complaint Status Portal</h2>
            
            <p>Hello {complaint.client_name},</p>
            
            <p>You can now track the status of your complaint and communicate with our team using the secure link below:</p>
            
            <div style="background: #f8fafc; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>Complaint:</strong> {complaint.title}<br>
                <strong>Reference ID:</strong> {complaint.id}<br>
                <strong>Priority:</strong> {complaint.get_priority_display()}<br>
                <strong>Status:</strong> {complaint.get_status_display()}
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{portal_url}" 
                   style="background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Access Your Complaint Portal
                </a>
            </div>
            
            <h3>What you can do:</h3>
            <ul>
                <li>View your complaint status and progress</li>
                <li>See task completion statistics</li>
                <li>Reply with additional information</li>
                <li>Track resolution progress</li>
            </ul>
            
            <div style="background: #fef3c7; padding: 10px; border-radius: 5px; margin: 20px 0;">
                <strong>Link Details:</strong><br>
                Valid until: {access_token.expires_at.strftime('%B %d, %Y')}<br>
                This link is secure and unique to your complaint.
            </div>
            
            <p>If you have any questions or need assistance, please don't hesitate to contact us.</p>
            
            <p>Best regards,<br>The Support Team</p>
        </div>
    </body>
    </html>
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com'),
            recipient_list=[complaint.client_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send email to {complaint.client_email}: {e}")
        return False


def send_client_reply_notification_email(complaint, reply):
    """
    Send notification to admins when client submits a reply
    """
    subject = f"New Client Reply - {complaint.title}"
    
    message = f"""
A client has submitted a new reply to their complaint:

Complaint: {complaint.title}
Client: {reply.client_name} ({reply.client_email})
Reference ID: {complaint.id}

Reply:
{reply.reply_text}

Please log in to the admin panel to review and respond to this message.

Time: {reply.created_at.strftime('%B %d, %Y at %I:%M %p')}
    """
    
    # Get admin emails (you might want to customize this)
    admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', ['admin@company.com'])
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com'),
            recipient_list=admin_emails,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
        return False


def send_admin_response_notification_email(complaint, reply):
    """
    Send notification to client when admin responds to their reply
    """
    if not reply.admin_response:
        return False
        
    subject = f"Response to Your Message - {complaint.title}"
    
    message = f"""
Hello {complaint.client_name},

We have responded to your recent message regarding your complaint:

Complaint: {complaint.title}
Reference ID: {complaint.id}

Your Message:
{reply.reply_text}

Our Response:
{reply.admin_response}

You can continue the conversation by visiting your complaint portal:
[Portal link would be included here]

Thank you for your patience.

Best regards,
The Support Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@company.com'),
            recipient_list=[complaint.client_email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send response notification to {complaint.client_email}: {e}")
        return False