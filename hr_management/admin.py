from django.contrib import admin
from .models import *

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'department', 'status', 'hire_date']
    list_filter = ['status', 'department', 'hire_date']
    search_fields = ['name', 'english_name']
    ordering = ['name']

@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ['employee', 'document_type', 'title', 'upload_date']
    list_filter = ['document_type', 'upload_date']
    search_fields = ['employee__name', 'title']

@admin.register(EmployeeNote)
class EmployeeNoteAdmin(admin.ModelAdmin):
    list_display = ['employee', 'created_by', 'created_date']
    list_filter = ['created_date']
    search_fields = ['employee__name', 'note']

