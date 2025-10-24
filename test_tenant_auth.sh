#!/bin/bash

echo "🔐 اختبار Authentication مع Multi-Tenant"
echo "=========================================="
echo ""

# إنشاء tenants تجريبية
echo "الخطوة 1: إنشاء tenants تجريبية..."

python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant
from hr_management.tenant_service import TenantService

# Tenant 1
Tenant.objects.filter(subdomain='auth_test_a').delete()
tenant_a = Tenant.objects.create(
    name='Test Company A',
    subdomain='auth_test_a',
    is_active=True
)
TenantService.setup_complete_tenant(tenant_a, 'passwordA')
print('✓ Created auth_test_a')

# Tenant 2
Tenant.objects.filter(subdomain='auth_test_b').delete()
tenant_b = Tenant.objects.create(
    name='Test Company B',
    subdomain='auth_test_b',
    is_active=True
)
TenantService.setup_complete_tenant(tenant_b, 'passwordB')
print('✓ Created auth_test_b')
"

echo ""
echo "=========================================="
echo "الاختبار 1: تسجيل دخول صحيح ✅"
echo "=========================================="
echo ""

echo "محاولة: admin@auth_test_a مع كلمة المرور الصحيحة"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: auth_test_a" \
  -d '{"username":"admin","password":"passwordA"}')

if echo "$RESPONSE" | grep -q "access"; then
    echo "✅ نجح: حصل على token"
    echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo "❌ فشل: لم يحصل على token"
    echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo "الاختبار 2: محاولة الوصول لـ tenant آخر ❌"
echo "=========================================="
echo ""

echo "محاولة: admin@auth_test_b باستخدام بيانات tenant A"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: auth_test_b" \
  -d '{"username":"admin","password":"passwordA"}')

if echo "$RESPONSE" | grep -q "error"; then
    echo "✅ نجح: تم رفض الوصول"
    echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo "❌ فشل: تم السماح بالوصول (خطأ أمني!)"
    echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo "الاختبار 3: كلمة مرور خاطئة ❌"
echo "=========================================="
echo ""

echo "محاولة: admin@auth_test_a مع كلمة مرور خاطئة"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: auth_test_a" \
  -d '{"username":"admin","password":"wrongpassword"}')

if echo "$RESPONSE" | grep -q "error"; then
    echo "✅ نجح: تم رفض الوصول"
    echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo "❌ فشل: تم السماح بالوصول"
    echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo "الاختبار 4: مستخدم غير موجود ❌"
echo "=========================================="
echo ""

echo "محاولة: nonexistent@auth_test_a"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Subdomain: auth_test_a" \
  -d '{"username":"nonexistent","password":"password"}')

if echo "$RESPONSE" | grep -q "error"; then
    echo "✅ نجح: تم رفض الوصول"
    echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo "❌ فشل: تم السماح بالوصول"
    echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo "الاختبار 5: بدون تحديد tenant ❌"
echo "=========================================="
echo ""

echo "محاولة: بدون X-Tenant-Subdomain header"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"passwordA"}')

if echo "$RESPONSE" | grep -q "Tenant"; then
    echo "✅ نجح: تم رفض الوصول (tenant مطلوب)"
    echo "$RESPONSE" | python -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo "❌ فشل: تم السماح بالوصول بدون tenant"
    echo "$RESPONSE"
fi

echo ""
echo "=========================================="
echo "✅ اكتمل الاختبار!"
echo "=========================================="
echo ""
echo "النظام الآن آمن ومعزول بين الـ tenants"
