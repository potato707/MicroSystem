# 🏢 Multi-Tenant SaaS System

A complete tenant management solution for Django + React SaaS applications. Create and manage multiple client tenants with customizable branding, modular features, and isolated configurations - all through a beautiful web interface.

[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18.0-blue.svg)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ✨ Features

### 🎨 Visual Tenant Creation
- Web interface for creating new tenants
- Auto-subdomain generation
- Logo upload with preview
- Color picker for branding
- Contact information management

### 🔧 Modular Feature System
- 8 predefined modules (Employees, Attendance, Wallet, Tasks, Complaints, Shifts, Reports, Notifications)
- Enable/disable features per tenant
- Core modules always enabled
- Locked module UI for disabled features

### 🎯 Backend Protection
- Automatic API access control
- Middleware-based enforcement
- Custom 403 responses with upgrade info
- URL pattern to module mapping

### 🚀 Scalable Architecture
- Support for 1000+ tenants
- Caching strategies
- CDN integration ready
- Multi-region deployment ready

### 📊 Admin Dashboard
- List all tenants
- Real-time statistics
- Module management modal
- Edit/Delete capabilities

---

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup_tenant_system.sh

# Start the server
python manage.py runserver
```

### Option 2: Manual Setup

```bash
# 1. Install dependencies
pip install Pillow

# 2. Run migrations
python manage.py makemigrations
python manage.py migrate

# 3. Initialize modules
python manage.py init_modules

# 4. Create directories
mkdir -p media/tenants/logos
mkdir -p tenants

# 5. Create superuser
python manage.py createsuperuser

# 6. Start server
python manage.py runserver
```

---

## 📖 Documentation

| Document | Description | Lines |
|----------|-------------|-------|
| **[TENANT_QUICK_START.md](TENANT_QUICK_START.md)** | 5-minute setup guide | 400+ |
| **[TENANT_SYSTEM_COMPLETE_GUIDE.md](TENANT_SYSTEM_COMPLETE_GUIDE.md)** | Full technical documentation | 1000+ |
| **[TENANT_ARCHITECTURE.md](TENANT_ARCHITECTURE.md)** | System architecture & diagrams | 600+ |
| **[TENANT_IMPLEMENTATION_SUMMARY.md](TENANT_IMPLEMENTATION_SUMMARY.md)** | Implementation overview | 800+ |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Admin Interface (React)         │
│  • Create Tenant Page                   │
│  • Tenant List & Management             │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Django REST API                 │
│  • Tenant Management Endpoints          │
│  • Module Management                    │
│  • Public Config API                    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│         Tenant Service Layer            │
│  • Config Generation                    │
│  • Folder Management                    │
│  • Business Logic                       │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌─────────┐      ┌─────────────┐
│Database │      │ File System │
│         │      │ /tenants/   │
│Tenant   │      │ /media/     │
│Records  │      │ config.json │
└─────────┘      └─────────────┘
```

---

## 📁 Project Structure

```
MicroSystem/
├── hr_management/
│   ├── tenant_models.py          # Tenant data models
│   ├── tenant_service.py         # Business logic
│   ├── tenant_serializers.py     # API serializers
│   ├── tenant_views.py           # API views
│   ├── tenant_urls.py            # URL routing
│   ├── tenant_middleware.py      # Access control
│   └── management/commands/
│       └── init_modules.py       # Module initialization
│
├── frontend/src/
│   ├── pages/
│   │   ├── CreateTenantPage.jsx  # Tenant creation UI
│   │   └── TenantListPage.jsx    # Tenant management UI
│   ├── components/
│   │   └── LockedModule.jsx      # Locked feature UI
│   └── utils/
│       ├── tenantApi.js          # API client
│       └── tenantConfig.js       # Config loader
│
├── tenants/                       # Tenant instances
│   └── {subdomain}/
│       └── config.json            # Tenant config
│
├── media/tenants/logos/           # Tenant logos
│
└── Documentation/
    ├── TENANT_QUICK_START.md
    ├── TENANT_SYSTEM_COMPLETE_GUIDE.md
    ├── TENANT_ARCHITECTURE.md
    └── TENANT_IMPLEMENTATION_SUMMARY.md
```

---

## 🔌 API Endpoints

### Tenant Management (Admin Only)

```bash
# List all tenants
GET /api/tenants/

# Create tenant
POST /api/tenants/
{
  "name": "Acme Corp",
  "subdomain": "acme",
  "primary_color": "#3498db",
  "secondary_color": "#2ecc71",
  "module_keys": ["employees", "attendance"]
}

# Get tenant details
GET /api/tenants/{id}/

# Update tenant
PATCH /api/tenants/{id}/

# Delete tenant
DELETE /api/tenants/{id}/

# Toggle module
POST /api/tenants/{id}/update_module/
{
  "module_key": "wallet",
  "is_enabled": true
}

# Get statistics
GET /api/tenants/statistics/
```

### Public Endpoints

```bash
# Get config by subdomain
GET /api/public/tenant-config/{subdomain}/

# Get config by domain
GET /api/public/tenant-config/
```

---

## 🎨 Frontend Usage

### Load Tenant Configuration

```javascript
import { useTenantConfig } from './utils/tenantConfig';

function Dashboard() {
  const { config, loading, hasModule } = useTenantConfig('acme');
  
  if (loading) return <Loading />;
  
  return (
    <div>
      <h1>Welcome to {config.name}</h1>
      
      {hasModule('attendance') && <AttendanceWidget />}
      
      {!hasModule('wallet') && (
        <LockedModule moduleName="Wallet" />
      )}
    </div>
  );
}
```

### Apply Tenant Theme

```javascript
import { applyTenantTheme } from './utils/tenantConfig';

useEffect(() => {
  if (config) {
    applyTenantTheme(config.theme);
  }
}, [config]);
```

### Display Module Grid

```javascript
import { ModuleCard } from './components/LockedModule';

const modules = [
  { key: 'employees', name: 'Employees', icon: '👥' },
  { key: 'attendance', name: 'Attendance', icon: '⏰' },
  { key: 'wallet', name: 'Wallet', icon: '💰' },
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
```

---

## 🔒 Security

- **Admin-only tenant management** - Requires admin authentication
- **JWT authentication** - Token-based API access
- **Middleware-based access control** - Automatic module enforcement
- **Input validation** - Subdomain and color validation
- **File upload validation** - Logo file type checking
- **CSRF protection** - Django built-in
- **XSS protection** - React automatic escaping

---

## 📈 Scaling

### Current: 1-100 Tenants
- Shared database
- File-based configs
- Simple architecture

### Medium: 100-500 Tenants
- Redis caching
- CDN for assets
- Database indexing
- Async operations

### Enterprise: 500+ Tenants
- Separate databases
- Multi-region deployment
- Microservices
- Event-driven architecture

**See [TENANT_SYSTEM_COMPLETE_GUIDE.md](TENANT_SYSTEM_COMPLETE_GUIDE.md) Section 8 for details**

---

## 🧪 Testing

```bash
# Backend tests
python manage.py test hr_management.tests.test_tenant_service

# Create test tenant
python manage.py shell
>>> from hr_management.tenant_service import TenantService
>>> tenant_data = {
...     'name': 'Test Corp',
...     'subdomain': 'testcorp',
...     'primary_color': '#3498db',
...     'secondary_color': '#2ecc71'
... }
>>> tenant, created = TenantService.create_tenant_with_modules(
...     tenant_data,
...     ['employees', 'attendance']
... )
>>> print(f"Created: {tenant.name}")
```

---

## 🐛 Troubleshooting

### Module definitions not found
```bash
python manage.py init_modules
```

### Config.json not generated
```python
from hr_management.tenant_service import TenantService
from hr_management.tenant_models import Tenant

tenant = Tenant.objects.get(subdomain='acme')
TenantService.update_tenant_config(tenant)
```

### 403 errors on API calls
Check `settings.py`:
```python
MIDDLEWARE = [
    # ...
    'hr_management.tenant_middleware.TenantMiddleware',
    'hr_management.tenant_middleware.TenantModuleAccessMiddleware',
]
```

---

## 📝 Configuration

### Available Modules

1. **Employee Management** (Core)
2. **Attendance Tracking**
3. **Wallet & Salary**
4. **Task Management**
5. **Complaint System**
6. **Shift Scheduling**
7. **Reports & Analytics**
8. **Notifications** (Core)

### Add Custom Module

```python
# In Django shell or migration
from hr_management.tenant_models import ModuleDefinition

ModuleDefinition.objects.create(
    module_key='inventory',
    module_name='Inventory Management',
    description='Track inventory and stock',
    icon='box',
    is_core=False,
    sort_order=9
)
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👏 Acknowledgments

- Django REST Framework
- React
- PostgreSQL
- All contributors and users

---

## 📞 Support

- 📚 Documentation: See `/docs` folder
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions

---

## 🎯 Roadmap

- [ ] Billing integration (Stripe)
- [ ] Tenant analytics dashboard
- [ ] Email notifications
- [ ] Multi-language support
- [ ] Automated backups
- [ ] Self-service tenant portal
- [ ] Custom domain SSL automation
- [ ] A/B testing per tenant

---

## 📊 Stats

- **Total Code**: 4,500+ lines
- **API Endpoints**: 13+
- **Frontend Pages**: 4
- **Components**: 3
- **Documentation**: 3,000+ lines
- **Modules**: 8 predefined

---

## 🚀 Getting Started Checklist

- [ ] Run `./setup_tenant_system.sh`
- [ ] Create superuser
- [ ] Access admin at `/admin/`
- [ ] Initialize modules
- [ ] Create first tenant
- [ ] Test API endpoints
- [ ] Integrate frontend pages
- [ ] Read documentation

---

**Built with ❤️ for scalable SaaS applications**

*Django + React Multi-Tenant System*
*Version 1.0.0*
