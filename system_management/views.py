# Create your views here.
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import SACcopolicyForm, StaffTaskForm, UserAdministrationForm
from .models import SACcopolicy, StaffTask, SystemAuditEvent
from .permissions import require_system_management
from .services import audit

User = get_user_model()

@login_required
def dashboard(request):
    require_system_management(request.user)
    context = {
        "users_count": User.objects.count(),
        "active_users_count": User.objects.filter(is_active=True).count(),
        "staff_count": User.objects.filter(is_staff_member=True, is_active=True).count(),
        "open_tasks_count": StaffTask.objects.exclude(status__in=[StaffTask.Status.COMPLETED, StaffTask.Status.CANCELLED]).count(),
        "pending_policies_count": SACcopolicy.objects.filter(is_active=False).count(),
        "recent_events": SystemAuditEvent.objects.select_related("actor")[:10],
    }
    return render(request, "system_management/dashboard.html", context)

@login_required
def user_list(request):
    require_system_management(request.user)
    q = request.GET.get("q", "").strip()
    users = User.objects.all().order_by("last_name", "first_name", "email")
    if q:
        users = users.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q) | Q(member_number__icontains=q))
    return render(request, "system_management/user_list.html", {"users": users, "q": q})

@login_required
def user_edit(request, pk):
    require_system_management(request.user)
    target = get_object_or_404(User, pk=pk)
    if target.is_superuser and not request.user.is_superuser:
        raise PermissionDenied("Only a superuser may edit a superuser account.")
    if request.method == "POST":
        form = UserAdministrationForm(request.POST, instance=target)
        if form.is_valid():
            # Do not permit the current administrator to lock themselves out.
            if target.pk == request.user.pk and not form.cleaned_data["is_active"]:
                form.add_error("is_active", "You cannot deactivate your own account here.")
            else:
                changed_fields = [name for name in form.changed_data]
                updated = form.save()
                audit(request, "user.updated", obj=updated, description="Updated fields: " + ", ".join(changed_fields))
                messages.success(request, "User account updated.")
                return redirect("system_management:user_list")
    else:
        form = UserAdministrationForm(instance=target)
    return render(request, "system_management/form.html", {"form": form, "page_title": "Edit user", "cancel_url": "system_management:user_list"})

@login_required
def task_list(request):
    require_system_management(request.user)
    tasks = StaffTask.objects.select_related("assigned_to", "assigned_by")
    return render(request, "system_management/task_list.html", {"tasks": tasks})

@login_required
def task_create(request):
    require_system_management(request.user)
    form = StaffTaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.assigned_by = request.user
        task.save()
        audit(request, "task.created", obj=task, description=f"Assigned to user ID {task.assigned_to_id}")
        messages.success(request, "Staff task created.")
        return redirect("system_management:task_list")
    return render(request, "system_management/form.html", {"form": form, "page_title": "Assign staff task", "cancel_url": "system_management:task_list"})

@login_required
def task_edit(request, pk):
    require_system_management(request.user)
    task = get_object_or_404(StaffTask, pk=pk)
    form = StaffTaskForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        task = form.save()
        audit(request, "task.updated", obj=task)
        messages.success(request, "Task updated.")
        return redirect("system_management:task_list")
    return render(request, "system_management/form.html", {"form": form, "page_title": "Edit staff task", "cancel_url": "system_management:task_list"})

@login_required
def policy_list(request):
    require_system_management(request.user)
    return render(request, "system_management/policy_list.html", {"policies": SACcopolicy.objects.all()})

@login_required
def policy_create(request):
    require_system_management(request.user)
    form = SACcopolicyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        policy = form.save(commit=False)
        policy.created_by = request.user
        policy.updated_by = request.user
        policy.save()
        audit(request, "policy.created", obj=policy)
        messages.success(request, "Policy saved.")
        return redirect("system_management:policy_list")
    return render(request, "system_management/form.html", {"form": form, "page_title": "Create SACCO policy", "cancel_url": "system_management:policy_list"})

@login_required
def policy_edit(request, pk):
    require_system_management(request.user)
    policy = get_object_or_404(SACcopolicy, pk=pk)
    form = SACcopolicyForm(request.POST or None, instance=policy)
    if request.method == "POST" and form.is_valid():
        policy = form.save(commit=False)
        policy.updated_by = request.user
        policy.save()
        audit(request, "policy.updated", obj=policy)
        messages.success(request, "Policy updated.")
        return redirect("system_management:policy_list")
    return render(request, "system_management/form.html", {"form": form, "page_title": "Edit SACCO policy", "cancel_url": "system_management:policy_list"})

@login_required
@require_POST
def policy_toggle(request, pk):
    require_system_management(request.user)
    policy = get_object_or_404(SACcopolicy, pk=pk)
    policy.is_active = not policy.is_active
    policy.updated_by = request.user
    policy.save(update_fields=["is_active", "updated_by", "updated_at"])
    audit(request, "policy.activated" if policy.is_active else "policy.deactivated", obj=policy)
    messages.success(request, f"Policy {'activated' if policy.is_active else 'deactivated'}.")
    return redirect("system_management:policy_list")

@login_required
def member_directory(request):
    require_system_management(request.user)
    q = request.GET.get("q", "").strip()
    members = User.objects.filter(is_member=True).order_by("last_name", "first_name")
    if q:
        members = members.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q) | Q(member_number__icontains=q))
    # Do not expose national ID in the list; open a specifically authorized workflow if needed.
    return render(request, "system_management/member_directory.html", {"members": members, "q": q})

@login_required
def audit_list(request):
    require_system_management(request.user)
    events = SystemAuditEvent.objects.select_related("actor")[:300]
    return render(request, "system_management/audit_list.html", {"events": events})
