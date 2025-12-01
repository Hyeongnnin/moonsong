# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    STATUS_CHOICES = (
        ("active", "Active"),
        ("withdrawn", "Withdrawn"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # ERD의 CreatedAt은 AbstractUser의 date_joined 그대로 사용
    # PasswordHash는 Django가 password 필드 + 해시로 관리

    def __str__(self):
        return self.username
