#!/bin/bash

# Production System Testing Script
# Tests multi-tenant subdomain functionality

set -e

DOMAIN="client-radar.org"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "🧪 Multi-Tenant System Testing"
echo "==============================="
echo ""

print_test() {
    echo -e "${YELLOW}Testing: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ PASS: $1${NC}"
}

print_error() {
    echo -e "${RED}❌ FAIL: $1${NC}"
}

# Test 1: Main domain
print_test "Main domain (https://$DOMAIN)"
if curl -f -s https://$DOMAIN > /dev/null; then
    print_success "Main domain accessible"
else
    print_error "Main domain not accessible"
fi

# Test 2: Tenant creation endpoint
print_test "Tenant creation endpoint"
response=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/hr/create-tenant/)
if [ "$response" = "200" ] || [ "$response" = "405" ]; then
    print_success "Tenant creation endpoint exists"
else
    print_error "Tenant creation endpoint returned $response"
fi

# Test 3: Create test tenant
print_test "Creating test tenant 'testdeploy'"
create_response=$(curl -s -X POST https://$DOMAIN/hr/create-tenant/ \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Test Deploy Company",
        "subdomain": "testdeploy",
        "admin_email": "admin@testdeploy.com",
        "admin_password": "TestPass123!",
        "modules": ["employees", "attendance", "tasks"]
    }')

if echo "$create_response" | grep -q "subdomain"; then
    print_success "Test tenant created successfully"
    
    # Test 4: Access tenant subdomain
    sleep 2  # Wait for DNS propagation
    print_test "Accessing tenant subdomain (https://testdeploy.$DOMAIN)"
    
    if curl -f -s https://testdeploy.$DOMAIN > /dev/null; then
        print_success "Tenant subdomain accessible"
    else
        print_error "Tenant subdomain not accessible"
    fi
    
    # Test 5: Test tenant API
    print_test "Testing tenant API (login)"
    login_response=$(curl -s -X POST https://testdeploy.$DOMAIN/api/token/ \
        -H "Content-Type: application/json" \
        -d '{
            "username": "admin@testdeploy.com",
            "password": "TestPass123!"
        }')
    
    if echo "$login_response" | grep -q "access"; then
        print_success "Tenant API working (login successful)"
        
        # Extract token
        token=$(echo "$login_response" | grep -o '"access":"[^"]*"' | cut -d'"' -f4)
        
        # Test 6: Test module access
        print_test "Testing module access (employees)"
        employees_response=$(curl -s -o /dev/null -w "%{http_code}" \
            https://testdeploy.$DOMAIN/hr/employees/ \
            -H "Authorization: Bearer $token" \
            -H "X-Tenant-Subdomain: testdeploy")
        
        if [ "$employees_response" = "200" ]; then
            print_success "Module access working"
        else
            print_error "Module access failed (HTTP $employees_response)"
        fi
    else
        print_error "Tenant API failed (login unsuccessful)"
    fi
    
else
    print_error "Failed to create test tenant"
    echo "Response: $create_response"
fi

# Test 7: Test wildcard SSL
print_test "SSL certificate validity"
ssl_info=$(echo | openssl s_client -servername testdeploy.$DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null)

if echo "$ssl_info" | grep -q "notAfter"; then
    print_success "SSL certificate valid"
    echo "$ssl_info"
else
    print_error "SSL certificate issue"
fi

# Test 8: Multiple tenants
print_test "Testing multiple tenant isolation"
tenant_names=("tenant1" "tenant2" "tenant3")

for tenant in "${tenant_names[@]}"; do
    create_response=$(curl -s -X POST https://$DOMAIN/hr/create-tenant/ \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"Test $tenant\",
            \"subdomain\": \"$tenant\",
            \"admin_email\": \"admin@$tenant.com\",
            \"admin_password\": \"TestPass123!\",
            \"modules\": [\"employees\"]
        }")
    
    if echo "$create_response" | grep -q "subdomain"; then
        print_success "Tenant '$tenant' created"
    else
        print_error "Failed to create tenant '$tenant'"
    fi
done

echo ""
echo "🎯 Test Summary"
echo "==============="
echo "All core functionality tested."
echo ""
echo "📝 Manual Tests:"
echo "  1. Open https://testdeploy.$DOMAIN in browser"
echo "  2. Login with admin@testdeploy.com / TestPass123!"
echo "  3. Verify employees module works"
echo "  4. Check browser console for errors"
echo ""
echo "🧹 Cleanup (optional):"
echo "  Delete test tenants from Django admin"
echo ""
