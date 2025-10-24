/**
 * Tenant API Utilities
 * Helper functions for interacting with the tenant management API
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Get authentication token from localStorage
 */
const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

/**
 * Make authenticated API request
 */
const makeAuthRequest = async (url, options = {}) => {
  const token = getAuthToken();
  const headers = {
    ...options.headers,
    'Authorization': token ? `Bearer ${token}` : '',
  };

  // Don't set Content-Type for FormData (browser will set it automatically with boundary)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || error.message || 'Request failed');
  }

  return response.json();
};

/**
 * Get all tenants
 */
export const getTenants = async () => {
  return makeAuthRequest('/api/tenants/');
};

/**
 * Get tenant by ID
 */
export const getTenant = async (id) => {
  return makeAuthRequest(`/api/tenants/${id}/`);
};

/**
 * Get tenant configuration
 */
export const getTenantConfig = async (id) => {
  return makeAuthRequest(`/api/tenants/${id}/config/`);
};

/**
 * Get tenant config by subdomain (public endpoint)
 */
export const getTenantConfigBySubdomain = async (subdomain) => {
  const response = await fetch(`${API_BASE_URL}/api/public/tenant-config/${subdomain}/`);
  if (!response.ok) {
    throw new Error('Tenant not found');
  }
  return response.json();
};

/**
 * Create a new tenant
 */
export const createTenant = async (tenantData) => {
  const formData = new FormData();
  
  // Add basic fields
  formData.append('name', tenantData.name);
  formData.append('subdomain', tenantData.subdomain);
  
  if (tenantData.custom_domain) {
    formData.append('custom_domain', tenantData.custom_domain);
  }
  
  if (tenantData.primary_color) {
    formData.append('primary_color', tenantData.primary_color);
  }
  
  if (tenantData.secondary_color) {
    formData.append('secondary_color', tenantData.secondary_color);
  }
  
  if (tenantData.contact_email) {
    formData.append('contact_email', tenantData.contact_email);
  }
  
  if (tenantData.contact_phone) {
    formData.append('contact_phone', tenantData.contact_phone);
  }
  
  // Add logo file if provided
  if (tenantData.logo) {
    formData.append('logo', tenantData.logo);
  }
  
  // Add module keys
  if (tenantData.module_keys && tenantData.module_keys.length > 0) {
    tenantData.module_keys.forEach(key => {
      formData.append('module_keys', key);
    });
  }
  
  return makeAuthRequest('/api/tenants/', {
    method: 'POST',
    body: formData,
  });
};

/**
 * Update tenant
 */
export const updateTenant = async (id, tenantData) => {
  const formData = new FormData();
  
  Object.keys(tenantData).forEach(key => {
    if (tenantData[key] !== null && tenantData[key] !== undefined) {
      if (key === 'logo' && tenantData[key] instanceof File) {
        formData.append(key, tenantData[key]);
      } else if (key !== 'logo') {
        formData.append(key, tenantData[key]);
      }
    }
  });
  
  return makeAuthRequest(`/api/tenants/${id}/`, {
    method: 'PATCH',
    body: formData,
  });
};

/**
 * Delete tenant
 */
export const deleteTenant = async (id) => {
  return makeAuthRequest(`/api/tenants/${id}/`, {
    method: 'DELETE',
  });
};

/**
 * Get all available modules
 */
export const getModuleDefinitions = async () => {
  return makeAuthRequest('/api/modules/');
};

/**
 * Get tenant modules
 */
export const getTenantModules = async (tenantId) => {
  return makeAuthRequest(`/api/tenants/${tenantId}/modules/`);
};

/**
 * Update tenant module status
 */
export const updateTenantModule = async (tenantId, moduleKey, isEnabled) => {
  return makeAuthRequest(`/api/tenants/${tenantId}/update_module/`, {
    method: 'POST',
    body: JSON.stringify({
      module_key: moduleKey,
      is_enabled: isEnabled,
    }),
  });
};

/**
 * Regenerate tenant config
 */
export const regenerateTenantConfig = async (tenantId) => {
  return makeAuthRequest(`/api/tenants/${tenantId}/regenerate_config/`, {
    method: 'POST',
  });
};

/**
 * Copy frontend template to tenant folder
 */
export const copyFrontendTemplate = async (tenantId) => {
  return makeAuthRequest(`/api/tenants/${tenantId}/copy_frontend/`, {
    method: 'POST',
  });
};

/**
 * Initialize module definitions
 */
export const initializeModules = async () => {
  return makeAuthRequest('/api/tenants/initialize_modules/', {
    method: 'POST',
  });
};

/**
 * Get tenant statistics
 */
export const getTenantStatistics = async () => {
  return makeAuthRequest('/api/tenants/statistics/');
};

/**
 * Check module access for a tenant
 */
export const checkModuleAccess = async (subdomain, moduleKey) => {
  return makeAuthRequest('/api/tenants/check-module-access/', {
    method: 'POST',
    body: JSON.stringify({
      subdomain,
      module_key: moduleKey,
    }),
  });
};
