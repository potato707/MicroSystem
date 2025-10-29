#!/bin/bash

# System Services Setup Script
# Configures systemd services for Django and monitoring

set -e

echo "⚙️  Setting up System Services"
echo "=============================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

PROJECT_DIR="/home/deploy/MicroSystem"

# Create log directories
echo "📁 Creating log directories..."
mkdir -p /var/log/django
mkdir -p /var/log/nginx
chown deploy:www-data /var/log/django
chmod 755 /var/log/django
echo "✅ Log directories created"

# Install gunicorn if not installed
echo ""
echo "📦 Installing Gunicorn..."
su - deploy -c "cd $PROJECT_DIR && source venv/bin/activate && pip install gunicorn"
echo "✅ Gunicorn installed"

# Copy Django service file
echo ""
echo "📝 Installing Django systemd service..."
cp $PROJECT_DIR/systemd/django.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable django
systemctl start django
echo "✅ Django service installed and started"

# Install PM2 for Next.js (if not installed)
echo ""
echo "📦 Setting up PM2 for Next.js..."
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2
    echo "✅ PM2 installed"
else
    echo "✅ PM2 already installed"
fi

# Setup PM2 to start Next.js
echo ""
echo "🚀 Starting Next.js with PM2..."
su - deploy -c "cd $PROJECT_DIR/microservice_frontend && pm2 start npm --name nextjs -- start"
su - deploy -c "pm2 save"
pm2 startup systemd -u deploy --hp /home/deploy
echo "✅ Next.js configured with PM2"

# Setup Nginx
echo ""
echo "🌐 Configuring Nginx..."
if [ -f "$PROJECT_DIR/nginx_production.conf" ]; then
    cp $PROJECT_DIR/nginx_production.conf /etc/nginx/sites-available/multitenant
    ln -sf /etc/nginx/sites-available/multitenant /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx config
    nginx -t
    systemctl reload nginx
    echo "✅ Nginx configured and reloaded"
else
    echo "⚠️  nginx_production.conf not found, skipping"
fi

echo ""
echo "📊 Service Status:"
echo "------------------"
systemctl status django --no-pager || true
su - deploy -c "pm2 status" || true
systemctl status nginx --no-pager || true

echo ""
echo "✅ Setup Complete!"
echo ""
echo "📝 Useful Commands:"
echo "  - View Django logs: journalctl -u django -f"
echo "  - View Next.js logs: pm2 logs nextjs"
echo "  - View Nginx logs: tail -f /var/log/nginx/tenant_access.log"
echo "  - Restart Django: systemctl restart django"
echo "  - Restart Next.js: pm2 restart nextjs"
echo "  - Restart Nginx: systemctl reload nginx"
echo ""
