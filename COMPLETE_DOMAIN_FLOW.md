# دليل الدومين الكامل - من البداية للنهاية 🌐

## 📋 الخطوات الكاملة لإعداد Tenant بـ Custom Domain

---

## المرحلة 1️⃣: إنشاء Tenant جديد

### الخطوة 1: إرسال Request
```bash
POST http://your-server.com/api/tenants/

{
  "name": "Adam Company",
  "domain_type": "custom",           # أو "subdomain"
  "custom_domain": "adamcompany.com", # إذا اخترت custom
  "subdomain": "adam",                # إذا اخترت subdomain
  "admin_username": "adam_admin",
  "admin_email": "admin@adamcompany.com",
  "admin_password": "SecurePass123!",
  "module_keys": ["hr", "crm"]
}
```

### الخطوة 2: ماذا يحدث في Backend؟

#### أ) Django يستقبل Request
```python
# في tenant_views.py -> TenantViewSet.create()
```

**العمليات:**
1. ✅ **التحقق من الـ Data (Validation)**
   - هل الـ subdomain متاح؟
   - هل الـ custom_domain صحيح؟
   - هل البيانات كاملة؟

2. ✅ **إنشاء Database للـ Tenant**
   ```python
   db_name = f'tenant_{subdomain}.sqlite3'
   # Creates: tenant_adam.sqlite3
   ```

3. ✅ **إنشاء مجلد Media**
   ```bash
   mkdir media/tenants/adam/
   # Structure:
   # media/tenants/adam/
   #   ├── avatars/
   #   ├── attachments/
   #   └── documents/
   ```

4. ✅ **تطبيق Migrations على Database الجديد**
   ```python
   call_command('migrate', database=db_name)
   # Creates all tables in tenant_adam.sqlite3
   ```

5. ✅ **إنشاء Admin User**
   ```python
   User.objects.using(db_name).create_user(
       username='adam_admin',
       email='admin@adamcompany.com',
       password='SecurePass123!',
       is_staff=True,
       is_superuser=True
   )
   ```

6. ✅ **حفظ Tenant في Main Database**
   ```python
   tenant = Tenant.objects.create(
       name='Adam Company',
       subdomain='adam',
       custom_domain='adamcompany.com',
       domain_type='custom',
       database_name='tenant_adam.sqlite3',
       is_active=True,
       ssl_enabled=False,  # سيتم تفعيله لاحقاً
       ssl_issued_at=None
   )
   ```

#### ب) Response
```json
{
  "id": "uuid-123-456",
  "name": "Adam Company",
  "subdomain": "adam",
  "custom_domain": "adamcompany.com",
  "domain_type": "custom",
  "is_active": true,
  "created_at": "2025-11-14T10:00:00Z",
  "ssl_enabled": false,
  "default_url": "http://adam.your-server.com",
  "custom_url": "http://adamcompany.com"
}
```

---

## المرحلة 2️⃣: إعداد DNS (يدوي من العميل)

### الخطوة 3: العميل يفتح صفحة DNS Guide
```
http://your-server.com/dns-setup/?tenant_id=uuid-123-456
```

**صفحة الإرشادات تعرض:**

#### أ) معلومات DNS المطلوبة
```
Domain: adamcompany.com
Type: A Record
Host: @ (or adamcompany.com)
Value: YOUR_SERVER_IP (e.g., 123.45.67.89)
TTL: 3600
```

#### ب) خطوات التطبيق حسب Provider

**مثال: Namecheap**
```
1. Log in to Namecheap
2. Go to Domain List → Manage
3. Advanced DNS → Add New Record
4. Type: A Record
5. Host: @
6. Value: 123.45.67.89
7. Save
```

**مثال: GoDaddy**
```
1. Log in to GoDaddy
2. My Products → DNS
3. Add Record
4. Type: A
5. Name: @
6. Value: 123.45.67.89
7. Save
```

**مثال: Cloudflare**
```
1. Log in to Cloudflare
2. Select Domain
3. DNS → Add Record
4. Type: A
5. Name: @
6. IPv4: 123.45.67.89
7. Proxy: Off (Orange Cloud)
8. Save
```

### الخطوة 4: العميل يطبق DNS
- العميل يدخل على provider حقه
- يضيف A Record
- ينتظر DNS Propagation (5-30 دقيقة)

### الخطوة 5: التحقق من DNS
```bash
# العميل أو الـ System يتحقق:
nslookup adamcompany.com
# Should return: YOUR_SERVER_IP

dig adamcompany.com
# Should show A record pointing to YOUR_SERVER_IP
```

---

## المرحلة 3️⃣: SSL Automation (أوتوماتيكي)

### الخطوة 6: Celery يبدأ العمل

#### أ) بعد 5 دقائق من إنشاء Tenant
```python
# في tenant_views.py -> perform_create()
setup_ssl_certificate.apply_async(
    args=[str(tenant.id)],
    kwargs={'email': 'admin@adamcompany.com'},
    countdown=300  # 5 minutes = 300 seconds
)
```

**لماذا 5 دقائق؟**
- لإعطاء وقت للـ DNS Propagation
- حتى لا يفشل certbot لأن الـ DNS مش جاهز

#### ب) Celery Task يبدأ التنفيذ
```python
# في ssl_tasks.py -> setup_ssl_certificate()

1. 📝 Log: "🔒 Starting SSL setup for: adamcompany.com"

2. 🔍 Verify DNS is working:
   - nslookup adamcompany.com
   - Check if IP matches server
   - If not ready → Retry in 10 minutes

3. 📜 Run Certbot:
   sudo certbot --nginx \
     -d adamcompany.com \
     --email admin@adamcompany.com \
     --agree-tos \
     --non-interactive \
     --redirect

4. ✅ Certbot creates:
   - SSL Certificate: /etc/letsencrypt/live/adamcompany.com/
   - Nginx Config: Updated with SSL
   - Auto-redirect: HTTP → HTTPS

5. 💾 Update Database:
   tenant.ssl_enabled = True
   tenant.ssl_issued_at = timezone.now()
   tenant.save()

6. 📝 Log: "✅ SSL enabled for adamcompany.com"
```

#### ج) إذا فشل Setup
```python
# Retry Logic:
Try 1: After 5 minutes  (countdown=300)
Try 2: After 15 minutes (if failed, retry countdown=600)
Try 3: After 25 minutes (if failed, retry countdown=600)

# After 3 failures:
- Mark tenant.ssl_enabled = False
- Log error message
- Send notification to admin
- Requires manual intervention
```

---

## المرحلة 4️⃣: Nginx Configuration

### الخطوة 7: Nginx يتعرف على Domain

#### أ) قبل SSL (HTTP only)
```nginx
# /etc/nginx/sites-available/microsystem

server {
    listen 80;
    server_name adamcompany.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

#### ب) بعد SSL (HTTPS + Redirect)
```nginx
# Certbot يضيف هذا أوتوماتيكياً:

# HTTP → HTTPS Redirect
server {
    listen 80;
    server_name adamcompany.com;
    
    # Certbot challenge path
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name adamcompany.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/adamcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/adamcompany.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## المرحلة 5️⃣: Request Routing

### الخطوة 8: العميل يفتح الموقع

#### أ) User Types in Browser
```
https://adamcompany.com
```

#### ب) DNS Resolution
```
1. Browser asks DNS: "What's the IP of adamcompany.com?"
2. DNS responds: "123.45.67.89"
3. Browser connects to: 123.45.67.89:443
```

#### ج) Nginx Receives Request
```nginx
Request arrives at Nginx:
Host: adamcompany.com
Port: 443 (HTTPS)

Nginx matches: server_name adamcompany.com;
```

#### د) Nginx Proxies to Django
```
Nginx → Django (port 8000)
Headers:
  Host: adamcompany.com
  X-Forwarded-For: client_ip
  X-Forwarded-Proto: https
```

#### ه) Django Middleware (tenant_middleware.py)
```python
def get_tenant_from_request(request):
    host = request.get_host()  # adamcompany.com
    
    # Try custom domain first
    tenant = Tenant.objects.filter(
        custom_domain=host,
        is_active=True
    ).first()
    
    if tenant:
        return tenant
    
    # If not found, try subdomain
    subdomain = host.split('.')[0]
    tenant = Tenant.objects.filter(
        subdomain=subdomain,
        is_active=True
    ).first()
    
    return tenant
```

#### و) Database Router
```python
# tenant_db_router.py
def db_for_read(self, model, **hints):
    tenant = get_current_tenant()
    if tenant:
        return tenant.database_name  # tenant_adam.sqlite3
    return 'default'
```

#### ز) Django Returns Response
```
Django → Nginx → Browser
Content: HTML/JSON from tenant_adam.sqlite3
```

---

## المرحلة 6️⃣: Auto-Renewal (أوتوماتيكي)

### الخطوة 9: Celery Beat Daily Check

#### أ) كل يوم الساعة 3 صباحاً
```python
# في celery.py
'check-ssl-expiry-daily': {
    'task': 'hr_management.ssl_tasks.check_ssl_expiry',
    'schedule': crontab(hour=3, minute=0),
}
```

#### ب) Check SSL Expiry Task
```python
# في ssl_tasks.py
@shared_task
def check_ssl_expiry():
    tenants = Tenant.objects.filter(
        ssl_enabled=True,
        domain_type='custom'
    )
    
    for tenant in tenants:
        # Check certificate expiry date
        cert_info = get_certificate_info(tenant.custom_domain)
        days_until_expiry = (cert_info.expiry - timezone.now()).days
        
        # Renew if < 30 days
        if days_until_expiry < 30:
            subprocess.run([
                'sudo', 'certbot', 'renew',
                '--cert-name', tenant.custom_domain,
                '--quiet'
            ])
            
            logger.info(f'🔄 Renewed SSL for {tenant.custom_domain}')
```

#### ج) Let's Encrypt Certificates
```
Issue Date: 2025-11-14
Expiry Date: 2026-02-12 (90 days)

Renewal Check: Daily at 3 AM
Renewal Trigger: When < 30 days remain
Auto-Renewal: Yes ✅
```

---

## 📊 Timeline الكامل

```
Time    Action                              Status
─────────────────────────────────────────────────────────────
00:00   User creates tenant                 ✅ Tenant saved
00:01   Tenant database created             ✅ tenant_adam.sqlite3
00:02   Media folder created                ✅ media/tenants/adam/
00:03   Admin user created                  ✅ adam_admin
00:04   SSL task scheduled                  ⏳ Waiting 5 minutes

05:00   Celery starts SSL setup             🔒 Running certbot
05:01   DNS verification                    🔍 Checking DNS
05:02   Certbot obtains certificate         📜 Let's Encrypt
05:03   Nginx config updated                ⚙️  SSL enabled
05:04   Database updated                    💾 ssl_enabled=True
05:05   HTTPS working                       ✅ https://adamcompany.com

─────────────────────────────────────────────────────────────
Daily   Celery Beat checks expiry           🔄 Auto-renewal
03:00   (Every day at 3 AM)
```

---

## 🔄 Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Creates Tenant                                      │
│    POST /api/tenants/ { custom_domain: "adamcompany.com" } │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Django Backend                                           │
│    ✅ Create tenant_adam.sqlite3                           │
│    ✅ Create media/tenants/adam/                           │
│    ✅ Run migrations                                        │
│    ✅ Create admin user                                     │
│    ✅ Save to main database                                 │
│    ⏳ Schedule SSL task (countdown=300s)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. User Sets Up DNS (Manual)                                │
│    📋 Follow DNS guide                                      │
│    ⚙️  Add A record to DNS provider                        │
│    ⏳ Wait for propagation (5-30 min)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Celery Worker (After 5 minutes)                          │
│    🔍 Verify DNS: nslookup adamcompany.com                 │
│    📜 Run: sudo certbot --nginx -d adamcompany.com         │
│    ✅ SSL certificate issued                                │
│    ⚙️  Nginx config updated (HTTPS + redirect)             │
│    💾 Update tenant.ssl_enabled = True                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. System Ready                                             │
│    ✅ http://adamcompany.com → redirects to HTTPS          │
│    ✅ https://adamcompany.com → Works with SSL             │
│    ✅ Middleware routes to tenant_adam.sqlite3             │
│    ✅ Auto-renewal scheduled (daily check)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🌐 User Journey

### Scenario: Adam ينشئ شركته

#### Day 1 - 00:00
```
Adam:
- يفتح Platform
- يسجل كـ Client
- يختار Plan
- يدفع Subscription
```

#### Day 1 - 00:05
```
Adam:
- ينشئ Tenant جديد
- يختار "Custom Domain"
- يكتب: adamcompany.com
- يضغط "Create"

System:
- ✅ Tenant created
- 📧 Email sent: "Welcome! Setup your DNS"
```

#### Day 1 - 00:10
```
Adam:
- يفتح Email
- يضغط على DNS Setup Guide
- يتبع الخطوات
- يضيف A Record في GoDaddy
- Server IP: 123.45.67.89
```

#### Day 1 - 00:15
```
DNS:
- ⏳ Propagating...
- Some servers see it
- Some servers don't yet
```

#### Day 1 - 00:20
```
Adam:
- يختبر: nslookup adamcompany.com
- ✅ DNS working!
- ينتظر SSL...
```

#### Day 1 - 00:25
```
Celery Worker:
- 🔒 Starting SSL setup
- 🔍 DNS verified
- 📜 Running certbot...
- ⏳ Getting certificate from Let's Encrypt
```

#### Day 1 - 00:30
```
System:
- ✅ SSL certificate issued
- ✅ Nginx configured
- ✅ HTTPS enabled
- 📧 Email sent: "Your domain is ready!"
```

#### Day 1 - 00:35
```
Adam:
- يفتح: https://adamcompany.com
- ✅ الموقع يفتح بـ HTTPS
- ✅ يسجل دخول كـ admin
- ✅ يبدأ يضيف موظفين
- 🎉 Happy!
```

#### Day 90 - 03:00 AM
```
Celery Beat:
- 🔄 Checking SSL expiry...
- ⚠️  Certificate expires in 29 days
- 📜 Running: certbot renew
- ✅ Certificate renewed
- New expiry: 90 days from now
```

---

## ❌ Error Scenarios

### Scenario 1: DNS Not Ready
```
Time: 5 minutes after creation
Celery: Attempts SSL setup
Error: DNS not resolving

Action:
- ⏳ Retry in 10 minutes
- If still failing → Retry in 10 minutes
- After 3 attempts → Mark as failed
- 📧 Send admin notification
```

### Scenario 2: Port 80 Blocked
```
Certbot: Can't verify domain ownership
Error: Port 80 not accessible

Action:
- ❌ SSL fails
- 📝 Log error
- 📧 Email admin: "Check firewall"
- Provide manual fix instructions
```

### Scenario 3: Rate Limit
```
Certbot: Too many requests for this domain
Error: Let's Encrypt rate limit (5 per week)

Action:
- ❌ SSL fails
- 📝 Log: "Rate limited"
- ⏳ Retry after 1 week
- 📧 Email: "Please wait 7 days"
```

---

## 🔍 Monitoring

### Check Tenant Status
```bash
GET /api/tenants/{id}/

Response:
{
  "name": "Adam Company",
  "custom_domain": "adamcompany.com",
  "ssl_enabled": true,
  "ssl_issued_at": "2025-11-14T00:30:00Z",
  "is_active": true
}
```

### Check SSL Status
```bash
GET /api/tenants/{id}/ssl_status/

Response:
{
  "ssl_enabled": true,
  "ssl_issued_at": "2025-11-14T00:30:00Z",
  "expires_at": "2026-02-12T00:30:00Z",
  "days_until_expiry": 89,
  "auto_renewal": true,
  "https_url": "https://adamcompany.com"
}
```

### Manual SSL Trigger
```bash
POST /api/tenants/{id}/setup_ssl/
{
  "email": "admin@adamcompany.com"
}

Response:
{
  "message": "SSL setup initiated",
  "task_id": "abc-123-def-456",
  "estimated_time": "10-15 minutes"
}
```

---

## ✅ Success Checklist

### For Admin:
- [ ] Redis/RabbitMQ running
- [ ] Celery worker running
- [ ] Celery beat running
- [ ] Nginx configured
- [ ] Certbot installed
- [ ] Sudo permissions configured
- [ ] Port 80 open
- [ ] Port 443 open

### For Client:
- [ ] Tenant created
- [ ] DNS A record added
- [ ] DNS propagated (nslookup)
- [ ] Wait 5-10 minutes
- [ ] Check email for confirmation
- [ ] Open https://yourdomain.com
- [ ] Login with admin credentials
- [ ] Start using the system!

---

## 📞 Troubleshooting

### "HTTPS not working after 30 minutes"

**Check:**
```bash
# 1. DNS
nslookup adamcompany.com

# 2. Celery logs
tail -f /var/log/celery/worker.log

# 3. Certbot logs
sudo tail -f /var/log/letsencrypt/letsencrypt.log

# 4. Nginx logs
sudo tail -f /var/log/nginx/error.log

# 5. Manual SSL
python manage.py setup_ssl adamcompany.com
```

---

## 🎯 Summary

**What happens automatically:**
1. ✅ Tenant database creation
2. ✅ Media folder setup
3. ✅ Admin user creation
4. ✅ SSL certificate (after DNS)
5. ✅ HTTPS redirect
6. ✅ Auto-renewal

**What user must do:**
1. 📝 Create tenant
2. ⚙️  Setup DNS (one time)
3. ⏳ Wait 5-30 minutes
4. 🎉 Done!

**Zero technical knowledge needed for clients!** 🚀
