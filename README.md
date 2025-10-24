# MicroSystem - Multi-Tenant HR Management System

A comprehensive Django-based multi-tenant HR management system with per-tenant databases and Next.js frontend.

## 🚀 Quick Start

### Backend (Django)
```bash
# Activate environment
conda activate eurolink

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver
```

### Frontend (Next.js)
```bash
cd v0-micro-system
npm install
npm run dev
```

## 📁 Project Structure

```
MicroSystem/
├── hr_management/          # Main Django app
│   ├── models.py          # Core models (Employee, Attendance, etc.)
│   ├── views.py           # API views
│   ├── serializers.py     # DRF serializers
│   ├── tenant_*.py        # Multi-tenant related files
│   └── migrations/        # Database migrations
├── MicroSystem/           # Django project settings
├── v0-micro-system/       # Next.js frontend
├── tenants/               # Tenant-specific folders
├── media/                 # Uploaded files
├── manage.py              # Django management
└── create_tenant_user.py  # Utility: Create tenant admin users

Database Files:
├── db.sqlite3                 # Main database (tenant metadata)
├── tenant_testc.sqlite3       # Tenant: testc
├── tenant_khalid.sqlite3      # Tenant: khalid
├── tenant_fares.sqlite3       # Tenant: fares
└── tenant_*.sqlite3           # Other tenant databases
```

## 🔑 Key Features

### Multi-Tenancy
- **Database-per-tenant architecture** - Each tenant has isolated SQLite database
- **Subdomain routing** - Access via `{tenant}.localhost:3000`
- **Automatic initialization** - Database and admin user created automatically
- **Custom tenant creator** - Beautiful UI at `/api/create-tenant/`

### HR Management
- **Employee Management** - CRUD operations, profiles, documents
- **Attendance Tracking** - Check-in/out, GPS location, status tracking
- **Shift Management** - Multiple shifts, overtime calculations
- **Leave Management** - Leave requests, approval workflow
- **Salary System** - Multi-wallet (main, reimbursement, advance)
- **Task Management** - Tasks, subtasks, assignments, progress tracking
- **Team Management** - Teams, permissions, role-based access

### Client Portal
- **Complaint System** - Submit and track complaints
- **Token-based Access** - Secure access without login
- **Status Tracking** - Real-time complaint status updates
- **Notifications** - Email notifications for updates

## 🛠️ Utilities

### Create Tenant Admin User
```bash
python create_tenant_user.py
```
Follow the prompts to create admin users for tenants manually.

### Access URLs
- **Django Admin**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/schema/swagger-ui/
- **Tenant Creator**: http://localhost:8000/api/create-tenant/
- **Frontend**: http://{tenant}.localhost:3000/

## 🗄️ Database Architecture

- **Main Database** (`db.sqlite3`): Stores tenant metadata, module definitions
- **Tenant Databases** (`tenant_{subdomain}.sqlite3`): Isolated per-tenant data
- **Dynamic Routing**: Automatic database selection based on subdomain

## 📝 API Endpoints

### Authentication
- `POST /api/login/` - User login (returns JWT)
- `POST /api/token/refresh/` - Refresh JWT token

### Tenants
- `GET /api/tenants/` - List all tenants
- `POST /api/tenants/` - Create new tenant
- `GET /api/tenants/{id}/` - Tenant details

### Employees (requires authentication)
- `GET /api/employees/` - List employees
- `POST /api/employees/` - Create employee
- `GET /api/employees/{id}/` - Employee details
- `PATCH /api/employees/{id}/` - Update employee

### Attendance
- `GET /api/attendance/` - List attendance records
- `POST /api/attendance/` - Check-in
- `PATCH /api/attendance/{id}/` - Check-out

### Tasks
- `GET /api/tasks/` - List tasks
- `POST /api/tasks/` - Create task
- `GET /api/tasks/{id}/` - Task details

## 🔐 Security

- **JWT Authentication** - Token-based auth for all protected endpoints
- **Role-based Access** - Admin/Employee permissions
- **CORS Configured** - Frontend at localhost:3000
- **Tenant Isolation** - Complete data separation per tenant

## 🧪 Testing

The workspace has been cleaned of all test scripts. For development testing:
1. Use Django shell: `python manage.py shell`
2. Use API tools like Postman or curl
3. Check browser console for frontend issues

## 📦 Dependencies

### Backend
- Django 4.2.13
- Django REST Framework
- djangorestframework-simplejwt
- django-cors-headers
- Pillow (for image handling)

### Frontend
- Next.js 14+
- React 18
- Tailwind CSS
- Axios for API calls

## 🤝 Contributing

This is a production-ready system. For modifications:
1. Create feature branches
2. Test thoroughly in development
3. Update migrations if models change
4. Document API changes

## 📄 License

Proprietary - All rights reserved

---

**Built with ❤️ by Ahmed Yasser**
