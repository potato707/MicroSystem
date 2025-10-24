# 🔧 Subdomain Cookie Issue - FIX

## 🐛 المشكلة مع Subdomains

### السبب الحقيقي:
عندما تستخدم **subdomain** مثل `testc.localhost:3000`، الـ cookies يجب أن تكون مضبوطة للـ **domain الصحيح**.

### المشكلة:
```javascript
// ❌ هذا لا يعمل مع subdomains:
document.cookie = `access_token=${token}; path=/; ...`

// Domain يكون: testc.localhost
// Cookie يُحفظ فقط لـ testc.localhost
// لكن middleware يقرأ من localhost
// النتيجة: Cookie not found!
```

### الحل:
```javascript
// ✅ يجب تحديد domain بشكل صريح:
document.cookie = `access_token=${token}; path=/; domain=.localhost; ...`

// الآن Cookie متاح لـ:
// - testc.localhost ✅
// - demo.localhost ✅
// - localhost ✅
// - أي subdomain.localhost ✅
```

---

## ✅ التغييرات المطبقة

### 1. lib/tenantApi.ts
```typescript
// Auto-detect if using localhost and set domain
const isLocalhost = window.location.hostname.includes('localhost');
const domain = isLocalhost ? 'domain=.localhost; ' : '';

document.cookie = `access_token=${token}; path=/; ${domain}max-age=...`;
```

### 2. src/contexts/TenantContext.tsx
```typescript
// Same logic for tenant cookies
const isLocalhost = window.location.hostname.includes('localhost');
const domain = isLocalhost ? 'domain=.localhost; ' : '';

document.cookie = `currentTenant=${...}; path=/; ${domain}max-age=...`;
```

### 3. middleware.ts
```typescript
// Added extensive logging:
console.log('[Middleware] Path:', path);
console.log('[Middleware] All cookies:', request.cookies.getAll());
console.log('[Middleware] Token found?', !!token);
```

---

## 🧪 Testing

### الخطوة 1: Clear Everything
افتح Chrome DevTools:
```
Application → Storage → Clear site data
```

### الخطوة 2: Login Again
```
1. افتح: http://testc.localhost:3000/login
2. أدخل: admin / admin123
3. اضغط Login
```

### الخطوة 3: Check Console
يجب أن ترى:
```
[tenantApi] Current cookies: access_token=...; refresh_token=...; currentTenant=...
[tenantApi] Current hostname: testc.localhost
[LOGIN] Redirecting to dashboard...

→ Page reloads

[Middleware] Path: /dashboard
[Middleware] All cookies: [
  {name: 'access_token', value: 'eyJ...'},
  {name: 'refresh_token', value: 'eyJ...'},
  {name: 'currentTenant', value: '{"subdomain":"testc"...}'}
]
[Middleware] Is protected path? true
[Middleware] Token found? true
[Middleware] TOKEN FOUND - Allowing access

✅ Dashboard loads!
```

### الخطوة 4: Check Cookies in DevTools
```
Application → Cookies → http://testc.localhost:3000

يجب أن ترى:
Name: access_token
Value: eyJ...
Domain: .localhost     ← مهم! يبدأ بنقطة
Path: /
```

---

## 🔍 Debugging

### إذا لم تظهر Cookies:

#### Check 1: Domain في Cookie
```javascript
// في Console:
document.cookie

// يجب أن ترى:
"access_token=...; domain=.localhost"
```

#### Check 2: الـ /etc/hosts صحيح؟
```bash
cat /etc/hosts | grep localhost

# يجب أن يكون:
127.0.0.1 localhost
127.0.0.1 testc.localhost
127.0.0.1 demo.localhost
```

#### Check 3: Middleware Logs
```
[Middleware] All cookies: []  ← إذا فاضي، المشكلة في domain!
```

---

## 📊 Cookie Domain Comparison

| Cookie Setting | Works on localhost | Works on testc.localhost | Works on demo.localhost |
|----------------|-------------------|-------------------------|------------------------|
| `(no domain)` | ✅ Yes | ❌ No | ❌ No |
| `domain=localhost` | ✅ Yes | ❌ No | ❌ No |
| `domain=.localhost` | ✅ Yes | ✅ Yes | ✅ Yes |
| `domain=testc.localhost` | ❌ No | ✅ Yes | ❌ No |

**الحل الصحيح:** `domain=.localhost` ← يعمل على جميع subdomains!

---

## 🎯 Why the Dot Matters

### Without Dot (domain=localhost):
```
Cookie domain: localhost (exact match only)
testc.localhost tries to read → ❌ Not found!
```

### With Dot (domain=.localhost):
```
Cookie domain: .localhost (includes all subdomains)
testc.localhost tries to read → ✅ Found!
demo.localhost tries to read → ✅ Found!
localhost tries to read → ✅ Found!
```

---

## ✅ الخلاصة

**المشكلة:** Cookies لا تُقرأ في subdomains  
**السبب:** Domain غير محدد أو محدد خطأ  
**الحل:** استخدام `domain=.localhost` للـ development  

**للـ Production:**
```typescript
// Use your actual domain:
const domain = isProduction ? 'domain=.yourdomain.com; ' : 'domain=.localhost; ';
```

---

## 🚀 جرب الآن!

1. **Clear all cookies وlocal storage**
2. **Login مرة أخرى**
3. **شاهد الـ console logs**
4. **تحقق من الـ cookies في DevTools**

**يجب أن يعمل الآن!** ✅

---

**Fixed:** October 23, 2025  
**Issue:** Subdomain cookie domain  
**Solution:** `domain=.localhost`  
**Status:** Ready for testing 🚀
