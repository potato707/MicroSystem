# 🏗️ Multi-Tenant System Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INTERNET / DNS                              │
│                                                                       │
│  demo.myapp.com ──┐                                                  │
│  acme.myapp.com ──┼──→  Wildcard DNS (*.myapp.com → Your Server)    │
│  test.myapp.com ──┘                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      WEB SERVER (Nginx / Caddy)                      │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Subdomain Router                                             │   │
│  │  • Extracts subdomain from request                            │   │
│  │  • Routes /api/* to Django                                    │   │
│  │  • Routes /* to /tenants/<subdomain>/public/                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                    │                                │
                    │ /api/*                         │ /*
                    ↓                                ↓
     ┌──────────────────────────┐      ┌──────────────────────────┐
     │   DJANGO BACKEND         │      │   TENANT STATIC FILES    │
     │   (Port 8000)            │      │   /tenants/<subdomain>/  │
     └──────────────────────────┘      └──────────────────────────┘
```

---

## Detailed Component Architecture

### 1. Frontend Layer (React Admin)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN FRONTEND (React)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Pages:                                                           │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ CreateTenantPage     │  │ TenantListPage       │             │
│  │                      │  │                      │             │
│  │ • Form with fields   │  │ • Grid of tenants    │             │
│  │ • Logo uploader      │  │ • Edit/Delete buttons│             │
│  │ • Color pickers      │  │ • Module manager     │             │
│  │ • Module checkboxes  │  │ • Search/filter      │             │
│  │ • Progress indicator │  │ • Statistics         │             │
│  └──────────────────────┘  └──────────────────────┘             │
│                                                                   │
│  Components:                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ ModuleGrid           │  │ LockedModule         │             │
│  │                      │  │                      │             │
│  │ • Shows ALL modules  │  │ • Locked overlay     │             │
│  │ • Locked = dimmed    │  │ • Upgrade tooltip    │             │
│  │ • Click to upgrade   │  │ • Icon + description │             │
│  └──────────────────────┘  └──────────────────────┘             │
│                                                                   │
│  Utilities:                                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ tenantApi.js         │  │ tenantConfig.js      │             │
│  │                      │  │                      │             │
│  │ • API client         │  │ • Config loader      │             │
│  │ • CRUD operations    │  │ • Theme applier      │             │
│  │ • FormData handling  │  │ • hasModule() check  │             │
│  └──────────────────────┘  └──────────────────────┘             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓ HTTP/HTTPS
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                      API LAYER (Django REST)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ViewSets:                                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ TenantViewSet                                             │   │
│  │                                                           │   │
│  │ CRUD Operations:                                          │   │
│  │ • POST   /api/tenants/           Create tenant           │   │
│  │ • GET    /api/tenants/           List tenants            │   │
│  │ • GET    /api/tenants/{id}/      Get details             │   │
│  │ • PATCH  /api/tenants/{id}/      Update tenant           │   │
│  │ • DELETE /api/tenants/{id}/      Delete tenant           │   │
│  │                                                           │   │
│  │ Custom Actions:                                           │   │
│  │ • POST   /api/tenants/{id}/deploy_frontend/              │   │
│  │ • POST   /api/tenants/{id}/update_module/                │   │
│  │ • GET    /api/tenants/{id}/health/                       │   │
│  │ • POST   /api/tenants/bulk-create/                       │   │
│  │                                                           │   │
│  │ Public Endpoints:                                         │   │
│  │ • GET    /api/tenants/by-subdomain/{sub}/config/         │   │
│  │ • GET    /api/tenants/by-subdomain/{sub}/assets/*        │   │
│  │ • GET    /api/tenants/statistics/                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ModuleDefinitionViewSet                                   │   │
│  │                                                           │   │
│  │ • GET    /api/modules/           List all modules        │   │
│  │ • GET    /api/modules/{id}/      Get module details      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                   MIDDLEWARE LAYER (Access Control)              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. TenantMiddleware                                              │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ • Extract subdomain from request                     │     │
│     │ • Load tenant from database                          │     │
│     │ • Attach to request.tenant                           │     │
│     │ • Used by all downstream views                       │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                   │
│  2. TenantModuleAccessMiddleware                                  │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ • Check if requested endpoint requires module        │     │
│     │ • Verify module is enabled for tenant                │     │
│     │ • Block with 403 if disabled                         │     │
│     │ • Return upgrade message                             │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                   │
│  3. TenantConfigMiddleware                                        │
│     ┌─────────────────────────────────────────────────────┐     │
│     │ • Load tenant config from cache/file                 │     │
│     │ • Add config headers to response                     │     │
│     │ • Enable CORS for tenant domains                     │     │
│     └─────────────────────────────────────────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER (Business Logic)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  TenantService:                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                           │   │
│  │  create_tenant_with_modules(data, module_keys):          │   │
│  │  ├─ Create Tenant record                                 │   │
│  │  ├─ Create 8 TenantModule records                        │   │
│  │  ├─ Handle logo upload                                   │   │
│  │  ├─ Create folder structure                              │   │
│  │  ├─ Copy v0-micro-system template                        │   │
│  │  └─ Generate config.json                                 │   │
│  │                                                           │   │
│  │  copy_v0_frontend_template(tenant):                      │   │
│  │  ├─ Copy app/, components/, lib/, public/, etc.          │   │
│  │  ├─ Copy package.json, next.config.mjs                   │   │
│  │  ├─ Customize package.json with tenant name              │   │
│  │  └─ Generate .env.local with tenant vars                 │   │
│  │                                                           │   │
│  │  generate_config_json(tenant):                           │   │
│  │  ├─ Collect tenant data                                  │   │
│  │  ├─ Get enabled modules                                  │   │
│  │  ├─ Build JSON structure                                 │   │
│  │  └─ Write to /tenants/<subdomain>/config.json            │   │
│  │                                                           │   │
│  │  update_tenant_config(tenant):                           │   │
│  │  ├─ Regenerate config.json                               │   │
│  │  └─ Invalidate cache                                     │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER (Models)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Tenant                                                    │   │
│  │ ├─ id (PK)                                                │   │
│  │ ├─ name: "Acme Corporation"                              │   │
│  │ ├─ subdomain: "acme" (unique, indexed)                   │   │
│  │ ├─ logo: ImageField                                       │   │
│  │ ├─ primary_color: "#3498db"                              │   │
│  │ ├─ secondary_color: "#2ecc71"                            │   │
│  │ ├─ contact_email                                          │   │
│  │ ├─ is_active: Boolean (indexed)                          │   │
│  │ ├─ created_at, updated_at                                │   │
│  │ └─ created_by: ForeignKey(User)                          │   │
│  │                                                           │   │
│  │ Properties:                                               │   │
│  │ • folder_path → /tenants/acme/                           │   │
│  │ • config_path → /tenants/acme/config.json                │   │
│  │ • domain → acme.myapp.com                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ TenantModule                                              │   │
│  │ ├─ id (PK)                                                │   │
│  │ ├─ tenant: ForeignKey(Tenant)                            │   │
│  │ ├─ module_key: "employees"                               │   │
│  │ ├─ module_name: "Employee Management"                    │   │
│  │ ├─ is_enabled: Boolean                                    │   │
│  │ └─ enabled_at: DateTime                                   │   │
│  │                                                           │   │
│  │ Unique Together: (tenant, module_key)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ModuleDefinition                                          │   │
│  │ ├─ id (PK)                                                │   │
│  │ ├─ module_key: "employees" (unique)                      │   │
│  │ ├─ module_name: "Employee Management"                    │   │
│  │ ├─ description: "Manage your team"                       │   │
│  │ ├─ icon: "users"                                         │   │
│  │ ├─ is_core: Boolean                                       │   │
│  │ └─ sort_order: Integer                                    │   │
│  │                                                           │   │
│  │ 8 Default Modules:                                        │   │
│  │ • employees (core)                                        │   │
│  │ • attendance                                              │   │
│  │ • wallet                                                  │   │
│  │ • tasks                                                   │   │
│  │ • complaints                                              │   │
│  │ • shifts                                                  │   │
│  │ • reports                                                 │   │
│  │ • notifications (core)                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────┐
│                     FILE SYSTEM LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  v0-micro-system/                    ← Source Template           │
│  ├── app/                            (Next.js App Router)        │
│  │   ├── page.tsx                                                │
│  │   ├── layout.tsx                                              │
│  │   └── [routes]...                                             │
│  ├── components/                     (React Components)          │
│  │   ├── Header.tsx                                              │
│  │   ├── Sidebar.tsx                                             │
│  │   └── [modules]...                                            │
│  ├── lib/                            (Utilities)                 │
│  ├── public/                         (Static Assets)             │
│  ├── styles/                         (CSS/Tailwind)              │
│  ├── types/                          (TypeScript Types)          │
│  ├── package.json                                                │
│  ├── next.config.mjs                                             │
│  └── tsconfig.json                                               │
│                                                                   │
│  ─────────────────────────────────────────────────────────────  │
│                       COPIED TO ↓                                │
│  ─────────────────────────────────────────────────────────────  │
│                                                                   │
│  tenants/                            ← Generated Tenant Apps     │
│  │                                                               │
│  ├── demo/                           (Tenant: Demo Company)      │
│  │   ├── app/                        ← Copied from v0           │
│  │   ├── components/                 ← Copied from v0           │
│  │   ├── lib/                        ← Copied from v0           │
│  │   ├── public/                     ← Copied from v0           │
│  │   ├── styles/                     ← Copied from v0           │
│  │   ├── types/                      ← Copied from v0           │
│  │   ├── config.json                 ← Generated                │
│  │   │   {                                                       │
│  │   │     "name": "Demo Company",                              │
│  │   │     "subdomain": "demo",                                 │
│  │   │     "modules": {                                         │
│  │   │       "employees": true,                                 │
│  │   │       "attendance": true,                                │
│  │   │       "wallet": false,                                   │
│  │   │       ...                                                │
│  │   │     },                                                   │
│  │   │     "theme": {                                           │
│  │   │       "primary": "#3498db",                              │
│  │   │       "secondary": "#2ecc71"                             │
│  │   │     }                                                    │
│  │   │   }                                                      │
│  │   ├── package.json                ← Customized               │
│  │   │   {                                                      │
│  │   │     "name": "demo-app",                                  │
│  │   │     "description": "App for Demo Company"               │
│  │   │   }                                                      │
│  │   ├── .env.local                  ← Generated                │
│  │   │   NEXT_PUBLIC_TENANT_NAME=Demo Company                   │
│  │   │   NEXT_PUBLIC_SUBDOMAIN=demo                            │
│  │   │   NEXT_PUBLIC_API_URL=https://api.myapp.com             │
│  │   │   NEXT_PUBLIC_PRIMARY_COLOR=#3498db                     │
│  │   └── [node_modules/]             (Run: npm install)         │
│  │                                                               │
│  ├── acme/                           (Tenant: Acme Corp)        │
│  │   └── [same structure...]                                    │
│  │                                                               │
│  └── company3/                       (Tenant: Company 3)        │
│      └── [same structure...]                                    │
│                                                                   │
│  media/                              ← Uploaded Assets           │
│  └── tenants/                                                    │
│      └── logos/                                                  │
│          ├── demo.png                                            │
│          ├── acme.png                                            │
│          └── company3.png                                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Flow 1: Creating a New Tenant

```
Admin User
    │
    │ Visits /admin/create-tenant
    ↓
┌─────────────────────────┐
│  CreateTenantPage.jsx   │
│  • Fills form           │
│  • Uploads logo         │
│  • Selects modules      │
│  • Clicks "Generate"    │
└─────────────────────────┘
    │
    │ POST /api/tenants/
    ↓
┌─────────────────────────┐
│  TenantViewSet          │
│  • Validates data       │
│  • Calls service        │
└─────────────────────────┘
    │
    │ TenantService.create_tenant_with_modules()
    ↓
┌─────────────────────────┐     ┌─────────────────────────┐
│  Database               │     │  File System            │
│  • Create Tenant        │     │  • Create folders       │
│  • Create 8 Modules     │     │  • Copy v0-micro-system │
└─────────────────────────┘     │  • Generate config.json │
                                │  • Customize files      │
                                └─────────────────────────┘
    │
    │ Response: { id, name, subdomain, ... }
    ↓
┌─────────────────────────┐
│  Frontend               │
│  • Show success         │
│  • Redirect to list     │
└─────────────────────────┘
```

### Flow 2: Accessing a Tenant App

```
End User
    │
    │ Visits: https://demo.myapp.com
    ↓
┌─────────────────────────┐
│  Nginx / Web Server     │
│  • Extract subdomain    │
│  • Route to tenant dir  │
└─────────────────────────┘
    │
    │ Serve from: /tenants/demo/public/
    ↓
┌─────────────────────────┐
│  Tenant Next.js App     │
│  • Load config.json     │
│  • Apply theme colors   │
│  • Check modules        │
└─────────────────────────┘
    │
    │ GET /api/tenants/by-subdomain/demo/config/
    ↓
┌─────────────────────────┐
│  Django API             │
│  • Return config.json   │
└─────────────────────────┘
    │
    │ config = { name, modules, theme, ... }
    ↓
┌─────────────────────────┐
│  Frontend Dashboard     │
│  • Show enabled modules │
│  • Dim locked modules   │
│  • Apply theme          │
└─────────────────────────┘
```

### Flow 3: API Request with Module Check

```
Tenant User
    │
    │ GET /api/wallet/transactions/
    ↓
┌─────────────────────────┐
│  Nginx                  │
│  • Forward to Django    │
└─────────────────────────┘
    │
    ↓
┌─────────────────────────┐
│  TenantMiddleware       │
│  • Extract subdomain    │
│  • Load tenant          │
│  • Attach to request    │
└─────────────────────────┘
    │
    ↓
┌─────────────────────────┐
│ ModuleAccessMiddleware  │
│  • Check /api/wallet    │
│  • Query TenantModule   │
│  • is_enabled?          │
└─────────────────────────┘
    │
    ├─ YES: Module Enabled
    │   │
    │   ↓
    │  ┌─────────────────────────┐
    │  │  WalletViewSet          │
    │  │  • Process request      │
    │  │  • Return data          │
    │  └─────────────────────────┘
    │
    └─ NO: Module Disabled
        │
        ↓
       ┌─────────────────────────┐
       │  403 Response           │
       │  {                      │
       │    "error": "Module     │
       │      not enabled",      │
       │    "module": "wallet",  │
       │    "upgrade": true      │
       │  }                      │
       └─────────────────────────┘
```

### Flow 4: Enabling a Module

```
Admin User
    │
    │ Visits /admin/tenants/
    ↓
┌─────────────────────────┐
│  TenantListPage.jsx     │
│  • Click "Modules" btn  │
│  • Opens modal          │
└─────────────────────────┘
    │
    ↓
┌─────────────────────────┐
│  ModuleManagementModal  │
│  • Show 8 modules       │
│  • Toggle "Wallet" ON   │
└─────────────────────────┘
    │
    │ POST /api/tenants/5/update_module/
    │ { module_key: "wallet", is_enabled: true }
    ↓
┌─────────────────────────┐
│  TenantViewSet          │
│  • Find TenantModule    │
│  • Set is_enabled=true  │
│  • Save                 │
└─────────────────────────┘
    │
    │ TenantService.update_tenant_config()
    ↓
┌─────────────────────────┐     ┌─────────────────────────┐
│  Database               │     │  File System            │
│  • Update record        │     │  • Regenerate config    │
└─────────────────────────┘     │  • Update modules obj   │
                                └─────────────────────────┘
    │
    │ Response: { success: true }
    ↓
┌─────────────────────────┐
│  Frontend               │
│  • Update UI            │
│  • Show success         │
└─────────────────────────┘
    │
    │ Cache invalidated
    ↓
┌─────────────────────────┐
│  Tenant App             │
│  • Reload config        │
│  • Wallet now unlocked  │
└─────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       SECURITY LAYERS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Layer 1: Authentication                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • JWT tokens for API access                              │   │
│  │ • Session-based auth for Django admin                    │   │
│  │ • Token refresh mechanism                                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Layer 2: Tenant Isolation                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Subdomain extracted from request                       │   │
│  │ • Tenant loaded and attached to request                  │   │
│  │ • All queries filtered by tenant                         │   │
│  │ • No cross-tenant data access                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Layer 3: Module Access Control                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Middleware checks module status                        │   │
│  │ • 403 returned if module disabled                        │   │
│  │ • Frontend also checks (UI layer)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Layer 4: File System Isolation                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Each tenant has separate folder                        │   │
│  │ • No path traversal vulnerabilities                      │   │
│  │ • Nginx serves only tenant's own files                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Layer 5: Rate Limiting (Optional)                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ • Per-tenant API rate limits                             │   │
│  │ • Prevents abuse                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Caching Architecture (Optional)

```
┌─────────────────────────────────────────────────────────────────┐
│                      CACHING STRATEGY                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Redis Cache:                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                                                           │   │
│  │  tenant_config_demo → { config.json data }               │   │
│  │  TTL: 1 hour                                              │   │
│  │                                                           │   │
│  │  tenant_config_acme → { config.json data }               │   │
│  │  TTL: 1 hour                                              │   │
│  │                                                           │   │
│  │  tenant_list_page_1 → [tenant1, tenant2, ...]            │   │
│  │  TTL: 5 minutes                                           │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Cache Invalidation:                                              │
│  • On tenant update → Clear tenant_config_{subdomain}            │
│  • On module toggle → Clear tenant_config_{subdomain}            │
│  • On tenant create → Clear tenant_list_*                        │
│  • On tenant delete → Clear tenant_config_* and tenant_list_*    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Development (Single Server)
```
┌──────────────────────────────────────┐
│  Single Server (localhost)           │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  Django (port 8000)            │ │
│  │  • Development server          │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  React Dev Server (port 3000)  │ │
│  │  • Hot reload enabled          │ │
│  └────────────────────────────────┘ │
│                                      │
│  ┌────────────────────────────────┐ │
│  │  SQLite Database               │ │
│  │  • db.sqlite3                  │ │
│  └────────────────────────────────┘ │
│                                      │
└──────────────────────────────────────┘
```

### Production (Multi-Server)
```
┌─────────────────────────────────────────────────────────┐
│  Load Balancer (Nginx/HAProxy)                          │
│  • SSL termination                                       │
│  • Subdomain routing                                     │
└─────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┴───────────────┐
        │                                │
┌───────▼──────────┐           ┌────────▼─────────┐
│  App Server 1    │           │  App Server 2    │
│  • Django        │           │  • Django        │
│  • Gunicorn      │           │  • Gunicorn      │
└──────────────────┘           └──────────────────┘
        │                                │
        └────────────────┬───────────────┘
                         │
                ┌────────▼─────────┐
                │  PostgreSQL      │
                │  • Primary DB    │
                └──────────────────┘
                         │
                ┌────────▼─────────┐
                │  Redis Cache     │
                │  • Configs       │
                └──────────────────┘
                         │
                ┌────────▼─────────┐
                │  S3 / CDN        │
                │  • Static assets │
                │  • Tenant files  │
                └──────────────────┘
```

---

## Summary

This architecture provides:

✅ **Scalability**: Handle 1000+ tenants  
✅ **Isolation**: Each tenant completely separated  
✅ **Security**: Multiple security layers  
✅ **Performance**: Caching at multiple levels  
✅ **Maintainability**: Clean separation of concerns  
✅ **Flexibility**: Easy to add new modules  
✅ **Automation**: Zero manual deployment  

**Your current system already implements 90% of this architecture!**
