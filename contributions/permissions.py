
from accounts.permissions import can_post_savings


def can_manage_contributions(user):
    if not user.is_authenticated:
        return False

    if user.is_superuser or user.is_staff:
        return True

    role = getattr(user, "sacco_role", None)

    return (
        getattr(user, "is_staff_member", False)
        or role in {
            "chairman",
            "secretary",
            "treasurer",
            "savings_officer",
            "system_admin",
        }
    )


def can_record_contribution_payment(user):
    return can_manage_contributions(user) and can_post_savings(user)
