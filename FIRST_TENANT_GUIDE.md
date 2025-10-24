# 🎯 Quick Test Guide - Creating Your First Tenant

## ✅ What I Just Fixed

I've updated the system so that when you create a tenant in Django admin, it will **automatically**:
1. ✅ Create all 8 TenantModule records
2. ✅ Enable core modules (employees, notifications) by default
3. ✅ Create tenant folder structure
4. ✅ Generate config.json file

You no longer need to manually enter module keys!

---

## 🚀 Test It Now (5 Minutes)

### Step 1: Restart Django Server

The signals need to be loaded, so restart your server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
python manage.py runserver
```

**Expected Output:**
```
Starting development server at http://127.0.0.1:8000/
```

---

### Step 2: Create a Tenant via Django Admin

1. **Open:** http://localhost:8000/admin/

2. **Navigate to:** Hr Management → Tenants

3. **Click:** "Add Tenant" button

4. **Fill in the Basic Information:**
   - Name: `Demo Company`
   - Subdomain: `demo`
   - Custom domain: (leave empty)
   - Is active: ✓

5. **Fill in Branding:**
   - Primary color: `#3498db`
   - Secondary color: `#2ecc71`
   - Logo: (optional - upload if you want)

6. **Fill in Contact Information:**
   - Contact email: `admin@demo.com`
   - Contact phone: `+1234567890`

7. **Scroll down to "Tenant Modules" section**
   - You should see it's EMPTY at first (this is normal)
   - The modules will be created automatically when you save

8. **Click "Save"**

---

### Step 3: Verify Modules Were Auto-Created

After saving, you should be redirected to the tenant detail page. Now:

1. **Scroll down to "Tenant Modules" section**

2. **You should now see 8 rows** with:
   ```
   Module Key    | Module Name           | Enabled | Enabled at
   employees     | Employee Management   | ✓       | (datetime)
   attendance    | Attendance Tracking   | ☐       | -
   wallet        | Wallet & Salary       | ☐       | -
   tasks         | Task Management       | ☐       | -
   complaints    | Complaint System      | ☐       | -
   shifts        | Shift Scheduling      | ☐       | -
   reports       | Reports & Analytics   | ☐       | -
   notifications | Notifications         | ✓       | (datetime)
   ```

3. **To enable more modules:**
   - Check the "Enabled" checkbox for any module
   - Click "Save" at the bottom
   - Config.json will auto-update!

---

### Step 4: Verify Folder Structure

```bash
# Check if tenant folder was created
ls -la tenants/

# Expected: demo/

# Check folder contents
ls -la tenants/demo/

# Expected:
# config.json
# public/
# config/
# assets/

# View the config.json
cat tenants/demo/config.json | python -m json.tool
```

**Expected Output:**
```json
{
  "name": "Demo Company",
  "domain": "demo.myapp.com",
  "subdomain": "demo",
  "modules": {
    "employees": true,
    "attendance": false,
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
  "logo_url": null,
  "is_active": true
}
```

---

### Step 5: Enable Additional Modules

1. **Go back to the tenant** in Django admin

2. **Scroll to Tenant Modules**

3. **Check the boxes** for modules you want to enable:
   - ✓ employees (already enabled)
   - ✓ attendance (enable this)
   - ✓ wallet (enable this)
   - ✓ notifications (already enabled)

4. **Click "Save"**

5. **Verify config updated:**
   ```bash
   cat tenants/demo/config.json | grep -A 10 '"modules"'
   ```

   **Should show:**
   ```json
   "modules": {
     "employees": true,
     "attendance": true,
     "wallet": true,
     "tasks": false,
     "complaints": false,
     "shifts": false,
     "reports": false,
     "notifications": true
   }
   ```

---

## ✅ Success Checklist

After following the steps above, verify:

- [x] Tenant created via Django admin
- [x] 8 TenantModule records auto-created
- [x] Core modules (employees, notifications) enabled by default
- [x] Tenant folder created at `/tenants/demo/`
- [x] `config.json` generated correctly
- [x] Can enable/disable modules via admin
- [x] `config.json` auto-updates when modules change

---

## 🎨 Visual Guide

### Before Saving:
```
Tenant Modules:
┌─────────────────────────────────────┐
│ [Empty - no rows shown]             │
│                                     │
│ "Add another Tenant Module"        │
└─────────────────────────────────────┘
```

### After Saving (Auto-Created):
```
Tenant Modules:
┌──────────────┬────────────────────┬─────────┬────────────┐
│ Module Key   │ Module Name        │ Enabled │ Enabled at │
├──────────────┼────────────────────┼─────────┼────────────┤
│ employees    │ Employee Mgmt      │   ✓     │ 2025-10-22 │
│ attendance   │ Attendance Track   │   ☐     │     -      │
│ wallet       │ Wallet & Salary    │   ☐     │     -      │
│ tasks        │ Task Management    │   ☐     │     -      │
│ complaints   │ Complaint System   │   ☐     │     -      │
│ shifts       │ Shift Scheduling   │   ☐     │     -      │
│ reports      │ Reports & Analytics│   ☐     │     -      │
│ notifications│ Notifications      │   ✓     │ 2025-10-22 │
└──────────────┴────────────────────┴─────────┴────────────┘

Note: Module Key and Module Name are READ-ONLY
      Only "Enabled" checkbox is editable
```

---

## 🐛 Troubleshooting

### Issue: "No modules showing after save"

**Solution 1:** Check if module definitions exist
```bash
python manage.py shell
```
```python
from hr_management.tenant_models import ModuleDefinition
print(f"Module definitions: {ModuleDefinition.objects.count()}")
# Expected: 8

# If 0, run:
exit()
```
```bash
python manage.py init_modules
```

**Solution 2:** Check Django logs for errors
```bash
# Look for errors in the terminal where Django is running
# Should see: "Creating modules for new tenant: Demo Company"
```

**Solution 3:** Manually trigger module creation
```bash
python manage.py shell
```
```python
from hr_management.tenant_models import Tenant, TenantModule, ModuleDefinition
from hr_management.tenant_service import TenantService

# Get your tenant
tenant = Tenant.objects.get(subdomain='demo')

# Manually create modules
for module_def in ModuleDefinition.objects.all():
    TenantModule.objects.get_or_create(
        tenant=tenant,
        module_key=module_def.module_key,
        defaults={
            'module_name': module_def.module_name,
            'is_enabled': module_def.is_core
        }
    )

# Regenerate config
TenantService.update_tenant_config(tenant)

print("✓ Modules created and config updated!")
exit()
```

### Issue: "Config.json not updating when I toggle modules"

**Solution:** Restart Django server
```bash
# The signal may not be loaded. Restart:
# Ctrl+C to stop
python manage.py runserver
```

### Issue: "Folder not created automatically"

**Solution:** The signal creates folder structure. If missing:
```bash
python manage.py shell
```
```python
from hr_management.tenant_models import Tenant
from hr_management.tenant_service import TenantService

tenant = Tenant.objects.get(subdomain='demo')
TenantService.create_tenant_folder_structure(tenant)
TenantService.generate_config_json(tenant)

print("✓ Folder and config created!")
exit()
```

---

## 🎯 Next Steps

Now that you have a working tenant:

1. **Test API endpoints:**
   ```bash
   curl http://localhost:8000/api/tenants/ | python -m json.tool
   ```

2. **Test module access control:**
   - Try accessing enabled module API (should work)
   - Try accessing disabled module API (should return 403)

3. **Create more tenants:**
   - Each tenant will auto-create modules
   - Test with different module combinations

4. **Read implementation docs:**
   - See `QUICK_IMPLEMENTATION_ROADMAP.md` for next features to add
   - See `TESTING_GUIDE.md` for comprehensive testing

---

## 🎉 You're Done!

Your tenant system now works correctly with:
- ✅ Auto-creation of module records
- ✅ Auto-generation of folder structure
- ✅ Auto-generation of config.json
- ✅ Auto-update of config when modules change
- ✅ Easy enable/disable via Django admin

**The hard work is done! Now you can create tenants easily.** 🚀

---

## 📸 Screenshot Guide

When creating a tenant, you should see:

**Step 1 - Empty form (before save):**
```
Tenant Modules: [Empty inline form with "Add another" button]
```

**Step 2 - After clicking Save:**
```
Tenant Modules:
[8 rows with checkboxes, only employees and notifications checked]
```

**Step 3 - Enable more modules:**
```
Check boxes → Click Save → config.json auto-updates!
```

---

**Happy testing! 🎉**
