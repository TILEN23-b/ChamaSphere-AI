
from django.conf import settings
from django.db import models


class Meeting(models.Model):
    class MeetingType(models.TextChoices):
        ANNUAL_GENERAL = "AGM", "Annual General Meeting"
        SPECIAL_GENERAL = "SGM", "Special General Meeting"
        BOARD = "BOARD", "Board Meeting"
        COMMITTEE = "COMMITTEE", "Committee Meeting"
        OTHER = "OTHER", "Other Meeting"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    title = models.CharField(max_length=200)

    meeting_type = models.CharField(
        max_length=20,
        choices=MeetingType.choices,
        default=MeetingType.OTHER,
    )

    meeting_date = models.DateTimeField()
    venue = models.CharField(max_length=255)

    agenda = models.TextField(
        blank=True,
        help_text="Topics planned for discussion.",
    )

    minutes = models.TextField(
        blank=True,
        help_text="Official record of discussions and decisions.",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_meetings",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-meeting_date"]
        verbose_name = "SACCO meeting"
        verbose_name_plural = "SACCO meetings"

    def __str__(self):
        return f"{self.title} - {self.meeting_date:%d %b %Y}"


class MeetingAttendance(models.Model):
    class AttendanceStatus(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        EXCUSED = "EXCUSED", "Excused"

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="meeting_attendance_records",
        limit_choices_to={"is_member": True},
    )

    status = models.CharField(
        max_length=10,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT,
    )

    remarks = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional explanation or attendance note.",
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_attendance_records",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["member__last_name", "member__first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "member"],
                name="unique_member_attendance_per_meeting",
            )
        ]
        verbose_name = "Meeting attendance record"
        verbose_name_plural = "Meeting attendance records"

    def __str__(self):
        return (
            f"{self.member} - {self.meeting.title} "
            f"({self.get_status_display()})"
        )
