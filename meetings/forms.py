from django import forms
from django.utils import timezone

from .models import Meeting


class MeetingForm(forms.ModelForm):
    meeting_date = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
            },
            format="%Y-%m-%dT%H:%M",
        ),
    )

    class Meta:
        model = Meeting
        fields = [
            "title",
            "meeting_type",
            "meeting_date",
            "venue",
            "agenda",
            "minutes",
            "status",
        ]

        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter meeting title",
            }),
            "meeting_type": forms.Select(attrs={
                "class": "form-select",
            }),
            "venue": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter meeting venue",
            }),
            "agenda": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Enter the meeting agenda",
            }),
            "minutes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Record discussions and decisions",
            }),
            "status": forms.Select(attrs={
                "class": "form-select",
            }),
        }

        labels = {
            "title": "Meeting title",
            "meeting_type": "Meeting type",
            "meeting_date": "Date and time",
            "venue": "Venue",
            "agenda": "Agenda",
            "minutes": "Meeting minutes",
            "status": "Meeting status",
        }

    def clean_meeting_date(self):
        meeting_date = self.cleaned_data["meeting_date"]

        if (
            timezone.is_aware(meeting_date)
            and meeting_date < timezone.now()
            and self.instance.pk is None
        ):
            raise forms.ValidationError(
                "A new meeting cannot be scheduled in the past."
            )

        return meeting_date