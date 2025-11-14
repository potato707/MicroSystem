"""
Celery tasks for automated SSL certificate management
"""
from celery import shared_task
from django.utils import timezone
from django.core.management import call_command
import subprocess
import time
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def setup_ssl_certificate(self, tenant_id, email='admin@localhost'):
    """
    Automatically set up SSL certificate for a tenant's custom domain.
    This runs as a background task with retry logic.
    
    Args:
        tenant_id: UUID of the tenant
        email: Email for Let's Encrypt notifications
    
    Returns:
        dict with success status and message
    """
    from hr_management.tenant_models import Tenant
    
    try:
        # Get tenant
        tenant = Tenant.objects.get(id=tenant_id)
        
        if tenant.domain_type != 'custom' or not tenant.custom_domain:
            return {
                'success': False,
                'message': 'Tenant does not have a custom domain'
            }
        
        domain = tenant.custom_domain
        logger.info(f'🔒 Starting SSL setup for: {domain}')
        
        # Step 1: Wait for DNS propagation (if recently created)
        if tenant.created_at and (timezone.now() - tenant.created_at).total_seconds() < 1800:
            wait_time = 300  # 5 minutes
            logger.info(f'⏳ Waiting {wait_time}s for DNS propagation...')
            time.sleep(wait_time)
        
        # Step 2: Verify DNS is working
        if not verify_dns(domain):
            logger.warning(f'⚠️  DNS not ready for {domain}, retrying in 5 minutes...')
            raise self.retry(countdown=300, exc=Exception('DNS not propagated yet'))
        
        # Step 3: Add domain to nginx config BEFORE certbot
        logger.info(f'📝 Adding {domain} to Nginx config...')
        if not add_domain_to_nginx(domain):
            logger.error(f'❌ Failed to add {domain} to Nginx config')
            raise Exception('Failed to configure Nginx')
        
        # Step 4: Reload nginx to apply new config
        subprocess.run(['sudo', 'nginx', '-t'], check=True)  # Test config first
        subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'], check=True)
        logger.info(f'✅ Nginx config updated and reloaded')
        
        # Step 5: Run certbot
        logger.info(f'📜 Running certbot for {domain}...')
        
        cmd = [
            'sudo', 'certbot',
            '--nginx',
            '-d', domain,
            '--email', email,
            '--agree-tos',
            '--non-interactive',
            '--redirect',
            '--keep-until-expiring'  # Don't fail if cert already exists
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            # Success!
            tenant.ssl_enabled = True
            tenant.ssl_issued_at = timezone.now()
            tenant.save()
            
            logger.info(f'✅ SSL enabled for {domain}')
            
            return {
                'success': True,
                'message': f'SSL certificate installed for {domain}',
                'domain': domain
            }
        else:
            error_msg = result.stderr or result.stdout
            logger.error(f'❌ Certbot failed for {domain}: {error_msg}')
            
            # Retry up to 3 times
            if self.request.retries < self.max_retries:
                raise self.retry(countdown=600, exc=Exception(error_msg))
            
            return {
                'success': False,
                'message': f'Failed after {self.max_retries} attempts: {error_msg}',
                'domain': domain
            }
    
    except Tenant.DoesNotExist:
        logger.error(f'❌ Tenant {tenant_id} not found')
        return {
            'success': False,
            'message': f'Tenant {tenant_id} not found'
        }
    
    except subprocess.TimeoutExpired:
        logger.error(f'❌ Certbot timeout for {domain}')
        return {
            'success': False,
            'message': 'Certbot command timed out'
        }
    
    except Exception as e:
        logger.error(f'❌ Unexpected error for {domain}: {e}')
        
        # Retry
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=600, exc=e)
        
        return {
            'success': False,
            'message': str(e)
        }


@shared_task
def check_ssl_expiry():
    """
    Check all tenants with SSL and renew certificates about to expire.
    Run this daily via cron or celery beat.
    """
    from hr_management.tenant_models import Tenant
    from datetime import timedelta
    
    logger.info('🔍 Checking SSL certificate expiry...')
    
    # Get tenants with SSL enabled
    tenants_with_ssl = Tenant.objects.filter(
        domain_type='custom',
        ssl_enabled=True,
        custom_domain__isnull=False
    )
    
    renewed_count = 0
    failed_count = 0
    
    for tenant in tenants_with_ssl:
        try:
            # Check if certificate expires in next 30 days
            if should_renew_certificate(tenant.custom_domain):
                logger.info(f'🔄 Renewing certificate for {tenant.custom_domain}')
                
                cmd = ['sudo', 'certbot', 'renew', '--cert-name', tenant.custom_domain]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    tenant.ssl_issued_at = timezone.now()
                    tenant.save()
                    renewed_count += 1
                    logger.info(f'✅ Renewed: {tenant.custom_domain}')
                else:
                    failed_count += 1
                    logger.error(f'❌ Failed to renew: {tenant.custom_domain}')
        
        except Exception as e:
            failed_count += 1
            logger.error(f'❌ Error checking {tenant.custom_domain}: {e}')
    
    logger.info(f'✓ SSL check complete: {renewed_count} renewed, {failed_count} failed')
    
    return {
        'renewed': renewed_count,
        'failed': failed_count
    }


def add_domain_to_nginx(domain):
    """
    Add a custom domain server block to client-radar.conf
    This creates an HTTP server block that certbot will then upgrade to HTTPS
    """
    nginx_config_path = '/etc/nginx/sites-available/client-radar.conf'
    
    # Server block template for custom domain
    server_block = f"""
# Custom domain: {domain}
server {{
    listen 80;
    server_name {domain};

    # Frontend (Next.js)
    location / {{
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}

    # Backend API (Django)
    location /hr/ {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}

    location /api/ {{
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}
}}
"""
    
    try:
        # Read current config
        with open(nginx_config_path, 'r') as f:
            config = f.read()
        
        # Check if domain already exists
        if f'server_name {domain}' in config:
            logger.info(f'✓ {domain} already in Nginx config')
            return True
        
        # Append new server block
        with open(nginx_config_path, 'a') as f:
            f.write('\n' + server_block)
        
        logger.info(f'✓ Added {domain} to {nginx_config_path}')
        return True
    
    except Exception as e:
        logger.error(f'Error adding {domain} to Nginx config: {e}')
        return False


def verify_dns(domain):
    """
    Verify that DNS is properly configured for the domain.
    Returns True if domain resolves to our server IP.
    """
    import socket
    
    try:
        # Get domain IP
        ip = socket.gethostbyname(domain)
        
        # Get server IP
        import requests
        server_ip = requests.get('https://api.ipify.org').text
        
        logger.info(f'DNS check: {domain} → {ip}, Server IP: {server_ip}')
        
        # Check if they match (or close enough)
        # In production, you might want more sophisticated checking
        return ip == server_ip
    
    except socket.gaierror:
        logger.warning(f'DNS lookup failed for {domain}')
        return False
    except Exception as e:
        logger.error(f'Error verifying DNS for {domain}: {e}')
        return False


def should_renew_certificate(domain):
    """
    Check if certificate should be renewed (expires in < 30 days)
    """
    try:
        cmd = ['sudo', 'certbot', 'certificates', '-d', domain]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout
            
            # Parse expiry date from output
            # Let's Encrypt certs are valid for 90 days
            # Certbot auto-renews at 30 days before expiry
            
            # Simple check: if certbot says "VALID" and near expiry, renew
            if 'VALID' in output and 'days' in output:
                # Extract days remaining (simplified)
                import re
                match = re.search(r'(\d+) day', output)
                if match:
                    days_remaining = int(match.group(1))
                    return days_remaining < 30
        
        return False
    
    except Exception as e:
        logger.error(f'Error checking certificate expiry for {domain}: {e}')
        return False


@shared_task
def cleanup_failed_ssl_attempts():
    """
    Clean up tenants that have been waiting for SSL for too long.
    Mark them for manual intervention.
    """
    from hr_management.tenant_models import Tenant
    from datetime import timedelta
    
    # Find tenants with custom domain but no SSL after 24 hours
    threshold = timezone.now() - timedelta(hours=24)
    
    tenants = Tenant.objects.filter(
        domain_type='custom',
        ssl_enabled=False,
        custom_domain__isnull=False,
        created_at__lt=threshold
    )
    
    for tenant in tenants:
        logger.warning(f'⚠️  SSL setup failed for {tenant.custom_domain} - needs manual intervention')
        
        # Could send notification to admin
        # send_admin_notification(f'SSL setup failed for {tenant.custom_domain}')
    
    return {
        'tenants_needing_attention': tenants.count()
    }
