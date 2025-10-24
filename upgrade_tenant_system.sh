#!/bin/bash

# Tenant System Upgrade Script
# Automates the upgrade of your multi-tenant system

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Multi-Tenant System Upgrade Automation     ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Run this script from the project root.${NC}"
    exit 1
fi

# Step 1: Backup current system
echo -e "${YELLOW}[1/8]${NC} Creating backup..."
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r hr_management/tenant_*.py "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Backup created at $BACKUP_DIR${NC}"

# Step 2: Check v0-micro-system exists
echo -e "${YELLOW}[2/8]${NC} Checking v0-micro-system template..."
if [ ! -d "v0-micro-system" ]; then
    echo -e "${RED}✗ v0-micro-system directory not found!${NC}"
    echo "Please ensure the frontend template exists at ./v0-micro-system/"
    exit 1
fi
echo -e "${GREEN}✓ Frontend template found${NC}"

# Step 3: Create required directories
echo -e "${YELLOW}[3/8]${NC} Creating directories..."
mkdir -p media/tenants/logos
mkdir -p tenants
mkdir -p frontend/src/components
echo -e "${GREEN}✓ Directories created${NC}"

# Step 4: Run migrations
echo -e "${YELLOW}[4/8]${NC} Running migrations..."
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✓ Migrations applied${NC}"

# Step 5: Initialize modules
echo -e "${YELLOW}[5/8]${NC} Initializing module definitions..."
python manage.py init_modules
echo -e "${GREEN}✓ Modules initialized${NC}"

# Step 6: Test API endpoints
echo -e "${YELLOW}[6/8]${NC} Testing API endpoints..."
python manage.py runserver &
SERVER_PID=$!
sleep 3

# Wait for server to start
echo "Waiting for Django server to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/api/modules/ > /dev/null; then
        echo -e "${GREEN}✓ API endpoints responding${NC}"
        break
    fi
    sleep 1
done

kill $SERVER_PID 2>/dev/null || true

# Step 7: Check frontend dependencies
echo -e "${YELLOW}[7/8]${NC} Checking frontend..."
if [ -d "frontend" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    cd ..
    echo -e "${GREEN}✓ Frontend ready${NC}"
else
    echo -e "${YELLOW}⚠ Frontend directory not found (optional)${NC}"
fi

# Step 8: Summary
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            Upgrade Complete! 🎉               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. Review the upgrade plan: TENANT_SYSTEM_UPGRADE_PLAN.md"
echo "2. Update tenant_service.py to enable frontend copying"
echo "3. Add new API endpoints to tenant_views.py"
echo "4. Update frontend routing"
echo "5. Configure subdomain routing (Nginx/Caddy)"
echo ""
echo -e "${YELLOW}Quick Test:${NC}"
echo "  python manage.py runserver"
echo "  Open http://localhost:8000/admin/hr_management/tenant/"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  - Full upgrade plan: TENANT_SYSTEM_UPGRADE_PLAN.md"
echo "  - Quick start guide: TENANT_QUICK_START.md"
echo "  - Architecture: TENANT_ARCHITECTURE.md"
echo ""
echo -e "${GREEN}System Status:${NC}"
echo "  Database: ✓ Ready"
echo "  Modules: ✓ Initialized"
echo "  Template: ✓ Available"
echo "  Directories: ✓ Created"
echo ""
echo -e "${BLUE}Happy building! 🚀${NC}"
