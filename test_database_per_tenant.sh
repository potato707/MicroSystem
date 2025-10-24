#!/bin/bash

echo "🧪 اختبار نظام قواعد البيانات المنفصلة"
echo "========================================"
echo ""

# التحقق من وجود Django
if ! python manage.py --version > /dev/null 2>&1; then
    echo "❌ خطأ: Django غير موجود"
    exit 1
fi

echo "✓ Django متوفر"
echo ""

# 1. إنشاء tenant تجريبي
echo "الخطوة 1: إنشاء tenant تجريبي..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant

# حذف أي tenant قديم
Tenant.objects.filter(subdomain='testdb').delete()

# إنشاء tenant جديد
tenant = Tenant.objects.create(
    name='Test Database Company',
    subdomain='testdb',
    primary_color='#e74c3c',
    secondary_color='#9b59b6',
    is_active=True
)

print(f'✓ تم إنشاء tenant: {tenant.name} ({tenant.subdomain})')
"

if [ $? -ne 0 ]; then
    echo "❌ فشل إنشاء tenant"
    exit 1
fi

echo ""

# 2. إعداد قاعدة البيانات
echo "الخطوة 2: إعداد قاعدة البيانات..."
python manage.py setup_tenant testdb --admin-password test123

if [ $? -ne 0 ]; then
    echo "❌ فشل إعداد قاعدة البيانات"
    exit 1
fi

echo ""

# 3. التحقق من الملفات
echo "الخطوة 3: التحقق من ملفات قاعدة البيانات..."
if [ -f "tenant_testdb.sqlite3" ]; then
    SIZE=$(ls -lh tenant_testdb.sqlite3 | awk '{print $5}')
    echo "✓ ملف قاعدة البيانات موجود: tenant_testdb.sqlite3 ($SIZE)"
else
    echo "❌ ملف قاعدة البيانات غير موجود!"
    exit 1
fi

echo ""

# 4. التحقق من المستخدمين
echo "الخطوة 4: التحقق من المستخدمين..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# مستخدمي testdb
users = User.objects.using('tenant_testdb').all()
print(f'✓ عدد المستخدمين في tenant_testdb: {users.count()}')

if users.count() > 0:
    for u in users:
        role = 'مدير' if u.is_superuser else 'مستخدم'
        print(f'  - {u.username} ({role})')
else:
    print('⚠️ لم يتم إنشاء أي مستخدمين')
"

echo ""

# 5. التحقق من الجداول
echo "الخطوة 5: التحقق من الجداول..."
TABLE_COUNT=$(sqlite3 tenant_testdb.sqlite3 ".tables" | wc -w)
echo "✓ عدد الجداول: $TABLE_COUNT"

echo ""

# 6. اختبار عزل البيانات
echo "الخطوة 6: اختبار عزل البيانات..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# إنشاء user في testdb
try:
    u1 = User.objects.using('tenant_testdb').create_user(
        username='isolated_user',
        email='test@testdb.com',
        password='pass123'
    )
    print(f'✓ تم إنشاء user: {u1.username}')
except:
    print('ℹ️ User موجود بالفعل')

# التحقق من عدم وجوده في القاعدة الرئيسية
main_users = User.objects.using('default').filter(username='isolated_user')
if main_users.exists():
    print('❌ فشل: User موجود في القاعدة الرئيسية!')
else:
    print('✓ نجح: User معزول في قاعدة بيانات tenant فقط')
"

echo ""

# 7. معلومات الوصول
echo "========================================"
echo "📋 معلومات الوصول:"
echo "========================================"
echo "  Subdomain:  testdb"
echo "  Database:   tenant_testdb.sqlite3"
echo "  Admin User: admin"
echo "  Password:   test123"
echo ""
echo "للوصول عبر API:"
echo '  curl -X POST http://localhost:8000/api/token/ \'
echo '    -H "Content-Type: application/json" \'
echo '    -H "X-Tenant-Subdomain: testdb" \'
echo '    -d '"'"'{"username":"admin","password":"test123"}'"'"
echo ""
echo "========================================"
echo "✅ تم الاختبار بنجاح!"
echo "========================================"
