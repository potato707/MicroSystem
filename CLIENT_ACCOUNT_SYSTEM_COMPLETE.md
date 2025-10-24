# Client Account System - Complete Implementation

## Overview
This document provides a comprehensive guide to the complete client account system, including both backend and frontend implementations. The system automatically creates client accounts when complaints are submitted and provides a secure portal for clients to manage their complaints.

## System Architecture

### Backend (Django + DRF)
- **Models**: Extended User model with 'client' role, ClientComplaint with client_user ForeignKey
- **Auto-Account Creation**: ClientComplaintSubmissionSerializer creates accounts automatically
- **Authentication**: JWT-based authentication using djangorestframework-simplejwt
- **Email Notifications**: Automated welcome emails with login credentials

### Frontend (Next.js + TypeScript)
- **Pages**: Login, Dashboard, Complaints List, Complaint Detail, New Complaint Form
- **API Integration**: Centralized API client with error handling
- **Authentication**: Client-side token management with localStorage
- **UI/UX**: Responsive design with Tailwind CSS

---

## Backend Implementation

### 1. Database Models

#### User Model Extension
```python
# hr_management/models.py
ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('manager', 'Manager'),
    ('employee', 'Employee'),
    ('client', 'Client'),  # NEW
]
```

#### ClientComplaint Model Extension
```python
client_user = models.ForeignKey(
    User, 
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True,
    related_name='client_complaints',
    help_text="The user account created for this client"
)
```

### 2. Auto-Account Creation

The `ClientComplaintSubmissionSerializer.create()` method handles:
- Checking for existing accounts
- Generating secure 12-character passwords
- Creating user accounts with 'client' role
- Sending welcome emails with credentials
- Linking complaints to user accounts

### 3. API Endpoints

#### Authentication Endpoints
```
POST   /client/auth/login/           - Login with email/password (returns JWT)
POST   /client/auth/logout/          - Logout and blacklist refresh token
GET    /client/auth/me/              - Get current user info + stats
POST   /client/auth/change-password/ - Change password
PATCH  /client/auth/profile/         - Update profile information
```

#### Dashboard Endpoints
```
GET    /client/dashboard/stats/                - Get dashboard statistics
GET    /client/complaints/                     - List all complaints (filtered, paginated)
GET    /client/complaints/<id>/                - Get complaint details
POST   /client/complaints/submit/              - Submit new complaint
GET    /client/complaints/categories/          - Get available categories
GET    /client/complaints/<id>/status-history/ - Get status change history
```

### 4. Permissions & Security
- All client endpoints require JWT authentication
- Clients can only access their own complaints
- Data is filtered by `request.user` automatically
- Passwords are hashed with Django's default hasher
- Refresh tokens are blacklisted on logout

---

## Frontend Implementation

### Project Structure
```
v0-micro-system/
├── app/
│   └── client/
│       ├── login/
│       │   └── page.tsx                 # Login page
│       ├── dashboard/
│       │   └── page.tsx                 # Dashboard with stats
│       ├── complaints/
│       │   ├── page.tsx                 # Complaints list with filters
│       │   ├── [id]/
│       │   │   └── page.tsx             # Complaint detail view
│       │   └── new/
│       │       └── page.tsx             # New complaint form
├── lib/
│   ├── api/
│   │   └── clientApi.ts                 # API client functions
│   └── auth/
│       └── clientAuth.ts                # Authentication utilities
├── types/
│   └── client.ts                        # TypeScript interfaces
└── .env.local                           # Environment variables
```

### Key Files

#### 1. TypeScript Types (`types/client.ts`)
Defines interfaces for:
- User
- LoginResponse
- Complaint
- DashboardStats
- Category
- PaginatedResponse
- Form data types

#### 2. Authentication Utilities (`lib/auth/clientAuth.ts`)
Provides:
- Token storage (access + refresh)
- Token retrieval
- Authentication check
- Authorization header generation
- Token clearing (logout)

#### 3. API Client (`lib/api/clientApi.ts`)
Functions for:
- Authentication (login, logout, getCurrentUser, changePassword, updateProfile)
- Dashboard (getDashboardStats, getComplaints, getComplaintById)
- Complaints (submitComplaint, getAvailableCategories)
- Error handling and response parsing

#### 4. Pages

**Login Page** (`app/client/login/page.tsx`)
- Email/password form
- JWT token storage on success
- Error handling
- Redirect to dashboard after login

**Dashboard** (`app/client/dashboard/page.tsx`)
- Statistics cards (total, pending, in-progress, resolved)
- Recent complaints list
- Quick actions (new complaint, view all)
- Logout functionality
- Protected route (redirects to login if not authenticated)

**Complaints List** (`app/client/complaints/page.tsx`)
- Search and filter (status, priority)
- Paginated results
- Status and priority badges
- Click to view details
- Protected route

**Complaint Detail** (`app/client/complaints/[id]/page.tsx`)
- Full complaint information
- Status and priority display
- Contact information
- Assignment details
- Resolution (if available)
- Protected route

**New Complaint Form** (`app/client/complaints/new/page.tsx`)
- Pre-filled contact information from user account
- Category selection
- Priority selection
- Form validation
- Success message with redirect
- Protected route

---

## Testing

### Backend Tests
Run the comprehensive test suite:
```bash
python test_client_account_system.py
```

Tests cover:
1. Account creation on complaint submission
2. No duplicate accounts for existing emails
3. Complaints linked to correct user accounts
4. Password authentication works correctly

### Test Credentials
After running tests, you can use:
- **Email**: testclient@example.com
- **Password**: (shown in test output, e.g., fP5Lwv##om&K)

---

## Setup & Deployment

### Backend Setup
1. Apply migrations:
   ```bash
   python manage.py migrate
   ```

2. Create categories (if not exist):
   ```bash
   python manage.py shell
   from hr_management.models import ComplaintCategory
   ComplaintCategory.objects.get_or_create(name='Technical Support')
   ComplaintCategory.objects.get_or_create(name='Billing')
   ComplaintCategory.objects.get_or_create(name='Service Quality')
   ```

3. Configure email settings in `settings.py`:
   ```python
   # For production, use a real email backend
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'your-email@gmail.com'
   EMAIL_HOST_PASSWORD = 'your-app-password'
   DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
   ```

4. Start Django server:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup
1. Install dependencies:
   ```bash
   cd v0-micro-system
   npm install
   ```

2. Verify `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/hr
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Access the client portal at:
   ```
   http://localhost:3000/client/login
   ```

---

## User Flows

### New Client Flow
1. Client submits complaint via public form at `/client-portal`
2. Backend creates user account automatically
3. Email sent with login credentials
4. Client logs in at `/client/login`
5. Client redirected to dashboard

### Existing Client Flow
1. Client logs in at `/client/login`
2. Dashboard shows statistics and recent complaints
3. Client can:
   - View all complaints with filtering
   - View detailed complaint information
   - Submit new complaints
   - Update profile
   - Change password

### Complaint Submission Flow
1. Click "Submit New Complaint" button
2. Fill in complaint form (contact info pre-filled)
3. Select category and priority
4. Submit form
5. Success message displayed
6. Redirect to complaints list

---

## Security Features

### Authentication
- JWT tokens with access/refresh mechanism
- Tokens stored in localStorage (client-side)
- Automatic token inclusion in API requests
- Token blacklisting on logout

### Authorization
- All client endpoints require authentication
- Clients can only access their own data
- Queries automatically filtered by user

### Data Protection
- Passwords hashed using Django's PBKDF2
- Auto-generated passwords are 12+ characters with mixed case, numbers, symbols
- CSRF protection enabled
- SQL injection prevention via ORM

---

## API Response Examples

### Login Success
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 5,
    "username": "client_john.doe@example.com",
    "email": "john.doe@example.com",
    "name": "John Doe",
    "role": "client"
  }
}
```

### Dashboard Stats
```json
{
  "total_complaints": 12,
  "pending_complaints": 3,
  "resolved_complaints": 7,
  "in_progress_complaints": 2
}
```

### Complaints List (Paginated)
```json
{
  "count": 12,
  "next": "http://localhost:8000/hr/client/complaints/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Login Issue",
      "description": "Cannot log into my account",
      "category": "Technical Support",
      "status": "in-progress",
      "priority": "high",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-16T14:20:00Z",
      "client_name": "John Doe",
      "client_email": "john.doe@example.com",
      "assigned_to_name": "Jane Smith"
    }
  ]
}
```

---

## Troubleshooting

### Backend Issues

**Migration Error**
```bash
# Reset migrations if needed
python manage.py migrate hr_management zero
python manage.py migrate
```

**Email Not Sending**
- Check EMAIL_BACKEND in settings.py
- For development, use console backend (emails printed to console)
- For production, configure SMTP settings

**JWT Token Issues**
```bash
# Install required package
pip install djangorestframework-simplejwt
```

### Frontend Issues

**API Connection Failed**
- Verify Django server is running on port 8000
- Check `.env.local` has correct API URL
- Check browser console for CORS errors
- Ensure Django CORS settings allow localhost:3000

**TypeScript Errors**
```bash
# Reinstall dependencies
rm -rf node_modules
npm install
```

**Environment Variables Not Loading**
- Restart Next.js dev server after changing `.env.local`
- Ensure variable names start with `NEXT_PUBLIC_`

---

## Future Enhancements

### Potential Features
1. **Real-time Notifications**: WebSocket integration for status updates
2. **File Uploads**: Allow clients to attach files to complaints
3. **Comment System**: Allow clients to comment on their complaints
4. **Email Notifications**: Notify clients of status changes
5. **Password Reset**: Forgot password functionality
6. **Multi-language Support**: Internationalization (i18n)
7. **Mobile App**: React Native implementation
8. **Analytics**: Detailed complaint analytics and reports

### Performance Optimizations
1. Implement Redis caching for frequently accessed data
2. Use pagination more aggressively
3. Add database indexes on frequently queried fields
4. Implement API response compression

---

## Support & Maintenance

### Monitoring
- Monitor failed login attempts
- Track API response times
- Log complaint submission errors
- Monitor email delivery status

### Regular Maintenance
- Rotate JWT secret keys periodically
- Clean up old blacklisted tokens
- Archive old resolved complaints
- Update dependencies regularly

---

## Conclusion

The client account system is now fully functional with both backend and frontend implementations. Clients can:
- Submit complaints and automatically get accounts
- Log in securely with JWT authentication
- View their dashboard with statistics
- Manage their complaints (view, filter, create)
- Access detailed complaint information

The system is production-ready with proper security measures, error handling, and a clean user interface.

For questions or issues, refer to the documentation files:
- `CLIENT_ACCOUNT_SYSTEM_IMPLEMENTATION.md` - Backend details
- `CLIENT_ACCOUNT_SYSTEM_TESTING.md` - Testing guide
- This file - Complete implementation guide
