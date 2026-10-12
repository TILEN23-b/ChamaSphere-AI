from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db import models


class EmailOrMemberNumberBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        identifier = (username or kwargs.get("email") or "").strip()

        if not identifier or not password:
            return None

        user = User.objects.filter(
            models.Q(email__iexact=identifier) |
            models.Q(member_number__iexact=identifier)
        ).first()

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
