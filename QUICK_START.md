# 🚀 Quick Start Guide

## ابدأ في 3 خطوات فقط!

### 1️⃣ شغل Backend
```bash
cd "/home/ahmedyasser/lab/Saas/Second attempt/MicroSystem"
python manage.py runserver
```

### 2️⃣ شغل Frontend
**في terminal جديد:**
```bash
cd "/home/ahmedyasser/lab/Saas/Second attempt/MicroSystem/v0-micro-system"
npm run dev
```

### 3️⃣ افتح المتصفح
اذهب إلى: **http://localhost:3000/tenants**

---

## 🎯 اختبر الآن!

### الخيار 1: استخدم tenant "testc"
1. افتح http://localhost:3000/tenants
2. اختر **"testc"**
3. Username: `admin`
4. Password: `admin123`
5. اضغط **تسجيل الدخول**

### الخيار 2: استخدم أي tenant آخر
- اختر من القائمة المتاحة:
  - Demo Company (`demo`)
  - Test Company (`testcompany`)
  - Test Company A (`auth_test_a`)
  - Test DB Fix (`test_db_fix`)

---

## ✅ ما يجب أن يحدث

### بعد اختيار Tenant:
✅ يتم حفظ tenant في localStorage  
✅ Redirect لصفحة login  
✅ تظهر معلومات الـ tenant المحدد

### بعد تسجيل الدخول:
✅ يتم حفظ JWT tokens  
✅ Redirect للـ dashboard  
✅ جميع API calls تحتوي على tenant header تلقائياً

---

## 🐛 مشاكل شائعة

### المشكلة: "Connection refused"
**الحل:** تأكد من تشغيل Backend على port 8000

### المشكلة: صفحة بيضاء في Frontend
**الحل:** 
```bash
cd v0-micro-system
npm install
npm run dev
```

### المشكلة: CORS error
**الحل:** أعد تشغيل Backend بعد التعديلات

---

## 📖 مزيد من المعلومات

انظر:
- `READY_TO_USE.md` - التعليمات الكاملة
- `CORS_FIX_COMPLETE.md` - تفاصيل CORS
- `FRONTEND_IMPLEMENTATION_COMPLETE.md` - تفاصيل Frontend

---

**الآن جرب بنفسك!** 🎉
