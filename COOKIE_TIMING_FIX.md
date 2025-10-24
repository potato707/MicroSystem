# 🔧 Cookie Timing Fix

## 🐛 المشكلة الجديدة

```
✅ Login successful
✅ Cookies stored
✅ router.push('/dashboard') called
❌ Middleware checks cookies → Not found yet!
❌ Redirects back to /login?redirect=/dashboard
```

### السبب:
**Race Condition!** الـ cookies لا تُحفظ فوراً قبل أن يتحقق middleware منها.

---

## ✅ الحل المطبق

### 1. استخدام `window.location.href` بدلاً من `router.push()`
```typescript
// BEFORE:
router.push('/dashboard')

// AFTER:
window.location.href = '/dashboard'
```

**لماذا؟**
- `router.push()` = Client-side navigation (soft navigation)
- `window.location.href` = Full page reload (hard navigation)
- Hard navigation يضمن أن middleware يقرأ الـ cookies الجديدة

### 2. إضافة Small Delay
```typescript
// Wait for cookies to be set
await new Promise(resolve => setTimeout(resolve, 100))

// Then redirect
window.location.href = '/dashboard'
```

### 3. Console Logs للتحقق
```typescript
console.log('[tenantApi] Access token stored in localStorage and cookie')
console.log('[tenantApi] Current cookies:', document.cookie)
```

---

## 🧪 اختبر الآن!

### الخطوات:
1. افتح: `http://testc.localhost:3000/login`
2. أدخل: admin / admin123
3. اضغط Login
4. راقب Console

### النتيجة المتوقعة:
```
[LOGIN] Attempting login for tenant: testc
[tenantApi] Login response received, storing tokens...
[tenantApi] Access token stored in localStorage and cookie
[tenantApi] Current cookies: access_token=eyJ...; refresh_token=eyJ...
[LOGIN] Login successful, response: {...}
[LOGIN] Tenant context updated, waiting for cookies...
[LOGIN] Redirecting to dashboard...
✅ Full page reload to /dashboard
✅ Dashboard loads successfully!
```

---

## 📊 Comparison

| Method | Type | Cookies Read | Result |
|--------|------|--------------|--------|
| `router.push()` | Soft navigation | ❌ May miss | Redirect loop |
| `window.location.href` | Hard navigation | ✅ Always reads | Success! |

---

## 🔍 Debugging

إذا لم يعمل، تحقق من:

1. **Console logs:**
```
[tenantApi] Current cookies: ...
```
هل الـ cookies موجودة؟

2. **DevTools → Application → Cookies:**
هل `access_token` موجود؟

3. **Network tab:**
هل request لـ `/dashboard` يحتوي على cookies؟

---

**جرب الآن!** 🚀
