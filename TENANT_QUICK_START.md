# Tenant Management System - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Run Migrations

```bash
cd /path/to/MicroSystem

# Create migrations for tenant models
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Step 2: Initialize Module Definitions

```bash
# This creates the default module definitions (Employees, Attendance, Wallet, etc.)
python manage.py init_modules
```

Expected output:
```
Initializing module definitions...
Successfully initialized 8 module definitions
```

### Step 3: Create Required Directories

```bash
# Create media directories for tenant logos
mkdir -p media/tenants/logos

# Create tenants root directory
mkdir -p tenants
```

### Step 4: Start the Django Server

```bash
python manage.py runserver
```

Server will start at `http://localhost:8000`

### Step 5: Access Admin Interface

1. Open `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Navigate to **Tenants** section
4. You'll see:
   - Tenants
   - Tenant Modules
   - Module Definitions

### Step 6: Test API Endpoints

#### Get Module Definitions
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/modules/
```

#### Create a Tenant (via API)
```bash
curl -X POST http://localhost:8000/api/tenants/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Company",
    "subdomain": "demo",
    "primary_color": "#3498db",
    "secondary_color": "#2ecc71",
    "contact_email": "admin@demo.com",
    "module_keys": ["employees", "attendance", "tasks"]
  }'
```

#### Get All Tenants
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/tenants/
```

### Step 7: Frontend Setup

#### Create Tenant via UI (React)

1. Start your React frontend:
```bash
cd frontend
npm install
npm start
```

2. Navigate to `/create-tenant` page

3. Fill in the form:
   - **Client Name**: "Test Company"
   - **Subdomain**: "testco"
   - **Select Modules**: Check the features you want
   - **Choose Colors**: Pick primary and secondary colors
   - **Upload Logo**: (optional)

4. Click **"Generate Tenant"**

5. ✅ Success! Tenant created with:
   - Database records
   - Config.json file
   - Tenant folder structure

### Step 8: View Tenants List

Navigate to `/tenants` to see all created tenants with:
- Tenant name and subdomain
- Active modules count
- Logo and brand colors
- Actions (Edit, Manage Modules, Delete)

---

## 📁 What Gets Created?

After creating a tenant called "demo":

### Database:
```
✅ Tenant record: Demo Company
✅ 8 TenantModule records (one for each feature)
✅ Logo stored in media/tenants/logos/
```

### File System:
```
tenants/
└── demo/
    ├── config.json          # Tenant configuration
    ├── public/
    │   └── images/
    ├── config/
    └── assets/
```

### Config.json:
```json
{
  "name": "Demo Company",
  "domain": "demo.myapp.com",
  "subdomain": "demo",
  "modules": {
    "employees": true,
    "attendance": true,
    "wallet": false,
    "tasks": true,
    "complaints": false,
    "shifts": false,
    "reports": false,
    "notifications": true
  },
  "theme": {
    "primary": "#3498db",
    "secondary": "#2ecc71"
  },
  "logo_url": "/media/tenants/logos/demo.png",
  "is_active": true
}
```

---

## 🎨 Frontend Usage Examples

### Example 1: Load Tenant Config
```javascript
import { useTenantConfig } from './utils/tenantConfig';

function Dashboard() {
  const { config, loading, hasModule } = useTenantConfig('demo');
  
  if (loading) return <Loading />;
  
  return (
    <div>
      <h1>Welcome to {config.name}</h1>
      
      {hasModule('attendance') && (
        <AttendanceWidget />
      )}
      
      {hasModule('wallet') ? (
        <WalletWidget />
      ) : (
        <LockedModule moduleName="Wallet" />
      )}
    </div>
  );
}
```

### Example 2: Show Module Grid
```javascript
import { ModuleCard } from './components/LockedModule';

function ModulesGrid({ config }) {
  const modules = [
    { key: 'employees', name: 'Employees', icon: '👥' },
    { key: 'attendance', name: 'Attendance', icon: '⏰' },
    { key: 'wallet', name: 'Wallet', icon: '💰' },
    { key: 'tasks', name: 'Tasks', icon: '📋' },
  ];
  
  return (
    <div className="grid">
      {modules.map(module => (
        <ModuleCard
          key={module.key}
          title={module.name}
          icon={module.icon}
          isLocked={!config.modules[module.key]}
          href={`/${module.key}`}
        />
      ))}
    </div>
  );
}
```

### Example 3: Apply Tenant Theme
```javascript
import { applyTenantTheme } from './utils/tenantConfig';

useEffect(() => {
  if (config) {
    // Applies CSS variables for primary and secondary colors
    applyTenantTheme(config.theme);
  }
}, [config]);

// Now you can use in CSS:
// background-color: var(--tenant-primary-color);
// color: var(--tenant-secondary-color);
```

---

## 🔒 Module Access Enforcement

### Automatic Backend Protection

Middleware automatically blocks access:

```
✅ GET /api/employees/       → Allowed (employees enabled)
✅ GET /api/attendance/      → Allowed (attendance enabled)
❌ GET /api/wallet/          → 403 Forbidden (wallet disabled)
```

Response for disabled module:
```json
{
  "error": "Module not enabled",
  "message": "The Wallet & Salary module is not enabled for your account.",
  "module": "wallet",
  "upgrade_required": true
}
```

### Manual Check in Views
```python
from hr_management.tenant_models import TenantModule

def my_view(request):
    tenant = request.tenant
    
    # Check access
    has_access = TenantModule.objects.filter(
        tenant=tenant,
        module_key='wallet',
        is_enabled=True
    ).exists()
    
    if not has_access:
        return JsonResponse({'error': 'Access denied'}, status=403)
```

---

## 🛠 Common Tasks

### Enable/Disable Module for Tenant

#### Via Admin:
1. Go to Django Admin → Tenant Modules
2. Find the tenant and module
3. Toggle "Is Enabled" checkbox
4. Save

#### Via API:
```bash
curl -X POST http://localhost:8000/api/tenants/TENANT_ID/update_module/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_key": "wallet",
    "is_enabled": true
  }'
```

#### Via UI:
1. Go to Tenant List page
2. Click "Modules" button on tenant card
3. Toggle switches for each module
4. Changes save automatically

### Update Tenant Branding

```bash
curl -X PATCH http://localhost:8000/api/tenants/TENANT_ID/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "primary_color=#e74c3c" \
  -F "secondary_color=#3498db" \
  -F "logo=@new_logo.png"
```

Config.json will automatically regenerate!

### Get Tenant Statistics

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/tenants/statistics/
```

Response:
```json
{
  "total_tenants": 15,
  "active_tenants": 12,
  "inactive_tenants": 3,
  "module_statistics": {
    "employees": {
      "name": "Employee Management",
      "enabled_count": 15,
      "percentage": 100.0
    },
    "attendance": {
      "name": "Attendance Tracking",
      "enabled_count": 10,
      "percentage": 66.67
    }
  }
}
```

---

## 🐛 Troubleshooting

### Issue: "Module definitions not found"
```bash
# Solution:
python manage.py init_modules
```

### Issue: "Tenant config not loading"
```python
# Check if config.json exists
import os
tenant = Tenant.objects.get(subdomain='demo')
print(os.path.exists(tenant.config_path))

# Regenerate if missing
from hr_management.tenant_service import TenantService
TenantService.update_tenant_config(tenant)
```

### Issue: "403 errors on all API calls"
```python
# Check middleware is enabled in settings.py
MIDDLEWARE = [
    # ...
    'hr_management.tenant_middleware.TenantMiddleware',
    'hr_management.tenant_middleware.TenantModuleAccessMiddleware',
]
```

### Issue: "Logo not displaying"
```python
# Check media files settings
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Check URL conf includes media
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 📊 Next Steps

1. **Customize Module Definitions**: Add your own modules
2. **Add Billing Integration**: Stripe/PayPal for upgrades
3. **Email Notifications**: Send tenant creation emails
4. **Analytics Dashboard**: Track tenant usage
5. **Multi-language Support**: i18n for tenant configs

---

## 🎯 Key Files Reference

| File | Purpose |
|------|---------|
| `tenant_models.py` | Database models |
| `tenant_service.py` | Business logic |
| `tenant_views.py` | API endpoints |
| `tenant_serializers.py` | API serializers |
| `tenant_middleware.py` | Access control |
| `tenant_urls.py` | URL routing |
| `CreateTenantPage.jsx` | Create tenant UI |
| `TenantListPage.jsx` | List tenants UI |
| `LockedModule.jsx` | Locked module UI |
| `tenantApi.js` | API client |
| `tenantConfig.js` | Config loader |

---

## ✅ Checklist

- [ ] Migrations applied
- [ ] Modules initialized
- [ ] Directories created
- [ ] First tenant created
- [ ] Config.json generated
- [ ] Frontend integrated
- [ ] Modules tested (enabled/disabled)
- [ ] Middleware working
- [ ] Documentation read

---

**You're all set! 🎉**

Start creating tenants and building your multi-tenant SaaS platform!
