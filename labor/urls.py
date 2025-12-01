# labor/urls.py
from rest_framework.routers import DefaultRouter
from .views import EmployeeViewSet, WorkRecordViewSet, CalculationResultViewSet

router = DefaultRouter()
# Job (Employee) 관련 엔드포인트
# GET /api/labor/jobs/ - 목록
# GET /api/labor/jobs/<id>/ - 상세
# GET /api/labor/jobs/<id>/summary/?month=2025-11 - 월별 요약
# GET /api/labor/jobs/<id>/work-records/?start=2025-11-01&end=2025-11-30 - 기간별 근로기록
router.register("jobs", EmployeeViewSet, basename="job")

# 직접 근로기록도 등록
router.register("work-records", WorkRecordViewSet, basename="workrecord")
router.register("calculation-results", CalculationResultViewSet, basename="calculationresult")

# 호환성을 위해 employees도 유지
router.register("employees", EmployeeViewSet, basename="employee")

urlpatterns = router.urls
