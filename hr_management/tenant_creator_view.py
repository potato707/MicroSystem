"""
Tenant Creator View - Custom page for creating new tenants
"""
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_http_methods
from .tenant_models import ModuleDefinition


@staff_member_required
@require_http_methods(["GET"])
def tenant_creator_view(request):
    """
    Display the tenant creator page.
    Only accessible to staff members.
    """
    # Get all available modules
    modules = ModuleDefinition.objects.all().order_by('sort_order')
    
    context = {
        'modules': modules
    }
    
    return render(request, 'tenant_creator.html', context)
