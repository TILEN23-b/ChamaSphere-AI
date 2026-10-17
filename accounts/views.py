from decimal import Decimal

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils import timezone
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileForm

from .forms import LoginForm, RegisterForm
from .permissions import (
    can_manage_meeting_records,
    can_manage_system_users,
    can_post_savings,
    can_view_financial_reports,
    can_view_governance_reports,
)
from savings.models import SavingsAccount


# ---------------------------------------------------------
# 1. LOGIN
# ---------------------------------------------------------

class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        request = self.request
        identifier = form.cleaned_data["username"].strip()

        user = authenticate(
            request,
            username=identifier,
            password=form.cleaned_data["password"],
        )

        if user is None:
            form.add_error(
                None,
                "Invalid email/member ID or password.",
            )
            return self.form_invalid(form)

        login(request, user)
        return redirect(self.get_success_url())


# ---------------------------------------------------------
# 2. MEMBER REGISTRATION
# ---------------------------------------------------------

def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:dashboard")
    else:
        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


# ---------------------------------------------------------
# 3. ROLE-AWARE DASHBOARD
# ---------------------------------------------------------

@login_required
def dashboard(request):
    user = request.user

    # Savings transaction posting permission.
    is_savings_staff = can_post_savings(user)

    # SACCO role-based capabilities.
    can_view_governance = can_view_governance_reports(user)
    can_manage_meetings = can_manage_meeting_records(user)
    can_view_finances = can_view_financial_reports(user)
    can_manage_users = can_manage_system_users(user)

    # Retrieve this user's own savings account, if one exists.
    savings_account = SavingsAccount.objects.filter(
        member=user
    ).first()

    savings_balance = (
        savings_account.balance
        if savings_account
        else Decimal("0.00")
    )

    # Display name with sensible fallbacks.
    member_name = (
        user.get_full_name().strip()
        or getattr(user, "username", "")
        or user.email
    )

    context = {
        # User details.
        "member": user,
        "member_name": member_name,
        "member_number": getattr(user, "member_number", ""),
        "today": timezone.localdate(),

        # SACCO role information.
        "sacco_role": getattr(user, "sacco_role", "member"),
        "sacco_role_display": (
            user.get_sacco_role_display()
            if hasattr(user, "get_sacco_role_display")
            else "Regular Member"
        ),

        # Existing dashboard permission flag.
        "is_savings_staff": is_savings_staff,

        # Role-specific capabilities for the dashboard template.
        "can_view_governance_reports": can_view_governance,
        "can_manage_meeting_records": can_manage_meetings,
        "can_view_financial_reports": can_view_finances,
        "can_manage_system_users": can_manage_users,

        # Real savings ledger balance.
        "savings_balance": savings_balance,

        # Placeholders until these modules are implemented.
        "loan_balance": Decimal("0.00"),
        "dividends": Decimal("0.00"),
        "contributions": Decimal("0.00"),

        # Retain the existing recent transactions placeholder.
        "recent_transactions": [],
    }

    return render(
        request,
        "accounts/dashboard.html",
        context,
    )

# ---------------------------------------------------------
# 4. MEMBER PROFILE
# ---------------------------------------------------------

@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your profile has been updated successfully."
            )
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile.html",
        {"form": form, "member": request.user},
    )
