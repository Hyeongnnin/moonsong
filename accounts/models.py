# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
import os


def _profile_image_upload_to(instance, filename):
    """Generate a unique path for uploaded profile images."""
    ext = os.path.splitext(filename)[1]
    return f"profile_images/{uuid.uuid4().hex}{ext}"


class User(AbstractUser):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("withdrawn", "Withdrawn"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # 프로필 이미지: media/profile_images/ 아래에 저장
    profile_image = models.ImageField(upload_to=_profile_image_upload_to, null=True, blank=True)

    # 전화번호
    phone_number = models.CharField(max_length=20, null=True, blank=True)

    # ERD의 CreatedAt은 AbstractUser의 date_joined 그대로 사용
    # PasswordHash는 Django가 password 필드 + 해시로 관리

    def __str__(self):
        return self.username
