/**
 * Create Tenant Page
 * Admin interface for creating new tenants/clients with module selection
 */

import React, { useState, useEffect } from 'react';
import { createTenant, getModuleDefinitions, initializeModules } from '../utils/tenantApi';
import './CreateTenantPage.css';

const CreateTenantPage = () => {
  const [loading, setLoading] = useState(false);
  const [modules, setModules] = useState([]);
  const [logoPreview, setLogoPreview] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    subdomain: '',
    custom_domain: '',
    primary_color: '#3498db',
    secondary_color: '#2ecc71',
    contact_email: '',
    contact_phone: '',
    logo: null,
    module_keys: [],
  });

  // Load available modules
  useEffect(() => {
    loadModules();
  }, []);

  const loadModules = async () => {
    try {
      const response = await getModuleDefinitions();
      setModules(response);
      
      // Pre-select core modules
      const coreModules = response
        .filter(module => module.is_core)
        .map(module => module.module_key);
      
      setFormData(prev => ({
        ...prev,
        module_keys: coreModules,
      }));
    } catch (err) {
      console.error('Error loading modules:', err);
      // If modules don't exist, try to initialize them
      try {
        await initializeModules();
        loadModules(); // Retry
      } catch (initErr) {
        setError('Failed to load modules. Please contact support.');
      }
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    
    // Auto-generate subdomain from name if subdomain is empty
    if (name === 'name' && !formData.subdomain) {
      const subdomain = value
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '');
      
      setFormData(prev => ({
        ...prev,
        [name]: value,
        subdomain: subdomain,
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value,
      }));
    }
  };

  const handleLogoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData(prev => ({ ...prev, logo: file }));
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleModuleToggle = (moduleKey) => {
    // Check if it's a core module (can't be disabled)
    const module = modules.find(m => m.module_key === moduleKey);
    if (module && module.is_core) {
      return; // Don't allow toggling core modules
    }

    setFormData(prev => {
      const moduleKeys = [...prev.module_keys];
      const index = moduleKeys.indexOf(moduleKey);
      
      if (index > -1) {
        moduleKeys.splice(index, 1);
      } else {
        moduleKeys.push(moduleKey);
      }
      
      return { ...prev, module_keys: moduleKeys };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Validate subdomain
      if (!/^[a-z0-9-]+$/.test(formData.subdomain)) {
        throw new Error('Subdomain can only contain lowercase letters, numbers, and hyphens');
      }

      // Create tenant
      const response = await createTenant(formData);
      
      setSuccess(`Tenant "${response.name}" created successfully! Subdomain: ${response.subdomain}`);
      
      // Reset form
      setFormData({
        name: '',
        subdomain: '',
        custom_domain: '',
        primary_color: '#3498db',
        secondary_color: '#2ecc71',
        contact_email: '',
        contact_phone: '',
        logo: null,
        module_keys: modules.filter(m => m.is_core).map(m => m.module_key),
      });
      setLogoPreview(null);
      
      // Scroll to top to show success message
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setError(err.message || 'Failed to create tenant');
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      setLoading(false);
    }
  };

  const isModuleSelected = (moduleKey) => {
    return formData.module_keys.includes(moduleKey);
  };

  return (
    <div className="create-tenant-page">
      <div className="page-header">
        <h1>Create New Tenant</h1>
        <p>Set up a new client with custom branding and module selection</p>
      </div>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <span className="alert-icon">✓</span>
          <span>{success}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="tenant-form">
        {/* Basic Information */}
        <section className="form-section">
          <h2>Basic Information</h2>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name">
                Client Name <span className="required">*</span>
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="e.g., Acme Corporation"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="subdomain">
                Subdomain <span className="required">*</span>
              </label>
              <div className="input-with-suffix">
                <input
                  type="text"
                  id="subdomain"
                  name="subdomain"
                  value={formData.subdomain}
                  onChange={handleInputChange}
                  placeholder="acme"
                  pattern="[a-z0-9-]+"
                  required
                />
                <span className="input-suffix">.myapp.com</span>
              </div>
              <small>Only lowercase letters, numbers, and hyphens</small>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="custom_domain">Custom Domain (Optional)</label>
            <input
              type="text"
              id="custom_domain"
              name="custom_domain"
              value={formData.custom_domain}
              onChange={handleInputChange}
              placeholder="e.g., client.myapp.com"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="contact_email">Contact Email</label>
              <input
                type="email"
                id="contact_email"
                name="contact_email"
                value={formData.contact_email}
                onChange={handleInputChange}
                placeholder="contact@client.com"
              />
            </div>

            <div className="form-group">
              <label htmlFor="contact_phone">Contact Phone</label>
              <input
                type="tel"
                id="contact_phone"
                name="contact_phone"
                value={formData.contact_phone}
                onChange={handleInputChange}
                placeholder="+1234567890"
              />
            </div>
          </div>
        </section>

        {/* Branding */}
        <section className="form-section">
          <h2>Branding</h2>
          
          <div className="form-group">
            <label htmlFor="logo">Logo Upload</label>
            <input
              type="file"
              id="logo"
              name="logo"
              accept="image/*"
              onChange={handleLogoChange}
            />
            {logoPreview && (
              <div className="logo-preview">
                <img src={logoPreview} alt="Logo preview" />
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="primary_color">Primary Color</label>
              <div className="color-input-group">
                <input
                  type="color"
                  id="primary_color"
                  name="primary_color"
                  value={formData.primary_color}
                  onChange={handleInputChange}
                />
                <input
                  type="text"
                  value={formData.primary_color}
                  onChange={handleInputChange}
                  name="primary_color"
                  pattern="^#[0-9A-Fa-f]{6}$"
                  placeholder="#3498db"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="secondary_color">Secondary Color</label>
              <div className="color-input-group">
                <input
                  type="color"
                  id="secondary_color"
                  name="secondary_color"
                  value={formData.secondary_color}
                  onChange={handleInputChange}
                />
                <input
                  type="text"
                  value={formData.secondary_color}
                  onChange={handleInputChange}
                  name="secondary_color"
                  pattern="^#[0-9A-Fa-f]{6}$"
                  placeholder="#2ecc71"
                />
              </div>
            </div>
          </div>

          <div className="color-preview">
            <div 
              className="color-preview-box" 
              style={{ backgroundColor: formData.primary_color }}
            >
              Primary
            </div>
            <div 
              className="color-preview-box" 
              style={{ backgroundColor: formData.secondary_color }}
            >
              Secondary
            </div>
          </div>
        </section>

        {/* Module Selection */}
        <section className="form-section">
          <h2>Feature Modules</h2>
          <p className="section-description">
            Select the features to enable for this tenant. Core modules are always enabled.
          </p>
          
          <div className="modules-grid">
            {modules.map((module) => {
              const selected = isModuleSelected(module.module_key);
              const isCore = module.is_core;
              
              return (
                <div
                  key={module.module_key}
                  className={`module-card ${selected ? 'selected' : ''} ${isCore ? 'core' : ''}`}
                  onClick={() => handleModuleToggle(module.module_key)}
                >
                  <div className="module-header">
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => {}}
                      disabled={isCore}
                    />
                    <h3>{module.module_name}</h3>
                  </div>
                  <p className="module-description">{module.description}</p>
                  {isCore && (
                    <span className="core-badge">Core Module</span>
                  )}
                </div>
              );
            })}
          </div>

          {modules.length === 0 && (
            <div className="empty-state">
              <p>Loading modules...</p>
            </div>
          )}
        </section>

        {/* Submit Button */}
        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? 'Creating Tenant...' : 'Generate Tenant'}
          </button>
          
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => window.history.back()}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateTenantPage;
