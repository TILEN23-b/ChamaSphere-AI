# Register your models here.
from django.contrib import admin

from .models import SavingsAccount, SavingsTransaction


@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    list_display = (
        "account_number",
        "member",
        "is_active",
        "created_at",
    )
    search_fields = (
        "account_number",
        "member__email",
        "member__member_number",
    )
    list_filter = ("is_active",)
    readonly_fields = (
        "account_number",
        "created_at",
        "updated_at",
    )


@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "account",
        "transaction_type",
        "amount",
        "status",
        "created_by",
        "created_at",
    )
    search_fields = (
        "reference",
        "account__account_number",
        "account__member__email",
    )
    list_filter = ("transaction_type", "status", "created_at")
    readonly_fields = (
        "reference",
        "account",
        "transaction_type",
        "amount",
        "description",
        "status",
        "created_by",
        "created_at",
    )

    def has_add_permission(self, request):
        # Transactions must be created through the controlled
        # transaction service, not manually in the admin.
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent financial ledger entries being edited in admin.
        return False

    def has_delete_permission(self, request, obj=None):
        # Preserve the audit trail.
        return False