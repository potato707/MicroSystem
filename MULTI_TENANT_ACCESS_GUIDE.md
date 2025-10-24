# 🎯 Multi-Tenant Access Guide

## ✅ النظام الجديد - الوصول المتعدد للـ Tenants

الآن يمكنك الوصول إلى أي tenant بعدة طرق مختلفة! النظام يكتشف تلقائياً الـ tenant ويرسل الـ `X-Tenant-Subdomain` header.

---

## 🚀 طرق الوصول المدعومة

### 1️⃣ Query Parameter (الأسهل)
```
http://localhost:3000/login?tenant=testc
```

**المميزات:**
- ✅ سهل الاستخدام
- ✅ يمكن مشاركة الـ URL
- ✅ يعمل مباشرة من أي مكان

**مثال:**
```
http://localhost:3000/login?tenant=demo
http://localhost:3000/login?tenant=testcompany
http://localhost:3000/login?tenant=auth_test_a
```

---

### 2️⃣ Path Parameter (Dynamic Route)
```
http://localhost:3000/login/testc
```

**المميزات:**
- ✅ URL أنظف
- ✅ RESTful pattern
- ✅ يدعم tenant-specific pages

**مثال:**
```
http://localhost:3000/login/demo
http://localhost:3000/login/testcompany
```

---

### 3️⃣ Subdomain (Production Ready)
```
http://testc.localhost:3000
```

**المميزات:**
- ✅ Professional
- ✅ Multi-tenant SaaS standard
- ✅ Domain isolation

**الإعداد:**
1. في `/etc/hosts` (Linux/Mac) أو `C:\Windows\System32\drivers\etc\hosts` (Windows):
```
127.0.0.1 testc.localhost
127.0.0.1 demo.localhost
127.0.0.1 testcompany.localhost
```

2. افتح المتصفح:
```
http://testc.localhost:3000
```

**ملاحظة:** في Production، استخدم domains حقيقية:
```
https://testc.yourdomain.com
https://demo.yourdomain.com
```

---

### 4️⃣ Tenant Selector (Default)
```
http://localhost:3000/tenants
```

**المميزات:**
- ✅ UI جميلة
- ✅ عرض جميع الـ tenants
- ✅ Visual selection

**Flow:**
1. افتح `/tenants`
2. اختر tenant من القائمة
3. يتم حفظه في localStorage
4. Redirect إلى login

---

## 🔍 Tenant Detection Priority

النظام يكتشف الـ tenant بالترتيب التالي:

```
1. Query Parameter (?tenant=testc)     ← أعلى أولوية
2. URL Path (/login/testc)
3. Subdomain (testc.localhost)
4. localStorage (previously selected)  ← أقل أولوية
```

إذا لم يتم العثور على tenant، يتم redirect إلى `/tenants`.

---

## 📋 أمثلة عملية

### مثال 1: Access Direct با Query
```bash
# افتح المتصفح على:
http://localhost:3000/login?tenant=testc

# سيحدث:
1. ✅ يتم اكتشاف tenant "testc" من query parameter
2. ✅ يتم تحميل معلومات الـ tenant من API
3. ✅ يظهر اسم الـ tenant في صفحة login
4. ✅ عند تسجيل الدخول، يتم إرسال X-Tenant-Subdomain: testc
5. ✅ Backend يوجه الطلب للـ database الصحيح
```

### مثال 2: Access با Path
```bash
# افتح المتصفح على:
http://localhost:3000/login/demo

# سيحدث:
1. ✅ يتم اكتشاف tenant "demo" من path
2. ✅ باقي الخطوات مماثلة للمثال 1
```

### مثال 3: Access با Subdomain
```bash
# أولاً، أضف في /etc/hosts:
127.0.0.1 testc.localhost

# افتح المتصفح على:
http://testc.localhost:3000

# سيحدث:
1. ✅ يتم اكتشاف tenant "testc" من subdomain
2. ✅ باقي الخطوات مماثلة
```

### مثال 4: Override با Query
```bash
# حتى لو كان لديك tenant محفوظ:
http://localhost:3000/login?tenant=demo

# سيحدث:
1. ✅ Query parameter له أولوية أعلى
2. ✅ يتم استبدال الـ tenant المحفوظ
3. ✅ يتم حفظ الـ tenant الجديد
```

---

## 🔐 Authentication Flow

### الخطوات الكاملة:

```
1. المستخدم يفتح: /login?tenant=testc
   ↓
2. detectTenant() يكتشف "testc"
   ↓
3. getTenantInfo() يحمل معلومات الـ tenant من API
   ↓
4. selectTenant() يحفظ في context و localStorage
   ↓
5. المستخدم يدخل username & password
   ↓
6. loginToTenant() يرسل:
   - URL: POST /api/auth/login/
   - Headers:
     * Content-Type: application/json
     * X-Tenant-Subdomain: testc
   - Body: {username, password}
   ↓
7. Backend:
   - يقرأ X-Tenant-Subdomain header
   - يتصل بـ database tenant_testc.sqlite3
   - يتحقق من المستخدم
   - يرجع JWT tokens
   ↓
8. Frontend:
   - يحفظ access token
   - يحفظ refresh token
   - Redirect إلى /dashboard
   ↓
9. جميع API calls التالية تحتوي على:
   - Authorization: Bearer {token}
   - X-Tenant-Subdomain: testc
```

---

## 🛠️ Technical Implementation

### Files Modified:

1. **`lib/tenantDetection.ts`** (NEW)
   - `detectTenant()` - Main detection function
   - `getTenantFromQuery()` - Extract from ?tenant=
   - `getTenantFromPath()` - Extract from /login/tenant
   - `getTenantFromSubdomain()` - Extract from subdomain.localhost
   - `getTenantInfo()` - Fetch tenant details from API

2. **`app/login/page.tsx`** (UPDATED)
   - Uses `detectTenant()` on mount
   - Redirects to `/tenants` if no tenant found
   - Shows tenant name in UI
   - Sends tenant header on login

3. **`lib/tenantApi.ts`** (UPDATED)
   - Uses `detectTenant()` instead of just localStorage
   - Automatic header injection based on detection

---

## 🧪 Testing

### Test 1: Query Parameter
```bash
# Open browser:
http://localhost:3000/login?tenant=testc

# Expected:
✅ Page title shows "testc" or tenant name
✅ Login form is visible
✅ "Change Tenant" button is present
```

### Test 2: Direct Login (No Tenant)
```bash
# Open browser:
http://localhost:3000/login

# Expected:
✅ Redirects to /tenants
✅ Shows tenant selection page
```

### Test 3: Login Success
```bash
# Open: http://localhost:3000/login?tenant=testc
# Enter: admin / admin123
# Click: Login

# Expected:
✅ Shows loading state
✅ Redirects to /dashboard
✅ Token saved in localStorage
✅ Tenant saved in context
```

### Test 4: Network Request
```bash
# Open browser DevTools → Network
# Login with tenant

# Check request to /api/auth/login/:
✅ Method: POST
✅ Headers include: X-Tenant-Subdomain: testc
✅ Response: {access, refresh, role, tenant}
```

---

## 📊 Comparison Table

| Method | URL Example | Priority | Use Case |
|--------|-------------|----------|----------|
| **Query Param** | `/login?tenant=testc` | 🥇 Highest | Direct links, sharing |
| **Path** | `/login/testc` | 🥈 High | RESTful URLs |
| **Subdomain** | `testc.localhost:3000` | 🥉 Medium | Production SaaS |
| **localStorage** | `/login` (if stored) | 4️⃣ Lowest | Return visits |
| **Selector** | `/tenants` | N/A | First-time users |

---

## 🎯 Use Cases

### Use Case 1: Customer Support
**Scenario:** Support team needs to login to customer's tenant

**Solution:**
```
# Send this link to support team:
http://localhost:3000/login?tenant=customer_subdomain

# They don't need to select from dropdown
```

### Use Case 2: Email Links
**Scenario:** Send login link in email

**Solution:**
```html
<a href="https://yourdomain.com/login?tenant=demo">
  Login to Demo Account
</a>
```

### Use Case 3: Multi-tenant SaaS
**Scenario:** Each customer has their own subdomain

**Solution:**
```
https://acme.yourdomain.com  → tenant: acme
https://globex.yourdomain.com  → tenant: globex
```

### Use Case 4: API Integration
**Scenario:** Third-party app needs to authenticate

**Solution:**
```javascript
// Redirect user to:
const loginUrl = `https://yourdomain.com/login?tenant=${clientTenant}`;
window.location.href = loginUrl;
```

---

## 🔒 Security Notes

1. **Tenant Validation:**
   - النظام يتحقق من وجود الـ tenant في database
   - إذا لم يكن موجود، يظهر error
   - لا يمكن الوصول لـ tenant غير موجود

2. **Header Injection:**
   - `X-Tenant-Subdomain` يتم إضافته تلقائياً
   - لا يمكن للمستخدم تغييره بعد login
   - Backend يتحقق من الـ header

3. **Isolation:**
   - كل tenant له database منفصلة
   - JWT tokens خاصة بكل tenant
   - لا يمكن استخدام token من tenant آخر

---

## ✅ الخلاصة

**الآن يمكنك:**
- ✅ الوصول لأي tenant با `/login?tenant=testc`
- ✅ استخدام URLs نظيفة `/login/testc`
- ✅ دعم subdomains `testc.localhost:3000`
- ✅ النظام يرسل tenant header تلقائياً
- ✅ Redirect تلقائي إذا لم يكن tenant محدد

**جرب الآن:**
```
http://localhost:3000/login?tenant=testc
```

Username: `admin`  
Password: `admin123`

---

**Created:** October 23, 2025  
**Status:** ✅ Multi-Access Ready  
**Supports:** Query, Path, Subdomain, localStorage
