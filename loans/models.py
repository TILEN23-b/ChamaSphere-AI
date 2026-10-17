# Create your models here.

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class LoanProduct(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    savings_multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("2.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    annual_interest_rate = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    min_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    max_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    max_months = models.PositiveIntegerField()
    guarantors_required = models.BooleanField(default=False)
    minimum_guarantors = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_loan_products",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_amount__gte=models.F("min_amount")),
                name="loan_product_max_gte_min",
            ),
            models.CheckConstraint(
                condition=models.Q(max_months__gt=0),
                name="loan_product_months_positive",
            ),
        ]

    def __str__(self):
        return self.name


class LoanApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loan_applications",
        limit_choices_to={"is_member": True},
    )

    product = models.ForeignKey(
        LoanProduct,
        on_delete=models.PROTECT,
        related_name="applications",
    )

    requested_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    requested_months = models.PositiveIntegerField()

    purpose = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        db_index=True,
    )

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(
                fields=["member", "status"],
                name="loan_app_member_status_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.member} - {self.product} "
            f"({self.requested_amount})"
        )

class LoanAssessment(models.Model):
    application = models.ForeignKey(
        LoanApplication,
        on_delete=models.PROTECT,
        related_name="assessments",
    )

    eligible_savings = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    savings_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    capacity_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    available_funds_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    product_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    recommended_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    eligible = models.BooleanField(default=False)

    reasons = models.JSONField(default=list, blank=True)

    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loan_assessments_performed",
    )

    assessed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assessed_at"]
        indexes = [
            models.Index(
                fields=["application", "-assessed_at"],
                name="loan_assess_app_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Assessment for application "
            f"#{self.application_id} - "
            f"{self.recommended_amount}"
        )

class LoanApprovalRule(models.Model):
    name = models.CharField(max_length=100, unique=True)

    min_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    max_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    required_roles = models.JSONField(default=list)

    minimum_approvals = models.PositiveSmallIntegerField(default=2)

    active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_loan_approval_rules",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["min_amount"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_amount__gte=models.F("min_amount")),
                name="loan_rule_max_gte_min",
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_approvals__gt=0),
                name="loan_rule_min_approvals_positive",
            ),
        ]

    def __str__(self):
        return self.name


class LoanDecision(models.Model):
    class DecisionType(models.TextChoices):
        APPROVE = "approve", "Approve"
        REJECT = "reject", "Reject"
        ABSTAIN = "abstain", "Abstain"

    application = models.ForeignKey(
        LoanApplication,
        on_delete=models.PROTECT,
        related_name="decisions",
    )

    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loan_decisions",
    )

    decision = models.CharField(
        max_length=10,
        choices=DecisionType.choices,
    )

    comments = models.TextField(blank=True)

    decided_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["decided_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "officer"],
                name="uniq_loan_decision_officer",
            ),
        ]

    def __str__(self):
        return (
            f"{self.officer} - {self.application_id} "
            f"- {self.get_decision_display()}"
        )

class OfficerAssignment(models.Model):
    class OfficerRole(models.TextChoices):
        CHAIRMAN = "chairman", "Chairman"
        TREASURER = "treasurer", "Treasurer"
        SAVINGS_OFFICER = "savings_officer", "Savings Officer"
        LOAN_OFFICER = "loan_officer", "Loan Officer"
        COMMITTEE_MEMBER = "committee_member", "Loan Committee Member"

    officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loan_officer_assignments",
    )

    role = models.CharField(
        max_length=30,
        choices=OfficerRole.choices,
    )

    is_active = models.BooleanField(default=True)

    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="loan_assignments_made",
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["officer__last_name", "officer__first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["officer", "role"],
                condition=models.Q(is_active=True),
                name="uniq_active_loan_officer_role",
            ),
        ]

    def __str__(self):
        return f"{self.officer} - {self.get_role_display()}"
