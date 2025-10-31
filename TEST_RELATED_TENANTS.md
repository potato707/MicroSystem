# اختبار ميزة ربط العملاء (Related Tenants)

## ✅ التحديثات المطبقة:

### 1. Django Admin
- ✅ أضيف حقل `related_tenants` في fieldsets
- ✅ أضيف `filter_horizontal` للحصول على واجهة جميلة
- 📍 **الموقع**: `/admin/hr_management/tenant/`

### 2. Tenant Creator Page
- ✅ أضيف `<select multiple>` لاختيار العملاء المرتبطين
- ✅ دالة `loadTenants()` تحمل جميع العملاء الموجودين
- ✅ يتم إرسال `related_tenants` مع بيانات الإنشاء
- 📍 **الموقع**: `/api/tenant-creator/`

### 3. Tenant Management Page
- ✅ عرض العملاء المرتبطين في بطاقة العميل
- ✅ `<select multiple>` في نافذة التعديل
- ✅ دالة `loadRelatedTenantsForEdit()` تحمل وتحدد العملاء
- ✅ يتم إرسال `related_tenants` عند التحديث
- 📍 **الموقع**: `/api/manage-tenants/`

### 4. API Serializers
- ✅ `TenantListSerializer`: أضيف `related_tenants` (PrimaryKeyRelatedField)
- ✅ `TenantDetailSerializer`: أضيف `related_tenants` و `related_tenants_ids`
- ✅ `TenantCreateSerializer`: أضيف `related_tenants`
- ✅ `TenantUpdateSerializer`: أضيف `related_tenants`

### 5. Database
- ✅ Migration 0054 & 0055 مطبقة بنجاح
- ✅ حقل `related_tenants` ManyToManyField موجود

## 📋 خطوات الاختبار:

### اختبار Django Admin:
1. افتح: `http://localhost:8000/admin/hr_management/tenant/`
2. اختر أي عميل موجود
3. يجب أن ترى قسم "العملاء المرتبطين" مع واجهة اختيار جميلة
4. اختر عملاء وحفظ

### اختبار صفحة الإنشاء:
1. افتح: `http://localhost:8000/api/tenant-creator/`
2. افتح Console في المتصفح (F12)
3. يجب أن ترى: `console.log('Loaded tenants:', data)`
4. يجب أن تظهر قائمة العملاء في select box
5. اختر عملاء وأنشئ عميل جديد

### اختبار صفحة الإدارة:
1. افتح: `http://localhost:8000/api/manage-tenants/`
2. انقر "تعديل" على أي عميل
3. يجب أن ترى قائمة "العملاء المرتبطين"
4. اختر عملاء وحفظ

## 🐛 استكشاف الأخطاء:

### إذا كانت القائمة فارغة في `/api/tenant-creator/`:
```javascript
// افتح Console وشوف:
// 1. هل في عملاء موجودة أصلاً؟
fetch('/api/tenants/').then(r => r.json()).then(console.log)

// 2. هل الresponse صحيح؟
// يجب أن ترى: { count: X, results: [...] } أو array مباشر
```

### إذا كان الحقل مش ظاهر في Django Admin:
```bash
# تأكد من تطبيق الmigrations:
python manage.py migrate hr_management

# تأكد من restart السيرفر:
# Ctrl+C ثم
python manage.py runserver
```

### إذا كان API مش بيستقبل related_tenants:
```python
# تحقق من TenantCreateSerializer في tenant_serializers.py
# يجب أن يحتوي على:
related_tenants = serializers.PrimaryKeyRelatedField(
    many=True,
    queryset=Tenant.objects.all(),
    required=False
)
```

## 📊 مثال على البيانات:

### POST /api/tenants/ (Create):
```json
{
  "name": "شركة التطوير",
  "subdomain": "dev",
  "admin_username": "admin",
  "admin_email": "admin@dev.com",
  "admin_password": "password123",
  "module_keys": ["employees", "tasks"],
  "related_tenants": ["uuid-1", "uuid-2"]
}
```

### PATCH /api/tenants/{id}/ (Update):
```json
{
  "name": "شركة التطوير المحدثة",
  "related_tenants": ["uuid-1", "uuid-3", "uuid-5"]
}
```

### GET /api/tenants/{id}/ (Detail):
```json
{
  "id": "uuid",
  "name": "شركة التطوير",
  "subdomain": "dev",
  "related_tenants": [
    {
      "id": "uuid-1",
      "name": "شركة أخرى",
      "subdomain": "other",
      "is_active": true
    }
  ],
  "related_tenants_ids": ["uuid-1"]
}
```

## ✨ الميزات:
- ✅ Many-to-Many غير متماثل (يمكن لـ A أن يربط B دون العكس)
- ✅ يعمل في Django Admin
- ✅ يعمل في صفحة الإنشاء
- ✅ يعمل في صفحة الإدارة
- ✅ يظهر في بطاقة العميل
- ✅ يتم حفظه في قاعدة البيانات
