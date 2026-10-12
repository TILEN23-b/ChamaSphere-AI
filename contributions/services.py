
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import (
    ContributionCampaign,
    ContributionObligation,
    ContributionTransaction,
)
from .permissions import can_record_contribution_payment


@transaction.atomic
def post_contribution(
    *,
    member_id,
    category_id,
    amount,
    actor,
    campaign_id=None,
    payment_method=ContributionTransaction.PaymentMethod.OTHER,
    external_reference="",
    description="",
):
    if not can_record_contribution_payment(actor):
        raise PermissionDenied(
            "You are not authorized to record contribution payments."
        )

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("Enter a valid contribution amount.")

    if not amount.is_finite() or amount <= Decimal("0.00"):
        raise ValidationError("The amount must be greater than zero.")

    if amount.as_tuple().exponent < -2:
        raise ValidationError(
            "The amount cannot have more than two decimal places."
        )

    allowed_methods = {
        choice[0]
        for choice in ContributionTransaction.PaymentMethod.choices
    }
    if payment_method not in allowed_methods:
        raise ValidationError("Select a valid payment method.")

    reference_text = (external_reference or "").strip()

    if reference_text:
        duplicate = ContributionTransaction.objects.filter(
            payment_method=payment_method,
            external_reference__iexact=reference_text,
        ).exists()

        if duplicate:
            raise ValidationError(
                "This payment reference has already been recorded "
                "for this payment method."
            )

    campaign = None
    if campaign_id is not None:
        campaign = (
            ContributionCampaign.objects
            .select_for_update()
            .filter(
                pk=campaign_id,
                status=ContributionCampaign.Status.ACTIVE,
            )
            .first()
        )
        if campaign is None:
            raise ValidationError(
                "The campaign does not exist or is not active."
            )

        if campaign.category_id != category_id:
            raise ValidationError(
                "The payment category does not match the campaign."
            )

    from django.contrib.auth import get_user_model

    User = get_user_model()
    member = User.objects.filter(pk=member_id, is_member=True).first()

    if member is None:
        raise ValidationError("The selected SACCO member was not found.")

    if campaign is not None:
        obligation = (
            ContributionObligation.objects
            .select_for_update()
            .filter(campaign=campaign, member=member)
            .first()
        )

        if obligation is None:
            raise ValidationError(
                "This member does not have an obligation for this campaign."
            )

        already_paid = (
            ContributionTransaction.objects.filter(
                campaign=campaign,
                member=member,
                status=ContributionTransaction.Status.POSTED,
            ).aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

        outstanding = obligation.amount_due - already_paid

        if outstanding <= Decimal("0.00"):
            raise ValidationError("This member has already paid in full.")

        if amount > outstanding:
            raise ValidationError(
                f"The amount exceeds the outstanding balance of "
                f"KSh {outstanding:.2f}."
            )

    return ContributionTransaction.objects.create(
        member=member,
        category_id=category_id,
        campaign=campaign,
        amount=amount,
        payment_method=payment_method,
        external_reference=reference_text[:100],
        description=(description or "").strip()[:255],
        created_by=actor,
        status=ContributionTransaction.Status.POSTED,
    )
