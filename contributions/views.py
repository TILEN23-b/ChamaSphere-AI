
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ContributionCampaignForm, ContributionPaymentForm
from .models import (
    ContributionCampaign,
    ContributionObligation,
    ContributionTransaction,
)
from .permissions import (
    can_manage_contributions,
    can_record_contribution_payment,
)
from .services import post_contribution


User = get_user_model()


def _paid_amount(campaign, member):
    return (
        ContributionTransaction.objects.filter(
            campaign=campaign,
            member=member,
            status=ContributionTransaction.Status.POSTED,
        ).aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )


@login_required
def campaign_list(request):
    if can_manage_contributions(request.user):
        campaigns = ContributionCampaign.objects.all()
    else:
        campaigns = ContributionCampaign.objects.filter(
            status=ContributionCampaign.Status.ACTIVE,
            obligations__member=request.user,
        ).distinct()

    return render(
        request,
        "contributions/campaign_list.html",
        {"campaigns": campaigns},
    )


@login_required
def campaign_create(request):
    if not can_manage_contributions(request.user):
        raise PermissionDenied(
            "You are not authorized to create contribution campaigns."
        )

    form = ContributionCampaignForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        campaign = form.save(commit=False)
        campaign.created_by = request.user
        campaign.status = ContributionCampaign.Status.DRAFT
        campaign.save()

        messages.success(
            request,
            "Campaign created as a draft. Review it before activation.",
        )
        return redirect("contributions:campaign_detail", pk=campaign.pk)

    return render(
        request,
        "contributions/campaign_form.html",
        {"form": form},
    )


@login_required
def campaign_detail(request, pk):
    campaign = get_object_or_404(ContributionCampaign, pk=pk)

    if not can_manage_contributions(request.user):
        if (
            campaign.status != ContributionCampaign.Status.ACTIVE
            or not campaign.obligations.filter(
                member=request.user
            ).exists()
        ):
            raise PermissionDenied(
                "You are not allowed to view this campaign."
            )

        obligation = get_object_or_404(
            ContributionObligation,
            campaign=campaign,
            member=request.user,
        )
        paid = _paid_amount(campaign, request.user)

        if paid >= obligation.amount_due:
            payment_status = "Paid"
        elif paid > 0:
            payment_status = "Partially Paid"
        else:
            payment_status = "Unpaid"

        return render(
            request,
            "contributions/member_campaign_detail.html",
            {
                "campaign": campaign,
                "obligation": obligation,
                "paid": paid,
                "outstanding": max(
                    obligation.amount_due - paid, Decimal("0.00")
                ),
                "payment_status": payment_status,
            },
        )

    obligations = campaign.obligations.select_related("member").all()
    rows = []

    for obligation in obligations:
        paid = _paid_amount(campaign, obligation.member)
        outstanding = max(obligation.amount_due - paid, Decimal("0.00"))

        if paid >= obligation.amount_due:
            status = "Paid"
        elif paid > 0:
            status = "Partially Paid"
        else:
            status = "Unpaid"

        rows.append({
            "obligation": obligation,
            "paid": paid,
            "outstanding": outstanding,
            "status": status,
        })

    total_due = sum(
        (row["obligation"].amount_due for row in rows),
        Decimal("0.00"),
    )
    total_paid = sum(
        (row["paid"] for row in rows),
        Decimal("0.00"),
    )

    return render(
        request,
        "contributions/campaign_detail.html",
        {
            "campaign": campaign,
            "rows": rows,
            "total_due": total_due,
            "total_paid": total_paid,
            "total_outstanding": max(
                total_due - total_paid, Decimal("0.00")
            ),
            "can_manage": can_manage_contributions(request.user),
        },
    )


@login_required
def campaign_activate(request, pk):
    if not can_manage_contributions(request.user):
        raise PermissionDenied(
            "You are not authorized to activate campaigns."
        )

    if request.method != "POST":
        raise PermissionDenied("Campaign activation requires a POST request.")

    with transaction.atomic():
        campaign = get_object_or_404(
            ContributionCampaign.objects.select_for_update(),
            pk=pk,
        )

        if campaign.status != ContributionCampaign.Status.DRAFT:
            messages.error(
                request,
                "Only draft campaigns can be activated.",
            )
            return redirect("contributions:campaign_detail", pk=pk)

        members = User.objects.filter(
            is_member=True,
            is_active=True,
        )

        if not members.exists():
            messages.error(
                request,
                "There are no active SACCO members to assign.",
            )
            return redirect("contributions:campaign_detail", pk=pk)

        ContributionObligation.objects.bulk_create(
            [
                ContributionObligation(
                    campaign=campaign,
                    member=member,
                    amount_due=campaign.amount_per_member,
                )
                for member in members
            ],
            ignore_conflicts=True,
        )

        campaign.status = ContributionCampaign.Status.ACTIVE
        campaign.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        "Campaign activated and member obligations created.",
    )
    return redirect("contributions:campaign_detail", pk=pk)


@login_required
def member_contributions(request):
    obligations = (
        ContributionObligation.objects
        .filter(
            member=request.user,
            campaign__status=ContributionCampaign.Status.ACTIVE,
        )
        .select_related("campaign", "campaign__category")
        .order_by("campaign__deadline", "campaign__title")
    )

    rows = []
    for obligation in obligations:
        paid = _paid_amount(obligation.campaign, request.user)
        rows.append({
            "obligation": obligation,
            "paid": paid,
            "outstanding": max(
                obligation.amount_due - paid, Decimal("0.00")
            ),
            "status": (
                "Paid" if paid >= obligation.amount_due
                else "Partially Paid" if paid > 0
                else "Unpaid"
            ),
        })

    return render(
        request,
        "contributions/member_portal.html",
        {"rows": rows},
    )

@login_required
def member_campaign_detail(request, pk):
    campaign = get_object_or_404(
        ContributionCampaign,
        pk=pk,
        status=ContributionCampaign.Status.ACTIVE,
    )

    obligation = get_object_or_404(
        ContributionObligation,
        campaign=campaign,
        member=request.user,
    )

    paid = _paid_amount(campaign, request.user)
    outstanding = max(
        obligation.amount_due - paid,
        Decimal("0.00"),
    )

    if paid >= obligation.amount_due:
        payment_status = "Paid"
    elif paid > 0:
        payment_status = "Partially Paid"
    else:
        payment_status = "Unpaid"

    return render(
        request,
        "contributions/member_campaign_detail.html",
        {
            "campaign": campaign,
            "obligation": obligation,
            "paid": paid,
            "outstanding": outstanding,
            "payment_status": payment_status,
        },
    )


@login_required
def staff_record_payment(request):
    if not can_record_contribution_payment(request.user):
        raise PermissionDenied(
            "You are not authorized to record contribution payments."
        )

    form = ContributionPaymentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        campaign = form.cleaned_data["campaign"]

        try:
            payment = post_contribution(
                member_id=form.cleaned_data["member"].pk,
                category_id=campaign.category_id,
                campaign_id=campaign.pk,
                amount=form.cleaned_data["amount"],
                actor=request.user,
                payment_method=form.cleaned_data["payment_method"],
                external_reference=form.cleaned_data["external_reference"],
                description=form.cleaned_data["description"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(
                request,
                f"Payment recorded. Internal reference: {payment.reference}",
            )
            return redirect(
                "contributions:campaign_detail",
                pk=campaign.pk,
            )

    return render(
        request,
        "contributions/payment_form.html",
        {"form": form},
    )


@login_required
def mpesa_payment_placeholder(request, pk):
    campaign = get_object_or_404(
        ContributionCampaign,
        pk=pk,
        status=ContributionCampaign.Status.ACTIVE,
    )

    obligation = get_object_or_404(
        ContributionObligation,
        campaign=campaign,
        member=request.user,
    )

    paid = _paid_amount(campaign, request.user)
    outstanding = max(obligation.amount_due - paid, Decimal("0.00"))

    if request.method != "POST":
        return redirect("contributions:member_portal")

    if outstanding <= 0:
        messages.info(request, "This contribution is already fully paid.")
    else:
        messages.info(
            request,
            "M-Pesa payments are not connected yet. No payment has been "
            "initiated or recorded. Please try again after integration.",
        )

    return redirect("contributions:member_campaign_detail", pk=campaign.pk)
