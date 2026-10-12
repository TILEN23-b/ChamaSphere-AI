
from django import forms
from django.contrib.auth import get_user_model

from .models import (
    ContributionCampaign,
    ContributionCategory,
    ContributionTransaction,
)

User = get_user_model()


class ContributionCampaignForm(forms.ModelForm):
    class Meta:
        model = ContributionCampaign
        fields = [
            "title",
            "category",
            "description",
            "amount_per_member",
            "deadline",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. Funeral Support Fund",
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Explain the purpose of this contribution",
            }),
            "amount_per_member": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0.01",
                "step": "0.01",
                "placeholder": "100.00",
            }),
            "deadline": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = (
            ContributionCategory.objects.filter(is_active=True).order_by("name")
        )


class ContributionPaymentForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=User.objects.none(),
        empty_label="Select a SACCO member",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    campaign = forms.ModelChoiceField(
        queryset=ContributionCampaign.objects.none(),
        empty_label="Select a campaign",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    amount = forms.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "0.01",
            "step": "0.01",
            "placeholder": "0.00",
        }),
    )
    payment_method = forms.ChoiceField(
        choices=ContributionTransaction.PaymentMethod.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    external_reference = forms.CharField(
        max_length=100,
        required=False,
        label="Receipt or payment reference",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter verified M-Pesa/bank receipt code",
        }),
    )
    description = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Optional payment notes",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["member"].queryset = User.objects.filter(
            is_member=True
        ).order_by("last_name", "first_name", "member_number")

        self.fields["campaign"].queryset = (
            ContributionCampaign.objects.filter(
                status=ContributionCampaign.Status.ACTIVE
            ).order_by("title")
        )
