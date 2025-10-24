# Client Account System - Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT ACCOUNT SYSTEM                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌─────────────────────────────────────┐
│                         │         │                                     │
│   PUBLIC COMPLAINT      │────────▶│   BACKEND API (Django)              │
│   FORM                  │         │                                     │
│   (No Login Required)   │         │   1. Check if user exists           │
│                         │         │   2. Create client account          │
│   • Name                │         │   3. Generate password              │
│   • Email               │         │   4. Send welcome email             │
│   • Phone               │         │   5. Link complaint to user         │
│   • Category            │         │                                     │
│   • Priority            │         │   ✓ ClientComplaintSubmission      │
│   • Title               │         │     Serializer.create()             │
│   • Description         │         │                                     │
│                         │         │                                     │
└─────────────────────────┘         └─────────────────────────────────────┘
                                                     │
                                                     ▼
                                    ┌─────────────────────────────────────┐
                                    │                                     │
                                    │   EMAIL NOTIFICATION                │
                                    │                                     │
                                    │   To: client@example.com            │
                                    │                                     │
                                    │   Subject: Your Account Details     │
                                    │                                     │
                                    │   Email: client@example.com         │
                                    │   Password: Abc123!@#XYZ            │
                                    │   Login: /client/login              │
                                    │   Dashboard: /client/dashboard      │
                                    │                                     │
                                    └─────────────────────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────┐         ┌─────────────────────────────────────┐
│                         │         │                                     │
│   CLIENT LOGIN PAGE     │────────▶│   AUTHENTICATION API                │
│                         │         │                                     │
│   • Email               │         │   POST /client/auth/login/          │
│   • Password            │         │                                     │
│                         │         │   1. Validate credentials           │
│   [Sign In Button]      │         │   2. Check role = 'client'          │
│                         │         │   3. Generate JWT tokens            │
│                         │         │   4. Return user data + tokens      │
│                         │         │                                     │
└─────────────────────────┘         └─────────────────────────────────────┘
                                                     │
                                                     ▼
                                    ┌─────────────────────────────────────┐
                                    │                                     │
                                    │   JWT TOKENS                        │
                                    │                                     │
                                    │   Access Token: eyJ0eXAi...         │
                                    │   Refresh Token: eyJ0eXAi...        │
                                    │                                     │
                                    │   Stored in: localStorage           │
                                    │                                     │
                                    └─────────────────────────────────────┘
                                                     │
                                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                        CLIENT DASHBOARD                                 │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                      STATISTICS CARDS                           │ │
│   │                                                                 │ │
│   │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │ │
│   │  │  Total    │  │In Progress│  │ Resolved  │  │  Urgent   │  │ │
│   │  │    12     │  │     5     │  │     7     │  │     2     │  │ │
│   │  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐ │
│   │                   RECENT COMPLAINTS                             │ │
│   │                                                                 │ │
│   │  • Website Login Issue           [In Progress] [Medium]        │ │
│   │  • Payment Gateway Error         [Pending]     [Urgent]        │ │
│   │  • Design Modification Request   [In Progress] [Low]           │ │
│   │  • Database Performance          [Resolved]    [High]          │ │
│   │                                                                 │ │
│   └─────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│   [Submit New Complaint]  [View All Complaints]  [Logout]              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                    │                              │
                    │                              │
        ┌───────────▼────────────┐    ┌───────────▼────────────┐
        │                        │    │                        │
        │  COMPLAINTS LIST       │    │  NEW COMPLAINT FORM    │
        │                        │    │                        │
        │  • Filter by status    │    │  • Category            │
        │  • Filter by priority  │    │  • Priority            │
        │  • Search              │    │  • Title               │
        │  • Pagination          │    │  • Description         │
        │                        │    │  • Project info        │
        │  [Complaint Cards]     │    │                        │
        │                        │    │  [Submit]              │
        │                        │    │                        │
        └────────┬───────────────┘    └────────────────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │                        │
        │  COMPLAINT DETAIL      │
        │                        │
        │  • Full description    │
        │  • Status history      │
        │  • Task progress       │
        │  • Comments            │
        │  • Attachments         │
        │  • Timeline            │
        │                        │
        └────────────────────────┘
```

## 🔄 Data Flow Diagram

```
PUBLIC COMPLAINT SUBMISSION FLOW
=================================

1. Client Submits Form
   │
   ├─> POST /hr/public/client-complaints/
   │
   └─> Backend Receives Data
       │
       ├─> Check User Exists?
       │   ├─> YES: Use existing user
       │   └─> NO:  Create new user
       │            ├─> Generate username
       │            ├─> Generate password (12 chars)
       │            ├─> Set role = 'client'
       │            ├─> Save user
       │            └─> Send welcome email
       │
       ├─> Create Complaint
       │   └─> Link to client_user
       │
       └─> Return Success Response


CLIENT LOGIN FLOW
==================

1. Client Enters Credentials
   │
   ├─> POST /hr/client/auth/login/
   │
   └─> Backend Validates
       │
       ├─> Find user by email
       ├─> Verify password
       ├─> Check role = 'client'
       ├─> Generate JWT tokens
       │   ├─> Access Token (short-lived)
       │   └─> Refresh Token (long-lived)
       │
       └─> Return tokens + user data


CLIENT DASHBOARD FLOW
=====================

1. Client Accesses Dashboard
   │
   ├─> GET /hr/client/dashboard/stats/
   │   └─> Header: Authorization: Bearer <token>
   │
   └─> Backend Processes
       │
       ├─> Verify JWT token
       ├─> Check role = 'client'
       ├─> Query complaints for this user
       │   └─> WHERE client_user = current_user
       │
       ├─> Calculate statistics
       │   ├─> Total complaints
       │   ├─> By status (pending, progress, resolved)
       │   ├─> By priority (urgent, medium, low)
       │   └─> Recent complaints
       │
       └─> Return dashboard data


NEW COMPLAINT SUBMISSION (LOGGED IN)
=====================================

1. Client Submits New Complaint
   │
   ├─> POST /hr/client/complaints/submit/
   │   └─> Header: Authorization: Bearer <token>
   │
   └─> Backend Processes
       │
       ├─> Verify JWT token
       ├─> Get current user from token
       ├─> Auto-fill client info
       │   ├─> client_name = user.name
       │   ├─> client_email = user.email
       │   └─> client_user = current_user
       │
       ├─> Create complaint
       ├─> Link to current user
       │
       └─> Return new complaint data
```

## 🗄️ Database Schema

```
┌────────────────────────┐
│        User            │
├────────────────────────┤
│ id (UUID)              │◄───────────┐
│ username               │            │
│ email                  │            │
│ name                   │            │
│ role                   │            │ ForeignKey
│   - admin              │            │ (client_user)
│   - employee           │            │
│   - manager            │            │
│   - client ◄───────────┼────────┐   │
│ password (hashed)      │        │   │
│ is_active              │        │   │
│ profile_picture        │        │   │
└────────────────────────┘        │   │
                                  │   │
┌────────────────────────┐        │   │
│   ClientComplaint      │        │   │
├────────────────────────┤        │   │
│ id (UUID)              │        │   │
│ client_name            │        │   │
│ client_email           │        │   │
│ client_phone           │        │   │
│ client_user ───────────┼────────┘   │
│ project_name           │            │
│ project_code           │            │
│ category               │            │
│ priority               │            │
│ title                  │            │
│ description            │            │
│ status                 │            │
│ created_at             │            │
│ updated_at             │            │
└────────────────────────┘            │
                                      │
Relationship:                         │
─────────────                        │
One User (role='client') can have    │
many ClientComplaints                │
                                      │
Query:                                │
──────                               │
user.client_complaints.all() ────────┘
Returns all complaints for this client
```

## 🔒 Security Architecture

```
┌───────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                       │
└───────────────────────────────────────────────────────────┘

Layer 1: Password Security
──────────────────────────
   • Auto-generated passwords (12 chars)
   • Complexity: Letters + Digits + Special
   • Django PBKDF2 hashing
   • Change password feature

Layer 2: Authentication
───────────────────────
   • JWT tokens (stateless)
   • Access token (short-lived)
   • Refresh token (long-lived)
   • Token blacklisting on logout

Layer 3: Authorization
──────────────────────
   • Role-based access control
   • Verify role = 'client' on all endpoints
   • Query filtering by client_user
   • No cross-client data access

Layer 4: API Security
─────────────────────
   • CORS configuration
   • HTTPS enforcement (production)
   • Rate limiting (production)
   • CSRF protection

Layer 5: Data Privacy
─────────────────────
   • Clients see only their complaints
   • Filtered queries at database level
   • No sensitive data in responses
   • Secure email delivery
```

## 📡 API Endpoints Map

```
PUBLIC ENDPOINTS (No Authentication)
════════════════════════════════════
┌─────────────────────────────────────────────────────────┐
│ POST   /hr/public/client-complaints/                    │
│        → Submit complaint (creates account)             │
│                                                         │
│ GET    /hr/public/complaint-categories/                 │
│        → Get available categories                       │
└─────────────────────────────────────────────────────────┘

CLIENT AUTHENTICATION (Token Required After Login)
══════════════════════════════════════════════════
┌─────────────────────────────────────────────────────────┐
│ POST   /hr/client/auth/login/                           │
│        → Login with email + password                    │
│        → Returns JWT tokens                             │
│                                                         │
│ POST   /hr/client/auth/logout/                          │
│        → Logout and blacklist token                     │
│                                                         │
│ GET    /hr/client/auth/me/                              │
│        → Get current user + statistics                  │
│                                                         │
│ POST   /hr/client/auth/change-password/                 │
│        → Change password                                │
│                                                         │
│ PATCH  /hr/client/auth/profile/                         │
│        → Update profile (name, picture)                 │
└─────────────────────────────────────────────────────────┘

CLIENT DASHBOARD (Token Required)
══════════════════════════════════
┌─────────────────────────────────────────────────────────┐
│ GET    /hr/client/dashboard/stats/                      │
│        → Dashboard statistics                           │
│                                                         │
│ GET    /hr/client/complaints/                           │
│        → List complaints (filtered, paginated)          │
│        → Query params: status, priority, category,      │
│          search, page                                   │
│                                                         │
│ GET    /hr/client/complaints/<uuid>/                    │
│        → Get complaint details                          │
│                                                         │
│ GET    /hr/client/complaints/<uuid>/history/            │
│        → Get status change history                      │
│                                                         │
│ POST   /hr/client/complaints/submit/                    │
│        → Submit new complaint (logged in)               │
│                                                         │
│ GET    /hr/client/categories/                           │
│        → Get available categories                       │
└─────────────────────────────────────────────────────────┘
```

## 🎨 Frontend Architecture (Next.js)

```
v0-micro-system/
│
├── app/
│   └── client/
│       ├── login/
│       │   └── page.tsx ──────────► Login Page
│       │
│       ├── dashboard/
│       │   └── page.tsx ──────────► Dashboard (Stats + Recent)
│       │
│       ├── complaints/
│       │   ├── page.tsx ──────────► List All Complaints
│       │   ├── [id]/
│       │   │   └── page.tsx ──────► Complaint Detail
│       │   └── new/
│       │       └── page.tsx ──────► New Complaint Form
│       │
│       └── profile/
│           └── page.tsx ──────────► Profile & Settings
│
├── components/
│   └── client/
│       ├── ClientLoginForm.tsx
│       ├── ClientDashboardStats.tsx
│       ├── ComplaintsList.tsx
│       ├── ComplaintCard.tsx
│       ├── ComplaintDetail.tsx
│       ├── NewComplaintForm.tsx
│       ├── ClientNavbar.tsx
│       └── ProtectedRoute.tsx
│
├── lib/
│   ├── api/
│   │   └── clientApi.ts ──────────► All API calls
│   │
│   └── auth/
│       └── clientAuth.ts ─────────► Auth utilities
│
└── types/
    └── client.ts ─────────────────► TypeScript types
```

---

**System Status:** ✅ Backend Complete | Frontend Ready for Implementation

**Last Updated:** October 16, 2025
