from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model

from .models import SavingsTransaction

User = get_user_model()


class ActiveMemberChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, member):
        full_name = member.get_full_name().strip()

        if not full_name:
            full_name = member.username or member.email

        return f"{full_name} — {member.member_number or 'No member number'}"


class StaffSavingsTransactionForm(forms.Form):
    member = ActiveMemberChoiceField(
        queryset=User.objects.none(),
        label="Find member",
        empty_label="Search and select a member",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_member",
                "required": True,
            }
        ),
    )

    transaction_type = forms.ChoiceField(
        choices=SavingsTransaction.Type.choices,
        label="Transaction type",
        widget=forms.Select(
            attrs={"class": "form-select"},
        ),
    )

    amount = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal("0.01"),
        label="Amount (KES)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0.01",
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )

    description = forms.CharField(
        max_length=255,
        required=False,
        label="Description / payment reference",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Confirmed payment reference",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["member"].queryset = (
            User.objects.filter(
                is_member=True,
                is_active=True,
            )
            .order_by("first_name", "last_name", "member_number")
        )
