from django.urls import path
from . import views

app_name = "system_management"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.user_list, name="user_list"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("members/", views.member_directory, name="member_directory"),
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("policies/", views.policy_list, name="policy_list"),
    path("policies/create/", views.policy_create, name="policy_create"),
    path("policies/<int:pk>/edit/", views.policy_edit, name="policy_edit"),
    path("policies/<int:pk>/toggle/", views.policy_toggle, name="policy_toggle"),
    path("audit/", views.audit_list, name="audit_list"),
]
