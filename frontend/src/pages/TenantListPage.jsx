/**
 * Tenant List Page
 * Admin interface for viewing and managing all tenants
 */

import React, { useState, useEffect } from 'react';
import { 
  getTenants, 
  deleteTenant, 
  updateTenantModule,
  getTenantStatistics 
} from '../utils/tenantApi';
import './TenantListPage.css';

const TenantListPage = () => {
  const [tenants, setTenants] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [showModuleModal, setShowModuleModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [tenantsData, statsData] = await Promise.all([
        getTenants(),
        getTenantStatistics()
      ]);
      setTenants(tenantsData);
      setStatistics(statsData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (tenantId, tenantName) => {
    if (!window.confirm(`Are you sure you want to delete tenant "${tenantName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await deleteTenant(tenantId);
      setTenants(tenants.filter(t => t.id !== tenantId));
      alert('Tenant deleted successfully');
    } catch (err) {
      alert(`Failed to delete tenant: ${err.message}`);
    }
  };

  const handleManageModules = (tenant) => {
    setSelectedTenant(tenant);
    setShowModuleModal(true);
  };

  const handleCreateNew = () => {
    window.location.href = '/create-tenant';
  };

  if (loading) {
    return (
      <div className="tenant-list-page">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading tenants...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tenant-list-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Tenant Management</h1>
          <p>Manage all client tenants and their configurations</p>
        </div>
        <button className="btn btn-primary" onClick={handleCreateNew}>
          + Create New Tenant
        </button>
      </div>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* Statistics */}
      {statistics && (
        <div className="statistics-grid">
          <div className="stat-card">
            <div className="stat-value">{statistics.total_tenants}</div>
            <div className="stat-label">Total Tenants</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{statistics.active_tenants}</div>
            <div className="stat-label">Active</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">{statistics.inactive_tenants}</div>
            <div className="stat-label">Inactive</div>
          </div>
        </div>
      )}

      {/* Tenant List */}
      <div className="tenant-list">
        {tenants.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🏢</div>
            <h3>No Tenants Yet</h3>
            <p>Create your first tenant to get started</p>
            <button className="btn btn-primary" onClick={handleCreateNew}>
              Create First Tenant
            </button>
          </div>
        ) : (
          <div className="tenants-grid">
            {tenants.map((tenant) => (
              <div key={tenant.id} className="tenant-card">
                <div className="tenant-card-header">
                  {tenant.logo && (
                    <img 
                      src={tenant.logo} 
                      alt={`${tenant.name} logo`}
                      className="tenant-logo"
                    />
                  )}
                  <div className="tenant-info">
                    <h3>{tenant.name}</h3>
                    <a 
                      href={`https://${tenant.full_domain}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="tenant-domain"
                    >
                      {tenant.full_domain} →
                    </a>
                  </div>
                  <div className={`status-badge ${tenant.is_active ? 'active' : 'inactive'}`}>
                    {tenant.is_active ? 'Active' : 'Inactive'}
                  </div>
                </div>

                <div className="tenant-card-body">
                  <div className="tenant-meta">
                    <div className="meta-item">
                      <span className="meta-label">Subdomain:</span>
                      <span className="meta-value">{tenant.subdomain}</span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Modules:</span>
                      <span className="meta-value">
                        {tenant.enabled_modules_count} / {tenant.module_count}
                      </span>
                    </div>
                    <div className="meta-item">
                      <span className="meta-label">Created:</span>
                      <span className="meta-value">
                        {new Date(tenant.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="tenant-colors">
                    <div 
                      className="color-swatch"
                      style={{ backgroundColor: tenant.primary_color }}
                      title="Primary Color"
                    />
                    <div 
                      className="color-swatch"
                      style={{ backgroundColor: tenant.secondary_color }}
                      title="Secondary Color"
                    />
                  </div>
                </div>

                <div className="tenant-card-actions">
                  <button 
                    className="btn-action"
                    onClick={() => window.location.href = `/tenants/${tenant.id}/edit`}
                  >
                    Edit
                  </button>
                  <button 
                    className="btn-action"
                    onClick={() => handleManageModules(tenant)}
                  >
                    Modules
                  </button>
                  <button 
                    className="btn-action danger"
                    onClick={() => handleDelete(tenant.id, tenant.name)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Module Management Modal */}
      {showModuleModal && selectedTenant && (
        <ModuleManagementModal
          tenant={selectedTenant}
          onClose={() => {
            setShowModuleModal(false);
            setSelectedTenant(null);
            loadData(); // Reload data after changes
          }}
        />
      )}
    </div>
  );
};

/**
 * Module Management Modal Component
 */
const ModuleManagementModal = ({ tenant, onClose }) => {
  const [modules, setModules] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadModules();
  }, []);

  const loadModules = async () => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/s/api/tenants/${tenant.id}/modules/`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          }
        }
      );
      const data = await response.json();
      setModules(data);
    } catch (err) {
      console.error('Error loading modules:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleModule = async (moduleKey, currentStatus) => {
    try {
      await updateTenantModule(tenant.id, moduleKey, !currentStatus);
      // Update local state
      setModules(modules.map(m => 
        m.module_key === moduleKey 
          ? { ...m, is_enabled: !currentStatus }
          : m
      ));
    } catch (err) {
      alert(`Failed to update module: ${err.message}`);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Manage Modules - {tenant.name}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {loading ? (
            <div className="loading-state">Loading modules...</div>
          ) : (
            <div className="modules-list">
              {modules.map((module) => (
                <div key={module.module_key} className="module-item">
                  <div className="module-item-info">
                    <h4>{module.module_name}</h4>
                    <span className="module-key">{module.module_key}</span>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={module.is_enabled}
                      onChange={() => handleToggleModule(module.module_key, module.is_enabled)}
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default TenantListPage;
