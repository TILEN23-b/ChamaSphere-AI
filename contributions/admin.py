
from django.contrib import admin

from .models import (
    ContributionCampaign,
    ContributionCategory,
    ContributionObligation,
    ContributionTransaction,
)


@admin.register(ContributionCategory)
class ContributionCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_by", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    exclude = ("created_by",)
    readonly_fields = ("created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContributionCampaign)
class ContributionCampaignAdmin(admin.ModelAdmin):
    list_display = (
        "title", "category", "amount_per_member",
        "deadline", "status", "created_by", "created_at",
    )
    list_filter = ("status", "category", "deadline")
    search_fields = ("title", "description")
    readonly_fields = ("created_at", "updated_at")
    exclude = ("created_by",)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContributionObligation)
class ContributionObligationAdmin(admin.ModelAdmin):
    list_display = ("campaign", "member", "amount_due", "created_at")
    list_filter = ("campaign",)
    search_fields = (
        "campaign__title",
        "member__member_number",
        "member__first_name",
        "member__last_name",
        "member__email",
    )
    readonly_fields = ("created_at",)


@admin.register(ContributionTransaction)
class ContributionTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "member", "campaign", "category", "amount",
        "payment_method", "external_reference", "status",
        "created_by", "created_at",
    )
    list_filter = ("status", "payment_method", "category", "created_at")
    search_fields = (
        "reference",
        "member__member_number",
        "member__first_name",
        "member__last_name",
        "member__email",
        "external_reference",
        "campaign__title",
    )
    readonly_fields = ("reference", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
