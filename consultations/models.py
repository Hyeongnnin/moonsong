# consultations/models.py
from django.db import models
from django.conf import settings
from labor.models import Employee, CalculationResult

User = settings.AUTH_USER_MODEL

class Consultation(models.Model):
    STATUS_CHOICES = (
        ("접수", "접수"),
        ("AI분석완료", "AI분석완료"),
        ("안내제공완료", "안내제공완료"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="consultations")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="consultations")
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    consultation_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="접수")

    ai_result_json = models.JSONField(null=True, blank=True)
    related_result = models.ForeignKey(
        CalculationResult, on_delete=models.SET_NULL, null=True, blank=True, related_name="consultations"
    )

    def __str__(self):
        return f"{self.title} ({self.user.username})"
