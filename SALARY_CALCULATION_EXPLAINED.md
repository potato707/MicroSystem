# 💰 شرح نظام حساب الرواتب التلقائي

## 🔄 كيف يعمل النظام

### **الـ Signal المسؤول:**
`@receiver(post_save, sender=WorkShift)` في `hr_management/signals.py`

يتم تشغيله **تلقائياً** عند:
- ✅ حفظ `WorkShift` بعد الـ check-out
- ✅ تحديث `WorkShift.check_out` من `None` إلى وقت محدد

---

## 📊 خطوات حساب الراتب

### 1. **جلب بيانات الشيفت المحدد**
```python
# يفحص WeeklyShiftSchedule للموظف لهذا اليوم
shift_schedule = WeeklyShiftSchedule.objects.get(
    employee=employee,
    day_of_week=our_day_of_week,  # السبت=6
    is_active=True
)

# يحصل على:
shift_hours = shift_schedule.calculate_hours()  # مثلاً: 4 ساعات (6 AM - 10 AM)
```

### 2. **حساب الساعات الفعلية**
```python
# الوقت الفعلي
check_in_datetime = instance.check_in    # مثلاً: 8:29 AM
check_out_datetime = instance.check_out  # مثلاً: 10:30 AM

# حساب المدة
worked_seconds = (check_out - check_in).total_seconds() - (break_minutes * 60)
worked_hours = worked_seconds / 3600  # مثلاً: 2.02 ساعة
```

### 3. **حساب الراتب الأساسي**
```python
# الراتب الشهري ÷ 30 يوم ÷ 8 ساعات = راتب الساعة
monthly_salary = 5000  # مثال
daily_salary = 5000 / 30 = 166.67
hourly_rate = 166.67 / 8 = 20.83 جنيه/ساعة

# الراتب الأساسي
base_hours = min(worked_hours, shift_hours)  # الأقل بين الفعلي والمجدول
base_salary = hourly_rate * base_hours
```

### 4. **حساب الساعات الإضافية (Overtime)**
```python
if worked_hours > shift_hours:
    overtime_hours = worked_hours - shift_hours
    overtime_rate = hourly_rate * 1.5  # أو employee.overtime_rate
    overtime_pay = overtime_rate * overtime_hours
    total_salary = base_salary + overtime_pay
else:
    total_salary = base_salary
```

### 5. **إضافة الراتب للمحفظة**
```python
# يضيف تلقائياً في MainWallet
create_multi_wallet_transaction(
    wallet_system=wallet_system,
    wallet_type='main',
    transaction_type='salary_credit',
    amount=total_salary,
    description=f"Shift salary for {employee.name} - {date}"
)
```

---

## 🧮 أمثلة عملية

### **مثال 1: موظف متأخر لكن أكمل شيفته**

**البيانات:**
- الراتب الشهري: 6000 جنيه
- الشيفت المحدد: 6:00 AM - 10:00 AM (4 ساعات)
- الحضور الفعلي: 8:29 AM
- الانصراف الفعلي: 10:00 AM
- الساعات الفعلية: 1.52 ساعة

**الحسابات:**
```python
hourly_rate = (6000 / 30) / 8 = 25 جنيه/ساعة
worked_hours = 1.52 ساعة
base_salary = 25 * 1.52 = 38 جنيه

# لا توجد ساعات إضافية (لم يتجاوز 4 ساعات)
total_salary = 38 جنيه ✅
```

**النتيجة:**
- ✅ يضاف 38 جنيه للمحفظة تلقائياً
- ⚠️ خصم بسبب التأخير (لم يعمل الـ 4 ساعات كاملة)

---

### **مثال 2: موظف في الوقت + ساعات إضافية**

**البيانات:**
- الراتب الشهري: 6000 جنيه
- الشيفت المحدد: 6:00 AM - 10:00 AM (4 ساعات)
- الحضور الفعلي: 6:00 AM
- الانصراف الفعلي: 11:00 AM
- الساعات الفعلية: 5 ساعات

**الحسابات:**
```python
hourly_rate = 25 جنيه/ساعة
base_hours = 4 ساعات (المجدول)
base_salary = 25 * 4 = 100 جنيه

overtime_hours = 5 - 4 = 1 ساعة
overtime_rate = 25 * 1.5 = 37.5 جنيه/ساعة
overtime_pay = 37.5 * 1 = 37.5 جنيه

total_salary = 100 + 37.5 = 137.5 جنيه ✅
```

**النتيجة:**
- ✅ يضاف 137.5 جنيه للمحفظة
- 🎉 بونص ساعات إضافية!

---

### **مثال 3: شيفت طويل (مع خصم استراحة)**

**البيانات:**
- الراتب الشهري: 6000 جنيه
- الشيفت المحدد: 8:00 AM - 6:00 PM (10 ساعات)
- الحضور الفعلي: 8:00 AM
- الانصراف الفعلي: 6:00 PM
- الساعات الفعلية: 10 ساعات
- **خصم استراحة:** 1 ساعة (للشيفتات >6 ساعات)

**الحسابات:**
```python
hourly_rate = 25 جنيه/ساعة
worked_hours = 10 - 1 (استراحة) = 9 ساعات
scheduled_hours = 10 - 1 = 9 ساعات

base_salary = 25 * 9 = 225 جنيه
# لا توجد ساعات إضافية
total_salary = 225 جنيه ✅
```

---

## ⚙️ متى يتم تشغيل الحساب

### **تلقائياً عند:**

1. **CheckOut API:**
```bash
POST /hr/attendance/checkout/{employee_id}/
# Signal يتم تشغيله تلقائياً بعد حفظ check_out
```

2. **تحديث WorkShift:**
```python
shift = WorkShift.objects.get(id=shift_id)
shift.check_out = timezone.now()
shift.save()  # ← Signal يشتغل هنا
```

3. **Admin Panel:**
عند تعديل `WorkShift` من لوحة التحكم وحفظه

---

## 🔍 تتبع الراتب

### **طريقة 1: فحص المحفظة**
```bash
GET /hr/api/employee-dashboard-stats/
```
Response:
```json
{
  "wallet_data": {
    "main_balance": "125.00",  ← هنا الراتب المتراكم
    "reimbursement_balance": "30.00",
    "advance_balance": "0.00"
  }
}
```

### **طريقة 2: فحص Transactions**
```python
from hr_management.models import MultiWalletTransaction

transactions = MultiWalletTransaction.objects.filter(
    wallet_system__employee=employee,
    transaction_type='salary_credit'
).order_by('-created_at')

for trans in transactions:
    print(f"{trans.created_at}: {trans.amount} - {trans.description}")
```

Output مثال:
```
2025-10-18 10:30: 38.00 - Shift salary for Ahmed - 2025-10-18 (regular: 1.5h)
2025-10-17 17:00: 137.50 - Shift salary for Ahmed - 2025-10-17 (regular: 5.0h + 1.0h OT)
```

---

## ⚠️ حالات خاصة

### **1. موظف بدون جدول شيفت محدد**
```python
# Fallback: يستخدم 8 ساعات كقيمة افتراضية
shift_hours = 8  # Default
```

### **2. موظف عمل أقل من ساعة**
```python
if worked_hours < 1:
    total_salary = 0  # ❌ لا راتب
```

### **3. موظف في إجازة مدفوعة**
```python
if attendance.status == 'on_leave' and is_paid_leave:
    daily_salary = (monthly_salary / 30)
    # يضاف الراتب اليومي كامل ✅
```

---

## 🧪 اختبار النظام

### **Test Case 1: فحص الراتب بعد Check-out**
```bash
# 1. Check-in
POST /hr/attendance/checkin/{employee_id}/

# 2. Check-out (بعد ساعات)
POST /hr/attendance/checkout/{employee_id}/

# 3. فحص المحفظة
GET /hr/api/employee-dashboard-stats/
# يجب أن ترى main_balance زادت ✅
```

### **Test Case 2: فحص Transaction Details**
```python
python manage.py shell

from hr_management.models import EmployeeWalletSystem, MultiWalletTransaction
from hr_management.models import Employee

employee = Employee.objects.get(id='uuid-here')
wallet = EmployeeWalletSystem.objects.get(employee=employee)

# اخر 5 معاملات
transactions = MultiWalletTransaction.objects.filter(
    wallet_system=wallet,
    wallet_type='main'
).order_by('-created_at')[:5]

for t in transactions:
    print(f"{t.transaction_type}: {t.amount} - {t.description}")
```

---

## 📝 ملاحظات مهمة

### ✅ **النظام الجديد:**
- يستخدم `WeeklyShiftSchedule` لتحديد الساعات المجدولة
- يحسب الساعات الإضافية تلقائياً
- يدعم شيفتات مختلفة لكل يوم في الأسبوع
- يخصم وقت الاستراحة للشيفتات الطويلة

### ⚠️ **Backward Compatibility:**
- لو مفيش `WeeklyShiftSchedule` → يستخدم 8 ساعات افتراضي
- Legacy Wallet System لا يزال يعمل بجانب Multi-Wallet

### 💡 **أفضل الممارسات:**
1. تأكد من إنشاء `WeeklyShiftSchedule` لجميع الموظفين
2. راجع معدل الـ overtime (`employee.overtime_rate`)
3. تحقق من الـ transactions بانتظام
4. استخدم `SHIFT_INTEGRATION_WITH_ATTENDANCE.md` كمرجع

---

## 🚀 الخلاصة

**النظام يعمل تلقائياً 100%!**

عند كل check-out:
1. ✅ يفحص الشيفت المحدد
2. ✅ يحسب الساعات الفعلية
3. ✅ يخصم وقت الاستراحة
4. ✅ يحسب الساعات الإضافية
5. ✅ يضيف الراتب للمحفظة
6. ✅ يسجل transaction مفصلة

**لا تحتاج لفعل شيء يدوياً!** 🎉
