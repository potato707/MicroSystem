"""
Django management command to set up SSL for custom domains
"""
import subprocess
import os
from django.core.management.base import BaseCommand, CommandError
from hr_management.tenant_models import Tenant


class Command(BaseCommand):
    help = 'Set up SSL certificate for a tenant custom domain using Let\'s Encrypt'

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            type=str,
            help='Custom domain to set up SSL for (e.g., adamcompany.com)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@localhost',
            help='Email for Let\'s Encrypt notifications'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Test the SSL setup without actually installing'
        )

    def handle(self, *args, **options):
        domain = options['domain']
        email = options['email']
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.WARNING(f'\n🔒 Setting up SSL for: {domain}'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        # Check if tenant exists
        try:
            tenant = Tenant.objects.filter(custom_domain=domain).first()
            if not tenant:
                raise CommandError(f'❌ Tenant with custom domain "{domain}" not found')
            
            self.stdout.write(self.style.SUCCESS(f'✓ Found tenant: {tenant.name}'))
        except Exception as e:
            raise CommandError(f'❌ Error finding tenant: {e}')
        
        # Check if certbot is installed
        if not self._check_certbot_installed():
            self.stdout.write(self.style.ERROR('❌ Certbot is not installed'))
            self.stdout.write(self.style.WARNING('\nInstall it with:'))
            self.stdout.write(self.style.WARNING('  sudo apt-get update'))
            self.stdout.write(self.style.WARNING('  sudo apt-get install certbot python3-certbot-nginx'))
            return
        
        # Check if nginx is installed
        if not self._check_nginx_installed():
            self.stdout.write(self.style.ERROR('❌ Nginx is not installed'))
            return
        
        # Run certbot
        try:
            if dry_run:
                self.stdout.write(self.style.WARNING('\n🧪 DRY RUN MODE - No changes will be made'))
                cmd = [
                    'sudo', 'certbot', 'certonly',
                    '--nginx',
                    '--dry-run',
                    '-d', domain,
                    '-d', f'www.{domain}',
                    '--email', email,
                    '--agree-tos',
                    '--non-interactive'
                ]
            else:
                self.stdout.write(self.style.WARNING('\n📜 Obtaining SSL certificate...'))
                cmd = [
                    'sudo', 'certbot',
                    '--nginx',
                    '-d', domain,
                    '-d', f'www.{domain}',
                    '--email', email,
                    '--agree-tos',
                    '--non-interactive',
                    '--redirect'  # Auto redirect HTTP to HTTPS
                ]
            
            self.stdout.write(self.style.WARNING(f'Running: {" ".join(cmd)}\n'))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                self.stdout.write(self.style.SUCCESS('\n✅ SSL certificate obtained successfully!'))
                self.stdout.write(self.style.SUCCESS(f'🌐 https://{domain} is now secure'))
                
                # Update tenant SSL status
                if not dry_run:
                    tenant.ssl_enabled = True
                    tenant.save()
                    self.stdout.write(self.style.SUCCESS('✓ Updated tenant SSL status'))
                
                # Show certificate info
                self._show_certificate_info(domain)
            else:
                self.stdout.write(self.style.ERROR('\n❌ Failed to obtain SSL certificate'))
                self.stdout.write(self.style.ERROR(f'Error: {result.stderr}'))
                
                # Show common issues
                self._show_troubleshooting()
        
        except subprocess.TimeoutExpired:
            raise CommandError('❌ Certbot command timed out (5 minutes)')
        except Exception as e:
            raise CommandError(f'❌ Error running certbot: {e}')
        
        # Show next steps
        self.stdout.write(self.style.WARNING('\n' + '=' * 60))
        self.stdout.write(self.style.WARNING('📋 Next Steps:'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'1. Test HTTPS: https://{domain}'))
        self.stdout.write(self.style.SUCCESS('2. Certificate auto-renews every 90 days'))
        self.stdout.write(self.style.SUCCESS('3. Check renewal: sudo certbot renew --dry-run'))
        self.stdout.write(self.style.SUCCESS('4. View certificates: sudo certbot certificates'))
        self.stdout.write('')
    
    def _check_certbot_installed(self):
        """Check if certbot is installed"""
        try:
            result = subprocess.run(
                ['which', 'certbot'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_nginx_installed(self):
        """Check if nginx is installed"""
        try:
            result = subprocess.run(
                ['which', 'nginx'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _show_certificate_info(self, domain):
        """Show certificate information"""
        try:
            result = subprocess.run(
                ['sudo', 'certbot', 'certificates', '-d', domain],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.stdout.write(self.style.WARNING('\n📜 Certificate Info:'))
                self.stdout.write(result.stdout)
        except Exception:
            pass
    
    def _show_troubleshooting(self):
        """Show common troubleshooting steps"""
        self.stdout.write(self.style.WARNING('\n🔧 Troubleshooting:'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write('')
        self.stdout.write('1. Check DNS is working:')
        self.stdout.write('   nslookup domain.com')
        self.stdout.write('')
        self.stdout.write('2. Check domain is pointing to this server:')
        self.stdout.write('   dig domain.com')
        self.stdout.write('')
        self.stdout.write('3. Check Nginx configuration:')
        self.stdout.write('   sudo nginx -t')
        self.stdout.write('')
        self.stdout.write('4. Check firewall allows port 80 and 443:')
        self.stdout.write('   sudo ufw status')
        self.stdout.write('')
        self.stdout.write('5. Wait 15-30 minutes for DNS propagation')
        self.stdout.write('')
