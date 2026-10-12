from django.core.exceptions import PermissionDenied


# ---------------------------------------------------------
# 1. CHECK A USER'S SACCO ROLE
# ---------------------------------------------------------

def is_sacco_role(user, *roles):
    """
    Return True when an authenticated user has one of
    the specified SACCO roles.

    Django superusers are treated as authorized by this
    helper, but SACCO roles do not grant Django superuser
    privileges.
    """
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or getattr(user, "sacco_role", None) in roles
        )
    )


def require_sacco_role(user, *roles):
    """
    Raise PermissionDenied when a user lacks the
    required SACCO role.
    """
    if not is_sacco_role(user, *roles):
        raise PermissionDenied(
            "You do not have permission to perform this action."
        )


# ---------------------------------------------------------
# 2. SAVINGS TRANSACTION PERMISSIONS
# ---------------------------------------------------------

def can_post_savings(user):
    """
    Check whether a user can post savings deposits
    and withdrawals.

    Legacy staff access is retained for compatibility.
    A future security step can remove these legacy
    permissions after existing staff accounts are reviewed.
    """
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.is_staff
            or getattr(user, "is_staff_member", False)
            or getattr(user, "sacco_role", None) == "savings_officer"
        )
    )


# ---------------------------------------------------------
# 3. GOVERNANCE AND OVERSIGHT PERMISSIONS
# ---------------------------------------------------------

def can_view_governance_reports(user):
    """
    Chairman and Django superusers may view governance
    and oversight reports.
    """
    return is_sacco_role(user, "chairman")


# ---------------------------------------------------------
# 4. MEETING AND ADMINISTRATIVE RECORDS
# ---------------------------------------------------------

def can_manage_meeting_records(user):
    """
    Secretary and Django superusers may manage meeting
    and administrative records.
    """
    return is_sacco_role(user, "secretary")


# ---------------------------------------------------------
# 5. FINANCIAL REPORTS
# ---------------------------------------------------------

def can_view_financial_reports(user):
    """
    Treasurer, Chairman and Django superusers may view
    financial reports.

    This permission does not authorize posting transactions.
    """
    return is_sacco_role(user, "treasurer", "chairman")


# ---------------------------------------------------------
# 6. TECHNICAL USER ADMINISTRATION
# ---------------------------------------------------------

def can_manage_system_users(user):
    """
    Only Django superusers or users who already possess
    Django's staff status and the appropriate Django
    user-management permissions may manage system users.

    The system_admin SACCO role alone does not grant
    Django admin access.
    """
    if not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    if not user.is_staff:
        return False

    return (
        user.has_perm("accounts.view_user")
        or user.has_perm("accounts.add_user")
        or user.has_perm("accounts.change_user")
        or user.has_perm("accounts.delete_user")
    )