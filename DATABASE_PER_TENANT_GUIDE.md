# 🏗️ نظام قواعد البيانات المنفصلة لكل عميل (Database-per-Tenant)

## 📋 نظرة عامة

تم تحويل النظام من **Shared Database** (قاعدة بيانات مشتركة) إلى **Database-per-Tenant** (قاعدة بيانات منفصلة لكل عميل).

---

## 🎯 ما الذي تغير؟

### قبل (Shared Database):
```
┌─────────────────────────────────┐
│   قاعدة بيانات واحدة (db.sqlite3)│
├─────────────────────────────────┤
│  Users (مشتركة)                │
│  Tenants (metadata فقط)         │
│  Employees (tenant_id filter)   │
│  Attendance (tenant_id filter)  │
└─────────────────────────────────┘
```

### بعد (Database-per-Tenant):
```
┌─────────────────┐  
│ db.sqlite3      │  ← قاعدة بيانات رئيسية (Tenant metadata فقط)
│ - Tenants       │
│ - ModuleDef     │
└─────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ tenant_demo.db   │  │ tenant_abc.db    │  │ tenant_xyz.db    │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│ ✅ Users         │  │ ✅ Users         │  │ ✅ Users         │
│ ✅ Superuser     │  │ ✅ Superuser     │  │ ✅ Superuser     │
│ ✅ Employees     │  │ ✅ Employees     │  │ ✅ Employees     │
│ ✅ Attendance    │  │ ✅ Attendance    │  │ ✅ Attendance    │
│ ✅ Tasks         │  │ ✅ Tasks         │  │ ✅ Tasks         │
│ ✅ Wallet        │  │ ✅ Wallet        │  │ ✅ Wallet        │
│ ✅ Complaints    │  │ ✅ Complaints    │  │ ✅ Complaints    │
│ ✅ Notifications │  │ ✅ Notifications │  │ ✅ Notifications │
└──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## ✨ المميزات الجديدة

### 1. عزل كامل للبيانات
```
✅ كل عميل له قاعدة بيانات منفصلة تماماً
✅ لا يمكن لعميل الوصول لبيانات عميل آخر (حتى بخطأ برمجي)
✅ مستخدمين منفصلين لكل عميل
✅ superuser منفصل لكل عميل
```

### 2. أمان محسّن
```
✅ استحالة تسريب البيانات بين العملاء
✅ كل عميل يمكنه إدارة مستخدميه بشكل مستقل
✅ صلاحيات منفصلة تماماً
```

### 3. نسخ احتياطي مستقل
```
✅ يمكن أخذ backup لكل عميل على حدة
✅ يمكن استعادة بيانات عميل دون التأثير على الآخرين
✅ سهولة ترحيل عميل إلى server منفصل
```

### 4. أداء أفضل
```
✅ استعلامات أسرع (جداول أصغر)
✅ لا حاجة لـ tenant_id في كل query
✅ indexes أصغر وأسرع
```

---

## 🚀 كيفية إنشاء عميل جديد

### الطريقة 1: باستخدام Django Admin (موصى بها)

#### الخطوة 1: إنشاء Tenant في Django Admin
```bash
# افتح Django Admin
http://localhost:8000/admin/

# اذهب إلى: HR Management → Tenants → Add Tenant
# املأ النموذج:
- Name: شركة تجريبية
- Subdomain: demo
- Primary Color: #3498db
- Secondary Color: #2ecc71

# احفظ
```

#### الخطوة 2: إعداد قاعدة البيانات
```bash
# في terminal:
python manage.py setup_tenant demo --admin-password yourpassword
```

**ستحصل على:**
```
============================================================
TENANT ACCESS INFORMATION:
============================================================
  Subdomain:  demo
  Database:   tenant_demo
  Admin User: admin
  Password:   yourpassword
  Modules:    8
============================================================
✓ Tenant setup complete!
```

---

### الطريقة 2: من Python Shell

```python
python manage.py shell

# إنشاء tenant
from hr_management.tenant_models import Tenant
from hr_management.tenant_service import TenantService

# 1. إنشاء tenant في القاعدة الرئيسية
tenant = Tenant.objects.create(
    name='شركة تجريبية',
    subdomain='demo',
    primary_color='#3498db',
    secondary_color='#2ecc71',
    is_active=True
)

# 2. إعداد قاعدة البيانات الكاملة
results = TenantService.setup_complete_tenant(tenant, admin_password='admin123')

# 3. عرض النتائج
print(f"Database: {results['db_alias']}")
print(f"Admin created: {results['superuser_created']}")
print(f"Modules: {results['modules_count']}")
```

---

## 🔍 التحقق من إنشاء قاعدة البيانات

### 1. التحقق من ملفات قاعدة البيانات
```bash
# عرض جميع ملفات قواعد البيانات
ls -lh *.sqlite3

# يجب أن ترى:
# db.sqlite3            ← القاعدة الرئيسية
# tenant_demo.sqlite3   ← قاعدة بيانات demo
# tenant_abc.sqlite3    ← قاعدة بيانات abc
```

### 2. التحقق من الجداول
```bash
# فتح قاعدة بيانات العميل
sqlite3 tenant_demo.sqlite3

# عرض الجداول
.tables

# يجب أن ترى:
# auth_user
# hr_management_employee
# hr_management_attendance
# hr_management_wallet
# hr_management_task
# ... إلخ
```

### 3. التحقق من المستخدمين
```bash
# من Python
python -c "
from django.contrib.auth import get_user_model
User = get_user_model()

# مستخدمي demo
demo_users = User.objects.using('tenant_demo').all()
print(f'Demo users: {demo_users.count()}')
for u in demo_users:
    print(f'  - {u.username} (admin: {u.is_superuser})')

# مستخدمي abc
abc_users = User.objects.using('tenant_abc').all()
print(f'ABC users: {abc_users.count()}')
"
```

---

## 🔐 تسجيل الدخول لكل عميل

### API Endpoint

```bash
# الحصول على Token للعميل demo
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: demo" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'

# النتيجة:
{
  "refresh": "...",
  "access": "..."
}
```

### تسجيل الدخول من Django Admin

**مشكلة:** Django admin يستخدم القاعدة الافتراضية فقط، لا يمكن تسجيل الدخول بمستخدمي tenant.

**الحل:** استخدم API endpoints أو أنشئ admin منفصل لكل tenant.

---

## 📊 الوصول إلى البيانات

### من API
```bash
# الحصول على employees لـ demo
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Tenant-Subdomain: demo" \
  http://localhost:8000/hr/employees/

# ستحصل فقط على employees من قاعدة بيانات demo
```

### من Python Code
```python
from hr_management.models import Employee
from hr_management.tenant_db_router import set_current_tenant
from hr_management.tenant_models import Tenant

# الحصول على tenant
tenant = Tenant.objects.get(subdomain='demo')

# تعيين tenant الحالي (للـ router)
set_current_tenant(tenant)

# الآن جميع الاستعلامات ستذهب إلى tenant_demo
employees = Employee.objects.all()  # من tenant_demo فقط
attendance = Attendance.objects.all()  # من tenant_demo فقط

# أو استخدم .using() مباشرة
employees = Employee.objects.using('tenant_demo').all()
```

---

## 🛠️ إدارة قواعد البيانات

### إضافة عمود جديد (Migration)

```bash
# 1. إنشاء migration
python manage.py makemigrations

# 2. تطبيق على القاعدة الرئيسية (metadata فقط)
python manage.py migrate

# 3. تطبيق على جميع tenant databases
python manage.py migrate --database=tenant_demo
python manage.py migrate --database=tenant_abc
python manage.py migrate --database=tenant_xyz

# أو تطبيق على الجميع تلقائياً:
for db in tenant_*; do
    db_name="${db%.sqlite3}"
    python manage.py migrate --database="$db_name"
done
```

### نسخ احتياطي لعميل محدد

```bash
# نسخ احتياطي لـ demo
cp tenant_demo.sqlite3 backups/tenant_demo_$(date +%Y%m%d).sqlite3

# استعادة
cp backups/tenant_demo_20251022.sqlite3 tenant_demo.sqlite3
```

### حذف عميل نهائياً

```bash
# 1. حذف من القاعدة الرئيسية
python -c "
from hr_management.tenant_models import Tenant
Tenant.objects.get(subdomain='demo').delete()
"

# 2. حذف قاعدة البيانات
rm tenant_demo.sqlite3

# 3. حذف مجلد التطبيق
rm -rf tenants/demo/
```

---

## ⚠️ ملاحظات مهمة

### 1. Django Admin
```
❌ لا يعمل Django admin مع tenant databases بشكل افتراضي
✅ الحل: استخدم API endpoints أو أنشئ admin interface منفصل
```

### 2. Migrations
```
⚠️ يجب تطبيق migrations على كل tenant database يدوياً
✅ يمكن أتمتة ذلك بـ script
```

### 3. Module Definitions
```
ℹ️ ModuleDefinition يبقى في القاعدة الرئيسية (shared)
ℹ️ TenantModule يُنشأ في كل tenant database
```

### 4. الأداء
```
✅ أسرع للاستعلامات (جداول أصغر)
⚠️ أبطأ لإنشاء tenant جديد (يحتاج migrations)
```

---

## 🧪 اختبار النظام

### سكريبت اختبار شامل

```bash
#!/bin/bash
# test_multi_tenant_db.sh

echo "🧪 Testing Multi-Tenant Database System"
echo "========================================"

# 1. إنشاء tenant جديد
echo "1. Creating test tenant..."
python -c "
from hr_management.tenant_models import Tenant
from hr_management.tenant_service import TenantService

tenant = Tenant.objects.create(
    name='Test Company',
    subdomain='test123',
    is_active=True
)
print(f'✓ Tenant created: {tenant.name}')

# Setup database
results = TenantService.setup_complete_tenant(tenant, 'testpass')
print(f'✓ Database: {results[\"db_alias\"]}')
print(f'✓ Admin created: {results[\"superuser_created\"]}')
"

# 2. التحقق من الملفات
echo ""
echo "2. Checking database files..."
if [ -f "tenant_test123.sqlite3" ]; then
    echo "✓ Database file created"
else
    echo "✗ Database file NOT found"
fi

# 3. التحقق من المستخدمين
echo ""
echo "3. Checking users..."
python -c "
from django.contrib.auth import get_user_model
User = get_user_model()

users = User.objects.using('tenant_test123').all()
print(f'✓ Users in tenant_test123: {users.count()}')
for u in users:
    print(f'  - {u.username} (superuser: {u.is_superuser})')
"

# 4. اختبار API
echo ""
echo "4. Testing API authentication..."
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: test123" \
  -d '{"username":"admin","password":"testpass"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access'])")

if [ ! -z "$TOKEN" ]; then
    echo "✓ Token obtained successfully"
else
    echo "✗ Failed to get token"
fi

# 5. اختبار عزل البيانات
echo ""
echo "5. Testing data isolation..."
python -c "
from django.contrib.auth import get_user_model
User = get_user_model()

# إنشاء user في test123
u1 = User.objects.using('tenant_test123').create_user('user1', password='pass')
print(f'✓ Created user in test123: {u1.username}')

# التحقق من أنه غير موجود في demo
demo_users = User.objects.using('tenant_demo').filter(username='user1')
if demo_users.exists():
    print('✗ FAILED: User leaked to demo database!')
else:
    print('✓ Data isolation working: user NOT in demo')
"

echo ""
echo "========================================"
echo "✓ All tests completed!"
```

**تشغيله:**
```bash
chmod +x test_multi_tenant_db.sh
./test_multi_tenant_db.sh
```

---

## 📈 المقارنة: قبل وبعد

| الميزة | Shared DB | Database-per-Tenant |
|--------|-----------|---------------------|
| **عزل البيانات** | متوسط (row-level) | ممتاز (database-level) |
| **الأمان** | جيد | ممتاز |
| **الأداء** | جيد | ممتاز (للاستعلامات) |
| **النسخ الاحتياطي** | الكل معاً | مستقل لكل عميل |
| **التكلفة** | منخفضة | متوسطة |
| **التعقيد** | بسيط | متوسط |
| **Migrations** | مرة واحدة | لكل tenant |
| **Scalability** | جيد (1000s) | جيد (100s-1000s) |

---

## 🎯 الخلاصة

### ✅ الآن لديك:
1. **عزل كامل** - كل عميل له قاعدة بيانات منفصلة تماماً
2. **مستخدمين منفصلين** - لكل عميل superuser وusers خاصين
3. **أمان محسّن** - استحالة تسريب البيانات بين العملاء
4. **نسخ احتياطي مستقل** - لكل عميل على حدة
5. **أداء أفضل** - استعلامات أسرع على جداول أصغر

### 📝 للبدء:
```bash
# 1. إنشاء tenant في Django Admin
http://localhost:8000/admin/hr_management/tenant/add/

# 2. إعداد قاعدة البيانات
python manage.py setup_tenant SUBDOMAIN --admin-password PASSWORD

# 3. تسجيل الدخول
curl -X POST http://localhost:8000/api/token/ \
  -H "X-Tenant-Subdomain: SUBDOMAIN" \
  -d '{"username":"admin","password":"PASSWORD"}'

# 4. استخدام التطبيق!
```

---

## 🆘 المساعدة

### المشكلة: "Database not found"
```bash
# تأكد من إنشاء قاعدة البيانات
python manage.py setup_tenant SUBDOMAIN
```

### المشكلة: "User does not exist"
```bash
# تأكد من إنشاء superuser
python -c "
from hr_management.tenant_service import TenantService
from hr_management.tenant_models import Tenant
tenant = Tenant.objects.get(subdomain='SUBDOMAIN')
TenantService.create_tenant_superuser(tenant, 'admin', password='admin123')
"
```

### المشكلة: "Migrations not applied"
```bash
# تطبيق migrations على tenant database
python manage.py migrate --database=tenant_SUBDOMAIN
```

---

**🎉 تهانينا! لديك الآن نظام multi-tenant كامل بقواعد بيانات منفصلة!**
