from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.permissions import can_manage_meeting_records
from .forms import MeetingForm
from django.contrib.auth import get_user_model

from .models import Meeting, MeetingAttendance


def require_meeting_permission(user):
    if not can_manage_meeting_records(user):
        raise PermissionDenied(
            "Only the SACCO Secretary or an authorized administrator "
            "can manage meeting records."
        )


@login_required
def meeting_list(request):
    # All logged-in users can view meeting records.
    search_query = request.GET.get("q", "").strip()

    meetings = Meeting.objects.select_related("recorded_by").all()

    if search_query:
        meetings = meetings.filter(
            Q(title__icontains=search_query)
            | Q(venue__icontains=search_query)
            | Q(agenda__icontains=search_query)
        )

    context = {
        "meetings": meetings,
        "search_query": search_query,
        "can_manage_meetings": can_manage_meeting_records(request.user),
    }

    return render(request, "meetings/meeting_list.html", context)


@login_required
def meeting_detail(request, pk):
    # All logged-in users can view meeting details.
    meeting = get_object_or_404(
        Meeting.objects.select_related("recorded_by"),
        pk=pk,
    )

    context = {
        "meeting": meeting,
        "can_manage_meetings": can_manage_meeting_records(request.user),
    }

    return render(request, "meetings/meeting_detail.html", context)


@login_required
def meeting_create(request):
    # Only authorized users can create meeting records.
    require_meeting_permission(request.user)

    if request.method == "POST":
        form = MeetingForm(request.POST)

        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.recorded_by = request.user
            meeting.save()

            messages.success(
                request,
                "Meeting record created successfully.",
            )

            return redirect("meetings:detail", pk=meeting.pk)
    else:
        form = MeetingForm()

    return render(
        request,
        "meetings/meeting_form.html",
        {
            "form": form,
            "page_title": "Record a Meeting",
            "button_label": "Save Meeting",
        },
    )


@login_required
def meeting_update(request, pk):
    # Only authorized users can edit meeting records.
    require_meeting_permission(request.user)

    meeting = get_object_or_404(Meeting, pk=pk)

    if request.method == "POST":
        form = MeetingForm(request.POST, instance=meeting)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Meeting record updated successfully.",
            )

            return redirect("meetings:detail", pk=meeting.pk)
    else:
        form = MeetingForm(instance=meeting)

    return render(
        request,
        "meetings/meeting_form.html",
        {
            "form": form,
            "meeting": meeting,
            "page_title": "Edit Meeting",
            "button_label": "Update Meeting",
        },
    )

@login_required
def meeting_attendance(request, pk):
    meeting = get_object_or_404(Meeting, pk=pk)

    # Only the Secretary or an authorized administrator can edit attendance.
    can_manage = can_manage_meeting_records(request.user)

    if request.method == "POST":
        if not can_manage:
            raise PermissionDenied(
                "You are not authorized to manage meeting attendance."
            )

        User = get_user_model()
        members = User.objects.filter(is_member=True).order_by(
            "last_name", "first_name", "member_number"
        )

        valid_statuses = {
            choice[0]
            for choice in MeetingAttendance.AttendanceStatus.choices
        }

        saved_count = 0

        for member in members:
            status = request.POST.get(f"status_{member.pk}", "")
            remarks = request.POST.get(
                f"remarks_{member.pk}", ""
            ).strip()

            # Ignore members whose attendance fields were not submitted.
            if not status:
                continue

            if status not in valid_statuses:
                messages.error(
                    request,
                    f"Invalid attendance status for {member}.",
                )
                continue

            MeetingAttendance.objects.update_or_create(
                meeting=meeting,
                member=member,
                defaults={
                    "status": status,
                    "remarks": remarks[:255],
                    "recorded_by": request.user,
                },
            )
            saved_count += 1

        if saved_count:
            messages.success(
                request,
                f"Attendance saved for {saved_count} member(s).",
            )

        return redirect(
            "meetings:attendance",
            pk=meeting.pk,
        )

    User = get_user_model()
    members = User.objects.filter(is_member=True).order_by(
        "last_name", "first_name", "member_number"
    )

    existing_records = {
        record.member_id: record
        for record in MeetingAttendance.objects.filter(meeting=meeting)
    }

    attendance_rows = []

    for member in members:
        record = existing_records.get(member.pk)

        attendance_rows.append({
            "member": member,
            "status": (
                record.status
                if record
                else MeetingAttendance.AttendanceStatus.ABSENT
            ),
            "remarks": record.remarks if record else "",
        })

    context = {
        "meeting": meeting,
        "attendance_rows": attendance_rows,
        "can_manage_attendance": can_manage,
        "present_count": sum(
            1 for row in attendance_rows
            if row["status"] == MeetingAttendance.AttendanceStatus.PRESENT
        ),
        "absent_count": sum(
            1 for row in attendance_rows
            if row["status"] == MeetingAttendance.AttendanceStatus.ABSENT
        ),
        "excused_count": sum(
            1 for row in attendance_rows
            if row["status"] == MeetingAttendance.AttendanceStatus.EXCUSED
        ),
    }

    return render(
        request,
        "meetings/attendance_register.html",
        context,
    )
