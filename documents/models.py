# documents/models.py
from django.db import models
from django.conf import settings
from labor.models import Employee
from consultations.models import Consultation

User = settings.AUTH_USER_MODEL

class DocumentTemplate(models.Model):
    name = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=50)  # contract, complaint, statement 등
    description = models.TextField(blank=True)
    law_reference = models.CharField(max_length=200, blank=True)
    required_fields_json = models.JSONField(null=True, blank=True)
    file_path = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.doc_type})"


class GeneratedDocument(models.Model):
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name="generated_documents")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="generated_documents")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="generated_documents")
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="generated_documents")

    filled_data_json = models.JSONField(null=True, blank=True)
    file_url = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default="작성중")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.template.name} for {self.user.username}"
