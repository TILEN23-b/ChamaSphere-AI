# Create your models here.

import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models import F, Q
from django.db.models.functions import Lower


class ContributionCategory(models.Model):
    """
    Defines a purpose for collecting member contributions.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_contribution_categories",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Contribution category"
        verbose_name_plural = "Contribution categories"

    def __str__(self):
        return self.name

class ContributionCampaign(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=150)
    category = models.ForeignKey(
        ContributionCategory,
        on_delete=models.PROTECT,
        related_name="campaigns",
    )
    description = models.TextField()
    amount_per_member = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_contribution_campaigns",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount_per_member__gt=0),
                name="campaign_amount_per_member_positive",
            ),
        ]

    def __str__(self):
        return self.title


class ContributionTransaction(models.Model):
    """
    Records a member contribution in the contribution ledger.
    """

    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        REVERSED = "reversed", "Reversed"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        MOBILE_MONEY = "mobile_money", "Mobile Money"
        BANK = "bank", "Bank Transfer"
        OTHER = "other", "Other"

    category = models.ForeignKey(
        ContributionCategory,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    
    campaign = models.ForeignKey(
        ContributionCampaign,
        on_delete=models.PROTECT,
        related_name="transactions",
        null=True,
        blank=True,
    )


    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contribution_transactions",
        limit_choices_to={"is_member": True},
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    reference = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.OTHER,
    )

    external_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional receipt, bank, or mobile-money reference.",
    )

    description = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.POSTED,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_contribution_transactions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="contribution_amount_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["member", "-created_at"],
                name="cont_member_created_idx",
            ),
            models.Index(
                fields=["category", "status"],
                name="cont_category_status_idx",
            ),
        ]
        models.UniqueConstraint(
    Lower("external_reference"),
    F("payment_method"),
    condition=~Q(external_reference=""),
    name="uniq_contrib_external_ref_method_ci",
),

    def __str__(self):
        return (
            f"{self.category.name}: {self.amount} "
            f"- {self.member} ({self.reference})"
        )
class ContributionObligation(models.Model):
    """
    Tracks the amount a member is expected to contribute
    toward a specific campaign.
    """

    campaign = models.ForeignKey(
        ContributionCampaign,
        on_delete=models.PROTECT,
        related_name="obligations",
    )

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="contribution_obligations",
        limit_choices_to={"is_member": True},
    )

    amount_due = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["campaign", "member"],
                name="unique_campaign_member_obligation",
            ),
            models.CheckConstraint(
                condition=Q(amount_due__gt=0),
                name="obligation_amount_due_positive",
            ),
        ]

    def __str__(self):
        return (
            f"{self.campaign.title} - {self.member}: "
            f"{self.amount_due}"
        )