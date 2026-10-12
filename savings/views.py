
import csv
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from .forms import StaffSavingsTransactionForm
from .models import SavingsAccount, SavingsTransaction
from .services import post_savings_transaction

from accounts.permissions import can_post_savings


# ---------------------------------------------------------
# 1. CHECK SAVINGS STAFF PERMISSIONS
# ---------------------------------------------------------


def require_savings_staff(user):
    if not can_post_savings(user):
        raise PermissionDenied(
            "You do not have permission to manage savings transactions."
        )


# ---------------------------------------------------------
# 2. VALIDATE STATEMENT DATE FILTERS
# ---------------------------------------------------------

def _statement_dates(request):
    """
    Read and validate the optional statement start and end dates.
    """
    start_raw = request.GET.get("start_date", "").strip()
    end_raw = request.GET.get("end_date", "").strip()

    start_date = parse_date(start_raw) if start_raw else None
    end_date = parse_date(end_raw) if end_raw else None

    if start_raw and start_date is None:
        return None, None, "Enter a valid start date."

    if end_raw and end_date is None:
        return None, None, "Enter a valid end date."

    if start_date and end_date and start_date > end_date:
        return (
            None,
            None,
            "The start date must not be after the end date.",
        )

    return start_date, end_date, None


# ---------------------------------------------------------
# 3. CALCULATE BALANCE BEFORE THE STATEMENT PERIOD
# ---------------------------------------------------------

def _posted_balance_before(account, start_date):
    """
    Calculate the balance immediately before the start date.
    """
    if start_date is None:
        return Decimal("0.00")

    previous_transactions = SavingsTransaction.objects.filter(
        account=account,
        status=SavingsTransaction.Status.POSTED,
        created_at__date__lt=start_date,
    )

    totals = previous_transactions.aggregate(
        deposits=Sum(
            "amount",
            filter=Q(
                transaction_type=SavingsTransaction.Type.DEPOSIT
            ),
        ),
        withdrawals=Sum(
            "amount",
            filter=Q(
                transaction_type=SavingsTransaction.Type.WITHDRAWAL
            ),
        ),
    )

    deposits = totals["deposits"] or Decimal("0.00")
    withdrawals = totals["withdrawals"] or Decimal("0.00")

    return deposits - withdrawals


# ---------------------------------------------------------
# 4. BUILD THE SAVINGS STATEMENT
# ---------------------------------------------------------

def _build_statement(account, start_date=None, end_date=None):
    """
    Build statement totals and running balances.

    Transactions are calculated in chronological order, then
    displayed newest first.
    """
    opening_balance = _posted_balance_before(
        account,
        start_date,
    )

    queryset = SavingsTransaction.objects.filter(
        account=account,
        status=SavingsTransaction.Status.POSTED,
    )

    if start_date:
        queryset = queryset.filter(
            created_at__date__gte=start_date
        )

    if end_date:
        queryset = queryset.filter(
            created_at__date__lte=end_date
        )

    chronological = list(
        queryset.order_by("created_at", "pk")
    )

    running_balance = opening_balance
    deposits_total = Decimal("0.00")
    withdrawals_total = Decimal("0.00")

    for transaction in chronological:
        if (
            transaction.transaction_type
            == SavingsTransaction.Type.DEPOSIT
        ):
            running_balance += transaction.amount
            deposits_total += transaction.amount
        else:
            running_balance -= transaction.amount
            withdrawals_total += transaction.amount

        # Temporary attribute used by the statement template.
        transaction.running_balance = running_balance

    closing_balance = running_balance

    # Display newest transaction first.
    transactions = list(reversed(chronological))

    return {
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "deposits_total": deposits_total,
        "withdrawals_total": withdrawals_total,
        "transactions": transactions,
    }


# ---------------------------------------------------------
# 5. MEMBER SAVINGS OVERVIEW AND STATEMENT
# ---------------------------------------------------------

@login_required
def savings_overview(request):
    """
    Display the logged-in member's savings account and statement.
    """
    user = request.user

    is_savings_staff = can_post_savings(user)

    if not user.is_member and not is_savings_staff:
        raise PermissionDenied(
            "You do not have permission to access savings."
        )

    # Staff who are not members go to the staff posting page.
    if not user.is_member:
        return redirect("savings:staff-post")

    account = SavingsAccount.objects.filter(
        member=user
    ).first()

    if account is None:
        account, _ = SavingsAccount.objects.get_or_create(
            member=user
        )

    start_date, end_date, date_error = _statement_dates(
        request
    )

    if date_error:
        statement = {
            "opening_balance": Decimal("0.00"),
            "closing_balance": Decimal("0.00"),
            "deposits_total": Decimal("0.00"),
            "withdrawals_total": Decimal("0.00"),
            "transactions": [],
        }
    else:
        statement = _build_statement(
            account,
            start_date,
            end_date,
        )

    context = {
        "account": account,
        "balance": account.balance,
        "start_date": start_date,
        "end_date": end_date,
        "date_error": date_error,
        **statement,
    }

    return render(
        request,
        "savings/overview.html",
        context,
    )


# ---------------------------------------------------------
# 6. EXPORT MEMBER STATEMENT AS CSV
# ---------------------------------------------------------

def _safe_csv_text(value):
    """
    Reduce spreadsheet formula-injection risk for text cells.
    """
    text = "" if value is None else str(value)

    if text.lstrip().startswith(
        ("=", "+", "-", "@", "\t", "\r")
    ):
        return "'" + text

    return text


@login_required
def export_savings_statement(request):
    """
    Export the logged-in member's own statement as a CSV file.
    """
    user = request.user

    if not getattr(user, "is_member", False):
        raise PermissionDenied(
            "This statement is available to SACCO members only."
        )

    account = SavingsAccount.objects.filter(
        member=user
    ).first()

    if account is None:
        messages.error(
            request,
            "You do not have a savings account to export yet.",
        )
        return redirect("savings:overview")

    start_date, end_date, date_error = _statement_dates(
        request
    )

    if date_error:
        return HttpResponse(
            date_error,
            status=400,
            content_type="text/plain; charset=utf-8",
        )

    statement = _build_statement(
        account,
        start_date,
        end_date,
    )

    response = HttpResponse(
        content_type="text/csv; charset=utf-8"
    )

    response["Content-Disposition"] = (
        'attachment; filename="greensacco_savings_statement.csv"'
    )

    # Excel-friendly UTF-8 marker.
    response.write("\ufeff")

    writer = csv.writer(response)

    writer.writerow(["GreenSACCO Savings Statement"])
    writer.writerow([
        "Member",
        _safe_csv_text(
            user.get_full_name() or user.username
        ),
    ])
    writer.writerow([
        "Member number",
        _safe_csv_text(user.member_number or ""),
    ])
    writer.writerow([
        "Savings account",
        _safe_csv_text(account.account_number),
    ])
    writer.writerow([
        "Statement start date",
        start_date.isoformat() if start_date else "All",
    ])
    writer.writerow([
        "Statement end date",
        end_date.isoformat() if end_date else "Through today",
    ])
    writer.writerow([
        "Opening balance (KES)",
        f"{statement['opening_balance']:.2f}",
    ])
    writer.writerow([
        "Total deposits (KES)",
        f"{statement['deposits_total']:.2f}",
    ])
    writer.writerow([
        "Total withdrawals (KES)",
        f"{statement['withdrawals_total']:.2f}",
    ])
    writer.writerow([
        "Closing balance (KES)",
        f"{statement['closing_balance']:.2f}",
    ])

    writer.writerow([])

    writer.writerow([
        "Date",
        "Transaction type",
        "Reference",
        "Description",
        "Deposit (KES)",
        "Withdrawal (KES)",
        "Running balance (KES)",
    ])

    # Reverse the newest-first list to export oldest first.
    for transaction in reversed(statement["transactions"]):
        is_deposit = (
            transaction.transaction_type
            == SavingsTransaction.Type.DEPOSIT
        )

        writer.writerow([
            transaction.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            transaction.get_transaction_type_display(),
            str(transaction.reference),
            _safe_csv_text(transaction.description or ""),
            (
                f"{transaction.amount:.2f}"
                if is_deposit
                else ""
            ),
            (
                ""
                if is_deposit
                else f"{transaction.amount:.2f}"
            ),
            f"{transaction.running_balance:.2f}",
        ])

    return response


# ---------------------------------------------------------
# 7. STAFF POSTING OF SAVINGS TRANSACTIONS
# ---------------------------------------------------------

@login_required
def staff_post_transaction(request):
    """
    Allow authorised staff to post a deposit or withdrawal.
    """
    require_savings_staff(request.user)

    if request.method == "POST":
        form = StaffSavingsTransactionForm(request.POST)

        if form.is_valid():
            member = form.cleaned_data["member"]

            account = SavingsAccount.objects.filter(
                member=member,
                is_active=True,
            ).first()

            if account is None:
                messages.error(
                    request,
                    "This member does not have an active savings account.",
                )
            else:
                try:
                    post_savings_transaction(
                        account_id=account.pk,
                        transaction_type=form.cleaned_data[
                            "transaction_type"
                        ],
                        amount=form.cleaned_data["amount"],
                        actor=request.user,
                        description=form.cleaned_data[
                            "description"
                        ],
                    )

                except ValidationError as exc:
                    for error in exc.messages:
                        form.add_error(None, error)

                else:
                    messages.success(
                        request,
                        "Savings transaction posted successfully.",
                    )
                    return redirect("savings:staff-post")

    else:
        form = StaffSavingsTransactionForm()

    return render(
        request,
        "savings/staff_post.html",
        {"form": form},
    )


# ---------------------------------------------------------
# 8. MEMBER TRANSACTION DETAILS
# ---------------------------------------------------------

@login_required
def transaction_detail(request, reference):
    """
    Show a transaction only if it belongs to the logged-in member.
    """
    if not getattr(request.user, "is_member", False):
        raise PermissionDenied(
            "This page is available to SACCO members only."
        )

    transaction_record = get_object_or_404(
        SavingsTransaction.objects.select_related(
            "account",
            "account__member",
        ),
        reference=reference,
        account__member=request.user,
    )

    return render(
        request,
        "savings/transaction_detail.html",
        {"transaction": transaction_record},
    )