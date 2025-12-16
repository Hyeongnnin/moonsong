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
    # template is optional now: user can upload a file and choose a doc_type without selecting an existing template
    template = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name="generated_documents", null=True, blank=True)
    # ✅ B 프로젝트 병합: 템플릿 없이도 서류 유형을 직접 지정할 수 있도록 doc_type 필드 추가
    doc_type = models.CharField(max_length=50, blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="generated_documents")
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="generated_documents")
    consultation = models.ForeignKey(Consultation, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name="generated_documents")

    title = models.CharField(max_length=200, blank=True, default="")
    filled_data_json = models.JSONField(null=True, blank=True)
    file_url = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, default="작성중")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        display = self.title or (self.template.name if self.template else "NoTemplate")
        return f"{display} for {self.user.username}"
