from django.core.exceptions import PermissionDenied


def can_manage_system(user):
    """Restrict administrative functions to superusers or active system admins.

    Keep this check on the server. Template visibility alone is not security.
    """
    return bool(
        user.is_authenticated
        and user.is_active
        and (user.is_superuser or (user.is_staff and getattr(user, "sacco_role", None) == "system_admin"))
    )


def require_system_management(user):
    if not can_manage_system(user):
        raise PermissionDenied("You are not authorized to manage GreenSACCO system settings.")
