from django.urls import path

from . import views

app_name = "meetings"

urlpatterns = [
    path("", views.meeting_list, name="list"),
    path("create/", views.meeting_create, name="create"),
    path("<int:pk>/", views.meeting_detail, name="detail"),
    path("<int:pk>/edit/", views.meeting_update, name="update"),
    path("<int:pk>/attendance/",views.meeting_attendance,name="attendance"),
]