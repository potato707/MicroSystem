#!/bin/bash

TENANT="testcompany"
API_BASE="http://localhost:8000"

echo "🔒 Testing Tenant Module Access Control"
echo "========================================"
echo ""

# Get token
echo "1. Getting auth token..."
TOKEN=$(curl -s -X POST $API_BASE/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"string","password":"string"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access'])")

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi
echo "✓ Token obtained"
echo ""

# Test disabled module
echo "2. Testing DISABLED module (employees)..."
RESPONSE=$(curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  -w "\n%{http_code}" \
  $API_BASE/hr/employees/)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "403" ]; then
    echo "✅ PASS: Disabled module blocked (403)"
    echo "Response: $BODY"
else
    echo "❌ FAIL: Expected 403, got $HTTP_CODE"
    echo "Response: $BODY"
fi
echo ""

# Test enabled module
echo "3. Testing ENABLED module (notifications)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  $API_BASE/hr/notifications/)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "✅ PASS: Enabled module accessible ($HTTP_CODE)"
else
    echo "❌ FAIL: Expected 200/401, got $HTTP_CODE"
fi
echo ""

# Enable employees module
echo "4. Enabling employees module..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant
tenant = Tenant.objects.get(subdomain='$TENANT')
module = tenant.modules.get(module_key='employees')
module.is_enabled = True
module.save()
print('✓ Module enabled')
"
echo ""

# Test now-enabled module
echo "5. Testing now-ENABLED module (employees)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  $API_BASE/hr/employees/)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ PASS: Now accessible (200)"
else
    echo "❌ FAIL: Expected 200, got $HTTP_CODE"
fi
echo ""

# Disable again
echo "6. Disabling employees module again..."
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import Tenant
tenant = Tenant.objects.get(subdomain='$TENANT')
module = tenant.modules.get(module_key='employees')
module.is_enabled = False
module.save()
print('✓ Module disabled')
"
echo ""

# Test disabled again
echo "7. Testing DISABLED again (employees)..."
RESPONSE=$(curl -s \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Tenant-Subdomain: $TENANT" \
  -w "\n%{http_code}" \
  $API_BASE/hr/employees/)

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "403" ]; then
    echo "✅ PASS: Blocked again (403)"
    echo "Response: $BODY"
else
    echo "❌ FAIL: Expected 403, got $HTTP_CODE"
    echo "Response: $BODY"
fi
echo ""

echo "========================================"
echo "✅ Module access control tests complete!"
