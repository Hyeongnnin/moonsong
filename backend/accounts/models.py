from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ("personal", "일반회원"),
        ("lawyer", "노무사"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="personal")
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.CharField(max_length=8, blank=True)  # YYYYMMDD
    gender = models.CharField(max_length=10, blank=True)     # male / female

class LawyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='lawyer_profile')
    license_number = models.CharField(max_length=50)
    office_name = models.CharField(max_length=200, blank=True)
    career = models.TextField(blank=True)
    introduction = models.TextField(blank=True)
    signup_source = models.CharField(max_length=50, blank=True)
    cert_file = models.FileField(upload_to='lawyer_certs/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.license_number}"
