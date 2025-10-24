/**
 * Tenant Configuration Hook
 * React hook to load and manage tenant configuration
 */

import { useState, useEffect } from 'react';
import { getTenantConfigBySubdomain } from './tenantApi';

/**
 * Hook to load tenant configuration
 * @param {string} subdomain - Tenant subdomain
 * @returns {Object} { config, loading, error, hasModule }
 */
export const useTenantConfig = (subdomain) => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!subdomain) {
      setLoading(false);
      return;
    }

    const loadConfig = async () => {
      try {
        setLoading(true);
        const data = await getTenantConfigBySubdomain(subdomain);
        setConfig(data);
        setError(null);
      } catch (err) {
        setError(err.message);
        setConfig(null);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, [subdomain]);

  /**
   * Check if a module is enabled
   * @param {string} moduleKey - Module key to check
   * @returns {boolean}
   */
  const hasModule = (moduleKey) => {
    return config?.modules?.[moduleKey] === true;
  };

  /**
   * Check if module is disabled
   * @param {string} moduleKey - Module key to check
   * @returns {boolean}
   */
  const isModuleLocked = (moduleKey) => {
    return config?.modules?.[moduleKey] === false;
  };

  return { config, loading, error, hasModule, isModuleLocked };
};

/**
 * Get tenant subdomain from current URL
 * @returns {string|null}
 */
export const getCurrentTenantSubdomain = () => {
  if (typeof window === 'undefined') return null;
  
  const host = window.location.hostname;
  const parts = host.split('.');
  
  // If localhost or main domain, return null
  if (host === 'localhost' || parts.length < 2) {
    return null;
  }
  
  // Return first part as subdomain
  return parts[0];
};

/**
 * Apply tenant theme to document
 * @param {Object} theme - Theme object with primary and secondary colors
 */
export const applyTenantTheme = (theme) => {
  if (!theme) return;
  
  const root = document.documentElement;
  
  if (theme.primary) {
    root.style.setProperty('--tenant-primary-color', theme.primary);
  }
  
  if (theme.secondary) {
    root.style.setProperty('--tenant-secondary-color', theme.secondary);
  }
};

/**
 * HOC to wrap components with tenant config
 * @param {Component} Component - React component to wrap
 * @returns {Component} Wrapped component with tenant config
 */
export const withTenantConfig = (Component) => {
  return (props) => {
    const subdomain = getCurrentTenantSubdomain();
    const tenantConfig = useTenantConfig(subdomain);
    
    return <Component {...props} tenantConfig={tenantConfig} />;
  };
};
