from .models import SystemAuditEvent


def audit(request, action, *, obj=None, description=""):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get("REMOTE_ADDR")
    # Only trust X-Forwarded-For when the deployment proxy is configured to sanitize it.
    SystemAuditEvent.objects.create(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        object_type=obj.__class__.__name__ if obj is not None else "",
        object_id=str(obj.pk) if obj is not None and obj.pk else "",
        description=description[:4000],
        ip_address=ip or None,
    )
