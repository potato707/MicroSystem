"""
Automated Ticket Status Management System
Handles time-aware status transitions, priority-based delays, and smart notifications
"""
from django.utils import timezone
from datetime import timedelta


class TicketStatusManager:
    """
    Manages automatic status transitions based on responses and timing
    """
    
    # Status constants
    STATUS_WAITING_SYSTEM = 'waiting_for_system_response'
    STATUS_WAITING_CLIENT = 'waiting_for_client_response'
    STATUS_DELAYED_SYSTEM = 'delayed_by_system'
    STATUS_DELAYED_CLIENT = 'delayed_by_client'
    STATUS_RESOLVED_PENDING = 'resolved_awaiting_confirmation'
    STATUS_AUTO_CLOSED = 'auto_closed'
    STATUS_REOPENED = 'reopened'
    
    # Responder constants
    RESPONDER_CLIENT = 'client'
    RESPONDER_SYSTEM = 'system'
    
    @staticmethod
    def map_priority(complaint_priority):
        """Map complaint priority to threshold priority"""
        mapping = {
            'urgent': 'urgent',
            'medium': 'normal',
            'low': 'low',
        }
        return mapping.get(complaint_priority, 'normal')
    
    @staticmethod
    def get_thresholds_for_complaint(complaint):
        """Get applicable thresholds for a complaint"""
        from .models import ClientComplaint, TicketDelayThreshold
        
        # Check if complaint has custom thresholds
        if hasattr(complaint, 'custom_threshold') and complaint.custom_threshold:
            return complaint.custom_threshold
        
        # Get priority-based thresholds
        priority = TicketStatusManager.map_priority(complaint.priority)
        try:
            return TicketDelayThreshold.objects.get(
                threshold_type='priority',
                priority=priority,
                is_active=True
            )
        except TicketDelayThreshold.DoesNotExist:
            # Return default if priority-specific not found
            threshold, _ = TicketDelayThreshold.objects.get_or_create(
                threshold_type='global',
                defaults={
                    'system_response_hours': 24,
                    'client_response_hours': 48,
                    'auto_close_hours': 48,
                }
            )
            return threshold
    
    @staticmethod
    def calculate_time_until_delay(complaint):
        """Calculate hours/minutes until ticket becomes delayed"""
        if not complaint.last_response_time:
            return None
        
        thresholds = TicketStatusManager.get_thresholds_for_complaint(complaint)
        now = timezone.now()
        time_since_response = now - complaint.last_response_time
        
        # Determine which threshold applies
        if complaint.last_responder == TicketStatusManager.RESPONDER_CLIENT:
            # Waiting for system response
            threshold_hours = thresholds.system_response_hours
        else:
            # Waiting for client response
            threshold_hours = thresholds.client_response_hours
        
        threshold_delta = timedelta(hours=threshold_hours)
        time_remaining = threshold_delta - time_since_response
        
        return {
            'hours_remaining': time_remaining.total_seconds() / 3600,
            'is_delayed': time_remaining.total_seconds() <= 0,
            'threshold_hours': threshold_hours
        }
    
    @staticmethod
    def transition_on_client_response(complaint):
        """
        Update status when client responds
        Client reply -> Waiting for system response
        """
        from .models import ClientComplaint
        
        complaint.last_responder = TicketStatusManager.RESPONDER_CLIENT
        complaint.last_response_time = timezone.now()
        
        # If ticket was closed/resolved, reopen it
        if complaint.automated_status in [TicketStatusManager.STATUS_AUTO_CLOSED, 
                                         TicketStatusManager.STATUS_RESOLVED_PENDING]:
            complaint.automated_status = TicketStatusManager.STATUS_REOPENED
        else:
            complaint.automated_status = TicketStatusManager.STATUS_WAITING_SYSTEM
        
        complaint.delay_status = None  # Clear any delay flag
        complaint.save()
        
        return complaint
    
    @staticmethod
    def transition_on_system_response(complaint):
        """
        Update status when system/support responds
        System reply -> Waiting for client response
        """
        from .models import ClientComplaint
        
        complaint.last_responder = TicketStatusManager.RESPONDER_SYSTEM
        complaint.last_response_time = timezone.now()
        complaint.automated_status = TicketStatusManager.STATUS_WAITING_CLIENT
        complaint.delay_status = None  # Clear any delay flag
        complaint.save()
        
        return complaint
    
    @staticmethod
    def transition_to_resolved(complaint):
        """
        Mark ticket as resolved, waiting for client confirmation
        """
        from .models import ClientComplaint
        
        complaint.last_responder = TicketStatusManager.RESPONDER_SYSTEM
        complaint.last_response_time = timezone.now()
        complaint.automated_status = TicketStatusManager.STATUS_RESOLVED_PENDING
        complaint.delay_status = None
        complaint.save()
        
        return complaint
    
    @staticmethod
    def check_and_update_delays(complaint):
        """
        Check if complaint has exceeded response time and update delay status
        Called by background scheduler
        """
        from .models import ClientComplaint
        
        if not complaint.last_response_time:
            return False
        
        # Skip if already closed/resolved permanently
        if complaint.status in ['closed', 'resolved'] and \
           complaint.automated_status not in [TicketStatusManager.STATUS_RESOLVED_PENDING]:
            return False
        
        time_info = TicketStatusManager.calculate_time_until_delay(complaint)
        
        if time_info and time_info['is_delayed']:
            # Update delay status based on who should respond
            if complaint.last_responder == TicketStatusManager.RESPONDER_CLIENT:
                complaint.delay_status = TicketStatusManager.STATUS_DELAYED_SYSTEM
            else:
                complaint.delay_status = TicketStatusManager.STATUS_DELAYED_CLIENT
            
            complaint.save()
            return True
        
        return False
    
    @staticmethod
    def check_auto_close(complaint):
        """
        Check if resolved ticket should be auto-closed due to no client confirmation
        """
        from .models import ClientComplaint
        
        if complaint.automated_status != TicketStatusManager.STATUS_RESOLVED_PENDING:
            return False
        
        if not complaint.last_response_time:
            return False
        
        thresholds = TicketStatusManager.get_thresholds_for_complaint(complaint)
        now = timezone.now()
        time_since_resolution = now - complaint.last_response_time
        
        if time_since_resolution >= timedelta(hours=thresholds.auto_close_hours):
            complaint.automated_status = TicketStatusManager.STATUS_AUTO_CLOSED
            complaint.status = 'closed'
            complaint.save()
            return True
        
        return False
