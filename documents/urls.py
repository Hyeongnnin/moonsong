from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentTemplateViewSet, GeneratedDocumentViewSet, ResumeGenerateView  # ✅ B 프로젝트 병합

router = DefaultRouter()
router.register(r"templates", DocumentTemplateViewSet, basename="documenttemplate")
router.register(r"generated", GeneratedDocumentViewSet, basename="generateddocument")

urlpatterns = [
	path("", include(router.urls)),
	# ✅ B 프로젝트 병합: 이력서 자동 생성 엔드포인트
	path("resume/generate/", ResumeGenerateView.as_view(), name="resume-generate"),
]
