# Automated SSL Setup Guide 🔒

## نظرة عامة
هذا الدليل يشرح كيفية إعداد SSL تلقائياً عند إنشاء Tenant بـ Custom Domain.

---

## 📋 المتطلبات (Requirements)

### 1️⃣ Install Celery
```bash
pip install celery redis
```

### 2️⃣ Install Redis (Broker)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Test Redis
redis-cli ping
# Should return: PONG
```

**بديل**: استخدم RabbitMQ أو Django DB كـ broker

### 3️⃣ Install Certbot
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

### 4️⃣ Configure Sudo Access
```bash
# Allow Django user to run certbot without password
sudo visudo

# Add this line (replace 'www-data' with your user):
www-data ALL=(ALL) NOPASSWD: /usr/bin/certbot

# For development (replace 'your_username'):
your_username ALL=(ALL) NOPASSWD: /usr/bin/certbot
```

---

## ⚙️ Configuration

### 1️⃣ Add to settings.py
```python
# MicroSystem/settings.py

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Cairo'
CELERY_ENABLE_UTC = True
```

### 2️⃣ Verify Files Created
```
✅ MicroSystem/celery.py
✅ MicroSystem/__init__.py (updated)
✅ hr_management/ssl_tasks.py
✅ hr_management/tenant_views.py (updated)
```

---

## 🚀 How to Run

### Option 1: Manual Start (Development)

#### Terminal 1: Django Server
```bash
python manage.py runserver
```

#### Terminal 2: Celery Worker
```bash
celery -A MicroSystem worker --loglevel=info
```

#### Terminal 3: Celery Beat (Scheduled Tasks)
```bash
celery -A MicroSystem beat --loglevel=info
```

---

### Option 2: Production (Systemd Services)

#### Create Celery Worker Service
```bash
sudo nano /etc/systemd/system/celery-worker.service
```

```ini
[Unit]
Description=Celery Worker
After=network.target redis.target

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/MicroSystem
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A MicroSystem worker --loglevel=info --detach

[Install]
WantedBy=multi-user.target
```

#### Create Celery Beat Service
```bash
sudo nano /etc/systemd/system/celery-beat.service
```

```ini
[Unit]
Description=Celery Beat
After=network.target redis.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/path/to/MicroSystem
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/celery -A MicroSystem beat --loglevel=info

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat

# Check status
sudo systemctl status celery-worker
sudo systemctl status celery-beat
```

---

## 🎯 How It Works

### Automatic Flow:

```
1. User creates Tenant with custom domain
   POST /api/tenants/
   {
     "name": "Adam Company",
     "domain_type": "custom",
     "custom_domain": "adamcompany.com",
     ...
   }
   ↓
2. Django saves Tenant to database
   ↓
3. perform_create() triggers SSL task
   setup_ssl_certificate.apply_async(countdown=300)
   ↓
4. Celery waits 5 minutes (for DNS propagation)
   ↓
5. Celery worker starts SSL setup:
   a. Verify DNS is working
   b. Run certbot --nginx -d adamcompany.com
   c. Update Nginx configuration
   d. Enable HTTPS redirect
   e. Update tenant.ssl_enabled = True
   ↓
6. ✅ Done! https://adamcompany.com works
```

### Automatic Renewal:

```
Celery Beat runs daily at 3 AM:
  ↓
check_ssl_expiry() task runs
  ↓
Checks all tenants with SSL
  ↓
Renews certificates expiring in < 30 days
  ↓
✅ Auto-renewal complete
```

---

## 📡 API Endpoints

### Check SSL Status
```bash
GET /api/tenants/{id}/ssl_status/

Response:
{
  "ssl_enabled": true,
  "ssl_issued_at": "2025-11-14T10:30:00Z",
  "custom_domain": "adamcompany.com",
  "https_url": "https://adamcompany.com"
}
```

### Manual SSL Setup
```bash
POST /api/tenants/{id}/setup_ssl/
{
  "email": "admin@mycompany.com"
}

Response:
{
  "message": "SSL setup initiated for adamcompany.com",
  "task_id": "abc123-def456",
  "domain": "adamcompany.com"
}
```

---

## 🔍 Monitoring

### Check Celery Tasks
```bash
# View active tasks
celery -A MicroSystem inspect active

# View scheduled tasks
celery -A MicroSystem inspect scheduled

# View registered tasks
celery -A MicroSystem inspect registered
```

### Check Logs
```bash
# Celery worker logs
tail -f /var/log/celery/worker.log

# Celery beat logs
tail -f /var/log/celery/beat.log

# Django logs
tail -f /var/log/django/app.log
```

### Monitor with Flower (Web UI)
```bash
# Install Flower
pip install flower

# Run Flower
celery -A MicroSystem flower

# Open browser
http://localhost:5555
```

---

## 🔧 Troubleshooting

### Problem: Celery can't connect to Redis
```bash
# Check Redis is running
sudo systemctl status redis

# Test connection
redis-cli ping

# Check port
sudo netstat -tulpn | grep 6379
```

### Problem: SSL setup fails with "Permission denied"
```bash
# Check sudo configuration
sudo -l

# Should show:
# User www-data may run the following commands:
#     (ALL) NOPASSWD: /usr/bin/certbot

# Test manually
sudo -u www-data sudo certbot --version
```

### Problem: Task stuck in queue
```bash
# Purge all tasks
celery -A MicroSystem purge

# Restart worker
sudo systemctl restart celery-worker
```

### Problem: DNS not propagated
```bash
# The task will automatically retry 3 times
# with 10-minute intervals

# Check DNS manually
nslookup adamcompany.com
dig adamcompany.com

# Task logs will show:
# ⚠️  DNS not ready for adamcompany.com, retrying in 5 minutes...
```

---

## 📊 Task Retry Logic

```python
@shared_task(bind=True, max_retries=3)
def setup_ssl_certificate(self, tenant_id, email):
    # Try 1: After 5 minutes
    # Try 2: After 15 minutes (5 + 10)
    # Try 3: After 25 minutes (15 + 10)
    # Give up after 3 attempts
```

**Timeline**:
```
0:00  - Tenant created, task scheduled
5:00  - First attempt (wait for DNS)
15:00 - Second attempt (if failed)
25:00 - Third attempt (if failed)
35:00 - Give up, needs manual intervention
```

---

## 🎛️ Configuration Options

### Adjust Wait Time
```python
# In tenant_views.py
setup_ssl_certificate.apply_async(
    countdown=600  # Wait 10 minutes instead of 5
)
```

### Change Retry Intervals
```python
# In ssl_tasks.py
raise self.retry(countdown=1200)  # Retry after 20 minutes
```

### Custom Email
```python
# When creating tenant
POST /api/tenants/
{
  "ssl_email": "admin@mycompany.com"
}
```

---

## 🔐 Security Notes

### Sudo Access
- ⚠️ **Important**: Only allow certbot command via sudo
- ❌ **Never**: Give full sudo access to web user
- ✅ **Correct**: `NOPASSWD: /usr/bin/certbot` only

### Task Queue
- Tasks run in background with web server privileges
- Certbot needs root access via sudo
- Logs should be monitored for security

---

## ✅ Testing

### Test Manual Setup
```bash
# Create test tenant
curl -X POST http://localhost:8000/api/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "domain_type": "custom",
    "custom_domain": "test.example.com",
    "subdomain": "test_abc",
    "admin_username": "admin",
    "admin_email": "admin@test.com",
    "admin_password": "testpass123",
    "module_keys": ["hr"]
  }'

# Check Celery logs
tail -f /var/log/celery/worker.log

# Should see:
# 🔒 Starting SSL setup for: test.example.com
# ⏳ Waiting 300s for DNS propagation...
# 📜 Running certbot...
# ✅ SSL enabled for test.example.com
```

---

## 📈 Scaling

For high-traffic systems:

### Multiple Workers
```bash
# Start multiple workers
celery -A MicroSystem worker --concurrency=4 --loglevel=info

# Or separate workers for different task types
celery -A MicroSystem worker --queue=ssl --concurrency=2
celery -A MicroSystem worker --queue=default --concurrency=4
```

### Task Priorities
```python
# High priority SSL tasks
setup_ssl_certificate.apply_async(priority=10)

# Low priority cleanup tasks
cleanup_failed_ssl_attempts.apply_async(priority=1)
```

---

## 🎉 Summary

✅ **Tenant created** → SSL setup **automatically** scheduled  
✅ **DNS propagates** → Celery waits patiently  
✅ **Certbot runs** → SSL certificate installed  
✅ **HTTPS enabled** → Customer happy!  
✅ **Auto-renewal** → Never expires  

**Zero manual intervention needed!** 🚀

---

## 📞 Support

If you encounter issues:
1. Check Celery worker logs
2. Verify Redis is running
3. Test sudo certbot access
4. Check DNS propagation
5. Review task queue in Flower

For manual intervention:
```bash
python manage.py setup_ssl domain.com
```
