# 🎯 Automated Ticket System - Quick Reference

## ✅ Status: PRODUCTION READY

### What's Working Right Now

✓ Database models created and migrated  
✓ 5 default thresholds initialized (1 global + 4 priorities)  
✓ Automatic status transitions on every reply  
✓ Background delay checker ready  
✓ Email notification system ready  
✓ Admin API for threshold management  
✓ Statistics endpoint  
✓ Zero breaking changes - all existing code works  

---

## 🚀 Quick Commands

### Test the System
```bash
# See what would happen (safe - no changes)
python manage.py check_ticket_delays --dry-run --verbose

# Actually run it
python manage.py check_ticket_delays
```

### View Thresholds
```python
python manage.py shell
>>> from hr_management.models import TicketDelayThreshold
>>> TicketDelayThreshold.objects.all()
```

### Setup Hourly Checks
```bash
# Edit crontab
crontab -e

# Add this line
0 * * * * cd /home/ahmedyasser/lab/MicroSystem && python manage.py check_ticket_delays
```

---

## 📡 API Endpoints

### Thresholds
```
GET    /hr/ticket-thresholds/           List all
GET    /hr/ticket-thresholds/{id}/      Get one
POST   /hr/ticket-thresholds/           Create (admin)
PUT    /hr/ticket-thresholds/{id}/      Update (admin)
DELETE /hr/ticket-thresholds/{id}/      Delete (admin)
```

### Stats
```
GET    /hr/ticket-automation/stats/     Get statistics
```

---

## ⏱️ Default Thresholds

| Priority | System Delay | Client Delay | Auto-Close |
|----------|--------------|--------------|------------|
| Urgent   | 4 hours      | 8 hours      | 12 hours   |
| High     | 12 hours     | 24 hours     | 24 hours   |
| Normal   | 24 hours     | 48 hours     | 48 hours   |
| Low      | 48 hours     | 72 hours     | 72 hours   |

---

## 🔄 Automatic Status Flow

```
Client Submits Complaint
    ↓
[Waiting for System] ← last_responder = client
    ↓ Admin/Support Replies
[Waiting for Client] ← last_responder = system
    ↓ Client Replies
[Waiting for System]
    ↓ (continues...)
    ↓ Marked Resolved
[Resolved - Awaiting Confirmation]
    ↓ No response after X hours
[Auto-Closed]
    ↓ Client replies
[Reopened] → back to [Waiting for System]
```

---

## 📧 Email Notifications

### When Sent Automatically

1. **System Delayed** → Admins notified  
2. **Client Delayed** → Client reminded  
3. **Ticket Resolved** → Client asked to confirm  
4. **Auto-Closed** → Client informed  
5. **Reopened** → Both client & admin notified  
6. **New Client Message** → Admins alerted  
7. **New System Message** → Client notified  

### Current Setup
- Development: Emails print to console
- Production: Configure SMTP in `settings.py`

---

## 🎯 What Happens Automatically

### When Client Submits/Replies
- ✓ `last_responder` = 'client'
- ✓ `last_response_time` = now
- ✓ `automated_status` = 'waiting_for_system_response'
- ✓ Admins notified

### When Admin/Support Replies  
- ✓ `last_responder` = 'system'
- ✓ `last_response_time` = now
- ✓ `automated_status` = 'waiting_for_client_response'
- ✓ Client notified

### Every Hour (via cron)
- ✓ Check all active tickets
- ✓ Calculate time since last response
- ✓ Compare to priority thresholds
- ✓ Mark as delayed if exceeded
- ✓ Send delay notifications
- ✓ Auto-close resolved tickets

---

## 🔧 Quick Configurations

### Update Urgent Threshold
```bash
curl -X PATCH http://localhost:8000/hr/ticket-thresholds/{id}/ \
  -H "Authorization: Bearer {token}" \
  -d '{"system_response_hours": 2}'
```

### Get Stats
```bash
curl http://localhost:8000/hr/ticket-automation/stats/ \
  -H "Authorization: Bearer {token}"
```

---

## 📂 Files Reference

### Core Logic
- `hr_management/ticket_automation.py` - Status manager
- `hr_management/notifications.py` - Email service

### Commands
- `check_ticket_delays` - Hourly checker
- `init_ticket_thresholds` - Initialize defaults

### Integration
- `client_dashboard_views.py` - Client replies
- `views.py` - Admin comments
- `models.py` - Database schema

### Documentation
- `TICKET_AUTOMATION_COMPLETE.md` - Quick start
- `TICKET_AUTOMATION_SYSTEM.md` - Full docs

---

## ✨ Key Features

1. **Zero Breaking Changes**: All existing functionality preserved
2. **Automatic**: No manual intervention needed after setup
3. **Flexible**: Thresholds customizable per priority or per ticket
4. **Smart**: Tracks who responded last, calculates delays
5. **Notifies**: Right person, right time, right message
6. **Tested**: Dry-run mode for safe testing

---

## 🎬 Next Steps

1. ✅ **DONE**: Backend fully implemented
2. ⏱️ **TODO**: Setup cron job for hourly checks
3. ⏱️ **TODO**: Frontend delay indicators (optional)
4. ⏱️ **TODO**: Configure production SMTP (when ready)

---

## 📞 Quick Help

**Test Command Not Working?**
```bash
python manage.py check_ticket_delays --help
```

**See All Thresholds?**
```bash
python manage.py shell -c "from hr_management.models import TicketDelayThreshold; print([str(t) for t in TicketDelayThreshold.objects.all()])"
```

**Check Django Admin?**
- Browse to: http://localhost:8000/admin/
- Look for: "Ticket Delay Thresholds"

---

**System is ready! Just add the cron job and it runs itself.** 🚀
