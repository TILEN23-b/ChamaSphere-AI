from django import forms
from django.contrib.auth import get_user_model
from .models import SACcopolicy, StaffTask

User = get_user_model()

class UserAdministrationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "phone_number", "sacco_role", "is_member", "is_staff_member", "is_active")
        widgets = {"is_member": forms.CheckboxInput(), "is_staff_member": forms.CheckboxInput(), "is_active": forms.CheckboxInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Django's staff/superuser privileges are intentionally not editable here.

class StaffTaskForm(forms.ModelForm):
    class Meta:
        model = StaffTask
        fields = ("title", "description", "assigned_to", "priority", "status", "due_date", "completion_notes")
        widgets = {"description": forms.Textarea(attrs={"rows": 4}), "completion_notes": forms.Textarea(attrs={"rows": 3}), "due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = User.objects.filter(is_active=True).order_by("last_name", "first_name", "email")

class SACcopolicyForm(forms.ModelForm):
    class Meta:
        model = SACcopolicy
        fields = ("title", "category", "body", "version", "effective_date", "review_date", "is_active")
        widgets = {"body": forms.Textarea(attrs={"rows": 8}), "effective_date": forms.DateInput(attrs={"type": "date"}), "review_date": forms.DateInput(attrs={"type": "date"})}
