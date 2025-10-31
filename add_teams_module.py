#!/usr/bin/env python
"""
Script to add Teams module to ModuleDefinition table
Run this on the production server
"""
import os
import sys
import django

# Add the project directory to the sys.path
sys.path.insert(0, '/root/saas/MicroSystem')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.tenant_models import ModuleDefinition

def add_teams_module():
    """Add Teams module to ModuleDefinition"""
    
    teams_module = {
        'module_key': 'teams',
        'module_name': 'Team Management',
        'description': 'Create and manage teams and team members',
        'icon': 'users-cog',
        'is_core': False,
        'sort_order': 6
    }
    
    module, created = ModuleDefinition.objects.get_or_create(
        module_key=teams_module['module_key'],
        defaults=teams_module
    )
    
    if created:
        print(f"✓ Created Teams module: {module.module_name}")
    else:
        print(f"✓ Teams module already exists: {module.module_name}")
    
    # List all modules
    print("\nAll available modules:")
    print("-" * 50)
    for mod in ModuleDefinition.objects.all().order_by('sort_order'):
        status = "✓ Core" if mod.is_core else "  "
        print(f"{status} [{mod.sort_order}] {mod.module_name} ({mod.module_key})")
    
    return module

if __name__ == '__main__':
    try:
        add_teams_module()
        print("\n✓ Teams module added successfully!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
