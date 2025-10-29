#!/bin/bash

# Complete Production Setup Guide
# Run this script on your production server

cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🚀 Multi-Tenant HR System - Production Setup 🚀         ║
║                                                              ║
║     Domain: client-radar.org                                 ║
║     Supports: *.client-radar.org (wildcard subdomains)       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

📋 PREREQUISITES CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ VPS/Server Requirements:
  • Ubuntu 20.04+ or similar Linux distribution
  • 2GB+ RAM (4GB recommended)
  • 20GB+ storage
  • Root or sudo access
  • Public IP address

✓ Domain Configuration:
  • Domain purchased: client-radar.org
  • Access to DNS management panel

✓ Software Requirements:
  • Python 3.10+
  • Node.js 18+
  • Nginx
  • Git

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


🔧 INSTALLATION STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: DNS Configuration
──────────────────────────────────────────────────────────────
Go to your domain provider's DNS management and add:

  Type: A Record
  Host: @
  Value: YOUR_SERVER_IP
  TTL: 3600

  Type: A Record
  Host: *
  Value: YOUR_SERVER_IP
  TTL: 3600

  Type: A Record (optional, for www)
  Host: www
  Value: YOUR_SERVER_IP
  TTL: 3600

⏱️  Wait 5-15 minutes for DNS propagation.

Test with: dig client-radar.org
           dig adam.client-radar.org


STEP 2: Server Preparation
──────────────────────────────────────────────────────────────
SSH into your server and run:

  # Update system
  sudo apt update && sudo apt upgrade -y

  # Install required packages
  sudo apt install -y python3.10 python3-pip python3-venv \
    nginx git curl nodejs npm build-essential

  # Create deploy user
  sudo useradd -m -s /bin/bash deploy
  sudo usermod -aG www-data deploy
  sudo mkdir -p /home/deploy
  sudo chown -R deploy:deploy /home/deploy


STEP 3: Clone Repository
──────────────────────────────────────────────────────────────
  sudo su - deploy
  cd /home/deploy
  git clone YOUR_REPO_URL MicroSystem
  cd MicroSystem


STEP 4: Python Environment Setup
──────────────────────────────────────────────────────────────
  # Create virtual environment
  python3 -m venv venv
  source venv/bin/activate

  # Install dependencies
  pip install --upgrade pip
  pip install -r requirements.txt
  pip install gunicorn

  # Run migrations
  python manage.py migrate


STEP 5: Frontend Setup
──────────────────────────────────────────────────────────────
  cd microservice_frontend
  
  # Install dependencies
  npm install

  # Create production env file
  cat > .env.local << 'ENVEOF'
NEXT_PUBLIC_API_URL=https://client-radar.org
NEXT_PUBLIC_DOMAIN=client-radar.org
NODE_ENV=production
ENVEOF

  # Build frontend
  npm run build


STEP 6: SSL Certificate Setup
──────────────────────────────────────────────────────────────
  cd /home/deploy/MicroSystem
  sudo ./setup_ssl.sh

  ⚠️  IMPORTANT: When prompted, add the TXT record to your DNS:
     
     Record Type: TXT
     Name: _acme-challenge.client-radar.org
     Value: [provided by Certbot]

  Wait 1-2 minutes for DNS propagation, then continue.


STEP 7: System Services Setup
──────────────────────────────────────────────────────────────
  sudo ./setup_services.sh

  This will:
  • Install and configure Gunicorn for Django
  • Install and configure PM2 for Next.js
  • Configure Nginx with wildcard subdomains
  • Start all services


STEP 8: Initial Configuration
──────────────────────────────────────────────────────────────
  # Create Django superuser
  python manage.py createsuperuser

  # Collect static files
  python manage.py collectstatic --noinput


STEP 9: Test the System
──────────────────────────────────────────────────────────────
  ./test_production.sh

  Or manually:
  • Visit https://client-radar.org
  • Create a test tenant
  • Access https://[tenant].client-radar.org


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


🎯 HOW IT WORKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. WILDCARD DNS (*.client-radar.org)
   ────────────────────────────────────────────────────────────
   • DNS A Record with * points ALL subdomains to server
   • adam.client-radar.org → YOUR_SERVER_IP ✓
   • khalid.client-radar.org → YOUR_SERVER_IP ✓
   • omar.client-radar.org → YOUR_SERVER_IP ✓
   • ANY subdomain → YOUR_SERVER_IP ✓


2. NGINX WILDCARD CONFIG
   ────────────────────────────────────────────────────────────
   server_name ~^(?<subdomain>[^.]+)\.client-radar\.org$;
   
   • Nginx captures subdomain from URL
   • Passes it to backend via X-Tenant-Subdomain header
   • Routes to appropriate service (Django or Next.js)


3. DJANGO TENANT MIDDLEWARE
   ────────────────────────────────────────────────────────────
   • Extracts subdomain from request
   • Looks up Tenant in database
   • Routes to tenant-specific database
   • Applies tenant-specific permissions


4. TENANT CREATION FLOW
   ────────────────────────────────────────────────────────────
   POST /hr/create-tenant/ {
     "subdomain": "adam",
     "name": "Adam Company"
   }
   
   Django automatically:
   • Creates Tenant record in main DB
   • Creates tenant_adam.sqlite3 database
   • Runs migrations on new database
   • Creates config: tenants/adam/config.json
   • Subdomain is INSTANTLY accessible! ✓


5. REQUEST ROUTING
   ────────────────────────────────────────────────────────────
   User visits: https://adam.client-radar.org
      ↓
   DNS: adam.client-radar.org → YOUR_SERVER_IP
      ↓
   Nginx: Captures subdomain="adam"
      ↓
   Next.js: Renders UI, sends API requests with X-Tenant-Subdomain: adam
      ↓
   Django: Reads header, loads tenant_adam database
      ↓
   Response: Tenant-specific data


6. SSL WILDCARD CERTIFICATE
   ────────────────────────────────────────────────────────────
   • Single certificate covers ALL subdomains
   • *.client-radar.org certificate
   • Secured by Let's Encrypt
   • Auto-renews every 60 days


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


📊 MONITORING & MAINTENANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View Logs:
──────────────────────────────────────────────────────────────
  # Django
  journalctl -u django -f

  # Next.js
  pm2 logs nextjs

  # Nginx
  tail -f /var/log/nginx/tenant_access.log
  tail -f /var/log/nginx/tenant_error.log


Service Management:
──────────────────────────────────────────────────────────────
  # Restart Django
  sudo systemctl restart django

  # Restart Next.js
  pm2 restart nextjs

  # Reload Nginx
  sudo systemctl reload nginx


Deployment Updates:
──────────────────────────────────────────────────────────────
  ./deploy_production.sh


Health Checks:
──────────────────────────────────────────────────────────────
  # Django
  curl https://client-radar.org/admin/

  # Tenant subdomain
  curl https://adam.client-radar.org/


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


✅ VERIFICATION CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ DNS wildcard record configured
□ Server packages installed
□ Project cloned and configured
□ Python dependencies installed
□ Frontend built successfully
□ SSL certificate obtained
□ System services running
□ Nginx configured and running
□ Can access https://client-radar.org
□ Can create test tenant
□ Can access https://test.client-radar.org
□ Tenant can login and use system


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


🎉 SUCCESS!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your multi-tenant system is now live!

Main Portal: https://client-radar.org
Tenant Example: https://adam.client-radar.org

Any new tenant created will automatically get their own subdomain.


📞 SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Common Issues:
  • 502 Bad Gateway → Check Django service running
  • SSL errors → Re-run setup_ssl.sh
  • Tenant not found → Check DNS propagation
  • Module access denied → Check TenantModule records

EOF
