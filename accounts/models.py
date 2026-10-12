
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)

    member_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    national_id = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )

    MEMBER_TYPES = (
        ("regular", "Regular Member"),
        ("corporate", "Corporate Member"),
    )

    member_type = models.CharField(
        max_length=20,
        choices=MEMBER_TYPES,
        default="regular",
    )

    SACCO_ROLES = (
        ("member", "Regular Member"),
        ("chairman", "Chairman"),
        ("secretary", "Secretary"),
        ("treasurer", "Treasurer"),
        ("savings_officer", "Savings Officer"),
        ("system_admin", "System Administrator"),
    )

    sacco_role = models.CharField(
        max_length=30,
        choices=SACCO_ROLES,
        default="member",
        help_text="The person's official role within GreenSACCO.",
    )

    is_member = models.BooleanField(default=True)

    is_staff_member = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.member_number:
            from django.utils.crypto import get_random_string

            prefix = "GS"

            while True:
                candidate = prefix + get_random_string(
                    8,
                    allowed_chars="0123456789",
                )

                if not User.objects.filter(
                    member_number=candidate
                ).exists():
                    self.member_number = candidate
                    break

        super().save(*args, **kwargs)

    def __str__(self):
        return self.email