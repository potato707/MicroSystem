#!/bin/bash

# Multi-Tenant SaaS System - Setup Script
# This script automates the initial setup of the tenant management system

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║    Multi-Tenant SaaS System - Installation Script            ║"
echo "║    Django + React Tenant Management System                    ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the project root.${NC}"
    exit 1
fi

echo -e "${BLUE}Step 1: Installing Python dependencies...${NC}"
pip install Pillow
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Pillow installed successfully${NC}"
else
    echo -e "${YELLOW}⚠ Pillow installation failed. Please install manually: pip install Pillow${NC}"
fi

echo ""
echo -e "${BLUE}Step 2: Creating database migrations...${NC}"
python manage.py makemigrations
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations created${NC}"
else
    echo -e "${RED}✗ Failed to create migrations${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 3: Applying migrations...${NC}"
python manage.py migrate
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migrations applied${NC}"
else
    echo -e "${RED}✗ Failed to apply migrations${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}Step 4: Creating required directories...${NC}"
mkdir -p media/tenants/logos
mkdir -p tenants
echo -e "${GREEN}✓ Created media/tenants/logos/${NC}"
echo -e "${GREEN}✓ Created tenants/${NC}"

echo ""
echo -e "${BLUE}Step 5: Initializing module definitions...${NC}"
python manage.py init_modules
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Module definitions initialized${NC}"
else
    echo -e "${YELLOW}⚠ Failed to initialize modules. You can do this later with: python manage.py init_modules${NC}"
fi

echo ""
echo -e "${BLUE}Step 6: Collecting static files (optional)...${NC}"
read -p "Do you want to collect static files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py collectstatic --noinput
    echo -e "${GREEN}✓ Static files collected${NC}"
fi

echo ""
echo -e "${BLUE}Step 7: Checking for superuser...${NC}"
read -p "Do you want to create a superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    Setup Complete! 🎉                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "1. Start the Django server:"
echo -e "   ${BLUE}python manage.py runserver${NC}"
echo ""
echo "2. Access the admin interface:"
echo -e "   ${BLUE}http://localhost:8000/admin/${NC}"
echo ""
echo "3. View API documentation:"
echo -e "   ${BLUE}http://localhost:8000/api/docs/${NC}"
echo ""
echo "4. Test tenant API:"
echo -e "   ${BLUE}curl http://localhost:8000/api/modules/${NC}"
echo ""
echo "5. Read the documentation:"
echo "   - Quick Start: TENANT_QUICK_START.md"
echo "   - Complete Guide: TENANT_SYSTEM_COMPLETE_GUIDE.md"
echo "   - Architecture: TENANT_ARCHITECTURE.md"
echo "   - Summary: TENANT_IMPLEMENTATION_SUMMARY.md"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo -e "${YELLOW}Frontend Setup (if not done):${NC}"
echo "   cd frontend"
echo "   npm install"
echo "   npm start"
echo ""
echo "─────────────────────────────────────────────────────────────────"
echo ""
echo "📚 Key API Endpoints:"
echo "   GET  /api/tenants/              - List all tenants"
echo "   POST /api/tenants/              - Create new tenant"
echo "   GET  /api/modules/              - List available modules"
echo "   GET  /api/tenants/statistics/   - Get statistics"
echo ""
echo "🎨 Frontend Pages to Create:"
echo "   /create-tenant   - Tenant creation form"
echo "   /tenants         - Tenant list and management"
echo ""
echo "🔒 Security Notes:"
echo "   - Tenant management requires admin authentication"
echo "   - Module access is enforced by middleware"
echo "   - Public config endpoint available for frontends"
echo ""
echo -e "${GREEN}Happy building! 🚀${NC}"
