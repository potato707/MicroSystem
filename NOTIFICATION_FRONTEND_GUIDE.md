# How to Check Notifications in the Frontend

## Current Implementation Status

### ✅ What's Working Now
The notification system currently sends **email notifications** only. There is no in-app notification UI or database yet.

### 📧 Email Notifications
When comments/replies are added to complaints, the system sends emails to:
1. Assigned team members
2. Directly assigned employees
3. Category handling teams (as fallback)

**How to verify email notifications:**

#### 1. Check Django Logs
```bash
cd /home/ahmedyasser/lab/MicroSystem
tail -f server.log | grep -i "email\|notification"
```

Look for messages like:
```
Email sent to user@example.com: New Client Message - Complaint Title
Failed to send email to user@example.com: [error message]
```

#### 2. Check Email Settings in Django
```bash
python manage.py shell
```

```python
from django.conf import settings

# Check email configuration
print("EMAIL_BACKEND:", settings.EMAIL_BACKEND)
print("EMAIL_HOST:", getattr(settings, 'EMAIL_HOST', 'Not set'))
print("EMAIL_PORT:", getattr(settings, 'EMAIL_PORT', 'Not set'))
print("EMAIL_USE_TLS:", getattr(settings, 'EMAIL_USE_TLS', False))
print("DEFAULT_FROM_EMAIL:", getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set'))
```

#### 3. Test Email Sending
```bash
python -c "
from django.core.mail import send_mail
from django.conf import settings
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

result = send_mail(
    'Test Email',
    'This is a test notification',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@example.com'],
    fail_silently=False,
)
print(f'Email sent: {result}')
"
```

## 🚀 Building an In-App Notification System

If you want to add in-app notifications (recommended for better UX), here's how:

### Step 1: Create Notification Model

**File**: `hr_management/models.py`

Add this model:

```python
class Notification(models.Model):
    """In-app notifications for users"""
    NOTIFICATION_TYPES = [
        ('complaint_comment', 'New Complaint Comment'),
        ('complaint_assigned', 'Complaint Assigned'),
        ('complaint_status', 'Complaint Status Changed'),
        ('task_assigned', 'Task Assigned'),
        ('system', 'System Notification'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=500, null=True, blank=True)  # URL to relevant page
    
    # Related object (optional)
    complaint = models.ForeignKey(
        'ClientComplaint',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.notification_type} for {self.recipient.username}"
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
```

Then run:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Update Notification Service

**File**: `hr_management/notifications.py`

Add method to create in-app notifications:

```python
@staticmethod
def create_notification(recipient, notification_type, title, message, complaint=None, link=None):
    """Create an in-app notification"""
    from .models import Notification
    
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        complaint=complaint,
        link=link
    )
    return notification

@staticmethod
def notify_new_client_message(complaint):
    """Send notification when client sends a message"""
    admin_emails = NotificationService._get_admin_emails(complaint)
    
    # Send emails (existing code)
    subject = f"New Client Message - {complaint.title}"
    message = f"Client {complaint.client_name} has sent a new message..."
    
    for email in admin_emails:
        NotificationService._send_email(subject, message, email)
    
    # NEW: Create in-app notifications
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    assigned_users = User.objects.filter(email__in=admin_emails)
    for user in assigned_users:
        NotificationService.create_notification(
            recipient=user,
            notification_type='complaint_comment',
            title=f"New message from {complaint.client_name}",
            message=f"Complaint: {complaint.title}",
            complaint=complaint,
            link=f"/dashboard/client-complaints/{complaint.id}"
        )
```

### Step 3: Create API Endpoints

**File**: `hr_management/views.py`

Add these ViewSets:

```python
from rest_framework.decorators import action

class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user notifications"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationDetailSerializer
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read"""
        notification = self.get_object()
        notification.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'status': 'all marked as read'})
```

**File**: `hr_management/urls.py`

Add to router:
```python
router.register(r'notifications', NotificationViewSet, basename='notification')
```

### Step 4: Create Frontend Component

**File**: `v0-micro-system/components/notifications/notification-bell.tsx`

```tsx
'use client'

import { useState, useEffect } from 'react'
import { Bell } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

interface Notification {
  id: number
  title: string
  message: string
  link?: string
  is_read: boolean
  created_at: string
}

export function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [isOpen, setIsOpen] = useState(false)

  // Fetch notifications
  const fetchNotifications = async () => {
    try {
      const token = localStorage.getItem('authToken')
      const response = await fetch('http://localhost:8000/hr/notifications/', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        setNotifications(data.results || data)
        
        // Get unread count
        const unreadResponse = await fetch('http://localhost:8000/hr/notifications/unread_count/', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        })
        const unreadData = await unreadResponse.json()
        setUnreadCount(unreadData.unread_count)
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error)
    }
  }

  // Mark notification as read
  const markAsRead = async (id: number) => {
    try {
      const token = localStorage.getItem('authToken')
      await fetch(`http://localhost:8000/hr/notifications/${id}/mark_as_read/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      fetchNotifications() // Refresh
    } catch (error) {
      console.error('Failed to mark as read:', error)
    }
  }

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      const token = localStorage.getItem('authToken')
      await fetch('http://localhost:8000/hr/notifications/mark_all_as_read/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      fetchNotifications() // Refresh
    } catch (error) {
      console.error('Failed to mark all as read:', error)
    }
  }

  useEffect(() => {
    fetchNotifications()
    
    // Poll for new notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {unreadCount > 0 && (
            <Badge 
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
              variant="destructive"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <div className="flex items-center justify-between px-4 py-2 border-b">
          <h3 className="font-semibold">Notifications</h3>
          {unreadCount > 0 && (
            <Button 
              variant="ghost" 
              size="sm"
              onClick={markAllAsRead}
            >
              Mark all as read
            </Button>
          )}
        </div>
        
        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="px-4 py-8 text-center text-muted-foreground">
              No notifications
            </div>
          ) : (
            notifications.map((notification) => (
              <DropdownMenuItem
                key={notification.id}
                className={`px-4 py-3 cursor-pointer ${
                  !notification.is_read ? 'bg-blue-50' : ''
                }`}
                onClick={() => {
                  markAsRead(notification.id)
                  if (notification.link) {
                    window.location.href = notification.link
                  }
                }}
              >
                <div className="flex flex-col gap-1 w-full">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium text-sm">{notification.title}</p>
                    {!notification.is_read && (
                      <div className="w-2 h-2 bg-blue-600 rounded-full flex-shrink-0 mt-1" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {notification.message}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(notification.created_at).toLocaleString()}
                  </p>
                </div>
              </DropdownMenuItem>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

### Step 5: Add to Layout

**File**: `v0-micro-system/app/dashboard/layout.tsx`

Import and add the NotificationBell component to your header/navbar.

## 📊 Quick Check Current System

Since you don't have in-app notifications yet, here's how to check if the email system is working:

### Check Server Logs
```bash
cd /home/ahmedyasser/lab/MicroSystem
tail -n 100 server.log | grep -i "notification\|email"
```

### Check Email Backend Settings
```bash
python manage.py shell -c "
from django.conf import settings
print('EMAIL_BACKEND:', settings.EMAIL_BACKEND)
"
```

Common backends:
- `django.core.mail.backends.console.EmailBackend` - Prints to console (development)
- `django.core.mail.backends.smtp.EmailBackend` - Sends real emails
- `django.core.mail.backends.filebased.EmailBackend` - Saves to files

### Enable Console Email Backend for Testing

**File**: `MicroSystem/settings.py`

Add this for development:
```python
# For development - emails will print to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Then restart your server and check the console output when adding comments.

## 🎯 Recommended Next Steps

1. **Short term**: Use console email backend to see notification emails in server output
2. **Medium term**: Implement the in-app notification system above
3. **Long term**: Add real-time notifications using WebSockets or Server-Sent Events

## 📝 Summary

**Current State**: Email notifications only (no frontend UI)  
**To Check**: Look at server logs or configure console email backend  
**To Improve**: Implement the in-app notification system I outlined above

Would you like me to help implement the in-app notification system?
