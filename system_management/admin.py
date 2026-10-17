# Register your models here.
from django.contrib import admin
from .models import SACcopolicy, StaffTask, SystemAuditEvent

@admin.register(StaffTask)
class StaffTaskAdmin(admin.ModelAdmin):
    list_display = ("title", "assigned_to", "assigned_by", "priority", "status", "due_date")
    list_filter = ("priority", "status")
    search_fields = ("title", "description", "assigned_to__email")

@admin.register(SACcopolicy)
class SACcopolicyAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "version", "is_active", "effective_date", "review_date")
    list_filter = ("category", "is_active")
    search_fields = ("title", "body")

@admin.register(SystemAuditEvent)
class SystemAuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "object_type", "object_id", "ip_address")
    list_filter = ("action", "object_type")
    search_fields = ("description", "actor__email", "object_id")
    readonly_fields = tuple(field.name for field in SystemAuditEvent._meta.fields)
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
