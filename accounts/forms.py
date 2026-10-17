from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User
from django import forms
from django.contrib.auth import get_user_model


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Email Address / Member ID",
        widget=forms.EmailInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Enter your email or member ID",
            "autocomplete": "username",
        }),
    )

    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Enter your password",
            "autocomplete": "current-password",
        }),
    )


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        label="Full Name",
        widget=forms.TextInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Enter your full name",
        }),
    )

    last_name = forms.CharField(
        label="",
        required=False,
        widget=forms.HiddenInput(),
    )

    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Enter your email address",
            "autocomplete": "email",
        }),
    )

    phone_number = forms.CharField(
        label="Phone Number",
        widget=forms.TextInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Enter your phone number",
            "autocomplete": "tel",
        }),
    )

    national_id = forms.CharField(
        label="National ID / Passport Number",
        widget=forms.TextInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Enter your ID or passport number",
        }),
    )

    member_type = forms.ChoiceField(
        label="Member Type",
        choices=User.MEMBER_TYPES,
        widget=forms.Select(attrs={
            "class": "form-select premium-input",
        }),
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Create a strong password",
            "autocomplete": "new-password",
        }),
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "class": "form-control premium-input",
            "placeholder": "Confirm your password",
            "autocomplete": "new-password",
        }),
    )

    agree_terms = forms.BooleanField(
        label="I agree to the Terms of Service and Privacy Policy.",
        required=True,
    )

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "national_id",
            "member_type",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_national_id(self):
        value = self.cleaned_data["national_id"].strip()
        if User.objects.filter(national_id=value).exists():
            raise forms.ValidationError("This ID or passport is already registered.")
        return value

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.national_id = self.cleaned_data["national_id"]
        user.member_type = self.cleaned_data["member_type"]

        if commit:
            user.save()

        return user



User = get_user_model()


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "national_id",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "First name"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Last name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "Email address"}
            ),
            "phone_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Phone number"}
            ),
            "national_id": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "National ID"}
            ),
        }
