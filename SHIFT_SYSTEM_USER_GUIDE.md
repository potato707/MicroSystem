# 🎯 نظام الشيفتات الكامل - دليل المستخدم النهائي

## 📚 جدول المحتويات
1. [نظرة عامة](#نظرة-عامة)
2. [الصفحات المتاحة](#الصفحات-المتاحة)
3. [سير العمل الكامل](#سير-العمل-الكامل)
4. [حساب الرواتب التلقائي](#حساب-الرواتب-التلقائي)
5. [الوثائق التفصيلية](#الوثائق-التفصيلية)

---

## 🌟 نظرة عامة

### ما هو النظام؟
نظام شامل لإدارة الشيفتات والحضور وحساب الرواتب تلقائياً بناءً على:
- ✅ جداول شيفتات أسبوعية مرنة (كل يوم له شيفت مختلف)
- ✅ كشف التأخير تلقائياً مع فترة سماح 15 دقيقة
- ✅ حساب الساعات الإضافية مع فترة سماح 30 دقيقة
- ✅ حساب الراتب تلقائياً بناءً على الساعات الفعلية
- ✅ مراقبة حية لحضور الموظفين في الوقت الفعلي

### المكونات الرئيسية:
1. **Backend (Django):** 32 API endpoint
2. **Frontend (Next.js):** صفحتين رئيسيتين
3. **Database:** 3 جداول جديدة
4. **Signals:** حساب تلقائي للرواتب

---

## 📱 الصفحات المتاحة

### 1. **إدارة جداول الدوام** (`/dashboard/shifts/schedules`)
**من يستخدمها:** المديرون والإداريون

**المميزات:**
- 📝 اختيار موظف من القائمة
- 📅 تحديد شيفت مختلف لكل يوم (الأحد → السبت)
- ⏰ تحديد وقت البداية والنهاية لكل يوم
- ✅ تفعيل/إلغاء أيام العمل
- 📊 حساب تلقائي لإجمالي الساعات الأسبوعية
- ⚡ إجراءات سريعة: تطبيق نفس الوقت على جميع الأيام
- 💾 حفظ الجدول كاملاً دفعة واحدة

**كيفية الاستخدام:**
```
1. افتح http://localhost:3000/dashboard/shifts/schedules
2. اختر الموظف من القائمة
3. حدد أيام العمل (ضع ✓ على كل يوم)
4. حدد وقت البداية والنهاية لكل يوم
5. راجع الملخص (عدد الأيام وإجمالي الساعات)
6. اضغط "حفظ الجدول"
```

**مثال:**
```
الموظف: أحمد محمد
الأحد: 9:00 AM - 5:00 PM (8 ساعات)
الإثنين: 9:00 AM - 5:00 PM (8 ساعات)
الثلاثاء: 9:00 AM - 5:00 PM (8 ساعات)
الأربعاء: 9:00 AM - 5:00 PM (8 ساعات)
الخميس: 9:00 AM - 1:00 PM (4 ساعات)
الجمعة: إجازة
السبت: 6:00 AM - 10:00 AM (4 ساعات)

إجمالي: 40 ساعة أسبوعياً
```

---

### 2. **مراقبة الدوام الحية** (`/dashboard/shifts/monitor`)
**من يستخدمها:** المديرون والإداريون

**المميزات:**
- 👁️ عرض حالة جميع الموظفين في الوقت الفعلي
- 🔄 تحديث تلقائي كل 30 ثانية
- 📊 إحصائيات فورية:
  - عدد الموظفين على الشيفت
  - عدد الحاضرين
  - عدد المتأخرين
  - عدد الذين لم يسجلوا حضور
- 🎨 ألوان مميزة:
  - أخضر: حاضر في الوقت
  - أصفر: متأخر
  - برتقالي: لم يسجل حضور بعد
- ⏱️ عرض دقائق التأخير
- 🕐 عرض وقت تسجيل الحضور

**كيفية الاستخدام:**
```
1. افتح http://localhost:3000/dashboard/shifts/monitor
2. شاهد قائمة الموظفين الحالية
3. الصفحة تتحدث تلقائياً كل 30 ثانية
4. يمكنك الضغط على "تحديث" للتحديث اليدوي
```

---

## 🔄 سير العمل الكامل

### **الخطوة 1: إعداد الجداول**
```
المدير → /dashboard/shifts/schedules
- يختار الموظف
- يحدد شيفت كل يوم
- يحفظ الجدول
✅ الجدول محفوظ في قاعدة البيانات
```

### **الخطوة 2: الموظف يسجل حضور**
```
الموظف → يفتح التطبيق
- يضغط "تسجيل حضور"
- API: POST /hr/attendance/checkin/{employee_id}/

النظام يفحص:
1. يجلب الشيفت المحدد لليوم الحالي
2. يقارن الوقت الحالي بوقت البداية المتوقع
3. فترة السماح: 15 دقيقة
   - إذا حضر قبل 6:15 AM (للشيفت 6:00 AM) → present ✅
   - إذا حضر بعد 6:15 AM → late ⚠️ + عدد دقائق التأخير

✅ الحضور مسجل في EmployeeAttendance
✅ WorkShift جديد تم إنشاؤه
```

### **الخطوة 3: المراقبة الحية**
```
المدير → /dashboard/shifts/monitor

يشاهد:
- أحمد محمد: late (20 دقيقة تأخير) ⚠️
- سارة علي: present ✅
- محمد حسن: لم يسجل حضور بعد 🔴

التحديث التلقائي كل 30 ثانية
```

### **الخطوة 4: الموظف يسجل انصراف**
```
الموظف → يضغط "تسجيل انصراف"
- API: POST /hr/attendance/checkout/{employee_id}/

النظام يحسب:
1. إجمالي الساعات الفعلية
2. خصم وقت الاستراحة (ساعة للشيفتات >6 ساعات)
3. الساعات الإضافية (فترة سماح 30 دقيقة)

مثال:
- الشيفت: 6:00 AM - 10:00 AM (4 ساعات)
- الحضور: 8:29 AM
- الانصراف: 10:30 AM
- الساعات الفعلية: 2.02 ساعة
- الساعات الإضافية: 0 (لم يتجاوز 10:30 AM)

✅ WorkShift.check_out محدث
✅ EmployeeAttendance.check_out محدث
```

### **الخطوة 5: حساب الراتب التلقائي**
```
🤖 Signal يشتغل تلقائياً عند حفظ check_out

الحسابات:
1. الراتب الشهري: 6000 جنيه
2. راتب الساعة: (6000 / 30) / 8 = 25 جنيه/ساعة
3. الساعات الفعلية: 2.02 ساعة
4. الراتب: 25 × 2.02 = 50.50 جنيه

✅ يضاف 50.50 جنيه لـ MainWallet
✅ MultiWalletTransaction مسجلة
✅ يظهر في الرصيد فوراً
```

### **الخطوة 6: الموظف يفحص رصيده**
```
الموظف → Dashboard
- API: GET /hr/employee-dashboard-stats/

Response:
{
  "attendance_today": {
    "status": "late",
    "late_minutes": 149,
    "checked_in": "08:29",
    "checked_out": "10:30"
  },
  "wallet_data": {
    "main_balance": "175.50",  ← زاد 50.50 جنيه!
    "total_balance": "175.50"
  }
}

✅ الموظف يرى رصيده المحدث
```

---

## 💰 حساب الرواتب التلقائي

### **كيف يعمل؟**

#### **1. عند Check-out:**
```python
# Signal يتم تشغيله تلقائياً
@receiver(post_save, sender=WorkShift)
def calculate_shift_salary(sender, instance, **kwargs):
    if instance.check_out:  # ← عند حفظ check_out
        # يبدأ الحساب
```

#### **2. الخطوات:**
```python
# أ. جلب الشيفت المحدد
shift_schedule = WeeklyShiftSchedule.objects.get(
    employee=employee,
    day_of_week=السبت  # مثلاً
)
scheduled_hours = 4  # من 6 AM إلى 10 AM

# ب. حساب الساعات الفعلية
worked_hours = (check_out - check_in).hours - break_time
# مثلاً: 2.02 ساعة

# ج. حساب الراتب الأساسي
hourly_rate = (monthly_salary / 30) / 8
base_salary = hourly_rate * worked_hours
# 25 × 2.02 = 50.50 جنيه

# د. حساب الساعات الإضافية (إن وجدت)
if worked_hours > scheduled_hours:
    overtime = worked_hours - scheduled_hours
    overtime_pay = overtime * (hourly_rate * 1.5)
    total_salary = base_salary + overtime_pay
else:
    total_salary = base_salary

# هـ. إضافة للمحفظة
create_multi_wallet_transaction(
    wallet_type='main',
    amount=total_salary,
    description=f"Shift salary - {date}"
)
```

### **أمثلة:**

#### **مثال 1: موظف متأخر**
```
الراتب الشهري: 6000 جنيه
الشيفت: 6:00 - 10:00 (4 ساعات)
الحضور: 8:29 AM
الانصراف: 10:00 AM
الساعات الفعلية: 1.52 ساعة

الحساب:
راتب الساعة = (6000/30)/8 = 25 جنيه
الراتب = 25 × 1.52 = 38 جنيه

النتيجة: 38 جنيه ✅
(خصم بسبب عدم إكمال الـ 4 ساعات)
```

#### **مثال 2: موظف + ساعات إضافية**
```
الراتب الشهري: 6000 جنيه
الشيفت: 6:00 - 10:00 (4 ساعات)
الحضور: 6:00 AM
الانصراف: 11:00 AM
الساعات الفعلية: 5 ساعات

الحساب:
راتب الساعة = 25 جنيه
الراتب الأساسي = 25 × 4 = 100 جنيه
الساعات الإضافية = 1 ساعة
معدل الإضافي = 25 × 1.5 = 37.5 جنيه
راتب الإضافي = 37.5 × 1 = 37.5 جنيه

النتيجة: 100 + 37.5 = 137.5 جنيه 🎉
```

---

## 📊 APIs المتاحة

### **Shift Schedules:**
```bash
# إنشاء جدول أسبوعي كامل
POST /hr/api/shift-schedules/bulk_create/
{
  "employee": "uuid",
  "schedules": [
    {"day_of_week": 6, "start_time": "06:00", "end_time": "10:00"}
  ]
}

# جلب جدول موظف
GET /hr/api/shift-schedules/employee_schedule/?employee_id=uuid

# تحديث يوم معين
PUT /hr/api/shift-schedules/{id}/

# حذف يوم
DELETE /hr/api/shift-schedules/{id}/
```

### **Attendance:**
```bash
# تسجيل حضور
POST /hr/attendance/checkin/{employee_id}/
Response: {status: "late", late_minutes: 20}

# تسجيل انصراف
POST /hr/attendance/checkout/{employee_id}/
Response: {total_hours: 2.02, overtime_minutes: 0}

# الحالة الحالية
GET /hr/api/shift-attendance/current_status/
```

### **Monitoring:**
```bash
# حالة جميع الموظفين على الشيفت الآن
GET /hr/api/shift-attendance/current_status/

# تقرير يومي
GET /hr/api/shift-attendance/daily_report/?date=2025-10-18

# ملخص شهري لموظف
GET /hr/api/shift-attendance/employee_summary/?employee_id=uuid&month=10&year=2025
```

---

## 📚 الوثائق التفصيلية

### **الملفات المتاحة:**

1. **SHIFT_QUICK_START.md**
   - دليل البداية السريعة
   - أوامر الاختبار
   - Troubleshooting

2. **SHIFT_SYSTEM_COMPLETE.md**
   - نظرة شاملة على النظام
   - إحصائيات كاملة
   - الملفات المعدلة

3. **SHIFT_INTEGRATION_WITH_ATTENDANCE.md**
   - كيف يتكامل مع نظام الحضور
   - معادلات حساب التأخير
   - أمثلة عملية

4. **SALARY_CALCULATION_EXPLAINED.md**
   - شرح تفصيلي لحساب الرواتب
   - Signal flow
   - Test cases

5. **SHIFT_SCHEDULING_DESIGN.md**
   - التصميم الأصلي للنظام
   - Database schema
   - API specifications

---

## 🎯 Quick Reference

### **البداية السريعة:**
```bash
# 1. Start servers
python manage.py runserver
cd v0-micro-system && npm run dev

# 2. إنشاء جداول
http://localhost:3000/dashboard/shifts/schedules

# 3. مراقبة
http://localhost:3000/dashboard/shifts/monitor
```

### **المميزات الرئيسية:**
- ✅ شيفت مختلف لكل يوم
- ✅ كشف تأخير تلقائي (15 دقيقة سماح)
- ✅ حساب ساعات إضافية (30 دقيقة سماح)
- ✅ راتب تلقائي بناءً على الساعات الفعلية
- ✅ مراقبة حية
- ✅ تحديث كل 30 ثانية

### **الإحصائيات:**
- 📊 **Backend:** 32 API endpoint
- 📊 **Frontend:** صفحتين + sidebar integration
- 📊 **Database:** 3 tables جديدة
- 📊 **Code:** ~2,000 lines
- 📊 **Docs:** 5 ملفات توثيق

---

## 🆘 الدعم

### **مشكلة شائعة: الموظف متأخر لكن يظهر "present"**
**الحل:**
1. تأكد من وجود `WeeklyShiftSchedule` محدد
2. تحقق من `day_of_week` صحيح
3. راجع `start_time` في الشيفت

### **مشكلة: الراتب لا يُحسب**
**الحل:**
1. تأكد من `check_out` محفوظ
2. تحقق من وجود `WeeklyShiftSchedule`
3. تأكد من الساعات > 1 ساعة

### **للمساعدة:**
راجع `SHIFT_INTEGRATION_WITH_ATTENDANCE.md` قسم Debugging

---

**🎉 النظام جاهز ويعمل بكفاءة!**

تاريخ آخر تحديث: أكتوبر 2025
