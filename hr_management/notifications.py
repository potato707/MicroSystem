"""
Notification Service for Ticket Automation
Handles email and in-app notifications for ticket status changes
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from hr_management.ticket_automation import TicketStatusManager
import logging

logger = logging.getLogger(__name__)


def get_notification_model():
    """Lazy import to avoid circular dependency"""
    from hr_management.models import Notification
    return Notification


class NotificationService:
    """
    Centralized service for sending notifications about ticket status changes
    """
    
    @staticmethod
    def create_notification(recipient, complaint, notification_type, title, message):
        """Create an in-app notification"""
        try:
            Notification = get_notification_model()
            notification = Notification.objects.create(
                recipient=recipient,
                complaint=complaint,
                notification_type=notification_type,
                title=title,
                message=message
            )
            logger.info(f'Created notification for {recipient.username}: {title}')
            return notification
        except Exception as e:
            logger.error(f'Failed to create notification: {e}')
            return None
    
    @staticmethod
    def _send_email(subject, message, recipient_email, html_message=None):
        """Internal method to send email"""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f'Email sent to {recipient_email}: {subject}')
            return True
        except Exception as e:
            logger.error(f'Failed to send email to {recipient_email}: {e}')
            return False
    
    @staticmethod
    def _get_admin_users(complaint):
        """Get list of admin/support users responsible for this complaint"""
        users = []
        
        # Get assigned teams' members
        team_assignments = complaint.assignments.filter(is_active=True)
        for assignment in team_assignments:
            # Get team members' users
            team_members = assignment.team.memberships.select_related('employee__user').all()
            for membership in team_members:
                if membership.employee.user:
                    users.append(membership.employee.user)
        
        # Get directly assigned employees
        employee_assignments = complaint.employee_assignments.filter(is_active=True)
        for assignment in employee_assignments:
            if assignment.employee.user:
                users.append(assignment.employee.user)
        
        # Fallback to category handlers if no specific assignment
        if not users and complaint.category:
            # Get assigned teams for this category
            category_teams = complaint.category.assigned_teams.all()
            for team in category_teams:
                team_members = team.memberships.select_related('employee__user').all()
                for membership in team_members:
                    if membership.employee.user:
                        users.append(membership.employee.user)
        
        # Final fallback: notify only admins (not complaint admins, as they should only see assigned complaints)
        if not users:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            # Get all admins
            admin_users = User.objects.filter(role='admin')
            users.extend(list(admin_users))
            
            logger.info(f'No specific assignments for complaint {complaint.id}, notifying {admin_users.count()} admins only')
        
        # Remove duplicates (compare by id)
        unique_users = []
        seen_ids = set()
        for user in users:
            if user.id not in seen_ids:
                unique_users.append(user)
                seen_ids.add(user.id)
        
        return unique_users
    
    @staticmethod
    def _get_admin_emails(complaint):
        """Get list of admin/support emails responsible for this complaint"""
        users = NotificationService._get_admin_users(complaint)
        return [user.email for user in users if user.email]
    
    @staticmethod
    def notify_system_delay(complaint):
        """
        Notify admin/support team that system response is delayed
        """
        admin_emails = NotificationService._get_admin_emails(complaint)
        
        if not admin_emails:
            logger.warning(f'No admin emails found for complaint {complaint.id}')
            return False
        
        thresholds = TicketStatusManager.get_thresholds_for_complaint(complaint)
        time_since = timezone.now() - complaint.last_response_time if complaint.last_response_time else None
        hours_delayed = time_since.total_seconds() / 3600 if time_since else 0
        
        subject = f'⚠️ Delayed Response Required - Ticket #{complaint.id}'
        message = f"""
        Alert: System Response Delayed
        
        Ticket #{complaint.id}: {complaint.title}
        Client: {complaint.client_name} ({complaint.client_email})
        Priority: {complaint.priority.upper()}
        
        Expected response time: {thresholds.system_response_hours} hours
        Time since client's last message: {hours_delayed:.1f} hours
        
        This ticket requires immediate attention.
        
        View ticket: {settings.FRONTEND_URL}/complaints/{complaint.id}
        """
        
        for email in admin_emails:
            NotificationService._send_email(subject, message, email)
        
        return True
    
    @staticmethod
    def notify_client_delay(complaint):
        """
        Notify client that their response is overdue
        """
        if not complaint.client_email:
            return False
        
        thresholds = TicketStatusManager.get_thresholds_for_complaint(complaint)
        time_since = timezone.now() - complaint.last_response_time if complaint.last_response_time else None
        hours_delayed = time_since.total_seconds() / 3600 if time_since else 0
        
        subject = f'Waiting for your response - Ticket #{complaint.id}'
        message = f"""
        Dear {complaint.client_name},
        
        We're waiting for your response on ticket #{complaint.id}: {complaint.title}
        
        Our support team responded {hours_delayed:.1f} hours ago, but we haven't heard back from you yet.
        
        Please log in to your dashboard to view and respond to our message:
        {settings.FRONTEND_URL}/client/complaints/{complaint.id}
        
        If this issue has been resolved, please confirm so we can close the ticket.
        
        Thank you!
        """
        
        NotificationService._send_email(subject, message, complaint.client_email)
        return True
    
    @staticmethod
    def notify_resolved(complaint):
        """
        Notify client that ticket has been marked as resolved
        """
        if not complaint.client_email:
            return False
        
        thresholds = TicketStatusManager.get_thresholds_for_complaint(complaint)
        
        subject = f'✅ Your ticket has been resolved - #{complaint.id}'
        message = f"""
        Dear {complaint.client_name},
        
        Good news! Your ticket #{complaint.id}: {complaint.title} has been marked as resolved.
        
        Please review the resolution and confirm if the issue is fixed:
        {settings.FRONTEND_URL}/client/complaints/{complaint.id}
        
        If you're satisfied with the resolution, the ticket will be automatically closed in {thresholds.auto_close_hours} hours.
        
        If you still have issues, please reply to reopen the ticket.
        
        Thank you for your patience!
        """
        
        NotificationService._send_email(subject, message, complaint.client_email)
        return True
    
    @staticmethod
    def notify_auto_closed(complaint):
        """
        Notify client that ticket was auto-closed due to inactivity
        """
        if not complaint.client_email:
            return False
        
        subject = f'Ticket auto-closed - #{complaint.id}'
        message = f"""
        Dear {complaint.client_name},
        
        Your ticket #{complaint.id}: {complaint.title} has been automatically closed due to no response after resolution.
        
        We're glad we could help resolve your issue!
        
        If you need to reopen this ticket or have additional questions, simply reply to it:
        {settings.FRONTEND_URL}/client/complaints/{complaint.id}
        
        Thank you for using our support system!
        """
        
        NotificationService._send_email(subject, message, complaint.client_email)
        return True
    
    @staticmethod
    def notify_reopened(complaint):
        """
        Notify both client and admins that ticket was reopened
        """
        # Notify client
        if complaint.client_email:
            subject_client = f'Your ticket has been reopened - #{complaint.id}'
            message_client = f"""
            Dear {complaint.client_name},
            
            Your ticket #{complaint.id}: {complaint.title} has been reopened and is now being reviewed by our support team.
            
            We'll respond as soon as possible.
            
            View ticket: {settings.FRONTEND_URL}/client/complaints/{complaint.id}
            
            Thank you!
            """
            NotificationService._send_email(subject_client, message_client, complaint.client_email)
        
        # Notify admins
        admin_emails = NotificationService._get_admin_emails(complaint)
        if admin_emails:
            subject_admin = f'🔄 Ticket Reopened - #{complaint.id}'
            message_admin = f"""
            Alert: Ticket Reopened
            
            Ticket #{complaint.id}: {complaint.title}
            Client: {complaint.client_name} ({complaint.client_email})
            Priority: {complaint.priority.upper()}
            
            The client has responded after closure. Please review and respond.
            
            View ticket: {settings.FRONTEND_URL}/complaints/{complaint.id}
            """
            
            for email in admin_emails:
                NotificationService._send_email(subject_admin, message_admin, email)
        
        return True
    
    @staticmethod
    def notify_new_client_message(complaint):
        """
        Notify admins when client sends a new message
        """
        admin_users = NotificationService._get_admin_users(complaint)
        
        if not admin_users:
            return False
        
        subject = f'New client message - Ticket #{complaint.id}'
        title = f'رسالة جديدة من العميل - #{complaint.id}'
        message = f"""رسالة جديدة من {complaint.client_name} على الشكوى: {complaint.title}"""
        
        email_message = f"""
        New Message Received
        
        Ticket #{complaint.id}: {complaint.title}
        Client: {complaint.client_name} ({complaint.client_email})
        Priority: {complaint.priority.upper()}
        
        The client has sent a new message. Please respond promptly.
        
        View ticket: {settings.FRONTEND_URL}/complaints/{complaint.id}
        """
        
        for user in admin_users:
            # Create in-app notification
            NotificationService.create_notification(
                recipient=user,
                complaint=complaint,
                notification_type='new_message',
                title=title,
                message=message
            )
            
            # Send email
            if user.email:
                NotificationService._send_email(subject, email_message, user.email)
        
        return True
    
    @staticmethod
    def notify_new_system_message(complaint):
        """
        Notify client when support team sends a message
        """
        if not complaint.client_email:
            return False
        
        subject = f'New response from support - Ticket #{complaint.id}'
        title = f'رد جديد من فريق الدعم - #{complaint.id}'
        notification_message = f"""رد جديد على شكواك: {complaint.title}"""
        
        email_message = f"""
        Dear {complaint.client_name},
        
        Our support team has responded to your ticket #{complaint.id}: {complaint.title}
        
        Please log in to view the response and reply if needed:
        {settings.FRONTEND_URL}/client/complaints/{complaint.id}
        
        Thank you!
        """
        
        # Create in-app notification if client has a user account
        if complaint.client_user:
            NotificationService.create_notification(
                recipient=complaint.client_user,
                complaint=complaint,
                notification_type='new_message',
                title=title,
                message=notification_message
            )
        
        # Send email
        NotificationService._send_email(subject, email_message, complaint.client_email)
        return True
