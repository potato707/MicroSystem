"""
Tenant Management Service
Handles tenant creation, configuration generation, and folder management
Supports database-per-tenant architecture
"""
import os
import shutil
import json
import subprocess
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.db import connections, connection
from .tenant_models import Tenant, TenantModule, ModuleDefinition
from .tenant_db_router import get_tenant_db_config
import logging

logger = logging.getLogger(__name__)


class TenantService:
    """Service for managing tenant lifecycle operations"""
    
    @staticmethod
    def get_base_frontend_path():
        """Returns the path to the base frontend template"""
        return os.path.join(settings.BASE_DIR, 'frontend')
    
    @staticmethod
    def get_tenants_root_path():
        """Returns the root path where all tenant folders are stored"""
        tenants_path = os.path.join(settings.BASE_DIR, 'tenants')
        os.makedirs(tenants_path, exist_ok=True)
        return tenants_path
    
    @staticmethod
    def create_tenant_folder_structure(tenant):
        """
        Creates the folder structure for a new tenant
        Returns the path to the tenant's folder
        """
        tenant_path = tenant.folder_path
        
        try:
            # Create main tenant folder
            os.makedirs(tenant_path, exist_ok=True)
            logger.info(f"Created tenant folder: {tenant_path}")
            
            # Create subdirectories
            subdirs = ['public', 'public/images', 'config', 'assets']
            for subdir in subdirs:
                subdir_path = os.path.join(tenant_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
            
            return tenant_path
        
        except Exception as e:
            logger.error(f"Error creating tenant folder structure: {e}")
            raise
    
    @staticmethod
    def copy_frontend_template(tenant):
        """
        Copies the base frontend template to the tenant's folder
        This creates a complete Next.js app instance for the tenant
        """
        base_frontend = TenantService.get_base_frontend_path()
        tenant_path = tenant.folder_path
        
        try:
            # Check if base frontend exists
            if not os.path.exists(base_frontend):
                logger.warning(f"Base frontend template not found at {base_frontend}")
                return False
            
            # Copy specific directories (avoid node_modules and .next)
            dirs_to_copy = ['src', 'public']
            files_to_copy = ['package.json', 'next.config.js', 'tsconfig.json', 
                           'tailwind.config.js', 'postcss.config.js', '.eslintrc.json']
            
            # Copy directories
            for dir_name in dirs_to_copy:
                src_dir = os.path.join(base_frontend, dir_name)
                dst_dir = os.path.join(tenant_path, dir_name)
                
                if os.path.exists(src_dir):
                    if os.path.exists(dst_dir):
                        shutil.rmtree(dst_dir)
                    shutil.copytree(src_dir, dst_dir)
                    logger.info(f"Copied {dir_name} to tenant folder")
            
            # Copy individual files
            for file_name in files_to_copy:
                src_file = os.path.join(base_frontend, file_name)
                dst_file = os.path.join(tenant_path, file_name)
                
                if os.path.exists(src_file):
                    shutil.copy2(src_file, dst_file)
                    logger.info(f"Copied {file_name} to tenant folder")
            
            return True
        
        except Exception as e:
            logger.error(f"Error copying frontend template: {e}")
            return False
    
    @staticmethod
    def generate_config_json(tenant):
        """
        Generates and writes the config.json file for a tenant
        Returns the path to the config file
        """
        config_data = tenant.generate_config_json()
        config_path = tenant.config_path
        
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Write config.json
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Generated config.json at {config_path}")
            return config_path
        
        except Exception as e:
            logger.error(f"Error generating config.json: {e}")
            raise
    
    @staticmethod
    def create_tenant_with_modules(tenant_data, module_keys, created_by=None):
        """
        Creates a new tenant with specified modules
        
        Args:
            tenant_data: Dictionary with tenant information
            module_keys: List of module keys to enable
            created_by: User who created the tenant
        
        Returns:
            Tuple of (tenant, created_successfully)
        """
        try:
            # Extract admin credentials if provided
            admin_credentials = tenant_data.pop('_admin_credentials', None)
            
            # Create tenant instance
            tenant = Tenant.objects.create(
                name=tenant_data['name'],
                subdomain=tenant_data['subdomain'],
                custom_domain=tenant_data.get('custom_domain'),
                primary_color=tenant_data.get('primary_color', '#3498db'),
                secondary_color=tenant_data.get('secondary_color', '#2ecc71'),
                contact_email=tenant_data.get('contact_email'),
                contact_phone=tenant_data.get('contact_phone'),
                created_by=created_by
            )
            
            # Attach credentials to tenant instance for the signal
            if admin_credentials:
                tenant._admin_credentials = admin_credentials
                # Save again to trigger signal with credentials
                tenant.save()
            
            # Handle logo upload if provided
            if 'logo' in tenant_data and tenant_data['logo']:
                tenant.logo = tenant_data['logo']
                tenant.save()
            
            # Create tenant modules (use get_or_create to avoid duplicates)
            module_definitions = ModuleDefinition.objects.all()
            for module_def in module_definitions:
                is_enabled = module_def.module_key in module_keys or module_def.is_core
                
                TenantModule.objects.get_or_create(
                    tenant=tenant,
                    module_key=module_def.module_key,
                    defaults={
                        'module_name': module_def.module_name,
                        'is_enabled': is_enabled
                    }
                )
            
            # Create folder structure
            TenantService.create_tenant_folder_structure(tenant)
            
            # Copy frontend template (optional, can be done on-demand)
            # TenantService.copy_frontend_template(tenant)
            
            # Generate config.json
            TenantService.generate_config_json(tenant)
            
            logger.info(f"Successfully created tenant: {tenant.name}")
            return tenant, True
        
        except Exception as e:
            logger.error(f"Error creating tenant: {e}")
            # Cleanup if tenant was created
            if 'tenant' in locals():
                tenant.delete()
            raise
    
    @staticmethod
    def update_tenant_config(tenant):
        """
        Updates the config.json file for an existing tenant
        Call this whenever tenant settings or modules change
        """
        try:
            TenantService.generate_config_json(tenant)
            return True
        except Exception as e:
            logger.error(f"Error updating tenant config: {e}")
            return False
    
    @staticmethod
    def delete_tenant_folder(tenant):
        """
        Deletes the tenant's folder structure
        Use with caution!
        """
        tenant_path = tenant.folder_path
        
        try:
            if os.path.exists(tenant_path):
                shutil.rmtree(tenant_path)
                logger.info(f"Deleted tenant folder: {tenant_path}")
                return True
            return False
        
        except Exception as e:
            logger.error(f"Error deleting tenant folder: {e}")
            return False
    
    @staticmethod
    def initialize_module_definitions():
        """
        Creates default module definitions if they don't exist
        Call this during initial setup
        """
        default_modules = [
            {
                'module_key': 'employees',
                'module_name': 'Employee Management',
                'description': 'Manage employees, departments, and positions',
                'icon': 'users',
                'is_core': True,
                'sort_order': 1
            },
            {
                'module_key': 'attendance',
                'module_name': 'Attendance Tracking',
                'description': 'Track employee attendance and working hours',
                'icon': 'clock',
                'is_core': False,
                'sort_order': 2
            },
            {
                'module_key': 'wallet',
                'module_name': 'Wallet & Salary',
                'description': 'Manage employee wallets, salaries, and transactions',
                'icon': 'wallet',
                'is_core': False,
                'sort_order': 3
            },
            {
                'module_key': 'tasks',
                'module_name': 'Task Management',
                'description': 'Assign and track tasks and projects',
                'icon': 'clipboard-list',
                'is_core': False,
                'sort_order': 4
            },
            {
                'module_key': 'complaints',
                'module_name': 'Complaint System',
                'description': 'Handle client complaints and support tickets',
                'icon': 'message-square',
                'is_core': False,
                'sort_order': 5
            },
            {
                'module_key': 'shifts',
                'module_name': 'Shift Scheduling',
                'description': 'Manage employee shifts and schedules',
                'icon': 'calendar',
                'is_core': False,
                'sort_order': 6
            },
            {
                'module_key': 'reports',
                'module_name': 'Reports & Analytics',
                'description': 'View detailed reports and analytics',
                'icon': 'bar-chart',
                'is_core': False,
                'sort_order': 7
            },
            {
                'module_key': 'notifications',
                'module_name': 'Notifications',
                'description': 'Email and system notifications',
                'icon': 'bell',
                'is_core': True,
                'sort_order': 8
            },
        ]
        
        created_count = 0
        for module_data in default_modules:
            module, created = ModuleDefinition.objects.get_or_create(
                module_key=module_data['module_key'],
                defaults=module_data
            )
            if created:
                created_count += 1
                logger.info(f"Created module definition: {module.module_name}")
        
        logger.info(f"Module definitions initialized. Created: {created_count}")
        return created_count
    
    
    # ==========================================
    # DATABASE-PER-TENANT METHODS
    # ==========================================
    
    @staticmethod
    def create_tenant_database(tenant):
        """
        Create a new database for the tenant
        
        Args:
            tenant: Tenant instance
        
        Returns:
            tuple: (success: bool, db_alias: str, error: str)
        """
        subdomain = tenant.subdomain
        db_alias = f"tenant_{subdomain}"
        
        logger.info(f"Creating database for tenant: {subdomain}")
        
        try:
            # Get database engine from settings
            engine = settings.DATABASES['default']['ENGINE']
            
            if 'postgresql' in engine:
                success, error = TenantService._create_postgresql_database(subdomain)
            elif 'mysql' in engine:
                success, error = TenantService._create_mysql_database(subdomain)
            elif 'sqlite' in engine:
                success, error = TenantService._create_sqlite_database(subdomain)
            else:
                return False, db_alias, f"Unsupported database engine: {engine}"
            
            if not success:
                return False, db_alias, error
            
            # Add database to Django settings
            TenantService._register_tenant_database(subdomain)
            
            logger.info(f"✓ Database created successfully: {db_alias}")
            return True, db_alias, None
            
        except Exception as e:
            error_msg = f"Error creating tenant database: {str(e)}"
            logger.error(error_msg)
            return False, db_alias, error_msg
    
    @staticmethod
    def _create_postgresql_database(subdomain):
        """Create PostgreSQL database"""
        db_name = f"tenant_{subdomain}"
        
        try:
            # Use default connection to create database
            with connection.cursor() as cursor:
                # Close any existing connections to the database
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{db_name}'
                    AND pid <> pg_backend_pid();
                """)
                
                # Create database
                cursor.execute(f'CREATE DATABASE "{db_name}"')
                
            logger.info(f"✓ PostgreSQL database created: {db_name}")
            return True, None
            
        except Exception as e:
            error_msg = f"PostgreSQL error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def _create_mysql_database(subdomain):
        """Create MySQL database"""
        db_name = f"tenant_{subdomain}"
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE DATABASE `{db_name}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
            
            logger.info(f"✓ MySQL database created: {db_name}")
            return True, None
            
        except Exception as e:
            error_msg = f"MySQL error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def _create_sqlite_database(subdomain):
        """Create SQLite database (just register it, file will be created on first write)"""
        db_name = f"tenant_{subdomain}.sqlite3"
        logger.info(f"✓ SQLite database will be created: {db_name}")
        return True, None
    
    @staticmethod
    def _register_tenant_database(subdomain):
        """
        Register tenant database in Django settings
        This allows Django to use the database
        """
        db_alias = f"tenant_{subdomain}"
        db_config = get_tenant_db_config(subdomain)
        
        # Add to settings.DATABASES
        settings.DATABASES[db_alias] = db_config
        
        # Force connection object to refresh its databases dict
        connections.databases[db_alias] = db_config
        
        # If connection already exists, close and remove it to force fresh connection
        if db_alias in connections:
            try:
                connections[db_alias].close()
            except:
                pass
            delattr(connections._connections, db_alias)
        
        logger.info(f"✓ Database registered in Django: {db_alias}")
        logger.debug(f"  Config: {db_config}")
    
    @staticmethod
    def migrate_tenant_database(tenant):
        """
        Run migrations on tenant database
        
        Args:
            tenant: Tenant instance
        
        Returns:
            tuple: (success: bool, error: str)
        """
        db_alias = f"tenant_{tenant.subdomain}"
        
        logger.info(f"Running migrations for {db_alias}...")
        
        try:
            # Use --fake-initial to handle existing tables
            call_command('migrate', '--fake-initial', database=db_alias, verbosity=0, interactive=False)
            
            logger.info(f"✓ Migrations completed for {db_alias}")
            return True, None
            
        except Exception as e:
            error_msg = f"Migration error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    @staticmethod
    def create_tenant_superuser(tenant, username='admin', email=None, password='admin123'):
        """
        Create superuser for tenant database
        
        Args:
            tenant: Tenant instance
            username: Username for superuser
            email: Email for superuser
            password: Password for superuser
        
        Returns:
            tuple: (success: bool, user, error: str)
        """
        from django.contrib.auth import get_user_model
        
        db_alias = f"tenant_{tenant.subdomain}"
        User = get_user_model()
        
        if email is None:
            email = f"admin@{tenant.subdomain}.com"
        
        logger.info(f"Creating superuser for {db_alias}: {username}")
        
        try:
            # Check if user already exists
            if User.objects.using(db_alias).filter(username=username).exists():
                user = User.objects.using(db_alias).get(username=username)
                logger.info(f"✓ Superuser already exists: {username}")
                return True, user, None
            
            # Create superuser in tenant database using db connection
            from django.db import connections
            from django.contrib.auth.hashers import make_password
            
            user = User(
                username=username,
                email=email,
                is_staff=True,
                is_superuser=True,
                is_active=True,
                password=make_password(password)
            )
            user.save(using=db_alias)
            
            logger.info(f"✓ Superuser created: {username}")
            return True, user, None
            
        except Exception as e:
            error_msg = f"Error creating superuser: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    @staticmethod
    def initialize_tenant_modules_in_db(tenant):
        """
        Initialize module definitions in tenant database
        
        Args:
            tenant: Tenant instance
        
        Returns:
            tuple: (success: bool, count: int, error: str)
        """
        db_alias = f"tenant_{tenant.subdomain}"
        
        logger.info(f"Initializing modules in {db_alias}...")
        
        try:
            # Get module definitions from default DB
            module_definitions = ModuleDefinition.objects.using('default').all()
            
            # Copy to tenant DB
            for module_def in module_definitions:
                ModuleDefinition.objects.using(db_alias).get_or_create(
                    module_key=module_def.module_key,
                    defaults={
                        'module_name': module_def.module_name,
                        'description': module_def.description,
                        'icon': module_def.icon,
                        'is_core': module_def.is_core,
                        'sort_order': module_def.sort_order,
                    }
                )
            
            count = ModuleDefinition.objects.using(db_alias).count()
            logger.info(f"✓ Modules initialized in {db_alias}: {count}")
            return True, count, None
            
        except Exception as e:
            error_msg = f"Error initializing modules: {str(e)}"
            logger.error(error_msg)
            return False, 0, error_msg
    
    @staticmethod
    def setup_complete_tenant(tenant, admin_password='admin123'):
        """
        Complete setup for a new tenant:
        1. Create database
        2. Run migrations
        3. Create superuser
        4. Initialize modules
        5. Create folder structure
        6. Generate config.json
        
        Args:
            tenant: Tenant instance
            admin_password: Password for admin user
        
        Returns:
            dict: Status of each step
        """
        logger.info(f"=" * 60)
        logger.info(f"Setting up complete tenant: {tenant.name} ({tenant.subdomain})")
        logger.info(f"=" * 60)
        
        results = {
            'tenant': tenant.subdomain,
            'database_created': False,
            'migrations_run': False,
            'superuser_created': False,
            'modules_initialized': False,
            'folder_created': False,
            'config_generated': False,
            'errors': []
        }
        
        # Step 1: Create database
        logger.info("Step 1: Creating database...")
        success, db_alias, error = TenantService.create_tenant_database(tenant)
        results['database_created'] = success
        results['db_alias'] = db_alias
        if not success:
            results['errors'].append(f"Database creation: {error}")
            return results
        
        # Step 2: Run migrations
        logger.info("Step 2: Running migrations...")
        success, error = TenantService.migrate_tenant_database(tenant)
        results['migrations_run'] = success
        if not success:
            results['errors'].append(f"Migrations: {error}")
            return results
        
        # Step 3: Create superuser
        logger.info("Step 3: Creating superuser...")
        success, user, error = TenantService.create_tenant_superuser(
            tenant, 
            password=admin_password
        )
        results['superuser_created'] = success
        results['admin_username'] = 'admin' if success else None
        if not success:
            results['errors'].append(f"Superuser: {error}")
            # Continue anyway
        
        # Step 4: Initialize modules
        logger.info("Step 4: Initializing modules...")
        success, count, error = TenantService.initialize_tenant_modules_in_db(tenant)
        results['modules_initialized'] = success
        results['modules_count'] = count if success else 0
        if not success:
            results['errors'].append(f"Modules: {error}")
            # Continue anyway
        
        # Step 5: Create folder structure
        logger.info("Step 5: Creating folder structure...")
        try:
            TenantService.create_tenant_folder_structure(tenant)
            results['folder_created'] = True
        except Exception as e:
            results['errors'].append(f"Folder: {str(e)}")
        
        # Step 6: Generate config.json
        logger.info("Step 6: Generating config.json...")
        try:
            TenantService.generate_config_json(tenant)
            results['config_generated'] = True
        except Exception as e:
            results['errors'].append(f"Config: {str(e)}")
        
        logger.info(f"=" * 60)
        logger.info(f"✓ Tenant setup complete: {tenant.subdomain}")
        logger.info(f"  Database: {db_alias}")
        logger.info(f"  Admin: admin / {admin_password}")
        logger.info(f"  Modules: {results.get('modules_count', 0)}")
        logger.info(f"=" * 60)
        
        return results

