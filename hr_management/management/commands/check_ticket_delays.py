"""
Django management command to check and update ticket delays
Run this command hourly via cron or celery beat
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from hr_management.models import ClientComplaint
from hr_management.ticket_automation import TicketStatusManager
from hr_management.notifications import NotificationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check all active tickets for delays and auto-close resolved tickets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making any changes to the database',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write(self.style.SUCCESS(f'Starting ticket delay check at {timezone.now()}'))
        
        # Get all active complaints (not closed permanently)
        active_complaints = ClientComplaint.objects.exclude(
            status='closed',
            automated_status__in=[
                TicketStatusManager.STATUS_AUTO_CLOSED,
                None
            ]
        )
        
        delayed_count = 0
        auto_closed_count = 0
        notifications_sent = 0
        
        for complaint in active_complaints:
            if verbose:
                self.stdout.write(f'  Checking complaint {complaint.id} - {complaint.title}')
            
            # Check for delays
            was_delayed_before = complaint.delay_status is not None
            
            if not dry_run:
                is_now_delayed = TicketStatusManager.check_and_update_delays(complaint)
                
                # Send notification if newly delayed
                if is_now_delayed and not was_delayed_before:
                    try:
                        if complaint.delay_status == TicketStatusManager.STATUS_DELAYED_SYSTEM:
                            NotificationService.notify_system_delay(complaint)
                        elif complaint.delay_status == TicketStatusManager.STATUS_DELAYED_CLIENT:
                            NotificationService.notify_client_delay(complaint)
                        notifications_sent += 1
                    except Exception as e:
                        logger.error(f'Failed to send delay notification for complaint {complaint.id}: {e}')
                
                if is_now_delayed:
                    delayed_count += 1
                    if verbose:
                        self.stdout.write(self.style.WARNING(f'    → Marked as delayed'))
            else:
                # Dry run - just check and report
                time_info = TicketStatusManager.calculate_time_until_delay(complaint)
                if time_info and time_info['is_delayed']:
                    delayed_count += 1
                    self.stdout.write(self.style.WARNING(
                        f'    → Would mark as delayed (threshold: {time_info["threshold_hours"]}h)'
                    ))
            
            # Check for auto-close
            if complaint.automated_status == TicketStatusManager.STATUS_RESOLVED_PENDING:
                if not dry_run:
                    was_closed = TicketStatusManager.check_auto_close(complaint)
                    if was_closed:
                        auto_closed_count += 1
                        try:
                            NotificationService.notify_auto_closed(complaint)
                            notifications_sent += 1
                        except Exception as e:
                            logger.error(f'Failed to send auto-close notification for complaint {complaint.id}: {e}')
                        
                        if verbose:
                            self.stdout.write(self.style.WARNING(f'    → Auto-closed'))
                else:
                    # Check if would be auto-closed
                    thresholds = TicketStatusManager.get_thresholds_for_complaint(complaint)
                    time_since = timezone.now() - complaint.last_response_time
                    hours_since = time_since.total_seconds() / 3600
                    if hours_since >= thresholds.auto_close_hours:
                        auto_closed_count += 1
                        self.stdout.write(self.style.WARNING(
                            f'    → Would auto-close (resolved {hours_since:.1f}h ago)'
                        ))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n✓ Ticket delay check complete'))
        self.stdout.write(f'  Total tickets checked: {active_complaints.count()}')
        self.stdout.write(f'  Tickets marked as delayed: {delayed_count}')
        self.stdout.write(f'  Tickets auto-closed: {auto_closed_count}')
        self.stdout.write(f'  Notifications sent: {notifications_sent}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠ DRY RUN - No changes were made'))
