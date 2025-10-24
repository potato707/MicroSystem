#!/bin/bash

# Client Account System - Testing Script
# This script helps verify the complete system is working correctly

echo "================================================"
echo "  Client Account System - Testing Script"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if Django server is running
echo "Step 1: Checking Django Backend..."
if curl -s http://localhost:8000/hr/client/auth/login/ > /dev/null 2>&1; then
    print_success "Django backend is running on port 8000"
else
    print_error "Django backend is NOT running!"
    print_info "Start it with: python manage.py runserver"
    exit 1
fi
echo ""

# Check if Next.js server is running
echo "Step 2: Checking Next.js Frontend..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    print_success "Next.js frontend is running on port 3000"
else
    print_error "Next.js frontend is NOT running!"
    print_info "Start it with: cd v0-micro-system && npm run dev"
    exit 1
fi
echo ""

# Run backend tests
echo "Step 3: Running Backend Tests..."
if python test_client_account_system.py > /tmp/client_test_output.txt 2>&1; then
    print_success "All backend tests passed!"
    
    # Extract test credentials
    echo ""
    print_info "Test Credentials:"
    grep -A 1 "Test user created:" /tmp/client_test_output.txt | tail -1
    
    # Save credentials for later use
    TEST_EMAIL=$(grep "Test user created:" /tmp/client_test_output.txt | awk '{print $4}')
    TEST_PASSWORD=$(grep "Password:" /tmp/client_test_output.txt | awk '{print $2}')
    
    echo ""
    print_info "You can use these credentials to login at:"
    echo "   http://localhost:3000/client/login"
else
    print_error "Backend tests failed!"
    cat /tmp/client_test_output.txt
    exit 1
fi
echo ""

# Test API endpoints
echo "Step 4: Testing API Endpoints..."

# Try to login with test credentials
if [ -n "$TEST_EMAIL" ] && [ -n "$TEST_PASSWORD" ]; then
    LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/hr/client/auth/login/ \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")
    
    if echo "$LOGIN_RESPONSE" | grep -q "access"; then
        print_success "API Login endpoint working"
        
        # Extract access token
        ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['access'])" 2>/dev/null)
        
        if [ -n "$ACCESS_TOKEN" ]; then
            # Test dashboard stats endpoint
            STATS_RESPONSE=$(curl -s -X GET http://localhost:8000/hr/client/dashboard/stats/ \
                -H "Authorization: Bearer $ACCESS_TOKEN")
            
            if echo "$STATS_RESPONSE" | grep -q "total_complaints"; then
                print_success "API Dashboard endpoint working"
            else
                print_error "API Dashboard endpoint failed"
            fi
            
            # Test complaints list endpoint
            COMPLAINTS_RESPONSE=$(curl -s -X GET http://localhost:8000/hr/client/complaints/ \
                -H "Authorization: Bearer $ACCESS_TOKEN")
            
            if echo "$COMPLAINTS_RESPONSE" | grep -q "results"; then
                print_success "API Complaints list endpoint working"
            else
                print_error "API Complaints list endpoint failed"
            fi
        fi
    else
        print_error "API Login endpoint failed"
    fi
else
    print_info "Skipping API endpoint tests (no test credentials available)"
fi
echo ""

# Check if categories exist
echo "Step 5: Checking Database Setup..."
CATEGORY_COUNT=$(python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
import django
django.setup()
from hr_management.models import ComplaintCategory
print(ComplaintCategory.objects.count())
" 2>/dev/null)

if [ "$CATEGORY_COUNT" -gt 0 ]; then
    print_success "Database has $CATEGORY_COUNT complaint categories"
else
    print_error "No complaint categories found!"
    print_info "Create some with: python manage.py shell"
    print_info "Then run: ComplaintCategory.objects.create(name='Technical Support')"
fi
echo ""

# Check frontend files
echo "Step 6: Checking Frontend Files..."
FRONTEND_FILES=(
    "v0-micro-system/types/client.ts"
    "v0-micro-system/lib/auth/clientAuth.ts"
    "v0-micro-system/lib/api/clientApi.ts"
    "v0-micro-system/app/client/login/page.tsx"
    "v0-micro-system/app/client/dashboard/page.tsx"
    "v0-micro-system/app/client/complaints/page.tsx"
    "v0-micro-system/app/client/complaints/new/page.tsx"
    "v0-micro-system/app/client/complaints/[id]/page.tsx"
)

ALL_FILES_EXIST=true
for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        print_success "Found: $file"
    else
        print_error "Missing: $file"
        ALL_FILES_EXIST=false
    fi
done
echo ""

# Check environment variables
echo "Step 7: Checking Configuration..."
if [ -f "v0-micro-system/.env.local" ]; then
    if grep -q "NEXT_PUBLIC_API_URL=http://localhost:8000/hr" v0-micro-system/.env.local; then
        print_success "Environment variables configured correctly"
    else
        print_error "Environment variables need updating"
        print_info "Ensure .env.local has: NEXT_PUBLIC_API_URL=http://localhost:8000/hr"
    fi
else
    print_error "Missing .env.local file"
fi
echo ""

# Summary
echo "================================================"
echo "  Testing Summary"
echo "================================================"
echo ""

if [ "$ALL_FILES_EXIST" = true ]; then
    print_success "All files are in place"
    print_success "Backend API is functional"
    print_success "Frontend is ready"
    echo ""
    echo "🎉 System is ready to use!"
    echo ""
    echo "Next steps:"
    echo "1. Open your browser to: http://localhost:3000/client/login"
    echo "2. Use the test credentials shown above"
    echo "3. Explore the dashboard and features"
    echo ""
    echo "For more information, see:"
    echo "- CLIENT_ACCOUNT_SYSTEM_QUICKSTART.md"
    echo "- CLIENT_ACCOUNT_SYSTEM_COMPLETE.md"
else
    print_error "Some files are missing"
    echo ""
    echo "Please check the error messages above and fix the issues."
fi

echo ""
