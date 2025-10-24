-- Add new permission fields to complaint admin permission tables

-- Add fields to hr_management_teamcomplaintadminpermission
ALTER TABLE hr_management_teamcomplaintadminpermission 
ADD COLUMN can_change_status BOOLEAN DEFAULT TRUE;

ALTER TABLE hr_management_teamcomplaintadminpermission 
ADD COLUMN can_delete BOOLEAN DEFAULT FALSE;

ALTER TABLE hr_management_teamcomplaintadminpermission 
ADD COLUMN can_manage_categories BOOLEAN DEFAULT FALSE;

-- Add fields to hr_management_employeecomplaintadminpermission
ALTER TABLE hr_management_employeecomplaintadminpermission 
ADD COLUMN can_change_status BOOLEAN DEFAULT TRUE;

ALTER TABLE hr_management_employeecomplaintadminpermission 
ADD COLUMN can_delete BOOLEAN DEFAULT FALSE;

ALTER TABLE hr_management_employeecomplaintadminpermission 
ADD COLUMN can_manage_categories BOOLEAN DEFAULT FALSE;

-- Update existing records to set can_manage_categories to TRUE for testing
UPDATE hr_management_employeecomplaintadminpermission 
SET can_manage_categories = TRUE 
WHERE is_active = TRUE;

UPDATE hr_management_teamcomplaintadminpermission 
SET can_manage_categories = TRUE 
WHERE is_active = TRUE;
