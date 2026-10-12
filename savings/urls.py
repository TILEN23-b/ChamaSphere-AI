
from django.urls import path

from . import views

app_name = "savings"

urlpatterns = [
    path("", views.savings_overview, name="overview"),
    path(
        "staff/post/",
        views.staff_post_transaction,
        name="staff-post",
    ),
    path(
        "transactions/<uuid:reference>/",
        views.transaction_detail,
        name="transaction-detail",
    ),
    path( 
        "statement/export/",
        views.export_savings_statement,
        name="statement-export", ),
]