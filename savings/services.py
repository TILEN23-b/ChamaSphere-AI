from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.permissions import can_post_savings
from .models import SavingsAccount, SavingsTransaction


@transaction.atomic
def post_savings_transaction(
    *,
    account_id,
    transaction_type,
    amount,
    actor,
    description="",
):
    """
    Post a deposit or withdrawal to a savings ledger.

    Only authorized users may post transactions.
    The account row is locked to serialize concurrent operations.
    """

    # Check whether the user is authorized to post savings transactions.
    if not can_post_savings(actor):
        raise PermissionDenied(
            "You are not authorised to post savings transactions."
        )

    # Validate the transaction type.
    if transaction_type not in (
        SavingsTransaction.Type.DEPOSIT,
        SavingsTransaction.Type.WITHDRAWAL,
    ):
        raise ValidationError("Invalid savings transaction type.")

    # Convert the amount safely to Decimal.
    try:
        amount = Decimal(str(amount))
    except (ValueError, TypeError, ArithmeticError):
        raise ValidationError("Enter a valid transaction amount.")

    # Reject NaN, infinity, zero, and negative amounts.
    if not amount.is_finite() or amount <= Decimal("0.00"):
        raise ValidationError(
            "The amount must be greater than zero."
        )

    # Allow a maximum of two decimal places.
    if amount.as_tuple().exponent < -2:
        raise ValidationError(
            "The amount cannot have more than two decimal places."
        )

    # Lock the account row to protect concurrent transactions.
    account = (
        SavingsAccount.objects
        .select_for_update()
        .filter(pk=account_id)
        .first()
    )

    if account is None:
        raise ValidationError("Savings account not found.")

    # Prevent transactions on inactive accounts.
    if not account.is_active:
        raise ValidationError(
            "This savings account is inactive."
        )

    # Prevent withdrawals exceeding the available balance.
    if transaction_type == SavingsTransaction.Type.WITHDRAWAL:
        if account.balance < amount:
            raise ValidationError(
                "Insufficient available savings for this withdrawal."
            )

    # Create the posted transaction.
    return SavingsTransaction.objects.create(
        account=account,
        transaction_type=transaction_type,
        amount=amount,
        description=description.strip(),
        created_by=actor,
        status=SavingsTransaction.Status.POSTED,
    )