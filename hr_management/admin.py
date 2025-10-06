from django.contrib import admin
from .models import *

class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0
    fields = ['title', 'status', 'priority', 'estimated_minutes', 'order']
    readonly_fields = ['time_spent', 'is_paused']

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


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'employee', 'status', 'priority', 'date', 'created_at']
    list_filter = ['status', 'priority', 'date', 'assigned_by_manager']
    search_fields = ['title', 'employee__name', 'description']
    ordering = ['-date', 'priority']
    readonly_fields = ['time_spent', 'is_overdue', 'is_paused']
    inlines = [SubtaskInline]

@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent_task', 'status', 'priority', 'created_at']
    list_filter = ['status', 'priority']
    search_fields = ['title', 'parent_task__title', 'parent_task__employee__name']
    ordering = ['parent_task', 'order', 'created_at']
    readonly_fields = ['time_spent', 'is_paused']

