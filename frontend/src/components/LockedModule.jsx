/**
 * Locked Module Component
 * Displays a dimmed/locked UI for disabled tenant modules
 */

import React from 'react';
import './LockedModule.css';

const LockedModule = ({ 
  moduleName, 
  moduleDescription,
  icon = '🔒',
  upgradeText = 'Upgrade to unlock this feature',
  onUpgradeClick 
}) => {
  return (
    <div className="locked-module-overlay">
      <div className="locked-module-content">
        <div className="locked-icon">{icon}</div>
        <h3 className="locked-title">{moduleName}</h3>
        {moduleDescription && (
          <p className="locked-description">{moduleDescription}</p>
        )}
        <p className="locked-message">{upgradeText}</p>
        {onUpgradeClick && (
          <button 
            className="btn-upgrade"
            onClick={onUpgradeClick}
          >
            Upgrade Now
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Module Wrapper Component
 * Conditionally renders content or locked state based on module access
 */
export const ModuleWrapper = ({ 
  moduleName,
  moduleKey,
  isEnabled,
  children,
  fallback
}) => {
  if (isEnabled) {
    return children;
  }

  if (fallback) {
    return fallback;
  }

  return (
    <LockedModule 
      moduleName={moduleName}
      moduleDescription={`The ${moduleName} module is not enabled for your account.`}
    />
  );
};

/**
 * Module Card Component with Lock State
 * Shows a card that can be in locked or unlocked state
 */
export const ModuleCard = ({
  title,
  description,
  icon,
  isLocked,
  onClick,
  href
}) => {
  const handleClick = () => {
    if (!isLocked && onClick) {
      onClick();
    }
  };

  const cardContent = (
    <>
      <div className="module-card-icon">{icon}</div>
      <h3 className="module-card-title">{title}</h3>
      <p className="module-card-description">{description}</p>
      {isLocked && <div className="module-card-lock">🔒</div>}
    </>
  );

  const className = `module-card ${isLocked ? 'locked' : ''}`;

  if (href && !isLocked) {
    return (
      <a href={href} className={className}>
        {cardContent}
      </a>
    );
  }

  return (
    <div 
      className={className}
      onClick={handleClick}
      style={{ cursor: isLocked ? 'not-allowed' : onClick ? 'pointer' : 'default' }}
    >
      {cardContent}
      {isLocked && (
        <div className="module-card-tooltip">
          Upgrade to unlock this feature
        </div>
      )}
    </div>
  );
};

export default LockedModule;
