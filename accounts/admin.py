
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        "username",
        "email",
        "member_number",
        "sacco_role",
        "is_member",
        "is_staff_member",
        "is_staff",
        "is_active",
    )

    list_filter = (
        "sacco_role",
        "member_type",
        "is_member",
        "is_staff_member",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "member_number",
        "phone_number",
        "national_id",
    )

    ordering = ("email",)

    # Display generated member numbers without allowing edits.
    readonly_fields = ("member_number", "created_at", "updated_at")

    fieldsets = UserAdmin.fieldsets + (
        (
            "GreenSACCO Information",
            {
                "fields": (
                    "member_number",
                    "phone_number",
                    "national_id",
                    "member_type",
                    "sacco_role",
                    "is_member",
                    "is_staff_member",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "GreenSACCO Information",
            {
                "fields": (
                    "email",
                    "phone_number",
                    "national_id",
                    "member_type",
                    "sacco_role",
                    "is_member",
                    "is_staff_member",
                )
            },
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Member numbers and timestamps are read-only on existing users.
        On the add form, these generated fields are omitted.
        """
        if obj is None:
            return tuple(
                field
                for field in self.readonly_fields
                if field not in ("member_number", "created_at", "updated_at")
            )

        return self.readonly_fields
