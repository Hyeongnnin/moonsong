# labor/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, timedelta, date
from decimal import Decimal
from .models import Employee, WorkRecord, CalculationResult
from .services import job_to_inputs, evaluate_labor, calculate_annual_leave
from .serializers import (
    EmployeeSerializer,
    EmployeeUpdateSerializer,
    WorkRecordSerializer,
    CalculationResultSerializer,
    JobSummarySerializer
)
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


class EmployeeViewSet(viewsets.ModelViewSet):
    """Job(알바) 관련 API
    
    GET /api/labor/employees/ - 사용자의 모든 Job 목록
    GET /api/labor/employees/<id>/ - 특정 Job 상세
    GET /api/labor/employees/<id>/summary/?month=2025-11 - 월별 요약
    GET /api/labor/employees/<id>/work-records/?start=2025-11-01&end=2025-11-30 - 기간별 근로기록
    POST /api/labor/employees/<id>/work-records/ - 근로기록 추가
    """
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Employee.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        """액션에 따라 다른 Serializer 사용"""
        if self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer
        return EmployeeSerializer

    def perform_update(self, serializer):
        """근로정보 수정 시 현재 사용자만 수정 가능하도록 검증"""
        serializer.save()

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """특정 Job의 월별 요약 정보"""
        job = self.get_object()
        month_str = request.query_params.get('month')  # YYYY-MM 형식
        
        if not month_str:
            return Response(
                {'error': 'month 파라미터 필수 (형식: YYYY-MM)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year, month = map(int, month_str.split('-'))
        except ValueError:
            return Response(
                {'error': 'month 형식 오류 (형식: YYYY-MM)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 월의 첫날과 마지막날
        if month == 12:
            period_start = date(year, month, 1)
            period_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            period_start = date(year, month, 1)
            period_end = date(year, month + 1, 1) - timedelta(days=1)
        
        # 해당 월의 근로기록
        records = job.work_records.filter(
            work_date__gte=period_start,
            work_date__lte=period_end
        )
        
        # 통계 계산
        total_hours = Decimal('0')
        total_days = records.count()
        
        for record in records:
            total_hours += record.get_total_hours()
        
        estimated_salary = total_hours * job.hourly_rate
        
        # 주별 통계
        week_stats = []
        current_week_start = period_start
        
        while current_week_start <= period_end:
            week_end = min(current_week_start + timedelta(days=6), period_end)
            week_records = records.filter(
                work_date__gte=current_week_start,
                work_date__lte=week_end
            )
            
            week_hours = Decimal('0')
            for record in week_records:
                week_hours += record.get_total_hours()
            
            week_stats.append({
                'start_date': current_week_start.isoformat(),
                'end_date': week_end.isoformat(),
                'hours': float(week_hours),
                'pay': float(week_hours * job.hourly_rate)
            })
            
            current_week_start = week_end + timedelta(days=1)
        
        data = {
            'job_id': job.id,
            'job_name': job.workplace_name,
            'workplace_name': job.workplace_name,
            'hourly_wage': float(job.hourly_rate),
            'month': month_str,
            'total_hours': float(total_hours),
            'total_days': total_days,
            'estimated_salary': float(estimated_salary),
            'week_stats': week_stats
        }
        
        return Response(data)

    @action(detail=True, methods=['get'])
    def evaluation(self, request, pk=None):
        """특정 Job(알바)의 노동법 기준 근로조건 평가 결과

        GET /api/labor/jobs/<id>/evaluation/
        또는 /api/labor/employees/<id>/evaluation/ (employees 라우트도 등록됨)
        반환 예:
        {
          "min_wage_ok": true,
          "min_wage_required": 10030,
          "weekly_holiday_pay": 12040,
          "annual_leave_days": 8.0,
          "severance_estimate": 0,
          "warnings": ["..."]
        }
        """
        job = self.get_object()
        inputs = job_to_inputs(job)
        result = evaluate_labor(inputs)
        return Response(result)

    @action(detail=True, methods=['get'], url_path='annual-leave')
    def annual_leave(self, request, pk=None):
        """연차휴가 요약

        GET /api/labor/jobs/<id>/annual-leave/
        응답: { total, used, available }
        """
        job = self.get_object()
        inputs = job_to_inputs(job)
        result = calculate_annual_leave(inputs)
        return Response(result)

    @action(detail=True, methods=['get'])
    def work_records(self, request, pk=None):
        """특정 Job의 기간별 근로기록"""
        job = self.get_object()
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start, end 파라미터 필수 (형식: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': '날짜 형식 오류 (형식: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        records = job.work_records.filter(
            work_date__gte=start,
            work_date__lte=end
        ).order_by('-work_date')
        
        serializer = WorkRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'], url_path='schedules')
    def schedules(self, request, pk=None):
        """GET: 리스트, POST: 추가/업데이트(weekday 단위)"""
        job = self.get_object()
        if request.method == 'GET':
            schedules = job.schedules.all()
            from .serializers import WorkScheduleSerializer
            serializer = WorkScheduleSerializer(schedules, many=True)
            return Response(serializer.data)
        else:
            # create or update per weekday
            data = request.data
            weekday = int(data.get('weekday'))
            start_time = data.get('start_time')  # HH:MM
            end_time = data.get('end_time')
            enabled = data.get('enabled', 'true') in ['1', 'true', True, 'True']
            schedule, created = job.schedules.get_or_create(weekday=weekday, defaults={
                'start_time': start_time or None,
                'end_time': end_time or None,
                'enabled': enabled,
            })
            if not created:
                schedule.start_time = start_time or None
                schedule.end_time = end_time or None
                schedule.enabled = enabled
                schedule.save()
            from .serializers import WorkScheduleSerializer
            return Response(WorkScheduleSerializer(schedule).data)

    @action(detail=True, methods=['get'], url_path='calendar')
    def calendar(self, request, pk=None):
        """Return month calendar highlighting scheduled weekdays and existing work_records"""
        job = self.get_object()
        month = request.query_params.get('month')  # YYYY-MM
        if not month:
            return Response({'error': 'month parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, mon = map(int, month.split('-'))
        except Exception:
            return Response({'error': 'month format error'}, status=status.HTTP_400_BAD_REQUEST)
        import calendar as pycal
        from datetime import date
        _, lastday = pycal.monthrange(year, mon)
        dates = []
        # collect scheduled weekdays
        schedules = job.schedules.filter(enabled=True)
        schedule_weekdays = {s.weekday: s for s in schedules}
        for day in range(1, lastday+1):
            d = date(year, mon, day)
            is_scheduled = d.weekday() in schedule_weekdays
            record = job.work_records.filter(work_date=d).first()
            dates.append({
                'date': d.isoformat(),
                'day': day,
                'is_scheduled': is_scheduled,
                'record': WorkRecordSerializer(record).data if record else None,
            })
        return Response({'dates': dates})

    def destroy(self, request, pk=None):
        """Ensure only owner can delete and return clear responses."""
        try:
            obj = self.get_object()
        except Http404:
            logger.warning('Attempt to delete non-existing Employee id=%s by user=%s', pk, request.user)
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # ownership check (get_queryset already filters by user, but double-check)
        if obj.user != request.user:
            logger.warning('User %s attempted to delete Employee id=%s owned by %s', request.user, pk, obj.user)
            return Response({'detail': '권한이 없습니다.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # debug: log related object counts
            work_count = obj.work_records.count()
            schedule_count = obj.schedules.count()
            calc_count = obj.calculation_results.count()
            logger.info('Deleting Employee id=%s: work_records=%s, schedules=%s, calculations=%s', pk, work_count, schedule_count, calc_count)

            obj.delete()
            logger.info('Employee id=%s deleted by user=%s', pk, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.exception('Failed to delete Employee id=%s by user=%s: %s', pk, request.user, e)
            # return exception message to frontend for debugging (will be improved before prod)
            return Response({'detail': f'삭제 중 오류가 발생했습니다: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkRecordViewSet(viewsets.ModelViewSet):
    """근로기록 관련 API"""
    serializer_class = WorkRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 로그인 유저의 Employee들에 한정
        return WorkRecord.objects.filter(employee__user=self.request.user)

    def perform_create(self, serializer):
        # employee_id를 validate하여 현재 사용자의 것인지 확인
        employee_id = self.request.data.get('employee')
        try:
            employee = Employee.objects.get(id=employee_id, user=self.request.user)
            serializer.save()
        except Employee.DoesNotExist:
            raise PermissionError("이 Job에 접근할 권한이 없습니다.")

    def perform_update(self, serializer):
        # ensure user owns this record
        instance = serializer.instance
        if instance.employee.user != self.request.user:
            raise PermissionError("이 작업을 수행할 권한이 없습니다.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.employee.user != self.request.user:
            raise PermissionError("이 작업을 수행할 권한이 없습니다.")
        instance.delete()


class CalculationResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CalculationResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CalculationResult.objects.filter(employee__user=self.request.user)

