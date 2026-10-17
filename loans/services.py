
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from .models import (
    LoanApplication,
    LoanApprovalRule,
    LoanDecision,
    OfficerAssignment,
)


@transaction.atomic
def record_loan_decision(
    *,
    application_id,
    officer,
    decision,
    comments="",
):
    try:
        application = (
            LoanApplication.objects
            .select_for_update()
            .get(pk=application_id)
        )
    except LoanApplication.DoesNotExist:
        raise ValidationError("Loan application not found.")

    if application.member_id == officer.pk:
        raise PermissionDenied(
            "You cannot make a decision on your own loan application."
        )

    authorized_roles = [
        OfficerAssignment.OfficerRole.CHAIRMAN,
        OfficerAssignment.OfficerRole.TREASURER,
        OfficerAssignment.OfficerRole.LOAN_OFFICER,
        OfficerAssignment.OfficerRole.COMMITTEE_MEMBER,
    ]

    has_authority = OfficerAssignment.objects.filter(
        officer=officer,
        is_active=True,
        role__in=authorized_roles,
    ).exists()

    if not has_authority:
        raise PermissionDenied(
            "You are not authorized to make loan decisions."
        )

    if application.status != LoanApplication.Status.UNDER_REVIEW:
        raise ValidationError(
            "The application must be under review before a decision."
        )

    valid_decisions = [
        choice[0] for choice in LoanDecision.DecisionType.choices
    ]

    if decision not in valid_decisions:
        raise ValidationError("Invalid loan decision.")

    already_decided = LoanDecision.objects.filter(
        application=application,
        officer=officer,
    ).exists()

    if already_decided:
        raise ValidationError(
            "You have already recorded a decision for this application."
        )

    return LoanDecision.objects.create(
        application=application,
        officer=officer,
        decision=decision,
        comments=comments.strip(),
    )


@transaction.atomic
def try_approve_loan_application(*, application_id):
    try:
        application = (
            LoanApplication.objects
            .select_for_update()
            .get(pk=application_id)
        )
    except LoanApplication.DoesNotExist:
        raise ValidationError("Loan application not found.")

    if application.status != LoanApplication.Status.UNDER_REVIEW:
        raise ValidationError(
            "Only applications under review can be approved."
        )

    rules = LoanApprovalRule.objects.filter(
        active=True,
        min_amount__lte=application.requested_amount,
        max_amount__gte=application.requested_amount,
    )

    if rules.count() != 1:
        raise ValidationError(
            "Exactly one active approval rule must match this loan amount."
        )

    rule = rules.get()

    authorized_roles = [
        OfficerAssignment.OfficerRole.CHAIRMAN,
        OfficerAssignment.OfficerRole.TREASURER,
        OfficerAssignment.OfficerRole.LOAN_OFFICER,
        OfficerAssignment.OfficerRole.COMMITTEE_MEMBER,
    ]

    approved_officer_ids = set(
        LoanDecision.objects.filter(
            application=application,
            decision=LoanDecision.DecisionType.APPROVE,
            officer__loan_officer_assignments__is_active=True,
            officer__loan_officer_assignments__role__in=authorized_roles,
        ).values_list("officer_id", flat=True).distinct()
    )

    if len(approved_officer_ids) < rule.minimum_approvals:
        return False

    for required_role in rule.required_roles:
        role_is_represented = OfficerAssignment.objects.filter(
            officer_id__in=approved_officer_ids,
            role=required_role,
            is_active=True,
        ).exists()

        if not role_is_represented:
            return False

    application.status = LoanApplication.Status.APPROVED
    application.save(update_fields=["status", "updated_at"])

    return True
