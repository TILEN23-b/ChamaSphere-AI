# Register your models here.
from django.contrib import admin
from .models import Meeting
from .models import Meeting, MeetingAttendance


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "meeting_type",
        "meeting_date",
        "venue",
        "status",
        "recorded_by",
        "created_at",
    )

    list_filter = (
        "meeting_type",
        "status",
        "meeting_date",
    )

    search_fields = (
        "title",
        "venue",
        "agenda",
        "minutes",
        "recorded_by__username",
        "recorded_by__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    date_hierarchy = "meeting_date"
    ordering = ("-meeting_date",)

    fieldsets = (
        ("Meeting Information", {
            "fields": (
                "title",
                "meeting_type",
                "meeting_date",
                "venue",
                "status",
            )
        }),
        ("Agenda and Minutes", {
            "fields": (
                "agenda",
                "minutes",
            )
        }),
        ("Record Details", {
            "fields": (
                "recorded_by",
                "created_at",
                "updated_at",
            )
        }),
    )

@admin.register(MeetingAttendance)
class MeetingAttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "meeting",
        "member",
        "status",
        "recorded_by",
        "updated_at",
    )
    list_filter = ("status", "meeting__meeting_type")
    search_fields = (
        "meeting__title",
        "member__first_name",
        "member__last_name",
        "member__member_number",
        "member__email",
    )
    readonly_fields = ("created_at", "updated_at")
