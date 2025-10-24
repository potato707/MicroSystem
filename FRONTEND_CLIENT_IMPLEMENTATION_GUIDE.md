# Client Dashboard Frontend Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing the client login and dashboard frontend using Next.js.

## Prerequisites
- Next.js project already set up at `/v0-micro-system/`
- Backend API running at `http://localhost:8000`
- Django migrations applied

## Directory Structure

Create the following structure in your Next.js project:

```
v0-micro-system/
├── app/
│   └── client/
│       ├── login/
│       │   └── page.tsx
│       ├── dashboard/
│       │   └── page.tsx
│       ├── complaints/
│       │   ├── page.tsx
│       │   ├── [id]/
│       │   │   └── page.tsx
│       │   └── new/
│       │       └── page.tsx
│       └── profile/
│           └── page.tsx
├── components/
│   └── client/
│       ├── ClientLoginForm.tsx
│       ├── ClientDashboardStats.tsx
│       ├── ComplaintsList.tsx
│       ├── ComplaintDetail.tsx
│       ├── NewComplaintForm.tsx
│       └── ClientNavbar.tsx
├── lib/
│   ├── api/
│   │   └── clientApi.ts
│   └── auth/
│       └── clientAuth.ts
└── types/
    └── client.ts
```

## Step 1: Type Definitions

Create `types/client.ts`:

```typescript
export interface User {
  id: string;
  username: string;
  email: string;
  name: string;
  role: string;
  profile_picture?: string;
}

export interface LoginResponse {
  message: string;
  user: User;
  access: string;
  refresh: string;
}

export interface Complaint {
  id: string;
  client_name: string;
  client_email: string;
  client_phone: string;
  project_name?: string;
  project_code?: string;
  category: string;
  category_name: string;
  category_color: string;
  priority: string;
  priority_display: string;
  title: string;
  description: string;
  status: string;
  status_display: string;
  status_color: string;
  created_at: string;
  updated_at: string;
  is_overdue: boolean;
  task_statistics: {
    total_tasks: number;
    completed_tasks: number;
    in_progress_tasks: number;
    pending_tasks: number;
    completion_percentage: number;
  };
}

export interface DashboardStats {
  stats: {
    total_complaints: number;
    by_status: {
      pending_review: number;
      approved: number;
      in_progress: number;
      resolved: number;
      closed: number;
      rejected: number;
    };
    by_priority: {
      urgent: number;
      medium: number;
      low: number;
    };
  };
  recent_complaints: Complaint[];
}

export interface Category {
  id: number;
  name: string;
  description: string;
  color: string;
  is_active: boolean;
}
```

## Step 2: API Client

Create `lib/api/clientApi.ts`:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/hr';

// Get stored tokens
const getAccessToken = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('client_access_token');
  }
  return null;
};

// API call wrapper with authentication
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const token = getAccessToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// Authentication
export const clientLogin = async (email: string, password: string) => {
  return apiCall('/client/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
};

export const clientLogout = async (refreshToken: string) => {
  return apiCall('/client/auth/logout/', {
    method: 'POST',
    body: JSON.stringify({ refresh: refreshToken }),
  });
};

export const getCurrentUser = async () => {
  return apiCall('/client/auth/me/');
};

// Dashboard
export const getDashboardStats = async () => {
  return apiCall('/client/dashboard/stats/');
};

export const getComplaints = async (params?: {
  status?: string;
  priority?: string;
  category?: string;
  search?: string;
  page?: number;
}) => {
  const queryString = params ? '?' + new URLSearchParams(params as any).toString() : '';
  return apiCall(`/client/complaints/${queryString}`);
};

export const getComplaintDetail = async (id: string) => {
  return apiCall(`/client/complaints/${id}/`);
};

export const submitComplaint = async (data: {
  client_phone: string;
  project_name?: string;
  project_code?: string;
  category: number;
  priority: string;
  title: string;
  description: string;
}) => {
  return apiCall('/client/complaints/submit/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const getCategories = async () => {
  return apiCall('/client/categories/');
};

export const getComplaintHistory = async (id: string) => {
  return apiCall(`/client/complaints/${id}/history/`);
};

export const changePassword = async (data: {
  current_password: string;
  new_password: string;
  confirm_password: string;
}) => {
  return apiCall('/client/auth/change-password/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
};

export const updateProfile = async (data: { name?: string; profile_picture?: string }) => {
  return apiCall('/client/auth/profile/', {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
};
```

## Step 3: Authentication Utilities

Create `lib/auth/clientAuth.ts`:

```typescript
export const saveTokens = (access: string, refresh: string) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('client_access_token', access);
    localStorage.setItem('client_refresh_token', refresh);
  }
};

export const removeTokens = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('client_access_token');
    localStorage.removeItem('client_refresh_token');
  }
};

export const getTokens = () => {
  if (typeof window !== 'undefined') {
    return {
      access: localStorage.getItem('client_access_token'),
      refresh: localStorage.getItem('client_refresh_token'),
    };
  }
  return { access: null, refresh: null };
};

export const isAuthenticated = () => {
  const { access } = getTokens();
  return !!access;
};
```

## Step 4: Client Login Page

Create `app/client/login/page.tsx`:

```typescript
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { clientLogin } from '@/lib/api/clientApi';
import { saveTokens } from '@/lib/auth/clientAuth';

export default function ClientLoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await clientLogin(email, password);
      
      // Save tokens
      saveTokens(response.access, response.refresh);
      
      // Redirect to dashboard
      router.push('/client/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-md">
        <div>
          <h2 className="text-3xl font-bold text-center text-gray-900">
            Client Login
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Access your complaint dashboard
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="you@example.com"
              />
            </div>
            
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="••••••••"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="text-center text-sm text-gray-600">
          <p>Don't have an account?</p>
          <p className="mt-1">Submit a complaint and an account will be created for you.</p>
        </div>
      </div>
    </div>
  );
}
```

## Step 5: Client Dashboard Page

Create `app/client/dashboard/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getDashboardStats } from '@/lib/api/clientApi';
import { isAuthenticated } from '@/lib/auth/clientAuth';
import type { DashboardStats } from '@/types/client';

export default function ClientDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    // Check authentication
    if (!isAuthenticated()) {
      router.push('/client/login');
      return;
    }

    // Fetch stats
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch (err: any) {
        setError(err.message);
        if (err.message.includes('401') || err.message.includes('403')) {
          router.push('/client/login');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [router]);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center min-h-screen text-red-600">{error}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">My Dashboard</h1>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">Total Complaints</p>
            <p className="text-3xl font-bold text-gray-900">
              {stats?.stats.total_complaints || 0}
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">In Progress</p>
            <p className="text-3xl font-bold text-blue-600">
              {stats?.stats.by_status.in_progress || 0}
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">Resolved</p>
            <p className="text-3xl font-bold text-green-600">
              {stats?.stats.by_status.resolved || 0}
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-lg shadow">
            <p className="text-sm text-gray-600">Urgent</p>
            <p className="text-3xl font-bold text-red-600">
              {stats?.stats.by_priority.urgent || 0}
            </p>
          </div>
        </div>

        {/* Recent Complaints */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Complaints</h2>
          {stats?.recent_complaints.length === 0 ? (
            <p className="text-gray-600">No complaints yet.</p>
          ) : (
            <div className="space-y-4">
              {stats?.recent_complaints.map((complaint) => (
                <div
                  key={complaint.id}
                  className="border-l-4 pl-4 py-2 cursor-pointer hover:bg-gray-50"
                  style={{ borderLeftColor: complaint.status_color }}
                  onClick={() => router.push(`/client/complaints/${complaint.id}`)}
                >
                  <h3 className="font-semibold text-gray-900">{complaint.title}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                    <span className="px-2 py-1 rounded" style={{ backgroundColor: complaint.category_color + '20', color: complaint.category_color }}>
                      {complaint.category_name}
                    </span>
                    <span>{complaint.status_display}</span>
                    <span>{complaint.priority_display}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={() => router.push('/client/complaints/new')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Submit New Complaint
          </button>
          <button
            onClick={() => router.push('/client/complaints')}
            className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            View All Complaints
          </button>
        </div>
      </div>
    </div>
  );
}
```

## Step 6: Complaints List Page

Create `app/client/complaints/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getComplaints } from '@/lib/api/clientApi';
import { isAuthenticated } from '@/lib/auth/clientAuth';
import type { Complaint } from '@/types/client';

export default function ComplaintsListPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    search: ''
  });
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/client/login');
      return;
    }

    const fetchComplaints = async () => {
      try {
        const data = await getComplaints(filters);
        setComplaints(data.results || data);
      } catch (err) {
        console.error('Failed to fetch complaints:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchComplaints();
  }, [filters, router]);

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Complaints</h1>
          <button
            onClick={() => router.push('/client/complaints/new')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            New Complaint
          </button>
        </div>

        {/* Filters */}
        <div className="bg-white p-4 rounded-lg shadow mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Search complaints..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          />
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="">All Statuses</option>
            <option value="pending_review">Pending Review</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
          <select
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
            className="px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="">All Priorities</option>
            <option value="urgent">Urgent</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Complaints List */}
        <div className="space-y-4">
          {complaints.length === 0 ? (
            <div className="bg-white p-8 rounded-lg shadow text-center text-gray-600">
              No complaints found.
            </div>
          ) : (
            complaints.map((complaint) => (
              <div
                key={complaint.id}
                className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition cursor-pointer"
                onClick={() => router.push(`/client/complaints/${complaint.id}`)}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {complaint.title}
                    </h3>
                    <p className="text-gray-600 mt-2 line-clamp-2">
                      {complaint.description}
                    </p>
                    <div className="flex items-center gap-4 mt-4">
                      <span
                        className="px-3 py-1 rounded-full text-sm"
                        style={{
                          backgroundColor: complaint.category_color + '20',
                          color: complaint.category_color
                        }}
                      >
                        {complaint.category_name}
                      </span>
                      <span
                        className="px-3 py-1 rounded-full text-sm text-white"
                        style={{ backgroundColor: complaint.status_color }}
                      >
                        {complaint.status_display}
                      </span>
                      <span className="text-sm text-gray-600">
                        {complaint.priority_display}
                      </span>
                    </div>
                  </div>
                  {complaint.task_statistics && (
                    <div className="ml-4 text-right">
                      <p className="text-sm text-gray-600">Progress</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {complaint.task_statistics.completion_percentage}%
                      </p>
                      <p className="text-xs text-gray-500">
                        {complaint.task_statistics.completed_tasks}/{complaint.task_statistics.total_tasks} tasks
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
```

## Step 7: New Complaint Form

Create `app/client/complaints/new/page.tsx`:

```typescript
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { submitComplaint, getCategories } from '@/lib/api/clientApi';
import { isAuthenticated } from '@/lib/auth/clientAuth';
import type { Category } from '@/types/client';

export default function NewComplaintPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [formData, setFormData] = useState({
    client_phone: '',
    project_name: '',
    project_code: '',
    category: '',
    priority: 'medium',
    title: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/client/login');
      return;
    }

    const fetchCategories = async () => {
      try {
        const data = await getCategories();
        setCategories(data);
      } catch (err) {
        console.error('Failed to fetch categories:', err);
      }
    };

    fetchCategories();
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await submitComplaint({
        ...formData,
        category: parseInt(formData.category)
      });
      
      router.push(`/client/complaints/${response.complaint.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit complaint');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Submit New Complaint</h1>
        
        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Phone Number *
            </label>
            <input
              type="tel"
              required
              value={formData.client_phone}
              onChange={(e) => setFormData({ ...formData, client_phone: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="+1234567890"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project Name
              </label>
              <input
                type="text"
                value={formData.project_name}
                onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Project Code
              </label>
              <input
                type="text"
                value={formData.project_code}
                onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Category *
              </label>
              <select
                required
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Select category...</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Priority *
              </label>
              <select
                required
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Title *
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="Brief description of the issue"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description *
            </label>
            <textarea
              required
              rows={6}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="Detailed description of the issue..."
            />
          </div>

          <div className="flex gap-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
            >
              {loading ? 'Submitting...' : 'Submit Complaint'}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

## Step 8: Environment Variables

Create `.env.local` in your Next.js project root:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/hr
```

## Step 9: Testing the Frontend

1. **Start Backend:**
   ```bash
   cd /home/ahmedyasser/lab/MicroSystem
   python manage.py runserver
   ```

2. **Start Frontend:**
   ```bash
   cd v0-micro-system
   npm run dev
   ```

3. **Test Flow:**
   - Submit complaint via public form (creates account)
   - Check console for welcome email with password
   - Visit `/client/login`
   - Login with email and password
   - View dashboard at `/client/dashboard`
   - View complaints list
   - Submit new complaint (logged in)

## Additional Features to Implement

1. **Protected Route Middleware:**
   - Create middleware to check authentication
   - Redirect unauthenticated users to login

2. **Token Refresh:**
   - Implement automatic token refresh
   - Handle expired tokens gracefully

3. **Logout Functionality:**
   - Add logout button to navbar
   - Clear tokens on logout

4. **Complaint Detail Page:**
   - Show full complaint information
   - Display status history timeline
   - Show task progress
   - Display comments/communication

5. **Profile Page:**
   - View/edit profile information
   - Change password form
   - View account statistics

## Styling Recommendations

- Use Tailwind CSS (already in your project)
- Use shadcn/ui components (already in your project)
- Add loading spinners for better UX
- Add success/error toast notifications
- Make responsive for mobile devices

## Security Best Practices

1. Never store sensitive data in localStorage
2. Use httpOnly cookies for tokens (if possible)
3. Implement CSRF protection
4. Validate all inputs on frontend and backend
5. Use HTTPS in production
6. Implement rate limiting on login endpoint
7. Add password strength indicator
8. Implement "forgot password" flow

## Next Steps

1. Implement all pages as outlined above
2. Add proper error handling and loading states
3. Implement toast notifications
4. Add form validation
5. Style with your design system
6. Test thoroughly
7. Deploy to production

## Support

For questions or issues, refer to:
- Backend API documentation
- CLIENT_ACCOUNT_SYSTEM_IMPLEMENTATION.md
- Django REST Framework documentation
- Next.js documentation
