# 🚀 الوصول للـ Tenants من Frontend (Next.js)

## 📋 الملخص

النظام الحالي يستخدم **Next.js** وليس React عادي. إليك كيفية الوصول لأي tenant باستخدام الـ subdomain.

---

## 🎯 الطريقة الحالية

### 1. استخدام X-Tenant-Subdomain Header ✅

الباك اند يتعرف على الـ tenant من خلال header:

```typescript
// في أي API call
headers: {
  'X-Tenant-Subdomain': 'demo', // أو 'testc' أو أي subdomain
}
```

---

## 📁 الملفات المطلوبة

### 1️⃣ Tenant Context

**المسار:** `v0-micro-system/src/contexts/TenantContext.tsx`

```typescript
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';

interface Tenant {
  subdomain: string;
  name: string;
  role?: string;
}

interface TenantContextType {
  currentTenant: Tenant | null;
  selectTenant: (tenant: Tenant) => void;
  clearTenant: () => void;
  subdomain: string | undefined;
  tenantName: string | undefined;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export const TenantProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentTenant, setCurrentTenant] = useState<Tenant | null>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('currentTenant');
      return saved ? JSON.parse(saved) : null;
    }
    return null;
  });

  useEffect(() => {
    if (currentTenant) {
      localStorage.setItem('currentTenant', JSON.stringify(currentTenant));
    } else {
      localStorage.removeItem('currentTenant');
    }
  }, [currentTenant]);

  const selectTenant = (tenant: Tenant) => {
    setCurrentTenant(tenant);
  };

  const clearTenant = () => {
    setCurrentTenant(null);
  };

  const value: TenantContextType = {
    currentTenant,
    selectTenant,
    clearTenant,
    subdomain: currentTenant?.subdomain,
    tenantName: currentTenant?.name,
  };

  return <TenantContext.Provider value={value}>{children}</TenantContext.Provider>;
};

export const useTenant = () => {
  const context = useContext(TenantContext);
  if (!context) {
    throw new Error('useTenant must be used within TenantProvider');
  }
  return context;
};
```

---

### 2️⃣ API Client مع Tenant Header

**المسار:** `v0-micro-system/lib/tenantApi.ts`

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Get current tenant from localStorage
const getCurrentTenant = () => {
  if (typeof window === 'undefined') return null;
  const saved = localStorage.getItem('currentTenant');
  return saved ? JSON.parse(saved) : null;
};

// Make API request with tenant header
export async function fetchWithTenant(url: string, options: RequestInit = {}) {
  const tenant = getCurrentTenant();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add tenant header if available
  if (tenant?.subdomain) {
    headers['X-Tenant-Subdomain'] = tenant.subdomain;
    console.log(`📤 API Request to ${url} for tenant: ${tenant.subdomain}`);
  }

  // Add auth token if available
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Request failed' }));
    throw new Error(error.message || `HTTP ${response.status}`);
  }

  return response.json();
}

// API Functions

export async function getAllTenants() {
  return fetchWithTenant('/api/tenants/');
}

export async function getTenantConfig(subdomain: string) {
  return fetchWithTenant(`/api/tenants/${subdomain}/config/`);
}

export async function loginToTenant(subdomain: string, username: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/api/token/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Tenant-Subdomain': subdomain,
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || error.error || 'Login failed');
  }

  const data = await response.json();
  
  // Save to localStorage
  if (typeof window !== 'undefined') {
    localStorage.setItem('token', data.access);
    localStorage.setItem('refreshToken', data.refresh);
    localStorage.setItem('currentTenant', JSON.stringify({
      subdomain: data.tenant,
      name: data.tenant_name,
      role: data.role,
    }));
  }

  return data;
}

export async function logout() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('currentTenant');
  }
}

// Module-specific functions (require tenant header)
export async function getEmployees() {
  return fetchWithTenant('/hr/employees/');
}

export async function getAttendance() {
  return fetchWithTenant('/hr/attendance/');
}

export async function getTasks() {
  return fetchWithTenant('/hr/tasks/');
}

export async function getComplaints() {
  return fetchWithTenant('/hr/complaints/');
}

export async function getWallet() {
  return fetchWithTenant('/hr/wallet/');
}
```

---

### 3️⃣ Tenant Selector Page

**المسار:** `v0-micro-system/app/tenants/page.tsx`

```typescript
'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getAllTenants } from '@/lib/tenantApi';
import { useTenant } from '@/contexts/TenantContext';

interface Tenant {
  id: number;
  name: string;
  subdomain: string;
  primary_color: string;
  secondary_color: string;
  logo?: string;
  is_active: boolean;
}

export default function TenantSelector() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { selectTenant } = useTenant();
  const router = useRouter();

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const data = await getAllTenants();
      setTenants(data);
    } catch (err) {
      setError('Failed to load tenants');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTenantSelect = (tenant: Tenant) => {
    selectTenant({
      subdomain: tenant.subdomain,
      name: tenant.name,
    });
    router.push(`/login/${tenant.subdomain}`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-purple-600 to-blue-600">
        <div className="text-white text-xl">Loading tenants...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-purple-600 to-blue-600">
        <div className="bg-white p-8 rounded-lg shadow-lg">
          <h2 className="text-red-600 text-xl font-bold mb-4">Error</h2>
          <p>{error}</p>
          <button
            onClick={loadTenants}
            className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="text-center text-white mb-12">
          <h1 className="text-5xl font-bold mb-4">🏢 Select Your Organization</h1>
          <p className="text-xl opacity-90">Choose which organization you want to access</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tenants.map((tenant) => (
            <div
              key={tenant.id}
              onClick={() => tenant.is_active && handleTenantSelect(tenant)}
              className={`bg-white rounded-2xl p-6 cursor-pointer transition-all hover:shadow-2xl hover:-translate-y-2 ${
                !tenant.is_active ? 'opacity-50 cursor-not-allowed' : ''
              }`}
              style={{ borderLeft: `6px solid ${tenant.primary_color}` }}
            >
              {tenant.logo && (
                <div className="w-20 h-20 mb-4 flex items-center justify-center bg-gray-100 rounded-xl">
                  <img src={tenant.logo} alt={tenant.name} className="max-w-full max-h-full" />
                </div>
              )}

              <h3 className="text-2xl font-bold text-gray-800 mb-2">{tenant.name}</h3>
              <p className="text-gray-600 text-sm mb-4">
                🔗 {tenant.subdomain}.mycompany.com
              </p>

              <div className="flex gap-2 mb-4">
                <div
                  className="w-8 h-8 rounded-full border-2 border-gray-200"
                  style={{ backgroundColor: tenant.primary_color }}
                  title="Primary color"
                />
                <div
                  className="w-8 h-8 rounded-full border-2 border-gray-200"
                  style={{ backgroundColor: tenant.secondary_color }}
                  title="Secondary color"
                />
              </div>

              <span
                className={`inline-block px-4 py-1 rounded-full text-sm font-semibold ${
                  tenant.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {tenant.is_active ? '✓ Active' : '⚠ Inactive'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

### 4️⃣ Login Page للـ Tenant

**المسار:** `v0-micro-system/app/login/[subdomain]/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { loginToTenant } from '@/lib/tenantApi';
import { useTenant } from '@/contexts/TenantContext';

export default function TenantLogin() {
  const params = useParams();
  const router = useRouter();
  const { currentTenant } = useTenant();
  
  const subdomain = params.subdomain as string;
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await loginToTenant(subdomain, username, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <button
          onClick={() => router.push('/tenants')}
          className="text-gray-600 mb-6 hover:text-blue-600"
        >
          ← Back to Organizations
        </button>

        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-gray-100 px-6 py-2 rounded-full mb-4">
            <span className="text-2xl">🏢</span>
            <span className="font-semibold">{currentTenant?.name || subdomain}</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Welcome Back!</h1>
          <p className="text-gray-600">Sign in to access your dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              ⚠️ {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none"
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 rounded-lg font-semibold hover:shadow-lg transition-all disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          <div className="text-center text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
            🔒 Logging in to: <strong className="text-blue-600">{subdomain}</strong>
          </div>
        </form>
      </div>
    </div>
  );
}
```

---

### 5️⃣ تحديث Layout الرئيسي

**المسار:** `v0-micro-system/app/layout.tsx`

```typescript
import { TenantProvider } from '@/contexts/TenantContext';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <TenantProvider>
          {children}
        </TenantProvider>
      </body>
    </html>
  );
}
```

---

## 🧪 الاستخدام

### 1. افتح صفحة Tenant Selector

```
http://localhost:3000/tenants
```

### 2. اختر Tenant

- سيعرض لك جميع الـ tenants المتاحة
- اضغط على أي tenant

### 3. Login

- سيوجهك لصفحة login
- ادخل username و password
- سيتم إرسال `X-Tenant-Subdomain` header تلقائياً

### 4. Access Dashboard

- بعد Login، جميع الـ API requests ستحتوي على tenant header
- يمكنك استدعاء أي API:

```typescript
import { getEmployees, getTasks } from '@/lib/tenantApi';

// Will automatically include X-Tenant-Subdomain header
const employees = await getEmployees();
const tasks = await getTasks();
```

---

## 📊 الخلاصة

### الملفات المطلوبة:

1. ✅ `src/contexts/TenantContext.tsx` - Tenant state management
2. ✅ `lib/tenantApi.ts` - API client مع tenant header
3. ✅ `app/tenants/page.tsx` - Tenant selector
4. ✅ `app/login/[subdomain]/page.tsx` - Login page
5. ✅ `app/layout.tsx` - Wrap with TenantProvider

### كيف يعمل:

1. User يختار tenant من `/tenants`
2. يتم حفظ tenant في localStorage
3. كل API request يضيف `X-Tenant-Subdomain` header تلقائياً
4. Backend يتعرف على tenant من header
5. يتم عرض البيانات الخاصة بالـ tenant فقط

---

**🎉 النظام جاهز للاستخدام!**
