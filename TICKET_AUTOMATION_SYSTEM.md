# Automated Ticket Status Management System

## 📋 Overview

A fully automated, time-aware ticket management system with priority-based delay handling and smart notifications. This system automatically tracks response times, updates ticket statuses, and sends notifications to the appropriate parties.

## ✨ Features

### 1. **Automatic Status Transitions**
- **Waiting for System Response**: Client has submitted or replied, system must respond next
- **Waiting for Client Response**: System has replied, client must respond next  
- **Delayed by System**: System exceeded allowed response time
- **Delayed by Client**: Client exceeded allowed response time
- **Resolved / Awaiting Confirmation**: System marked ticket as solved, waiting for client confirmation
- **Auto-Closed**: Client didn't confirm within allowed time, ticket automatically closed
- **Reopened**: Client replied after closure, automatically returns to "Waiting for System Response"

### 2. **Priority-Based Thresholds**

| Priority | System Delay | Client Delay | Auto-Close Time |
|----------|--------------|--------------|-----------------|
| Urgent   | 4 hours      | 8 hours      | 12 hours        |
| High     | 12 hours     | 24 hours     | 24 hours        |
| Normal   | 24 hours     | 48 hours     | 48 hours        |
| Low      | 48 hours     | 72 hours     | 72 hours        |

### 3. **Smart Notifications**
- **System Delayed**: Notifies admin/support team
- **Client Delayed**: Notifies client
- **Resolved**: Notifies client to confirm resolution
- **Auto-Closed**: Notifies client about closure
- **Reopened**: Notifies both client and admin

### 4. **Flexible Threshold Management**
- Global default thresholds
- Priority-specific thresholds
- Per-ticket custom thresholds

## 🗄️ Database Models

### TicketDelayThreshold
Stores threshold configurations for response times.

```python
Fields:
- threshold_type: 'global' | 'priority' | 'custom'
- priority: 'urgent' | 'high' | 'normal' | 'low' (for priority-based)
- system_response_hours: Hours allowed for system response
- client_response_hours: Hours allowed for client response
- auto_close_hours: Hours after resolution before auto-close
- is_active: Boolean flag
```

### ClientComplaint (Updated)
Added new fields for automation:

```python
New Fields:
- last_response_time: DateTime of last response
- last_responder: 'client' | 'system'
- automated_status: Current automated status
- delay_status: Delay flag ('delayed_by_system' | 'delayed_by_client')
- custom_threshold: FK to TicketDelayThreshold (optional)
```

## 🔄 Automatic Status Flow

```
New Complaint
    ↓
[Waiting for System Response]
    ↓ (system replies)
[Waiting for Client Response]
    ↓ (client replies)
[Waiting for System Response]
    ...
    ↓ (marked resolved)
[Resolved - Awaiting Confirmation]
    ↓ (no response after X hours)
[Auto-Closed]
    ↓ (client replies)
[Reopened] → back to [Waiting for System Response]
```

## 🚀 Setup & Installation

### 1. Database Migration
```bash
# Already applied - migration 0048
python manage.py migrate hr_management
```

### 2. Initialize Default Thresholds
```bash
python manage.py init_ticket_thresholds
```

This creates:
- 1 global default threshold
- 4 priority-specific thresholds (urgent, high, normal, low)

### 3. Setup Background Scheduler

#### Option A: Cron Job (Recommended for Production)
```bash
# Edit crontab
crontab -e

# Add this line to run every hour
0 * * * * cd /path/to/project && python manage.py check_ticket_delays
```

#### Option B: Celery Beat (For Django Projects with Celery)
```python
# In your celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'check-ticket-delays': {
        'task': 'hr_management.tasks.check_ticket_delays',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

### 4. Test the System
```bash
# Dry run to see what would happen
python manage.py check_ticket_delays --dry-run --verbose

# Actual run
python manage.py check_ticket_delays --verbose
```

## 📡 API Endpoints

### Threshold Management

#### List All Thresholds
```http
GET /hr/ticket-thresholds/
```

#### Get Specific Threshold
```http
GET /hr/ticket-thresholds/{id}/
```

#### Create Threshold (Admin Only)
```http
POST /hr/ticket-thresholds/
Content-Type: application/json

{
  "threshold_type": "priority",
  "priority": "high",
  "system_response_hours": 12,
  "client_response_hours": 24,
  "auto_close_hours": 24
}
```

#### Update Threshold (Admin Only)
```http
PUT /hr/ticket-thresholds/{id}/
PATCH /hr/ticket-thresholds/{id}/
```

#### Delete Threshold (Admin Only)
```http
DELETE /hr/ticket-thresholds/{id}/
```

### Statistics

#### Get Automation Stats
```http
GET /hr/ticket-automation/stats/

Response:
{
  "total_active_tickets": 45,
  "waiting_for_system": 12,
  "waiting_for_client": 18,
  "delayed_by_system": 3,
  "delayed_by_client": 8,
  "resolved_pending_confirmation": 4,
  "reopened": 0,
  "auto_closed_last_24h": 5
}
```

## 🔧 Integration Points

### Automatic Triggers

#### 1. Client Submits Complaint
```python
# In ClientSubmitComplaintView
complaint.last_responder = 'client'
complaint.last_response_time = timezone.now()
complaint.automated_status = 'waiting_for_system_response'
```

#### 2. Client Replies
```python
# In ClientComplaintAddReplyView
TicketStatusManager.transition_on_client_response(complaint)
NotificationService.notify_new_client_message(complaint)
```

#### 3. System/Admin Replies
```python
# In ClientComplaintCommentViewSet
TicketStatusManager.transition_on_system_response(complaint)
NotificationService.notify_new_system_message(complaint)
```

#### 4. Background Check (Hourly)
```python
# Via management command
for complaint in active_complaints:
    TicketStatusManager.check_and_update_delays(complaint)
    TicketStatusManager.check_auto_close(complaint)
```

## 📧 Email Notifications

### Configuration
Emails are sent using Django's email backend. Configure in `settings.py`:

```python
# Development (prints to console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Production (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@company.com'
```

### Notification Types

1. **System Delay Alert** (to admins)
   - Subject: "⚠️ Delayed Response Required - Ticket #..."
   - Triggered when system exceeds response threshold

2. **Client Delay Reminder** (to client)
   - Subject: "Waiting for your response - Ticket #..."
   - Triggered when client exceeds response threshold

3. **Resolved Notification** (to client)
   - Subject: "✅ Your ticket has been resolved - #..."
   - Triggered when ticket marked as resolved

4. **Auto-Close Notification** (to client)
   - Subject: "Ticket auto-closed - #..."
   - Triggered when ticket auto-closes

5. **Reopened Alert** (to both)
   - Subject: "🔄 Ticket Reopened - #..."
   - Triggered when client replies after closure

## 🎯 Usage Examples

### Example 1: Customize Urgent Priority Threshold
```python
# Via API or Django shell
threshold = TicketDelayThreshold.objects.get(
    threshold_type='priority',
    priority='urgent'
)
threshold.system_response_hours = 2  # Change from 4 to 2 hours
threshold.save()
```

### Example 2: Set Custom Threshold for Specific Ticket
```python
# Create custom threshold
custom_threshold = TicketDelayThreshold.objects.create(
    threshold_type='custom',
    system_response_hours=1,
    client_response_hours=6,
    auto_close_hours=12
)

# Assign to complaint
complaint.custom_threshold = custom_threshold
complaint.save()
```

### Example 3: Check Time Until Delay
```python
from hr_management.ticket_automation import TicketStatusManager

time_info = TicketStatusManager.calculate_time_until_delay(complaint)
# Returns:
# {
#     'hours_remaining': 2.5,
#     'is_delayed': False,
#     'threshold_hours': 24
# }
```

### Example 4: Manual Status Transition
```python
from hr_management.ticket_automation import TicketStatusManager

# When marking ticket as resolved
TicketStatusManager.transition_to_resolved(complaint)

# When client responds
TicketStatusManager.transition_on_client_response(complaint)

# When admin responds
TicketStatusManager.transition_on_system_response(complaint)
```

## 🧪 Testing

### Test Scenarios

1. **Test Delay Detection**
   ```bash
   python manage.py check_ticket_delays --dry-run --verbose
   ```

2. **Test Auto-Close**
   - Create a ticket
   - Mark it as resolved
   - Wait past auto-close threshold (or manually update timestamps)
   - Run: `python manage.py check_ticket_delays`

3. **Test Reopening**
   - Auto-close a ticket
   - Submit a client reply
   - Verify status changes to "reopened"

4. **Test Notifications**
   - Monitor console (development) or email logs (production)
   - Verify notifications sent at correct times

## 📊 Monitoring & Metrics

### Key Metrics to Track

1. **Average Response Time**
   - System response time per priority
   - Client response time per priority

2. **SLA Compliance**
   - % of tickets responded within threshold
   - Number of delayed tickets per day/week

3. **Auto-Close Rate**
   - % of tickets auto-closed
   - Average time to auto-close

4. **Reopen Rate**
   - % of tickets reopened after closure
   - Common reasons for reopening

### Dashboard Queries

```python
# Get delayed tickets
delayed = ClientComplaint.objects.filter(
    delay_status__isnull=False
).count()

# Get tickets by automated status
status_breakdown = ClientComplaint.objects.values(
    'automated_status'
).annotate(count=Count('id'))

# Average resolution time
from django.db.models import Avg, F
avg_resolution = ClientComplaint.objects.filter(
    resolved_at__isnull=False
).aggregate(
    avg_hours=Avg(F('resolved_at') - F('created_at'))
)
```

## 🔒 Security & Permissions

- **Threshold Management**: Admin only
- **View Thresholds**: All authenticated users
- **Automation Stats**: All authenticated users
- **Manual Commands**: Server access required

## 🐛 Troubleshooting

### Issue: Notifications not sending
**Solution**: Check EMAIL_BACKEND configuration and credentials

### Issue: Delays not being detected
**Solution**: Verify cron job is running, check last_response_time is set

### Issue: Wrong thresholds applied
**Solution**: Check priority mapping and custom_threshold field

### Issue: Tickets not auto-closing
**Solution**: Ensure automated_status is 'resolved_awaiting_confirmation'

## 📝 Files Created/Modified

### New Files
- `hr_management/ticket_automation.py` - Core automation logic
- `hr_management/notifications.py` - Notification service
- `hr_management/management/commands/check_ticket_delays.py` - Scheduler command
- `hr_management/management/commands/init_ticket_thresholds.py` - Init command
- `hr_management/migrations/0048_*.py` - Database migration

### Modified Files
- `hr_management/models.py` - Added TicketDelayThreshold, updated ClientComplaint
- `hr_management/serializers.py` - Added TicketDelayThresholdSerializer
- `hr_management/views.py` - Added threshold management views
- `hr_management/urls.py` - Added new URL patterns
- `hr_management/client_dashboard_views.py` - Integrated status transitions
- `MicroSystem/settings.py` - Added FRONTEND_URL setting

## 🚀 Future Enhancements

1. **Machine Learning**: Predict resolution time based on historical data
2. **Escalation Rules**: Auto-escalate severely delayed tickets
3. **Business Hours**: Only count delays during business hours
4. **SLA Reports**: Generate monthly SLA compliance reports
5. **Webhook Integration**: Notify external systems (Slack, Teams, etc.)
6. **Client Satisfaction**: Auto-send satisfaction surveys after resolution

## ✅ Completion Checklist

- [x] Database models created
- [x] Migration applied
- [x] Default thresholds initialized
- [x] Status transition logic implemented
- [x] Background scheduler created
- [x] Notification system built
- [x] API endpoints added
- [x] Integration with existing endpoints
- [x] Documentation completed
- [ ] Frontend UI for delay indicators (next step)
- [ ] Comprehensive testing
- [ ] Production deployment

## 📞 Support

For issues or questions, contact the development team or refer to:
- Django documentation: https://docs.djangoproject.com/
- Project GitHub: [your-repo-url]
