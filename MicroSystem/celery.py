"""
Celery configuration for automated background tasks
"""
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')

app = Celery('MicroSystem')

# Load config from Django settings with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()


# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    # Check SSL expiry daily at 3 AM
    'check-ssl-expiry-daily': {
        'task': 'hr_management.ssl_tasks.check_ssl_expiry',
        'schedule': crontab(hour=3, minute=0),
    },
    
    # Cleanup failed SSL attempts daily at 4 AM
    'cleanup-failed-ssl-daily': {
        'task': 'hr_management.ssl_tasks.cleanup_failed_ssl_attempts',
        'schedule': crontab(hour=4, minute=0),
    },
}


@app.task(bind=True)
def debug_task(self):
    """Debug task to test Celery"""
    print(f'Request: {self.request!r}')
