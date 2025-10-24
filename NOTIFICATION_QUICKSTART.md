# 🚀 Quick Start: Testing the Notification System

## Step 1: Start Backend Server

```bash
cd /home/ahmedyasser/lab/MicroSystem
python manage.py runserver
```

Keep this terminal open to see console email output!

---

## Step 2: Start Frontend Server

Open a NEW terminal:

```bash
cd /home/ahmedyasser/lab/MicroSystem/v0-micro-system
npm run dev
```

---

## Step 3: Login to Dashboard

1. Open browser: http://localhost:3000/login
2. Login with admin credentials
3. Look for the **🔔 bell icon** in the top right corner

---

## Step 4: Create a Test Notification

### Option A: Via Test Script
```bash
cd /home/ahmedyasser/lab/MicroSystem
python test_complete_notifications.py
```

This will create a test notification. Refresh the dashboard and click the bell icon!

### Option B: Via API (Add Comment to Complaint)

First, get your auth token and a complaint ID:
```bash
# Login and get token
curl -X POST 'http://localhost:8000/hr/api/token/' \
  -H 'Content-Type: application/json' \
  --data-raw '{"username":"your-username","password":"your-password"}'

# Copy the "access" token from response
```

Then add a comment:
```bash
curl -X POST 'http://localhost:8000/hr/client-complaints/COMPLAINT_ID/comments/' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE' \
  -H 'Content-Type: application/json' \
  --data-raw '{"comment":"Test notification message","is_internal":false}'
```

### Option C: Via Frontend UI

1. Go to: http://localhost:3000/dashboard/client-complaints
2. Click on any complaint
3. Scroll to comments section
4. Add a new comment
5. Check the bell icon - it should show a red badge!

---

## Step 5: Test Notification Features

### See Unread Count
- Look at the **red badge** on the bell icon
- It shows how many unread notifications you have

### Open Notifications
- Click the bell icon
- A dropdown menu appears with all notifications
- Unread notifications have a **blue background**

### Read a Notification
- Click on any notification
- It will mark as read and navigate you to the complaint
- The notification background turns gray

### Mark All as Read
- Click "تعيين الكل كمقروء" button at the top
- All notifications become gray
- Red badge disappears

---

## 🎯 What You Should See

### In the Frontend:
1. ✅ Bell icon in top right corner
2. ✅ Red badge with number (if unread notifications exist)
3. ✅ Dropdown menu when clicking bell
4. ✅ List of notifications with titles and messages
5. ✅ Blue background for unread items
6. ✅ Click notification → navigates to complaint page

### In the Django Console:
```
Content-Type: text/plain; charset="utf-8"
...
Subject: New client message - Ticket #...
...
The client has sent a new message. Please respond promptly.
```

---

## 🐛 Common Issues

### Bell icon not showing?
```bash
# Restart Next.js server
cd v0-micro-system
# Ctrl+C to stop
npm run dev
```

### No notifications appearing?
1. Make sure you're logged in with an admin account
2. Run test script to create a test notification:
   ```bash
   python test_complete_notifications.py
   ```
3. Refresh the browser

### 401 Unauthorized error?
- Your token expired
- Logout and login again

---

## 📊 Quick API Tests

### Get unread count:
```bash
curl -X GET 'http://localhost:8000/hr/notifications/unread_count/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Get all notifications:
```bash
curl -X GET 'http://localhost:8000/hr/notifications/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Mark all as read:
```bash
curl -X POST 'http://localhost:8000/hr/notifications/mark_all_as_read/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

---

## ✨ Success!

If you can see the bell icon with notifications, **congratulations!** 🎉

The complete notification system is working:
- ✅ Backend API
- ✅ Database storage
- ✅ Frontend UI
- ✅ Real-time updates
- ✅ Email notifications

---

## 📝 Next Steps

1. **Assign teams to complaints** so more users receive notifications
2. **Test with multiple users** to see different notification views
3. **Add more comments** to generate more notifications
4. **Check Django console** to see email output

---

**Need Help?**
- Check `NOTIFICATION_SYSTEM_IMPLEMENTATION.md` for full documentation
- Run `python test_complete_notifications.py` to verify backend
- Check browser console (F12) for frontend errors
