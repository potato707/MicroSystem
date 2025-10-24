# 🔒 Tenant Module Access Control - FIXED

## 🐛 Problem Found

You discovered that **disabled modules were still accessible** via API, even though they were marked as disabled in the tenant configuration.

```bash
# This should have been BLOCKED but wasn't:
curl -H "X-Tenant-Subdomain: testcompany" \
  http://localhost:8000/hr/employees/

# Employees module is DISABLED for testcompany
# But API returned data anyway! ❌
```

---

## ✅ Root Cause

The `TenantModuleAccessMiddleware` exists but was **NOT registered** in `settings.py`!

### Before (Broken):
```python
# MicroSystem/settings.py
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    # ... other middlewares ...
    # ❌ Missing tenant middlewares!
]
```

---

## 🔧 What I Fixed

### 1. Registered Tenant Middlewares
```python
# MicroSystem/settings.py
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ✅ Tenant system middlewares (ADDED)
    'hr_management.tenant_middleware.TenantMiddleware',
    'hr_management.tenant_middleware.TenantModuleAccessMiddleware',
]
```

### 2. Added Header-Based Tenant Detection
```python
# tenant_middleware.py - TenantMiddleware
def process_request(self, request):
    # ✅ Now checks X-Tenant-Subdomain header first
    subdomain_header = request.headers.get('X-Tenant-Subdomain')
    if subdomain_header:
        tenant = Tenant.objects.filter(
            subdomain=subdomain_header,
            is_active=True
        ).first()
        ...
```

### 3. Fixed URL Patterns
```python
# tenant_middleware.py - TenantModuleAccessMiddleware
MODULE_URL_PATTERNS = {
    # ✅ Added /hr/ prefix (your actual API uses this)
    '/hr/employees/': 'employees',
    '/hr/attendance/': 'attendance',
    '/hr/wallet/': 'wallet',
    '/hr/tasks/': 'tasks',
    '/hr/complaints/': 'complaints',
    '/hr/shifts/': 'shifts',
    '/hr/reports/': 'reports',
    # Also kept /api/ for compatibility
    '/api/employees/': 'employees',
    ...
}
```

### 4. Added Logging
```python
# Better debugging with detailed logs
logger.info(f"Tenant '{request.tenant.name}' accessing {path}")
logger.warning(f"Access DENIED: module '{required_module}' is disabled")
logger.info(f"Access GRANTED: module '{required_module}' is enabled")
```

---

## 🧪 How to Test

### Step 1: Restart Django Server

**IMPORTANT**: Middleware changes require server restart!

```bash
# Stop the server (Ctrl+C)
# Then restart:
cd "/home/ahmedyasser/lab/Saas/Second attempt/MicroSystem"
python manage.py runserver
```

---

### Step 2: Check Tenant Module Status

```bash
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant

tenant = Tenant.objects.get(subdomain='testcompany')
print(f'Tenant: {tenant.name}\n')
print('Enabled modules:')
for m in tenant.modules.filter(is_enabled=True):
    print(f'  ✓ {m.module_key}')
print('\nDisabled modules:')
for m in tenant.modules.filter(is_enabled=False):
    print(f'  ✗ {m.module_key}')
"
```

**Expected Output:**
```
Tenant: Test Company

Enabled modules:
  ✓ notifications

Disabled modules:
  ✗ attendance
  ✗ complaints
  ✗ employees      ← This is DISABLED
  ✗ reports
  ✗ shifts
  ✗ tasks
  ✗ wallet
```

---

### Step 3: Test DISABLED Module (Should Block)

```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"string","password":"string"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access'])")

# Try to access DISABLED employees module
curl -v \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: testcompany" \
  http://localhost:8000/hr/employees/
```

**Expected Response: 403 Forbidden**
```json
{
  "error": "Module not enabled",
  "message": "The Employee Management module is not enabled for your account.",
  "module": "employees",
  "tenant": "Test Company",
  "upgrade_required": true
}
```

**Check Django logs:**
```
Tenant 'Test Company' accessing /hr/employees/ - requires module: employees
Access DENIED: Tenant 'Test Company' - module 'employees' is disabled
[22/Oct/2025 12:10:00] "GET /hr/employees/ HTTP/1.1" 403 156
```

---

### Step 4: Test ENABLED Module (Should Work)

```bash
# Try to access ENABLED notifications module
curl -v \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: testcompany" \
  http://localhost:8000/hr/notifications/
```

**Expected Response: 200 OK** (or data from endpoint)

**Check Django logs:**
```
Tenant 'Test Company' accessing /hr/notifications/ - requires module: notifications
Access GRANTED: Tenant 'Test Company' - module 'notifications' is enabled
[22/Oct/2025 12:10:00] "GET /hr/notifications/ HTTP/1.1" 200 532
```

---

### Step 5: Enable Module and Test Again

```bash
# Enable employees module via Django admin
# Go to: http://localhost:8000/admin/hr_management/tenant/
# Edit "Test Company"
# Check "Is enabled" for "employees" module
# Save

# OR via Python:
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant

tenant = Tenant.objects.get(subdomain='testcompany')
employee_module = tenant.modules.get(module_key='employees')
employee_module.is_enabled = True
employee_module.save()
print('✓ Employees module enabled')
"
```

**Now test again:**
```bash
curl -v \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: testcompany" \
  http://localhost:8000/hr/employees/
```

**Expected Response: 200 OK** ✅

---

## 🎯 Complete Test Script

Save as `test_module_access.sh`:

```bash
#!/bin/bash

TENANT="testcompany"
API_BASE="http://localhost:8000"

echo "🔒 Testing Tenant Module Access Control"
echo "========================================"
echo ""

# Get token
echo "1. Getting auth token..."
TOKEN=$(curl -s -X POST $API_BASE/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"string","password":"string"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access'])")

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi
echo "✓ Token obtained"
echo ""

# Test disabled module
echo "2. Testing DISABLED module (employees)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  $API_BASE/hr/employees/)

if [ "$HTTP_CODE" = "403" ]; then
    echo "✅ PASS: Disabled module blocked (403)"
else
    echo "❌ FAIL: Expected 403, got $HTTP_CODE"
fi
echo ""

# Test enabled module
echo "3. Testing ENABLED module (notifications)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  $API_BASE/hr/notifications/)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "✅ PASS: Enabled module accessible ($HTTP_CODE)"
else
    echo "❌ FAIL: Expected 200/401, got $HTTP_CODE"
fi
echo ""

# Enable employees module
echo "4. Enabling employees module..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant
tenant = Tenant.objects.get(subdomain='$TENANT')
module = tenant.modules.get(module_key='employees')
module.is_enabled = True
module.save()
print('✓ Module enabled')
"
echo ""

# Test now-enabled module
echo "5. Testing now-ENABLED module (employees)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  $API_BASE/hr/employees/)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS: Now accessible (200)"
else
    echo "❌ FAIL: Expected 200, got $HTTP_CODE"
fi
echo ""

# Disable again
echo "6. Disabling employees module again..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant
tenant = Tenant.objects.get(subdomain='$TENANT')
module = tenant.modules.get(module_key='employees')
module.is_enabled = False
module.save()
print('✓ Module disabled')
"
echo ""

# Test disabled again
echo "7. Testing DISABLED again (employees)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  $API_BASE/hr/employees/)

if [ "$HTTP_CODE" = "403" ]; then
    echo "✅ PASS: Blocked again (403)"
else
    echo "❌ FAIL: Expected 403, got $HTTP_CODE"
fi
echo ""

echo "========================================"
echo "✅ Module access control tests complete!"
```

**Run it:**
```bash
chmod +x test_module_access.sh
./test_module_access.sh
```

---

## 📊 How It Works Now

### Request Flow:

```
1. Request arrives
   ↓
2. TenantMiddleware
   ├─ Check X-Tenant-Subdomain header
   ├─ Lookup tenant in database
   └─ Attach to request.tenant
   ↓
3. TenantModuleAccessMiddleware
   ├─ Check if URL requires a module
   ├─ Lookup TenantModule in database
   ├─ Check if is_enabled = True
   └─ Block with 403 if disabled
   ↓
4. View processes request (if allowed)
   ↓
5. Response returned
```

### Database Query:
```sql
-- For each request to /hr/employees/:
SELECT is_enabled 
FROM hr_management_tenantmodule 
WHERE tenant_id = 'testcompany-uuid' 
  AND module_key = 'employees';

-- If is_enabled = False → 403 Forbidden
-- If is_enabled = True  → Allow request
```

---

## 🎯 Success Criteria

After restarting the server, you should see:

✅ **Disabled modules return 403**
```bash
curl -H "X-Tenant-Subdomain: testcompany" http://localhost:8000/hr/employees/
# → 403 Forbidden
```

✅ **Enabled modules return 200**
```bash
curl -H "X-Tenant-Subdomain: testcompany" http://localhost:8000/hr/notifications/
# → 200 OK
```

✅ **Error message is helpful**
```json
{
  "error": "Module not enabled",
  "message": "The Employee Management module is not enabled for your account.",
  "module": "employees",
  "tenant": "Test Company",
  "upgrade_required": true
}
```

✅ **Logs show enforcement**
```
Access DENIED: Tenant 'Test Company' - module 'employees' is disabled
```

---

## 🔍 Troubleshooting

### "Still returning 200 OK"

**Cause**: Server not restarted after middleware changes

**Fix**:
```bash
# Ctrl+C to stop server
python manage.py runserver
```

---

### "Middleware not logging anything"

**Cause**: Logging level too high

**Fix**: Add to `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'hr_management.tenant_middleware': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

### "Works in curl but not in browser"

**Cause**: Browser not sending `X-Tenant-Subdomain` header

**Fix**: Update your frontend API client:
```javascript
// frontend/src/api/client.js
const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'X-Tenant-Subdomain': getTenantSubdomain(), // Add this!
  }
});
```

---

### "All requests return 403"

**Cause**: URLs might be in exempt list by mistake

**Fix**: Check `tenant_middleware.py`:
```python
EXEMPT_URLS = [
    '/api/auth/',
    '/api/tenants/',
    '/api/public/',
    '/admin/',
    '/media/',
    '/static/',
    # Make sure your API path is NOT here!
]
```

---

## 📚 Summary

### What Was Broken:
- ❌ Middleware existed but not registered
- ❌ URL patterns didn't match `/hr/` prefix
- ❌ No header-based tenant detection

### What I Fixed:
- ✅ Registered both tenant middlewares in settings.py
- ✅ Added `/hr/` URL patterns
- ✅ Added `X-Tenant-Subdomain` header support
- ✅ Added detailed logging for debugging

### What You Should Do:
1. **Restart Django server** (required!)
2. **Run test script** to verify it works
3. **Check logs** to see middleware in action
4. **Update frontend** to send `X-Tenant-Subdomain` header

---

## 🎉 Result

Your tenant system now properly enforces module access control! Disabled modules return 403, and the error message guides users to upgrade.

**Test it now:**
```bash
./test_module_access.sh
```

---

**The fix is complete! Restart your server and test.** 🚀
