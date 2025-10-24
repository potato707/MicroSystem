# Multi-Tenant SaaS System Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          ADMIN INTERFACE                            │
│  ┌──────────────────┐         ┌──────────────────┐                 │
│  │ Create Tenant    │         │  Tenant List     │                 │
│  │  Page (React)    │────────▶│  Page (React)    │                 │
│  │                  │         │                  │                 │
│  │ - Form Inputs    │         │ - Grid View      │                 │
│  │ - Logo Upload    │         │ - Statistics     │                 │
│  │ - Color Picker   │         │ - Module Manager │                 │
│  │ - Module Select  │         │ - Edit/Delete    │                 │
│  └────────┬─────────┘         └────────┬─────────┘                 │
│           │                            │                            │
└───────────┼────────────────────────────┼────────────────────────────┘
            │                            │
            │   ┌────────────────────────┘
            │   │
            ▼   ▼
   ┌────────────────────────────────────────┐
   │      DJANGO REST API (Backend)         │
   │                                        │
   │  ┌──────────────────────────────────┐ │
   │  │   Tenant Management API          │ │
   │  │   /api/tenants/                  │ │
   │  │                                  │ │
   │  │  - POST   Create Tenant          │ │
   │  │  - GET    List Tenants           │ │
   │  │  - PATCH  Update Tenant          │ │
   │  │  - DELETE Delete Tenant          │ │
   │  │  - POST   Toggle Module          │ │
   │  └──────────┬───────────────────────┘ │
   │             │                          │
   │  ┌──────────▼───────────────────────┐ │
   │  │   TenantService (Business Logic) │ │
   │  │                                  │ │
   │  │  - create_tenant_with_modules()  │ │
   │  │  - generate_config_json()        │ │
   │  │  - create_folder_structure()     │ │
   │  │  - copy_frontend_template()      │ │
   │  │  - update_tenant_config()        │ │
   │  └──────────┬───────────────────────┘ │
   │             │                          │
   │  ┌──────────▼───────────────────────┐ │
   │  │   Database Models                │ │
   │  │                                  │ │
   │  │  - Tenant                        │ │
   │  │  - TenantModule                  │ │
   │  │  - ModuleDefinition              │ │
   │  └──────────┬───────────────────────┘ │
   └─────────────┼──────────────────────────┘
                 │
    ┌────────────┴─────────────┐
    │                          │
    ▼                          ▼
┌─────────┐            ┌──────────────┐
│Database │            │ File System  │
│         │            │              │
│ Tenant  │            │ /tenants/    │
│ Records │            │  └─client1/  │
│         │            │    config.json│
│ Module  │            │              │
│ Settings│            │ /media/      │
└─────────┘            │  └─tenants/  │
                       │    └─logos/  │
                       └──────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    MIDDLEWARE LAYER (Security)                      │
│                                                                     │
│  ┌──────────────────────┐        ┌──────────────────────────┐     │
│  │ TenantMiddleware     │        │ ModuleAccessMiddleware   │     │
│  │                      │        │                          │     │
│  │ - Detect subdomain   │───────▶│ - Check module access    │     │
│  │ - Load tenant        │        │ - Block disabled modules │     │
│  │ - Attach to request  │        │ - Return 403 if blocked  │     │
│  └──────────────────────┘        └──────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    CLIENT FRONTEND (Per Tenant)                     │
│                                                                     │
│  Client visits: clientname.myapp.com                               │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Frontend Application (React)                                 │ │
│  │                                                               │ │
│  │  1. useTenantConfig('clientname')  ──────────┐              │ │
│  │                                               │              │ │
│  │  2. Load config.json ◀────────────────────────┘              │ │
│  │     GET /api/public/tenant-config/clientname/               │ │
│  │                                                               │ │
│  │  3. Apply theme colors                                       │ │
│  │     applyTenantTheme(config.theme)                           │ │
│  │                                                               │ │
│  │  4. Check module access                                      │ │
│  │     hasModule('attendance') → true/false                     │ │
│  │                                                               │ │
│  │  ┌────────────────────────────────────────────┐             │ │
│  │  │  Dashboard                                  │             │ │
│  │  │                                            │             │ │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐│             │ │
│  │  │  │ ✅       │  │ ✅       │  │ 🔒       ││             │ │
│  │  │  │Employees │  │Attendance│  │  Wallet  ││             │ │
│  │  │  │(Enabled) │  │(Enabled) │  │(Locked)  ││             │ │
│  │  │  └──────────┘  └──────────┘  └──────────┘│             │ │
│  │  │                                            │             │ │
│  │  └────────────────────────────────────────────┘             │ │
│  │                                                               │ │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Tenant Creation Flow

```
┌─────────┐
│  Admin  │
└────┬────┘
     │ 1. Fill form on /create-tenant
     │    (name, subdomain, modules, colors, logo)
     │
     ▼
┌─────────────────┐
│  React Frontend │
└────┬────────────┘
     │ 2. POST /api/tenants/
     │    FormData with all fields
     │
     ▼
┌─────────────────────┐
│  Django API View    │
│  (tenant_views.py)  │
└────┬────────────────┘
     │ 3. Validate & Serialize
     │
     ▼
┌──────────────────────┐
│   TenantService      │
│                      │
│  ┌────────────────┐  │
│  │ Create Tenant  │  │
│  │ Record in DB   │  │
│  └────────┬───────┘  │
│           │          │
│  ┌────────▼───────┐  │
│  │ Create Modules │  │
│  │ (8 records)    │  │
│  └────────┬───────┘  │
│           │          │
│  ┌────────▼───────┐  │
│  │ Create Folder  │  │
│  │ /tenants/xxx/  │  │
│  └────────┬───────┘  │
│           │          │
│  ┌────────▼───────┐  │
│  │ Generate JSON  │  │
│  │ config.json    │  │
│  └────────┬───────┘  │
│           │          │
└───────────┼──────────┘
            │
     ┌──────┴──────┐
     │             │
     ▼             ▼
┌─────────┐   ┌─────────┐
│Database │   │  Files  │
│         │   │         │
│Tenant   │   │config   │
│Modules  │   │.json    │
└─────────┘   └─────────┘
```

### 2. Client Access Flow

```
┌──────────────┐
│   Client     │
│   Browser    │
└──────┬───────┘
       │ 1. Visit: clientname.myapp.com
       │
       ▼
┌──────────────────┐
│   DNS / Web      │
│   Server         │
└──────┬───────────┘
       │ 2. Route to app
       │
       ▼
┌──────────────────────┐
│  TenantMiddleware    │
│                      │
│  - Extract subdomain │
│  - Find tenant in DB │
│  - Attach to request │
└──────┬───────────────┘
       │ 3. request.tenant = Tenant(clientname)
       │
       ▼
┌──────────────────────────┐
│   Frontend Loads         │
│                          │
│   GET /api/public/       │
│       tenant-config/     │
│       clientname/        │
└──────┬───────────────────┘
       │ 4. Returns config.json
       │
       ▼
┌──────────────────────────┐
│   React App              │
│                          │
│   config = {             │
│     modules: {           │
│       employees: true,   │
│       wallet: false      │
│     },                   │
│     theme: {...}         │
│   }                      │
└──────┬───────────────────┘
       │ 5. Apply theme & render
       │
       ▼
┌──────────────────────────┐
│   UI Rendered            │
│                          │
│   ✅ Employees (visible) │
│   🔒 Wallet (locked)     │
└──────────────────────────┘
```

### 3. API Access Control Flow

```
┌──────────────┐
│   Client     │
│   Frontend   │
└──────┬───────┘
       │ 1. API Call: GET /api/wallet/transactions
       │
       ▼
┌────────────────────────────────┐
│  ModuleAccessMiddleware        │
│                                │
│  1. Check URL: /api/wallet/    │
│  2. Required module: 'wallet'  │
│  3. Check tenant.modules       │
└────────┬───────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────┐   ┌─────────┐
│ YES │   │   NO    │
│     │   │         │
│Allow│   │Block    │
└──┬──┘   └────┬────┘
   │           │
   │           ▼
   │      ┌────────────────────┐
   │      │ Return 403         │
   │      │ {                  │
   │      │   error: "Module   │
   │      │     not enabled",  │
   │      │   upgrade: true    │
   │      │ }                  │
   │      └────────────────────┘
   │
   ▼
┌──────────────┐
│ Continue to  │
│ View Handler │
│              │
│ Return Data  │
└──────────────┘
```

---

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                      ADMIN DASHBOARD                           │
│                                                                │
│  ┌─────────────────────┐        ┌──────────────────────┐     │
│  │  CreateTenantPage   │        │   TenantListPage     │     │
│  │                     │        │                      │     │
│  │  Uses:              │        │  Uses:               │     │
│  │  - tenantApi.js     │───────▶│  - tenantApi.js      │     │
│  │  - FormData         │        │  - Statistics        │     │
│  │  - Validation       │        │  - Modal             │     │
│  └─────────────────────┘        └──────────────────────┘     │
└────────────────────────────────────────────────────────────────┘
                         │
                         │ API Calls
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                     BACKEND API LAYER                          │
│                                                                │
│  ┌──────────────────┐      ┌─────────────────────────────┐   │
│  │ tenant_views.py  │      │   tenant_serializers.py     │   │
│  │                  │      │                             │   │
│  │ - TenantViewSet  │◀─────│ - TenantCreateSerializer    │   │
│  │ - Endpoints      │      │ - TenantDetailSerializer    │   │
│  │ - Permissions    │      │ - TenantModuleSerializer    │   │
│  └────────┬─────────┘      └─────────────────────────────┘   │
│           │                                                    │
│           ▼                                                    │
│  ┌─────────────────────┐                                      │
│  │ tenant_service.py   │                                      │
│  │                     │                                      │
│  │ - Business Logic    │                                      │
│  │ - File Operations   │                                      │
│  │ - Config Generation │                                      │
│  └────────┬────────────┘                                      │
│           │                                                    │
│           ▼                                                    │
│  ┌─────────────────────┐                                      │
│  │ tenant_models.py    │                                      │
│  │                     │                                      │
│  │ - Tenant            │                                      │
│  │ - TenantModule      │                                      │
│  │ - ModuleDefinition  │                                      │
│  └─────────────────────┘                                      │
└────────────────────────────────────────────────────────────────┘
                         │
                         │ Queries
                         │
                         ▼
┌────────────────────────────────────────────────────────────────┐
│                     DATA LAYER                                 │
│                                                                │
│  ┌──────────────┐              ┌─────────────────┐           │
│  │  PostgreSQL  │              │  File System    │           │
│  │              │              │                 │           │
│  │  - tenants   │              │  /tenants/      │           │
│  │  - modules   │              │  /media/        │           │
│  └──────────────┘              └─────────────────┘           │
└────────────────────────────────────────────────────────────────┘
```

---

## Module System Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  MODULE DEFINITION LAYER                      │
│                      (Global)                                 │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ModuleDefinition Table                               │   │
│  │                                                       │   │
│  │  ┌─────────────┬────────────────┬──────┬──────────┐ │   │
│  │  │ Module Key  │ Name           │ Core │ Order    │ │   │
│  │  ├─────────────┼────────────────┼──────┼──────────┤ │   │
│  │  │ employees   │ Employees      │ ✓    │ 1        │ │   │
│  │  │ attendance  │ Attendance     │ ✗    │ 2        │ │   │
│  │  │ wallet      │ Wallet         │ ✗    │ 3        │ │   │
│  │  │ tasks       │ Tasks          │ ✗    │ 4        │ │   │
│  │  │ complaints  │ Complaints     │ ✗    │ 5        │ │   │
│  │  │ shifts      │ Shifts         │ ✗    │ 6        │ │   │
│  │  │ reports     │ Reports        │ ✗    │ 7        │ │   │
│  │  │ notifications│ Notifications │ ✓    │ 8        │ │   │
│  │  └─────────────┴────────────────┴──────┴──────────┘ │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
                              │
                              │ Instances created for each tenant
                              │
                              ▼
┌───────────────────────────────────────────────────────────────┐
│                TENANT MODULE LAYER                            │
│                  (Per Tenant)                                 │
│                                                               │
│  Tenant: "Acme Corp"                                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  TenantModule Table                                   │   │
│  │                                                       │   │
│  │  ┌─────────────┬──────────┬──────────────┐          │   │
│  │  │ Module Key  │ Enabled  │ Last Changed │          │   │
│  │  ├─────────────┼──────────┼──────────────┤          │   │
│  │  │ employees   │ ✓        │ 2025-10-22   │  Core   │   │
│  │  │ attendance  │ ✓        │ 2025-10-22   │         │   │
│  │  │ wallet      │ ✗        │ 2025-10-22   │  🔒     │   │
│  │  │ tasks       │ ✓        │ 2025-10-22   │         │   │
│  │  │ complaints  │ ✗        │ 2025-10-22   │  🔒     │   │
│  │  │ shifts      │ ✗        │ 2025-10-22   │  🔒     │   │
│  │  │ reports     │ ✗        │ 2025-10-22   │  🔒     │   │
│  │  │ notifications│ ✓       │ 2025-10-22   │  Core   │   │
│  │  └─────────────┴──────────┴──────────────┘          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  Tenant: "Beta Inc"                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Different module configuration...                    │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## Frontend State Management

```
┌────────────────────────────────────────────────────────┐
│              useTenantConfig Hook                      │
│                                                        │
│  Input: subdomain ("acme")                            │
│                                                        │
│  ┌──────────────────────────────────────────────┐    │
│  │  1. Fetch Config                              │    │
│  │     GET /api/public/tenant-config/acme/       │    │
│  └────────────┬─────────────────────────────────┘    │
│               │                                        │
│  ┌────────────▼─────────────────────────────────┐    │
│  │  2. Parse Response                            │    │
│  │     {                                         │    │
│  │       name: "Acme Corp",                      │    │
│  │       modules: { ... },                       │    │
│  │       theme: { ... }                          │    │
│  │     }                                         │    │
│  └────────────┬─────────────────────────────────┘    │
│               │                                        │
│  ┌────────────▼─────────────────────────────────┐    │
│  │  3. Store in State                            │    │
│  │     const [config, setConfig] = useState(null)│    │
│  └────────────┬─────────────────────────────────┘    │
│               │                                        │
│  ┌────────────▼─────────────────────────────────┐    │
│  │  4. Return Methods                            │    │
│  │     - config                                  │    │
│  │     - loading                                 │    │
│  │     - hasModule(key)                          │    │
│  │     - isModuleLocked(key)                     │    │
│  └───────────────────────────────────────────────┘    │
│                                                        │
│  Usage in Components:                                 │
│  ────────────────────                                 │
│  const { config, hasModule } = useTenantConfig('acme')│
│  if (hasModule('wallet')) { /* show wallet */ }      │
└────────────────────────────────────────────────────────┘
```

---

## Security & Permission Model

```
┌────────────────────────────────────────────────────────────┐
│                    PERMISSION LAYERS                       │
└────────────────────────────────────────────────────────────┘

Layer 1: User Authentication
─────────────────────────────
    ┌──────────────┐
    │   JWT Token  │
    │   Required   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────────┐
    │  IsAuthenticated │
    │   Permission     │
    └──────────────────┘

Layer 2: Admin Authorization
─────────────────────────────
    ┌──────────────────┐
    │  IsAdminUser     │
    │  Permission      │
    └──────┬───────────┘
           │
           ▼
    ┌──────────────────────────┐
    │  Tenant Management API   │
    │  (Create, Edit, Delete)  │
    └──────────────────────────┘

Layer 3: Tenant Identification
───────────────────────────────
    ┌──────────────────────┐
    │  TenantMiddleware    │
    │  - Extract subdomain │
    │  - Load tenant       │
    └──────┬───────────────┘
           │
           ▼
    ┌─────────────────────┐
    │  request.tenant     │
    └─────────────────────┘

Layer 4: Module Access Control
───────────────────────────────
    ┌────────────────────────────┐
    │  ModuleAccessMiddleware    │
    │  - Check module enabled    │
    │  - Block if disabled       │
    └──────┬─────────────────────┘
           │
      ┌────┴────┐
      │         │
      ▼         ▼
  ┌─────┐   ┌────────┐
  │Allow│   │Block   │
  │ ✓   │   │403 ✗   │
  └─────┘   └────────┘

Layer 5: Data Isolation
────────────────────────
    ┌──────────────────────────┐
    │  All queries filtered by │
    │  tenant_id               │
    └──────────────────────────┘
```

---

## Deployment Architecture (Production)

```
┌──────────────────────────────────────────────────────────────┐
│                         INTERNET                             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  CloudFlare  │
                  │  CDN / DNS   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Load Balancer│
                  │  (Nginx)     │
                  └──────┬───────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │ Django  │     │ Django  │     │ Django  │
   │ Server 1│     │ Server 2│     │ Server 3│
   └────┬────┘     └────┬────┘     └────┬────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
           ┌────────────┼────────────┐
           │            │            │
           ▼            ▼            ▼
    ┌──────────┐  ┌─────────┐  ┌─────────┐
    │PostgreSQL│  │  Redis  │  │   S3    │
    │ Database │  │  Cache  │  │ Storage │
    └──────────┘  └─────────┘  └─────────┘
         │
         ▼
    ┌──────────┐
    │  Backup  │
    │  System  │
    └──────────┘
```

---

## Scaling Roadmap

```
Stage 1: Single Server (1-10 tenants)
──────────────────────────────────────
    Django + PostgreSQL + Files
    Simple, cost-effective
    
    ┌─────────────┐
    │   Server    │
    │ ┌─────────┐ │
    │ │ Django  │ │
    │ ├─────────┤ │
    │ │PostgreSQL│ │
    │ ├─────────┤ │
    │ │  Files  │ │
    │ └─────────┘ │
    └─────────────┘

Stage 2: Separate Database (10-100 tenants)
────────────────────────────────────────────
    Add caching, separate DB
    
    ┌──────────┐     ┌──────────┐
    │  Django  │────▶│PostgreSQL│
    │  Server  │     └──────────┘
    └────┬─────┘
         │
         ▼
    ┌─────────┐
    │  Redis  │
    └─────────┘

Stage 3: Load Balanced (100-500 tenants)
─────────────────────────────────────────
    Multiple servers, CDN
    
                  ┌──────────┐
                  │   Load   │
                  │ Balancer │
                  └─────┬────┘
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      ┌────────┐  ┌────────┐  ┌────────┐
      │Django 1│  │Django 2│  │Django 3│
      └────────┘  └────────┘  └────────┘
           │            │            │
           └────────────┼────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
     ┌─────────┐  ┌────────┐  ┌──────┐
     │PostgreSQL│  │ Redis  │  │  S3  │
     └─────────┘  └────────┘  └──────┘

Stage 4: Microservices (500+ tenants)
──────────────────────────────────────
    Separate services, multi-region
    
    ┌───────────────────────────────────┐
    │         API Gateway               │
    └───────┬───────────────────────────┘
            │
    ┌───────┼───────────────────────────┐
    │       │                           │
    ▼       ▼                           ▼
┌────────┐ ┌────────┐         ┌─────────────┐
│Tenant  │ │Module  │  ...    │ Analytics   │
│Service │ │Service │         │ Service     │
└────────┘ └────────┘         └─────────────┘
```

---

## Summary

This architecture provides:

✅ **Scalable multi-tenant system**
✅ **Modular feature control**
✅ **Secure access enforcement**
✅ **Flexible deployment options**
✅ **Clear component separation**
✅ **Production-ready design**

Ready to scale from 1 to 1000+ tenants! 🚀
