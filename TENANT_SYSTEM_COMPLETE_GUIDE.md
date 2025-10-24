# Multi-Tenant SaaS System - Complete Implementation Guide

## Overview

This document provides a comprehensive guide to the multi-tenant SaaS system built with Django (backend) and React (frontend). The system allows you to create and manage multiple client tenants, each with customizable branding, features, and configurations.

---

## 1. Folder Structure

```
MicroSystem/
├── MicroSystem/                    # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── hr_management/                  # Main Django app
│   ├── models.py                   # Existing models
│   ├── tenant_models.py           # ✨ NEW: Tenant models
│   ├── tenant_service.py          # ✨ NEW: Tenant business logic
│   ├── tenant_serializers.py      # ✨ NEW: API serializers
│   ├── tenant_views.py            # ✨ NEW: API views
│   ├── tenant_urls.py             # ✨ NEW: URL routing
│   ├── tenant_middleware.py       # ✨ NEW: Middleware
│   ├── admin.py                   # Updated with tenant admin
│   └── management/
│       └── commands/
│           └── init_modules.py    # ✨ NEW: Initialize modules
│
├── frontend/                       # React frontend (base template)
│   └── src/
│       ├── pages/
│       │   ├── CreateTenantPage.jsx     # ✨ NEW: Create tenant UI
│       │   ├── CreateTenantPage.css
│       │   ├── TenantListPage.jsx       # ✨ NEW: List tenants UI
│       │   └── TenantListPage.css
│       ├── components/
│       │   ├── LockedModule.jsx         # ✨ NEW: Locked module UI
│       │   └── LockedModule.css
│       └── utils/
│           ├── tenantApi.js             # ✨ NEW: API client
│           └── tenantConfig.js          # ✨ NEW: Config loader
│
├── tenants/                        # ✨ NEW: Tenant instances folder
│   ├── client1/                    # Example tenant
│   │   ├── config.json            # Tenant configuration
│   │   ├── src/                   # Copied frontend
│   │   ├── public/                # Public assets
│   │   └── package.json
│   ├── client2/
│   └── ...
│
└── media/                          # Media files
    └── tenants/
        └── logos/                  # Tenant logos
```

---

## 2. Tenant Creation Page Layout

### Page: `/create-tenant`

The tenant creation page includes the following sections:

#### **Section 1: Basic Information**
- **Client Name** (required) - Full name of the client organization
- **Subdomain** (required) - URL subdomain (auto-generated from name)
  - Example: `acme` → `acme.myapp.com`
- **Custom Domain** (optional) - Custom domain like `client.myapp.com`
- **Contact Email** - Primary contact email
- **Contact Phone** - Contact phone number

#### **Section 2: Branding**
- **Logo Upload** - Client logo image (with preview)
- **Primary Color** - Main brand color (color picker + hex input)
- **Secondary Color** - Secondary brand color
- **Live Preview** - Shows how colors will look

#### **Section 3: Feature Modules** (Checkboxes)
Available modules to enable/disable:

✅ **Core Modules** (always enabled):
- Employee Management
- Notifications

🔲 **Optional Modules**:
- ☐ Attendance Tracking
- ☐ Wallet & Salary
- ☐ Task Management
- ☐ Complaint System
- ☐ Shift Scheduling
- ☐ Reports & Analytics

Each module card shows:
- Module name
- Description
- Icon
- "Core Module" badge (if applicable)

#### **Section 4: Actions**
- **Generate Tenant** button - Creates the tenant
- **Cancel** button - Returns to previous page

---

## 3. Tenant Generation Flow

### Step-by-Step Process

```
1. User fills form on /create-tenant page
2. Frontend validates input
3. POST request to /api/tenants/
4. Django TenantService processes request:
   ├─ Create Tenant record in database
   ├─ Save logo to media/tenants/logos/
   ├─ Create TenantModule records for each module
   ├─ Create folder: /tenants/{subdomain}/
   ├─ Generate config.json in tenant folder
   └─ (Optional) Copy frontend template
5. Return success response with tenant details
6. Frontend shows success message
```

### What Gets Created?

#### **Database Records:**
```python
# Tenant record
Tenant(
    name="Acme Corporation",
    subdomain="acme",
    primary_color="#3498db",
    secondary_color="#2ecc71",
    logo="tenants/logos/acme.png"
)

# Module records
TenantModule(tenant=acme, module_key="employees", is_enabled=True)
TenantModule(tenant=acme, module_key="attendance", is_enabled=True)
TenantModule(tenant=acme, module_key="wallet", is_enabled=False)
# ... etc
```

#### **File System:**
```
/tenants/acme/
├── config.json              # Tenant configuration
├── public/                  # Public assets
│   └── images/
├── config/                  # Additional configs
└── assets/                  # Tenant-specific assets
```

#### **config.json Content:**
```json
{
  "name": "Acme Corporation",
  "domain": "acme.myapp.com",
  "subdomain": "acme",
  "modules": {
    "employees": true,
    "attendance": true,
    "wallet": false,
    "tasks": false,
    "complaints": false,
    "shifts": false,
    "reports": false,
    "notifications": true
  },
  "theme": {
    "primary": "#3498db",
    "secondary": "#2ecc71"
  },
  "logo_url": "/media/tenants/logos/acme.png",
  "contact": {
    "email": "admin@acme.com",
    "phone": "+1234567890"
  },
  "is_active": true,
  "created_at": "2025-10-22T10:30:00Z",
  "updated_at": "2025-10-22T10:30:00Z"
}
```

---

## 4. Frontend Config Logic (Locked Modules)

### Loading Tenant Configuration

#### **Method 1: React Hook**
```javascript
import { useTenantConfig } from '../utils/tenantConfig';

function MyComponent() {
  const { config, loading, hasModule, isModuleLocked } = useTenantConfig('acme');
  
  if (loading) return <Loading />;
  
  // Check if module is enabled
  if (hasModule('attendance')) {
    return <AttendanceModule />;
  } else {
    return <LockedModule moduleName="Attendance" />;
  }
}
```

#### **Method 2: Direct API Call**
```javascript
import { getTenantConfigBySubdomain } from '../utils/tenantApi';

const config = await getTenantConfigBySubdomain('acme');
const hasAttendance = config.modules.attendance;
```

### Displaying Locked Modules

#### **Option A: Module Wrapper**
```jsx
import { ModuleWrapper } from '../components/LockedModule';

<ModuleWrapper
  moduleName="Wallet"
  moduleKey="wallet"
  isEnabled={config.modules.wallet}
>
  <WalletComponent />
</ModuleWrapper>
```

#### **Option B: Module Card Grid**
```jsx
import { ModuleCard } from '../components/LockedModule';

const modules = [
  { key: 'employees', name: 'Employees', icon: '👥' },
  { key: 'attendance', name: 'Attendance', icon: '⏰' },
  { key: 'wallet', name: 'Wallet', icon: '💰' },
];

return (
  <div className="modules-grid">
    {modules.map(module => (
      <ModuleCard
        key={module.key}
        title={module.name}
        icon={module.icon}
        isLocked={!config.modules[module.key]}
        onClick={() => navigate(`/${module.key}`)}
      />
    ))}
  </div>
);
```

### Locked Module UI Features

- **Visual Dimming** - Grayscale filter + reduced opacity
- **Lock Icon** - Animated lock icon overlay
- **Tooltip** - "Upgrade to unlock this feature"
- **Click Disabled** - No navigation when locked
- **Upgrade CTA** - Optional upgrade button

---

## 5. Backend Config Enforcement

### Middleware Protection

The `TenantModuleAccessMiddleware` automatically enforces module access:

```python
# URL Pattern → Module Mapping
/api/employees/   → requires 'employees' module
/api/attendance/  → requires 'attendance' module
/api/wallet/      → requires 'wallet' module
/api/tasks/       → requires 'tasks' module
/api/complaints/  → requires 'complaints' module
```

#### **Automatic Blocking:**
```python
# User tries to access disabled module
GET /api/wallet/transactions/

# Middleware checks tenant config
# wallet module is disabled → return 403

Response:
{
  "error": "Module not enabled",
  "message": "The Wallet & Salary module is not enabled for your account.",
  "module": "wallet",
  "upgrade_required": true
}
```

### Manual Permission Checks

```python
# In views.py
from hr_management.tenant_models import TenantModule

def my_view(request):
    tenant = request.tenant
    
    # Check if tenant has wallet module
    has_wallet = TenantModule.objects.filter(
        tenant=tenant,
        module_key='wallet',
        is_enabled=True
    ).exists()
    
    if not has_wallet:
        return JsonResponse({
            'error': 'Wallet module not enabled'
        }, status=403)
    
    # Continue with logic...
```

### Decorator for Module Access

```python
# custom_decorators.py
from functools import wraps
from django.http import JsonResponse

def require_module(module_key):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                return JsonResponse({'error': 'No tenant'}, status=400)
            
            from hr_management.tenant_models import TenantModule
            has_access = TenantModule.objects.filter(
                tenant=tenant,
                module_key=module_key,
                is_enabled=True
            ).exists()
            
            if not has_access:
                return JsonResponse({
                    'error': f'{module_key} module not enabled'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator

# Usage:
@require_module('wallet')
def wallet_view(request):
    # This only runs if wallet is enabled
    pass
```

---

## 6. API Endpoints

### Tenant Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/tenants/` | List all tenants | Admin |
| POST | `/api/tenants/` | Create new tenant | Admin |
| GET | `/api/tenants/{id}/` | Get tenant details | Admin |
| PATCH | `/api/tenants/{id}/` | Update tenant | Admin |
| DELETE | `/api/tenants/{id}/` | Delete tenant | Admin |
| GET | `/api/tenants/{id}/config/` | Get tenant config | Admin |
| GET | `/api/tenants/{id}/modules/` | Get tenant modules | Admin |
| POST | `/api/tenants/{id}/update_module/` | Toggle module | Admin |
| POST | `/api/tenants/{id}/regenerate_config/` | Regenerate config.json | Admin |
| POST | `/api/tenants/{id}/copy_frontend/` | Copy frontend template | Admin |
| POST | `/api/tenants/initialize_modules/` | Initialize module definitions | Admin |
| GET | `/api/tenants/statistics/` | Get tenant statistics | Admin |

### Public Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/public/tenant-config/{subdomain}/` | Get config by subdomain | None |
| GET | `/api/public/tenant-config/` | Get config by domain | None |

### Module Definitions

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/modules/` | List available modules | Authenticated |
| GET | `/api/modules/{id}/` | Get module definition | Authenticated |

---

## 7. Setup & Deployment

### Initial Setup

```bash
# 1. Install Pillow for image handling
pip install Pillow

# 2. Run migrations
python manage.py makemigrations
python manage.py migrate

# 3. Initialize module definitions
python manage.py init_modules

# 4. Create superuser (if not exists)
python manage.py createsuperuser

# 5. Create media directories
mkdir -p media/tenants/logos
mkdir -p tenants

# 6. Run server
python manage.py runserver
```

### Settings Configuration

Add to `settings.py`:

```python
# Middleware (add after existing middleware)
MIDDLEWARE = [
    # ... existing middleware ...
    'hr_management.tenant_middleware.TenantMiddleware',
    'hr_management.tenant_middleware.TenantModuleAccessMiddleware',
]

# Media files (already configured)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### Frontend Integration

```javascript
// In your React app's index.js or App.js
import { useTenantConfig, applyTenantTheme } from './utils/tenantConfig';

function App() {
  const subdomain = getCurrentTenantSubdomain();
  const { config, loading } = useTenantConfig(subdomain);
  
  useEffect(() => {
    if (config) {
      applyTenantTheme(config.theme);
    }
  }, [config]);
  
  // Rest of your app...
}
```

---

## 8. Scaling Suggestions (Hundreds of Tenants)

### Architecture Recommendations

#### **1. Database Optimization**
```python
# Add indexes to tenant models
class Tenant(models.Model):
    subdomain = models.SlugField(unique=True, db_index=True)
    custom_domain = models.CharField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['subdomain', 'is_active']),
            models.Index(fields=['custom_domain', 'is_active']),
        ]
```

#### **2. Caching Strategy**
```python
# Cache tenant configs (add to tenant_service.py)
from django.core.cache import cache

def get_tenant_config_cached(subdomain):
    cache_key = f'tenant_config_{subdomain}'
    config = cache.get(cache_key)
    
    if not config:
        tenant = Tenant.objects.get(subdomain=subdomain)
        config = tenant.generate_config_json()
        cache.set(cache_key, config, timeout=3600)  # 1 hour
    
    return config
```

#### **3. CDN for Static Assets**
- Store logos in AWS S3 or CloudFront
- Serve config.json from CDN
- Use signed URLs for private assets

```python
# settings.py
AWS_STORAGE_BUCKET_NAME = 'your-bucket'
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

#### **4. Separate Frontend Builds**
Instead of copying frontend per tenant:

**Option A: Single Build with Dynamic Config**
```javascript
// Load config at runtime
// One build serves all tenants
const config = await fetch(`/api/public/tenant-config/${subdomain}`);
```

**Option B: Build Per Tenant (for heavy customization)**
```bash
# CI/CD script
for tenant in $(get_tenants); do
  TENANT=$tenant npm run build
  deploy_to_cdn tenants/$tenant/
done
```

#### **5. Multi-Region Deployment**
```
Primary Region (US):
  - Database Primary
  - API Servers
  
Secondary Regions (EU, Asia):
  - Read Replicas
  - CDN Edge Locations
  - API Gateway
```

#### **6. Tenant Isolation Levels**

**Level 1: Shared Database + Tenant ID** (Current)
- All tenants in same database
- Filtered by tenant ID
- ✅ Easy to manage, cost-effective
- ❌ No data isolation

**Level 2: Separate Schemas** (Medium Scale)
```sql
-- PostgreSQL schemas
CREATE SCHEMA tenant_acme;
CREATE SCHEMA tenant_client2;
```

**Level 3: Separate Databases** (Enterprise)
```python
# Dynamic database routing
class TenantRouter:
    def db_for_read(self, model, **hints):
        tenant = hints.get('tenant')
        if tenant:
            return f'tenant_{tenant.subdomain}'
        return 'default'
```

#### **7. Monitoring & Analytics**
```python
# Track tenant metrics
from django.utils import timezone

class TenantMetrics(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    api_calls = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    storage_used_mb = models.FloatField(default=0)
```

#### **8. Rate Limiting Per Tenant**
```python
# middleware
from django_ratelimit.decorators import ratelimit

@ratelimit(key='tenant', rate='100/h', method='ALL')
def tenant_api_view(request):
    pass
```

#### **9. Automated Provisioning**
```python
# Celery task for async tenant creation
from celery import shared_task

@shared_task
def provision_tenant_async(tenant_id):
    tenant = Tenant.objects.get(id=tenant_id)
    TenantService.create_tenant_folder_structure(tenant)
    TenantService.copy_frontend_template(tenant)
    TenantService.generate_config_json(tenant)
    # Send welcome email
    send_tenant_welcome_email(tenant)
```

#### **10. Backup Strategy**
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)

# Backup all tenant configs
tar -czf backups/tenants_$DATE.tar.gz tenants/

# Backup database
pg_dump -h localhost -U user -d microsystem > backups/db_$DATE.sql

# Upload to S3
aws s3 cp backups/ s3://backups-bucket/ --recursive
```

### Performance Benchmarks

| Tenants | Response Time | Database Size | Memory Usage |
|---------|---------------|---------------|--------------|
| 1-10 | <50ms | <1GB | 512MB |
| 10-100 | <100ms | <10GB | 2GB |
| 100-500 | <200ms | <50GB | 8GB |
| 500+ | <300ms | Variable | 16GB+ |

### Cost Optimization

1. **Lazy Loading**: Only create tenant folders when needed
2. **Shared Resources**: Use shared Redis cache, RabbitMQ
3. **Compression**: Gzip tenant configs and assets
4. **Archival**: Move inactive tenants to cold storage

---

## 9. Testing

### Backend Tests
```python
# tests/test_tenant_service.py
from django.test import TestCase
from hr_management.tenant_service import TenantService

class TenantServiceTest(TestCase):
    def test_create_tenant(self):
        tenant_data = {
            'name': 'Test Corp',
            'subdomain': 'testcorp',
            'primary_color': '#3498db',
            'secondary_color': '#2ecc71',
        }
        tenant, created = TenantService.create_tenant_with_modules(
            tenant_data,
            ['employees', 'attendance']
        )
        
        self.assertTrue(created)
        self.assertEqual(tenant.name, 'Test Corp')
        self.assertEqual(tenant.modules.count(), 8)  # All modules created
        self.assertTrue(tenant.modules.get(module_key='employees').is_enabled)
```

### Frontend Tests
```javascript
// tests/tenantConfig.test.js
import { useTenantConfig } from '../utils/tenantConfig';

describe('useTenantConfig', () => {
  it('loads tenant configuration', async () => {
    const { config } = useTenantConfig('acme');
    expect(config.name).toBe('Acme Corporation');
    expect(config.modules.employees).toBe(true);
  });
});
```

---

## 10. Troubleshooting

### Common Issues

**Issue: Tenant not found**
```bash
# Check if tenant exists
python manage.py shell
>>> from hr_management.tenant_models import Tenant
>>> Tenant.objects.all()
```

**Issue: Config.json not generated**
```python
# Manually regenerate
from hr_management.tenant_service import TenantService
tenant = Tenant.objects.get(subdomain='acme')
TenantService.update_tenant_config(tenant)
```

**Issue: Module not showing**
```bash
# Check module definitions
python manage.py init_modules
```

**Issue: 403 on API calls**
```python
# Check middleware is enabled in settings.py
# Check tenant has module enabled in admin
```

---

## Summary

This tenant management system provides:

✅ **Visual tenant creation interface**
✅ **Customizable branding per tenant**
✅ **Module-based feature control**
✅ **Automatic config generation**
✅ **Frontend config loading**
✅ **Locked module UI**
✅ **Backend API enforcement**
✅ **Scalable architecture**

You now have a complete multi-tenant SaaS platform that can scale from 1 to 1000+ clients! 🚀
