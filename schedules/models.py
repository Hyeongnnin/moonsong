# schedules/models.py
from django.db import models
from django.conf import settings
from labor.models import Employee

User = settings.AUTH_USER_MODEL

class CalendarEvent(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calendar_events")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="calendar_events")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(null=True, blank=True)
    event_type = models.CharField(max_length=50, blank=True)  # shift, deadline 등
    related_type = models.CharField(max_length=50, blank=True)
    related_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"
