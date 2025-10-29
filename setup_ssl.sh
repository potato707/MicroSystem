#!/bin/bash

# SSL Setup Script for Multi-Tenant Wildcard Certificate
# Domain: client-radar.org
# Supports: *.client-radar.org

set -e  # Exit on any error

echo "🔐 Starting SSL Certificate Setup for client-radar.org"
echo "=================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run this script as root (use sudo)"
    exit 1
fi

# Install Certbot if not installed
echo "📦 Checking Certbot installation..."
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    apt update
    apt install -y certbot python3-certbot-nginx
else
    echo "✅ Certbot already installed"
fi

echo ""
echo "🌐 Getting Wildcard SSL Certificate for client-radar.org"
echo "=================================================="
echo ""
echo "IMPORTANT: You will need to add a TXT record to your DNS:"
echo "1. When prompted, add the TXT record shown by Certbot"
echo "2. Record Name: _acme-challenge.client-radar.org"
echo "3. Record Type: TXT"
echo "4. Record Value: (will be provided by Certbot)"
echo "5. Wait 1-2 minutes for DNS propagation"
echo "6. Press Enter to continue verification"
echo ""
read -p "Press Enter to continue..."

# Get wildcard certificate using manual DNS challenge
certbot certonly \
    --manual \
    --preferred-challenges=dns \
    --email admin@client-radar.org \
    --agree-tos \
    --no-eff-email \
    -d client-radar.org \
    -d *.client-radar.org

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL Certificate obtained successfully!"
    echo ""
    echo "📄 Certificate files location:"
    echo "  - Certificate: /etc/letsencrypt/live/client-radar.org/fullchain.pem"
    echo "  - Private Key: /etc/letsencrypt/live/client-radar.org/privkey.pem"
    echo ""
    
    # Set up auto-renewal
    echo "⚙️  Setting up automatic certificate renewal..."
    
    # Create renewal hook to reload nginx
    cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
echo "$(date): Nginx reloaded after certificate renewal" >> /var/log/certbot-renewal.log
EOF
    
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
    
    # Test renewal
    echo "🧪 Testing certificate renewal..."
    certbot renew --dry-run
    
    echo ""
    echo "✅ Setup Complete!"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Copy nginx_production.conf to /etc/nginx/sites-available/multitenant"
    echo "  2. Create symlink: ln -s /etc/nginx/sites-available/multitenant /etc/nginx/sites-enabled/"
    echo "  3. Test nginx config: nginx -t"
    echo "  4. Reload nginx: systemctl reload nginx"
    echo ""
    echo "🔄 Certificate will auto-renew every 60 days"
    echo ""
else
    echo "❌ Failed to obtain SSL certificate"
    exit 1
fi
