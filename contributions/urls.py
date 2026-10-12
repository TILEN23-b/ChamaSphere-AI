
from django.urls import path

from . import views

app_name = "contributions"

urlpatterns = [
    path("", views.campaign_list, name="campaign_list"),
    path("create/", views.campaign_create, name="campaign_create"),
    path("campaign/<int:pk>/", views.campaign_detail, name="campaign_detail"),
    path(
        "campaign/<int:pk>/activate/",
        views.campaign_activate,
        name="campaign_activate",
    ),
    path("my-contributions/", views.member_contributions, name="member_portal"),
    path(
        "campaign/<int:pk>/pay/",
        views.mpesa_payment_placeholder,
        name="mpesa_pay",
    ),
    path("record-payment/", views.staff_record_payment, name="record_payment"),
]
