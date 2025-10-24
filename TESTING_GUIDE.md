# 🧪 Complete Testing Guide - Your Multi-Tenant System

## 🎯 Understanding Your Setup

Your system has:
- **Backend**: Django app in `/hr_management/`
- **Main Frontend**: Next.js app in `/v0-micro-system/` (This is your working frontend!)
- **React Components**: Additional components in `/frontend/src/` (To be integrated)

---

## 🚀 Quick Start Testing (10 Minutes)

### Step 1: Start Django Backend

```bash
# From project root
cd "/home/ahmedyasser/lab/Saas/Second attempt/MicroSystem"

# Activate your virtual environment (if using one)
conda activate eurolink  # or your environment name

# Start Django server
python manage.py runserver
```

**Expected Output:**
```
System check identified some issues:
...
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

✅ **Verify**: Open http://localhost:8000/admin/ (should see Django admin login)

---

### Step 2: Test Module Definitions

```bash
# Open new terminal
cd "/home/ahmedyasser/lab/Saas/Second attempt/MicroSystem"
conda activate eurolink

# Check modules
python manage.py shell
```

```python
from hr_management.tenant_models import ModuleDefinition, Tenant, TenantModule

# Test 1: Check module definitions
modules = ModuleDefinition.objects.all()
print(f"✓ Found {modules.count()} modules")
for m in modules:
    print(f"  - {m.module_key}: {m.module_name}")

# Expected output:
# ✓ Found 8 modules
#   - employees: Employee Management
#   - attendance: Attendance Tracking
#   - wallet: Wallet & Salary
#   - tasks: Task Management
#   - complaints: Complaint System
#   - shifts: Shift Scheduling
#   - reports: Reports & Analytics
#   - notifications: Notifications

# Exit
exit()
```

✅ **Pass**: All 8 modules exist

---

### Step 3: Create Test Tenant via Django Admin

```bash
# Keep Django server running

# Open browser
http://localhost:8000/admin/

# Login with superuser credentials
# If you don't have one, create it:
python manage.py createsuperuser
# Username: admin
# Email: admin@test.com
# Password: admin123
```

**In Django Admin:**
1. Navigate to **Hr Management → Tenants**
2. Click **"Add Tenant"**
3. Fill in:
   - Name: `Test Company`
   - Subdomain: `testco`
   - Primary color: `#3498db`
   - Secondary color: `#2ecc71`
   - Contact email: `admin@testco.com`
   - Is active: ✓
4. Scroll down to **Tenant Modules** inline
5. You'll see 8 module entries, enable:
   - employees ✓
   - attendance ✓
   - notifications ✓
6. Click **"Save"**

✅ **Verify**: Check if folder created:
```bash
ls -la tenants/testco/
# Should see: config.json, public/, config/, assets/

cat tenants/testco/config.json
# Should see JSON with modules configuration
```

---

### Step 4: Test Tenant API Endpoints

```bash
# Test module definitions API
curl http://localhost:8000/api/modules/

# Expected: JSON array with 8 modules

# Test tenants list API
curl http://localhost:8000/api/tenants/

# Expected: JSON array with your test tenant
```

✅ **Pass**: API returns tenant data

---

### Step 5: Test Module Access Control

```bash
# Test with Python
python manage.py shell
```

```python
from hr_management.tenant_models import Tenant, TenantModule

# Get test tenant
tenant = Tenant.objects.get(subdomain='testco')
print(f"Tenant: {tenant.name}")

# Check enabled modules
enabled = tenant.modules.filter(is_enabled=True)
print(f"\nEnabled modules ({enabled.count()}):")
for m in enabled:
    print(f"  ✓ {m.module_key}")

# Check disabled modules
disabled = tenant.modules.filter(is_enabled=False)
print(f"\nDisabled modules ({disabled.count()}):")
for m in disabled:
    print(f"  ✗ {m.module_key}")

# Test: Enable wallet module
wallet = tenant.modules.get(module_key='wallet')
wallet.is_enabled = True
wallet.save()
print(f"\n✓ Enabled wallet module")

# Regenerate config
from hr_management.tenant_service import TenantService
TenantService.update_tenant_config(tenant)
print("✓ Config updated")

exit()
```

```bash
# Verify config updated
cat tenants/testco/config.json | grep wallet
# Should show: "wallet": true
```

✅ **Pass**: Module toggling works and updates config.json

---

## 🎨 Frontend Testing (Main Next.js App)

### Step 6: Start Next.js Frontend

```bash
# Open new terminal
cd "/home/ahmedyasser/lab/Saas/Second attempt/MicroSystem/v0-micro-system"

# Install dependencies (first time only)
npm install
# or if you prefer:
# yarn install

# Start development server
npm run dev
# or: yarn dev
```

**Expected Output:**
```
  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
  - Ready in X.Xs
```

✅ **Verify**: Open http://localhost:3000/ (should see your Next.js app)

---

### Step 7: Check What's Available in Next.js App

```bash
# List available routes
ls -la v0-micro-system/app/

# Check components
ls -la v0-micro-system/components/
```

Your Next.js app should have pages for various modules. Test navigation through the UI.

---

## 🔧 Testing the Tenant Components

Since your tenant management components (`CreateTenantPage.jsx`, `TenantListPage.jsx`) are in `/frontend/src/`, you need to integrate them into the Next.js app.

### Step 8: Integrate Tenant Pages into Next.js

**Option A: Copy Components to Next.js App**

```bash
# Create admin pages directory
mkdir -p "v0-micro-system/app/admin/create-tenant"
mkdir -p "v0-micro-system/app/admin/tenants"

# Copy utilities
mkdir -p "v0-micro-system/lib/tenant"
cp frontend/src/utils/tenantApi.js v0-micro-system/lib/tenant/
cp frontend/src/utils/tenantConfig.js v0-micro-system/lib/tenant/

# Copy components
mkdir -p "v0-micro-system/components/tenant"
cp frontend/src/components/LockedModule.jsx v0-micro-system/components/tenant/
cp frontend/src/components/LockedModule.css v0-micro-system/components/tenant/
```

**Option B: Create Quick Test Route**

Create: `v0-micro-system/app/test-tenant/page.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';

export default function TestTenantPage() {
  const [tenants, setTenants] = useState([]);
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        // Fetch tenants
        const tenantsRes = await fetch('http://localhost:8000/api/tenants/');
        const tenantsData = await tenantsRes.json();
        setTenants(tenantsData);

        // Fetch modules
        const modulesRes = await fetch('http://localhost:8000/api/modules/');
        const modulesData = await modulesRes.json();
        setModules(modulesData);

        setLoading(false);
      } catch (error) {
        console.error('Error loading data:', error);
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) return <div className="p-8">Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Tenant System Test</h1>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Module Definitions ({modules.length})</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {modules.map((module: any) => (
            <div 
              key={module.id} 
              className="border rounded-lg p-4 hover:shadow-lg transition"
            >
              <div className="text-2xl mb-2">{getModuleIcon(module.icon)}</div>
              <h3 className="font-semibold">{module.module_name}</h3>
              <p className="text-sm text-gray-600">{module.description}</p>
              {module.is_core && (
                <span className="inline-block mt-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                  CORE
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-semibold mb-4">Tenants ({tenants.length})</h2>
        <div className="grid gap-4">
          {tenants.map((tenant: any) => (
            <div 
              key={tenant.id} 
              className="border rounded-lg p-6 hover:shadow-lg transition"
            >
              <div className="flex items-center gap-4">
                {tenant.logo && (
                  <img 
                    src={`http://localhost:8000${tenant.logo}`} 
                    alt={tenant.name}
                    className="w-16 h-16 object-contain"
                  />
                )}
                <div className="flex-1">
                  <h3 className="text-xl font-semibold">{tenant.name}</h3>
                  <p className="text-gray-600">{tenant.subdomain}.myapp.com</p>
                  <p className="text-sm text-gray-500">
                    Active modules: {tenant.active_modules_count || 0}
                  </p>
                </div>
                <div className="flex gap-2">
                  <div 
                    className="w-8 h-8 rounded-full"
                    style={{ backgroundColor: tenant.primary_color }}
                    title="Primary color"
                  />
                  <div 
                    className="w-8 h-8 rounded-full"
                    style={{ backgroundColor: tenant.secondary_color }}
                    title="Secondary color"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function getModuleIcon(iconName: string) {
  const icons: Record<string, string> = {
    'users': '👥',
    'clock': '⏰',
    'wallet': '💰',
    'clipboard-list': '📋',
    'message-square': '💬',
    'calendar': '📅',
    'bar-chart': '📊',
    'bell': '🔔',
  };
  return icons[iconName] || '📦';
}
```

**Test it:**
```
http://localhost:3000/test-tenant
```

✅ **Pass**: Should display all modules and tenants

---

## 📊 Complete Testing Checklist

### Backend Tests ✅

```bash
# Run these commands one by one

# Test 1: Database
python manage.py shell -c "from hr_management.tenant_models import Tenant; print(f'Tenants: {Tenant.objects.count()}')"

# Test 2: Modules
python manage.py shell -c "from hr_management.tenant_models import ModuleDefinition; print(f'Modules: {ModuleDefinition.objects.count()}')"

# Test 3: API
curl -s http://localhost:8000/api/modules/ | python -m json.tool | head -20

# Test 4: Tenant folders
ls -la tenants/

# Test 5: Config files
find tenants/ -name "config.json" -exec echo {} \; -exec cat {} \;
```

### Manual Testing Checklist

Print and check off:

```
Backend API Tests:
[ ] GET /api/modules/ returns 8 modules
[ ] GET /api/tenants/ returns tenant list
[ ] Tenant created via Django admin works
[ ] Tenant folder created in /tenants/{subdomain}/
[ ] config.json generated correctly
[ ] Module enable/disable updates config.json

Frontend Tests (v0-micro-system):
[ ] npm run dev starts successfully
[ ] Home page loads at http://localhost:3000
[ ] Test page shows modules and tenants
[ ] Can navigate through app pages
[ ] No console errors in browser

File System Tests:
[ ] tenants/ directory exists
[ ] media/tenants/logos/ directory exists
[ ] Tenant folders have correct structure:
    [ ] config.json
    [ ] public/
    [ ] config/
    [ ] assets/

Django Admin Tests:
[ ] Can login to /admin/
[ ] Can see Tenants section
[ ] Can create new tenant
[ ] Can edit tenant
[ ] Can enable/disable modules inline
[ ] Can delete tenant

Integration Tests:
[ ] Creating tenant via admin triggers folder creation
[ ] Updating tenant updates config.json
[ ] Enabling module updates config immediately
[ ] Logo upload saves to correct location
```

---

## 🐛 Troubleshooting

### Issue: "npm start" doesn't work in /frontend/

**Solution**: Your main frontend is in `/v0-micro-system/`, not `/frontend/`

```bash
# Use this instead:
cd v0-micro-system
npm run dev
```

### Issue: "Module definitions not found"

```bash
python manage.py init_modules
```

### Issue: "Permission denied" when creating tenant folder

```bash
# Fix permissions
sudo chmod 755 tenants/
sudo chown -R $USER:$USER tenants/
```

### Issue: "CORS errors" in browser console

Add to `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

### Issue: Can't access API from Next.js

Create `.env.local` in v0-micro-system:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🎯 Quick Test Script

Save this as `quick_test.sh`:

```bash
#!/bin/bash

echo "🧪 Quick Tenant System Test"
echo ""

# Check if Django is running
curl -s http://localhost:8000/api/modules/ > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Django API is running"
else
    echo "❌ Django API is NOT running"
    echo "   Run: python manage.py runserver"
fi

# Check if Next.js is running
curl -s http://localhost:3000/ > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Next.js frontend is running"
else
    echo "❌ Next.js is NOT running"
    echo "   Run: cd v0-micro-system && npm run dev"
fi

# Check tenant folders
if [ -d "tenants" ]; then
    TENANT_COUNT=$(ls -1 tenants/ 2>/dev/null | wc -l)
    echo "✅ Tenants directory exists ($TENANT_COUNT tenants)"
else
    echo "❌ Tenants directory missing"
    echo "   Run: mkdir -p tenants"
fi

# Check modules
MODULE_COUNT=$(python manage.py shell -c "from hr_management.tenant_models import ModuleDefinition; print(ModuleDefinition.objects.count())" 2>/dev/null)
if [ "$MODULE_COUNT" = "8" ]; then
    echo "✅ All 8 modules initialized"
else
    echo "⚠️  Only $MODULE_COUNT modules found (expected 8)"
    echo "   Run: python manage.py init_modules"
fi

echo ""
echo "Test URLs:"
echo "  Backend Admin: http://localhost:8000/admin/"
echo "  API Modules:   http://localhost:8000/api/modules/"
echo "  API Tenants:   http://localhost:8000/api/tenants/"
echo "  Frontend:      http://localhost:3000/"
echo "  Test Page:     http://localhost:3000/test-tenant"
```

```bash
chmod +x quick_test.sh
./quick_test.sh
```

---

## ✅ Success Criteria

Your system is working correctly when:

1. ✅ Django server runs without errors
2. ✅ `/api/modules/` returns 8 modules
3. ✅ `/api/tenants/` returns tenant list
4. ✅ Can create tenant via Django admin
5. ✅ Tenant folder automatically created
6. ✅ `config.json` generated correctly
7. ✅ Next.js app runs at port 3000
8. ✅ Test page shows modules and tenants
9. ✅ Module enable/disable updates config
10. ✅ No errors in terminal or browser console

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. **Integrate Tenant Pages**: Copy `CreateTenantPage.jsx` and `TenantListPage.jsx` into Next.js app
2. **Add Routing**: Set up `/admin/create-tenant` and `/admin/tenants` routes
3. **Enable Template Copying**: Uncomment `copy_v0_frontend_template()` in `tenant_service.py`
4. **Configure Subdomain Routing**: Set up Nginx/Caddy for subdomain access
5. **Add Caching**: Implement Redis caching for performance

Refer to `QUICK_IMPLEMENTATION_ROADMAP.md` for detailed implementation steps.

---

**You're now ready to test! Start with the Quick Start section above.** 🎉
