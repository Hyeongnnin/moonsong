# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/labor/", include("labor.urls")),
    path("api/consultations/", include("consultations.urls")),
    path("api/documents/", include("documents.urls")),
    path("api/schedules/", include("schedules.urls")),
    path("api/procedures/", include("procedures.urls")),
]
