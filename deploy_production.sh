#!/bin/bash

# Production Deployment Script
# Deploys Multi-Tenant System to Production Server

set -e  # Exit on any error

echo "🚀 Multi-Tenant Production Deployment"
echo "====================================="
echo ""

# Configuration
PROJECT_DIR="/home/deploy/MicroSystem"
FRONTEND_DIR="$PROJECT_DIR/microservice_frontend"
VENV_DIR="$PROJECT_DIR/venv"
DJANGO_USER="deploy"
DOMAIN="client-radar.org"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if running as deploy user
if [ "$USER" != "$DJANGO_USER" ] && [ "$EUID" -ne 0 ]; then
    print_error "Please run as $DJANGO_USER user or root"
    exit 1
fi

echo "📋 Pre-deployment Checklist"
echo "----------------------------"
echo "1. DNS wildcard record configured (*.client-radar.org)"
echo "2. SSL certificate obtained"
echo "3. Nginx installed and configured"
echo "4. PostgreSQL/MySQL installed (if using)"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "📥 Step 1: Pull Latest Code"
echo "----------------------------"
cd $PROJECT_DIR
git pull origin main
print_success "Code updated"

echo ""
echo "🐍 Step 2: Update Python Dependencies"
echo "--------------------------------------"
source $VENV_DIR/bin/activate
pip install -r requirements.txt
print_success "Python dependencies updated"

echo ""
echo "📦 Step 3: Update Node.js Dependencies"
echo "---------------------------------------"
cd $FRONTEND_DIR
npm install
print_success "Node.js dependencies updated"

echo ""
echo "🔨 Step 4: Build Frontend"
echo "-------------------------"
npm run build
print_success "Frontend built successfully"

echo ""
echo "📊 Step 5: Django Migrations"
echo "----------------------------"
cd $PROJECT_DIR
python manage.py migrate --database=default
print_success "Main database migrated"

# Migrate all tenant databases
echo "Migrating tenant databases..."
for tenant_db in tenant_*.sqlite3; do
    if [ -f "$tenant_db" ]; then
        tenant_name=$(echo $tenant_db | sed 's/tenant_//' | sed 's/.sqlite3//')
        echo "  - Migrating $tenant_name..."
        python manage.py migrate --database=tenant_$tenant_name || print_info "    Skipped (might not exist in settings)"
    fi
done
print_success "Tenant databases migrated"

echo ""
echo "📁 Step 6: Collect Static Files"
echo "--------------------------------"
python manage.py collectstatic --noinput
print_success "Static files collected"

echo ""
echo "🔄 Step 7: Restart Services"
echo "---------------------------"

# Restart Django (using systemd)
if systemctl is-active --quiet django; then
    sudo systemctl restart django
    print_success "Django restarted"
else
    print_info "Django service not found, please start manually"
fi

# Restart Next.js (using PM2)
if command -v pm2 &> /dev/null; then
    pm2 restart nextjs || pm2 start npm --name "nextjs" -- start
    print_success "Next.js restarted"
else
    print_info "PM2 not found, please start Next.js manually"
fi

# Reload Nginx
sudo systemctl reload nginx
print_success "Nginx reloaded"

echo ""
echo "🧪 Step 8: Health Checks"
echo "------------------------"

# Check Django
if curl -f http://localhost:8000/admin/ > /dev/null 2>&1; then
    print_success "Django is responding"
else
    print_error "Django health check failed"
fi

# Check Next.js
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_success "Next.js is responding"
else
    print_error "Next.js health check failed"
fi

# Check HTTPS
if curl -f https://$DOMAIN > /dev/null 2>&1; then
    print_success "HTTPS is working"
else
    print_error "HTTPS health check failed"
fi

echo ""
echo "✨ Deployment Complete!"
echo "======================="
echo ""
echo "🌐 Your multi-tenant system is now live at:"
echo "   Main: https://$DOMAIN"
echo "   Tenants: https://*.client-radar.org"
echo ""
echo "📝 Test tenant creation:"
echo "   1. Go to https://$DOMAIN/hr/create-tenant/"
echo "   2. Create tenant 'adam'"
echo "   3. Access at https://adam.$DOMAIN"
echo ""
echo "📊 Monitor logs:"
echo "   Django: journalctl -u django -f"
echo "   Next.js: pm2 logs nextjs"
echo "   Nginx: tail -f /var/log/nginx/tenant_access.log"
echo ""
