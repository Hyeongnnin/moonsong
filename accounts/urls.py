# accounts/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import SignupView, MeView, ProfileImageUploadView, ProfileMeView, ChangePasswordView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("upload-image/", ProfileImageUploadView.as_view(), name="upload_image"),
    path("profile/me/", ProfileMeView.as_view(), name="profile_me"),
    path("profile/change-password/", ChangePasswordView.as_view(), name="change_password"),
]
