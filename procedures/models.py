# procedures/models.py
from django.db import models

class ReportProcedure(models.Model):
    code = models.CharField(max_length=50, unique=True)  # wage_claim, dismissal 등
    title = models.CharField(max_length=200)
    authority = models.CharField(max_length=100, blank=True)  # 노동청 등
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ReportStep(models.Model):
    procedure = models.ForeignKey(ReportProcedure, on_delete=models.CASCADE, related_name="steps")
    step_order = models.IntegerField()
    title = models.CharField(max_length=200)
    step_type = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    required_docs_json = models.JSONField(null=True, blank=True)
    estimated_days = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ["procedure", "step_order"]

    def __str__(self):
        return f"{self.procedure.title} - {self.step_order}. {self.title}"
