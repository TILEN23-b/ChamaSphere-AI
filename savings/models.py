# Create your models here.

import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.core.validators import MinValueValidator


class SavingsAccount(models.Model):
    """
    One savings account per member.

    The transaction ledger is the source of truth for the balance.
    """

    member = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="savings_account",
    )

    account_number = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            # UUID-based account number; retry on the extremely
            # unlikely chance of a collision.
            while True:
                candidate = "GS-SAV-" + uuid.uuid4().hex[:12].upper()
                if not SavingsAccount.objects.filter(
                    account_number=candidate
                ).exists():
                    self.account_number = candidate
                    break

        super().save(*args, **kwargs)

    @property
    def balance(self):
        """
        Calculate the posted balance from ledger entries.

        Deposits add to the balance; withdrawals subtract from it.
        """
        totals = self.transactions.filter(
            status=SavingsTransaction.Status.POSTED
        ).aggregate(
            deposits=Sum(
                "amount",
                filter=Q(
                    transaction_type=SavingsTransaction.Type.DEPOSIT
                ),
            ),
            withdrawals=Sum(
                "amount",
                filter=Q(
                    transaction_type=SavingsTransaction.Type.WITHDRAWAL
                ),
            ),
        )

        deposits = totals["deposits"] or Decimal("0.00")
        withdrawals = totals["withdrawals"] or Decimal("0.00")

        return deposits - withdrawals

    def __str__(self):
        return f"{self.account_number} - {self.member}"


class SavingsTransaction(models.Model):
    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"

    class Status(models.TextChoices):
        POSTED = "posted", "Posted"
        REVERSED = "reversed", "Reversed"

    account = models.ForeignKey(
        SavingsAccount,
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=12,
        choices=Type.choices,
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

    description = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.POSTED,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_savings_transactions",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="savings_transaction_amount_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["account", "-created_at"],
                name="sav_acct_created_idx",
            ),
            models.Index(
                fields=["status", "transaction_type"],
                name="sav_status_type_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.get_transaction_type_display()} "
            f"{self.amount} - {self.reference}"
        )