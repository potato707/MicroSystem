# Custom Domain Setup Guide 🌐

## نظرة عامة
يدعم النظام الآن استخدام **Custom Domains** بجانب Subdomains للعملاء.

---

## الفرق بين Subdomain و Custom Domain

### Subdomain (النظام الافتراضي)
```
https://adam.yourdomain.com
https://khalid.yourdomain.com
```
- سهل في الإعداد
- يتم تلقائياً بدون تدخل العميل
- مناسب للعملاء الصغار

### Custom Domain (النظام الجديد)
```
https://adamcompany.com
https://khalidco.com
```
- العميل يستخدم الدومين الخاص به
- يحتاج إعداد DNS من قبل العميل
- أكثر احترافية ومناسب للشركات الكبيرة

---

## كيفية إعداد Custom Domain للعميل

### 1️⃣ إنشاء Tenant باستخدام Custom Domain

#### من صفحة إنشاء العملاء:
1. افتح: `http://localhost:8000/api/create-tenant/`
2. اختر **Custom Domain** من Radio Buttons
3. أدخل الدومين: `adamcompany.com`
4. أكمل باقي البيانات
5. اضغط "إنشاء العميل الآن"

#### من API مباشرة:
```bash
curl -X POST http://localhost:8000/api/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Adam Company",
    "domain_type": "custom",
    "custom_domain": "adamcompany.com",
    "subdomain": "custom_1699999999",
    "admin_username": "admin",
    "admin_email": "admin@adamcompany.com",
    "admin_password": "secure123",
    "module_keys": ["hr", "tasks"]
  }'
```

---

### 2️⃣ DNS Configuration (على جهة العميل)

العميل يحتاج يروح عند Domain Provider بتاعه (GoDaddy, Namecheap, Cloudflare, etc.) ويعمل الآتي:

#### Option A: CNAME Record (موصى به)
```
Type:  CNAME
Name:  @ (or blank for root domain)
Value: yourdomain.com
TTL:   Auto or 3600
```

#### Option B: A Record (بديل)
```
Type:  A
Name:  @ (or blank for root domain)
Value: 123.456.789.0  ← IP address للسيرفر بتاعك
TTL:   Auto or 3600
```

#### تفعيل www subdomain (اختياري):
```
Type:  CNAME
Name:  www
Value: adamcompany.com
TTL:   Auto or 3600
```

---

### 3️⃣ SSL/HTTPS Setup

#### باستخدام Let's Encrypt (مجاني):

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d adamcompany.com -d www.adamcompany.com

# Auto-renewal (optional)
sudo certbot renew --dry-run
```

#### Nginx Configuration:
```nginx
server {
    listen 80;
    server_name adamcompany.com www.adamcompany.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name adamcompany.com www.adamcompany.com;
    
    ssl_certificate /etc/letsencrypt/live/adamcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/adamcompany.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### 4️⃣ التحقق من التشغيل

#### A. تحقق من DNS:
```bash
# Check DNS propagation
nslookup adamcompany.com

# Or use online tool
# https://dnschecker.org
```

#### B. تحقق من Backend:
```bash
# Test tenant detection
curl -H "Host: adamcompany.com" http://localhost:8000/api/tenants/me/
```

#### C. تحقق من Frontend:
```bash
# Open in browser
https://adamcompany.com

# Should show login page for that tenant
```

---

## كيف يعمل النظام داخلياً؟

### Backend Flow:

```python
# في tenant_middleware.py

def process_request(request):
    host = request.get_host()  # adamcompany.com
    
    # PRIORITY 1: Try custom domain first
    tenant = Tenant.objects.filter(
        domain_type='custom',
        custom_domain=host
    ).first()
    
    if tenant:
        # Found! Use this tenant
        request.tenant = tenant
        return
    
    # PRIORITY 2: Try subdomain
    subdomain = extract_subdomain(host)  # adam
    tenant = Tenant.objects.filter(subdomain=subdomain).first()
    
    request.tenant = tenant
```

### Frontend Flow:

```typescript
// الفرونت إند لا يحتاج أي تعديل!

// User opens: https://adamcompany.com
const api = new ApiClient()

// Browser sends request to adamcompany.com
// Backend sees: request.get_host() = "adamcompany.com"
// Backend finds tenant automatically
// ✅ Done!
```

---

## Troubleshooting 🔧

### مشكلة: DNS لم ينتشر بعد
```bash
# Wait 5-30 minutes for DNS propagation
# Check status:
dig adamcompany.com
```

### مشكلة: SSL Certificate Error
```bash
# Renew certificate
sudo certbot renew

# Check certificate expiry
sudo certbot certificates
```

### مشكلة: Tenant Not Found
```python
# Check in Django shell
python manage.py shell

from hr_management.tenant_models import Tenant
tenant = Tenant.objects.filter(custom_domain='adamcompany.com').first()
print(tenant)  # Should show tenant object
```

### مشكلة: Frontend لا يعمل
```bash
# Check if domain is pointing to correct IP
ping adamcompany.com

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

---

## Production Deployment Checklist ✅

### قبل نشر Custom Domain:

- [ ] SSL Certificate جاهز
- [ ] DNS Configuration صحيح
- [ ] Nginx Configuration محدث
- [ ] Tenant موجود في Database
- [ ] Domain Type = 'custom'
- [ ] Custom Domain = 'adamcompany.com'
- [ ] تم اختبار الوصول للموقع
- [ ] تم اختبار تسجيل الدخول
- [ ] تم اختبار API Requests

---

## مثال كامل: إعداد عميل جديد

### الخطوة 1: إنشاء Tenant
```bash
POST /api/tenants/
{
  "name": "Adam Technology",
  "domain_type": "custom",
  "custom_domain": "adamtech.com",
  "subdomain": "custom_adam_tech",
  "admin_username": "adamadmin",
  "admin_email": "admin@adamtech.com",
  "admin_password": "securePass123!",
  "module_keys": ["hr", "tasks", "wallet"]
}
```

### الخطوة 2: إعداد DNS (العميل يعمله)
```
في GoDaddy/Namecheap:
1. Login to domain panel
2. Find DNS Management
3. Add CNAME record:
   - Type: CNAME
   - Name: @ 
   - Points to: yoursaasplatform.com
   - TTL: 3600
4. Save changes
5. Wait 5-30 minutes
```

### الخطوة 3: إعداد SSL (على السيرفر)
```bash
sudo certbot --nginx -d adamtech.com -d www.adamtech.com
```

### الخطوة 4: اختبار
```bash
# Test DNS
nslookup adamtech.com

# Test website
curl https://adamtech.com

# Test API
curl https://adamtech.com/api/tenants/me/
```

### الخطوة 5: إبلاغ العميل
```
✅ Custom domain جاهز!

الموقع: https://adamtech.com
اسم المستخدم: adamadmin
كلمة المرور: securePass123!

يمكنك الآن تسجيل الدخول والبدء في استخدام النظام.
```

---

## أسئلة شائعة (FAQ)

### Q: هل يمكن تغيير من Subdomain إلى Custom Domain؟
**A:** نعم! فقط حدث الـ Tenant:
```python
tenant.domain_type = 'custom'
tenant.custom_domain = 'newdomain.com'
tenant.save()
```

### Q: هل يمكن استخدام الاثنين معاً؟
**A:** نعم! Custom Domain له الأولوية، لكن Subdomain سيستمر في العمل.

### Q: كم يستغرق DNS propagation؟
**A:** من 5 دقائق إلى 48 ساعة (عادة 30 دقيقة).

### Q: هل SSL مجاني؟
**A:** نعم مع Let's Encrypt! ويتجدد تلقائياً كل 90 يوم.

### Q: ماذا لو العميل باع الدومين؟
**A:** غير Custom Domain في Database، والعميل الجديد يعمل DNS setup.

---

## الخلاصة 🎯

### مميزات Custom Domain:
✅ احترافية أكثر للعملاء  
✅ Branding كامل  
✅ SEO أفضل  
✅ ثقة أكبر من العملاء  

### عيوب Custom Domain:
❌ يحتاج إعداد DNS من العميل  
❌ يحتاج SSL certificate منفصل  
❌ أكثر تعقيداً في الصيانة  

### متى تستخدم أيهما؟

| نوع العميل | الاختيار المناسب |
|-----------|------------------|
| شركة صغيرة / Startup | Subdomain |
| شركة متوسطة | Custom Domain |
| شركة كبيرة / Enterprise | Custom Domain |
| تجربة / Demo | Subdomain |
| Production / عملاء حقيقيين | Custom Domain |

---

## دعم فني

إذا واجهت مشكلة في إعداد Custom Domain، تواصل مع فريق الدعم الفني.

**Happy Hosting! 🚀**
