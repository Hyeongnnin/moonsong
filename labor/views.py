# labor/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes as drf_permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List
from django.db import models
from .models import Employee, WorkRecord, CalculationResult, LeaveUsage, WorkSchedule
from .services import job_to_inputs, evaluate_labor, calculate_annual_leave, compute_monthly_schedule_stats, monthly_scheduled_dates
from .holidays import get_holidays_for_month
from .serializers import (
    EmployeeSerializer,
    EmployeeUpdateSerializer,
    WorkRecordSerializer,
    CalculationResultSerializer,
    JobSummarySerializer
)
from django.http import Http404
import logging
from django.utils import timezone

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

    @action(detail=True, methods=['get'], url_path='holiday-pay')
    def holiday_pay(self, request, pk=None):
        """이번 주 주휴수당 계산 (동적 정책 적용)

        - 기준 날짜는 ?date=YYYY-MM-DD 쿼리 파라미터로 전달
        - 없으면 서버 today 기준
        - 기준 날짜가 속한 주(월~일)를 범위로 사용
        """
        from .policy_manager import PolicyManager

        job = self.get_object()

        # 기준 날짜 파라미터 처리
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'date format error'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = date.today()

        # 정책 로드
        rules = PolicyManager.get_holiday_pay_rules()
        min_weekly_hours = Decimal(str(rules.get('min_weekly_hours', 15)))
        require_attendance = rules.get('require_perfect_attendance', True)
        calc_method = rules.get('calculation_method', 'daily_average')

        # 기준 날짜가 속한 주 범위 (월~일)
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # 활성화된 스케줄 (소정근로일 기준: enabled=True + start/end 설정)
        schedules = job.schedules.filter(enabled=True)
        schedule_map = {s.weekday: s for s in schedules if s.start_time and s.end_time}

        # 이번 주 근로기록
        records = job.work_records.filter(
            work_date__gte=start_of_week,
            work_date__lte=end_of_week
        )
        record_map = {r.work_date: r for r in records}

        # 디버깅 로그
        logger.info(f'=== Holiday Pay Debug (Employee {job.id}) ===')
        logger.info(f'Week range: {start_of_week} ~ {end_of_week}')
        logger.info(f'Records count: {records.count()}')
        for r in records:
            logger.info(f'  {r.work_date}: {r.get_total_hours()} hours')

        weekly_scheduled_hours = Decimal('0')
        scheduled_days_count = 0

        # 디버깅/프론트 표시용 보조 정보
        scheduled_weekdays = sorted(schedule_map.keys())
        checked_dates: List[str] = []

        # 실제 근무 시간 합산 (핵심 변경: 개근 여부가 아닌 실제 일한 시간으로 판단)
        actual_worked_hours = Decimal('0')

        # 월요일부터 일요일까지 순회
        current_date = start_of_week
        while current_date <= end_of_week:
            weekday = current_date.weekday()

            record = record_map.get(current_date)
            is_canceled = record and record.get_total_hours() == 0

            # 취소된 날짜(0시간 기록)는 스케줄 및 결근 체크에서 모두 제외
            if is_canceled:
                current_date += timedelta(days=1)
                continue

            # 실제 근무 기록이 있으면 시간 합산
            if record and record.get_total_hours() > 0:
                actual_worked_hours += Decimal(str(record.get_total_hours()))

            if weekday in schedule_map:
                schedule = schedule_map[weekday]

                # 이 날짜는 소정근로일로 체크 대상
                checked_dates.append(current_date.isoformat())

                # 시간 차이 계산
                dummy_date = date(2000, 1, 1)
                dt_start = datetime.combine(dummy_date, schedule.start_time)
                dt_end = datetime.combine(dummy_date, schedule.end_time)
                diff = dt_end - dt_start
                hours = Decimal(str(diff.total_seconds() / 3600))

                weekly_scheduled_hours += hours
                scheduled_days_count += 1

            current_date += timedelta(days=1)

        # 디버깅 로그 2
        logger.info(f'After loop - actual_worked_hours: {actual_worked_hours}')
        logger.info(f'Threshold: {min_weekly_hours}')
        logger.info(f'Pass threshold? {actual_worked_hours >= min_weekly_hours}')

        # 조건 1: 실제 근무 시간이 최소 기준(15시간) 미만이면 0원
        if actual_worked_hours < min_weekly_hours:
            return Response({
                'amount': 0,
                'hours': 0,
                'reason': 'less_than_threshold',
                'weekly_hours': float(weekly_scheduled_hours),
                'actual_worked_hours': float(actual_worked_hours),
                'scheduled_weekdays': scheduled_weekdays,
                'checked_dates': checked_dates,
                'policy_threshold': float(min_weekly_hours),
                'week_start': start_of_week.isoformat(),
                'week_end': end_of_week.isoformat()
            })

        # 1일 소정근로시간 (주휴시간) 계산
        # 실제 일한 날 수를 기준으로 평균 계산
        actual_work_days = sum(1 for r in records if r.get_total_hours() > 0)
        
        if actual_work_days > 0:
            # 실제 일한 날 기준 평균
            daily_avg_hours = actual_worked_hours / Decimal(str(actual_work_days))
        elif scheduled_days_count > 0:
            # 실제 기록이 없으면 스케줄 기준
            if calc_method == 'daily_average':
                daily_avg_hours = weekly_scheduled_hours / Decimal(str(scheduled_days_count))
            else:
                daily_avg_hours = weekly_scheduled_hours / Decimal(str(scheduled_days_count))
        else:
            daily_avg_hours = Decimal('0')

        # 실제 근무 시간이 15시간 이상이면 자격 부여
        # 계산: 1일 소정근로시간 * 시급
        holiday_pay = daily_avg_hours * job.hourly_rate

        return Response({
            'amount': float(holiday_pay),
            'hours': float(daily_avg_hours),
            'reason': 'eligible',
            'weekly_hours': float(weekly_scheduled_hours),
            'actual_worked_hours': float(actual_worked_hours),
            'scheduled_weekdays': scheduled_weekdays,
            'checked_dates': checked_dates,
            'policy_threshold': float(min_weekly_hours),
            'week_start': start_of_week.isoformat(),
            'week_end': end_of_week.isoformat()
        })

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

    @action(detail=True, methods=['get'], url_path='retirement-pay')
    def retirement_pay(self, request, pk=None):
        """퇴직금 예상액 계산 (근로기준법 제34조)

        GET /api/labor/employees/<id>/retirement-pay/
        
        응답:
        {
            "retirement_pay": 퇴직금 예상액 (원),
            "average_wage": 평균임금 (일급),
            "regular_wage": 통상임금 (일급),
            "service_days": 재직일수,
            "service_months": 재직개월수,
            "eligible": 자격 여부 (1년 이상),
            "calculation_details": 계산 상세 정보
        }
        
        법적 근거:
        - 근로기준법 제34조: 1년 이상 계속 근로한 근로자에게 퇴직금 지급
        - 평균임금 = 퇴직 전 3개월간 임금총액 / 90일(역일수)
        - 평균임금 < 통상임금일 경우, 통상임금 적용
        - 퇴직금 = 평균임금 × 30일 × (재직일수 / 365)
        """
        from .services import calculate_retirement_pay
        
        job = self.get_object()
        result = calculate_retirement_pay(job)
        return Response(result)

    @action(detail=True, methods=['get'], url_path='work-records')
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
        """GET: 리스트, POST: 추가/업데이트(weekday 단위)
        
        POST 시 스케줄 저장과 동시에 과거 날짜의 근로기록 자동 생성
        """
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
            
            # 스케줄 저장
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
            
            # 스케줄이 활성화되고 시간이 설정된 경우, 과거 날짜에 근로기록 자동 생성
            # 변경점(v3): 기존 기록이 있더라도 모두 **강제 덮어쓰기**하여
            #            주간 스케줄 변경 효과가 과거 달/날짜까지 즉시 반영되도록 함
            created_records_count = 0
            updated_empty_records_count = 0
            overridden_records_count = 0
            if enabled and start_time and end_time:
                from datetime import datetime as dt
                
                today = timezone.now().date()
                job_start_date = job.start_date
                
                # 근로 시작일부터 오늘까지 순회
                if job_start_date and job_start_date <= today:
                    current_date = job_start_date
                    
                    # 시간 문자열을 time 객체로 변환
                    try:
                        start_time_obj = dt.strptime(start_time, '%H:%M').time()
                        end_time_obj = dt.strptime(end_time, '%H:%M').time()
                    except ValueError:
                        start_time_obj = schedule.start_time
                        end_time_obj = schedule.end_time
                    
                    while current_date <= today:
                        # 해당 요일인 경우
                        if current_date.weekday() == weekday:
                            # 기존 근로기록이 없으면 생성
                            existing_record = WorkRecord.objects.filter(
                                employee=job,
                                work_date=current_date
                            ).first()
                            
                            if not existing_record:
                                # DateTime 객체 생성 (날짜 + 시간)
                                time_in_dt = datetime.combine(current_date, start_time_obj)
                                time_out_dt = datetime.combine(current_date, end_time_obj)
                                
                                WorkRecord.objects.create(
                                    employee=job,
                                    work_date=current_date,
                                    time_in=time_in_dt,
                                    time_out=time_out_dt,
                                    break_minutes=0
                                )
                                created_records_count += 1
                            else:
                                # 기존 기록을 **무조건** 스케줄 시간으로 덮어쓰기
                                try:
                                    prev_hours = float(existing_record.get_total_hours()) if (existing_record.time_in and existing_record.time_out) else 0.0
                                    existing_record.time_in = datetime.combine(current_date, start_time_obj)
                                    existing_record.time_out = datetime.combine(current_date, end_time_obj)
                                    if existing_record.break_minutes is None:
                                        existing_record.break_minutes = 0
                                    existing_record.save()
                                    if prev_hours == 0.0:
                                        updated_empty_records_count += 1
                                    else:
                                        overridden_records_count += 1
                                except Exception:
                                    pass
                        
                        current_date += timedelta(days=1)
            
            # 스케줄 변경 후 최신 통계 계산
            today = timezone.now().date()
            year = today.year
            month = today.month
            
            from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
            stats = compute_monthly_schedule_stats(job, year, month)
            dates = monthly_scheduled_dates(job, year, month)
            cumulative_stats = self.get_cumulative_stats_data(job)
            
            from .serializers import WorkScheduleSerializer
            message = f'주간 근무 스케줄이 저장되었습니다.'
            if created_records_count > 0:
                message += f' ({created_records_count}건의 근로기록이 자동 생성되었습니다.)'
            if updated_empty_records_count > 0:
                message += f' (취소된 {updated_empty_records_count}건이 스케줄로 복구되었습니다.)'
            if overridden_records_count > 0:
                message += f' (기존 기록 {overridden_records_count}건을 새 스케줄로 덮어썼습니다.)'
            
            return Response({
                'schedule': WorkScheduleSerializer(schedule).data,
                'stats': stats,
                'dates': dates,
                'cumulative_stats': cumulative_stats,
                'created_records': created_records_count,
                'updated_empty_records': updated_empty_records_count,
                'overridden_records': overridden_records_count,
                'message': message
            })

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

    @action(detail=True, methods=['delete'], url_path='monthly-work-records')
    def delete_monthly_work_records(self, request, pk=None):
        """특정 월의 모든 근로기록 삭제
        
        DELETE /api/labor/employees/<id>/monthly-work-records/?month=YYYY-MM
        """
        job = self.get_object()
        month = request.query_params.get('month')
        
        if not month:
            return Response(
                {'error': 'month parameter required (format: YYYY-MM)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            year, mon = map(int, month.split('-'))
        except Exception:
            return Response(
                {'error': 'month format error (expected: YYYY-MM)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 해당 월의 시작일과 종료일 계산
        from datetime import date
        import calendar as pycal
        from .models import MonthlySchedule
        
        start_date = date(year, mon, 1)
        _, last_day = pycal.monthrange(year, mon)
        end_date = date(year, mon, last_day)
        
        # 1. 해당 월의 근로기록(WorkRecord) 삭제
        work_records = job.work_records.filter(
            work_date__gte=start_date,
            work_date__lte=end_date
        )
        work_records_count = work_records.count()
        work_records.delete()
        
        # 2. 해당 월의 월별 스케줄(MonthlySchedule) 삭제
        monthly_schedules = MonthlySchedule.objects.filter(
            employee=job,
            year=year,
            month=mon
        )
        monthly_schedules_count = monthly_schedules.count()
        monthly_schedules.delete()
        
        total_deleted = work_records_count + monthly_schedules_count
        
        # 최신 통계 계산
        from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
        stats = compute_monthly_schedule_stats(job, year, mon)
        dates = monthly_scheduled_dates(job, year, mon)
        
        # 누적 통계도 함께 반환
        cumulative_stats = self.get_cumulative_stats_data(job)
        
        message_parts = []
        if work_records_count > 0:
            message_parts.append(f'근로기록 {work_records_count}건')
        if monthly_schedules_count > 0:
            message_parts.append(f'월별 스케줄 {monthly_schedules_count}건')
        
        if message_parts:
            message = f'{year}년 {mon}월의 {", ".join(message_parts)}이 삭제되었습니다.'
        else:
            message = f'{year}년 {mon}월에는 삭제할 데이터가 없습니다.'
        
        return Response({
            'message': message,
            'deleted_count': total_deleted,
            'work_records_deleted': work_records_count,
            'monthly_schedules_deleted': monthly_schedules_count,
            'stats': stats,
            'dates': dates,
            'cumulative_stats': cumulative_stats
        }, status=status.HTTP_200_OK)
    
    def get_cumulative_stats_data(self, job):
        """누적 통계 계산 헬퍼 메소드 - 실제 근로기록만 집계 (전체 기간)

        변경점:
        - 하한을 `job.start_date`로 제한하던 기존 로직을 제거하고, **사용자의 모든 실제 근로기록**을 집계합니다.
        - 상한은 오늘 날짜(`today`)까지만 포함합니다.
        - 디버깅을 위해 집계에 포함된 `record_ids` 및 레코드별 상세(`records_debug`)를 함께 반환합니다.
        """
        today = timezone.now().date()

        # 실제 근로기록만 조회 (스케줄 기반 예상 근로는 제외)
        work_records = WorkRecord.objects.filter(
            employee=job,
            work_date__lte=today
        ).order_by('work_date')

        total_hours = Decimal('0.0')
        total_work_days = 0
        record_ids = []
        records_debug = []

        # 실제 근로기록만 집계
        for record in work_records:
            hours = record.get_total_hours()
            # 디버깅용 상세 내역 수집
            records_debug.append({
                'id': record.id,
                'date': record.work_date.isoformat(),
                'time_in': record.time_in.isoformat() if record.time_in else None,
                'time_out': record.time_out.isoformat() if record.time_out else None,
                'break_minutes': record.break_minutes,
                'daily_work_minutes': float(hours) * 60.0 if hours else 0.0
            })
            if hours > 0:
                total_hours += hours
                total_work_days += 1
                record_ids.append(record.id)

        hourly_rate = job.hourly_rate or Decimal('0.0')
        total_earnings = total_hours * hourly_rate

        logger.info(
            f"[get_cumulative_stats_data] Job {job.id}: "
            f"records={work_records.count()}, hours={total_hours}, "
            f"days={total_work_days}, earnings={total_earnings}"
        )

        # 집계 시작일은 실제 기록 중 가장 이른 날짜로 설정 (없으면 None)
        earliest = work_records.first().work_date.isoformat() if work_records.exists() else None

        return {
            'total_hours': float(total_hours),
            'total_earnings': float(total_earnings),
            'total_work_days': total_work_days,
            'start_date': earliest,
            'record_ids': record_ids,
            'records_debug': records_debug,
        }

    @action(detail=True, methods=['get'], url_path='monthly-schedule')
    def monthly_schedule(self, request, pk=None):
        """주간 스케줄을 기반으로 해당 달의 스케줄 정보를 반환

        GET /api/labor/employees/<id>/monthly-schedule/?month=YYYY-MM
        응답: { dates: [ {date, day, is_scheduled, start_time, end_time} ] }
        """
        job = self.get_object()
        month = request.query_params.get('month')
        if not month:
            return Response({'error': 'month parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, mon = map(int, month.split('-'))
        except Exception:
            return Response({'error': 'month format error'}, status=status.HTTP_400_BAD_REQUEST)

        from .services import monthly_scheduled_dates
        dates = monthly_scheduled_dates(job, year, mon)
        return Response({'dates': dates})

    @action(detail=True, methods=['get'], url_path='monthly-summary')
    def monthly_summary(self, request, pk=None):
        """주간 스케줄을 기반으로 특정 달의 예정 근무일과 통계를 반환합니다.

        GET /api/labor/employees/<id>/monthly-summary/?month=YYYY-MM
        
        중요: 미래 월(현재 월 이후)의 경우 통계는 계산하되,
              실제 근로 발생 시점이 아니므로 별도 표시 필요
        
        반환 예:
        {
          'month': '2025-09',
          'is_future_month': false,
          'scheduled_dates': [...],
          'scheduled_total_hours': 80.0,
          'scheduled_estimated_salary': 800000.0,
          'scheduled_week_stats': [...],
          'scheduled_this_week_hours': 16.0
        }
        """
        job = self.get_object()
        month = request.query_params.get('month')
        if not month:
            return Response({'error': 'month parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, mon = map(int, month.split('-'))
        except Exception:
            return Response({'error': 'month format error'}, status=status.HTTP_400_BAD_REQUEST)

        # 미래 월 여부 확인
        today = timezone.now().date()
        today_year = today.year
        today_month = today.month
        is_future = (year > today_year) or (year == today_year and mon > today_month)

        from .services import compute_monthly_schedule_stats
        stats = compute_monthly_schedule_stats(job, year, mon)
        stats['month'] = month
        stats['is_future_month'] = is_future
        
        return Response(stats)

    @action(detail=True, methods=['get'], url_path='monthly-payroll')
    def monthly_payroll(self, request, pk=None):
        """해당 Job의 월별 실제 급여 예상액 계산(노동법 가산 포함)

        GET /api/labor/jobs/<id>/monthly-payroll/?month=YYYY-MM
        """
        job = self.get_object()
        month = request.query_params.get('month')
        if not month:
            return Response({'error': 'month parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, mon = map(int, month.split('-'))
        except Exception:
            return Response({'error': 'month format error'}, status=status.HTTP_400_BAD_REQUEST)

        from .services import compute_monthly_payroll
        data = compute_monthly_payroll(job, year, mon)
        return Response(data)

    @action(detail=True, methods=['get'], url_path='date-schedule')
    def date_schedule(self, request, pk=None):
        """특정 날짜의 기본 스케줄 정보 반환 (모달 기본값용)
        
        GET /api/labor/jobs/<id>/date-schedule/?date=YYYY-MM-DD
        응답: { 
            has_schedule: true/false,
            start_time: "13:00",
            end_time: "19:00",
            work_record: { ... } or null  // 실제 근로기록이 있으면 반환
        }
        """
        job = self.get_object()
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 해당 날짜의 요일 확인 (Python: 월요일=0)
        weekday = target_date.weekday()
        
        # 해당 요일의 스케줄 조회
        schedule = job.schedules.filter(weekday=weekday, enabled=True).first()
        
        # 실제 근로기록 조회
        work_record = job.work_records.filter(work_date=target_date).first()
        
        response_data = {
            'has_schedule': schedule is not None,
            'start_time': schedule.start_time.strftime('%H:%M') if schedule and schedule.start_time else None,
            'end_time': schedule.end_time.strftime('%H:%M') if schedule and schedule.end_time else None,
            'work_record': WorkRecordSerializer(work_record).data if work_record else None,
        }
        
        return Response(response_data)

    @action(detail=True, methods=['get', 'post'], url_path='monthly-schedule-override')
    def monthly_schedule_override(self, request, pk=None):
        """특정 월의 근무 스케줄 조회 및 설정
        
        GET /api/labor/employees/<id>/monthly-schedule-override/?year=2025&month=3
        - 해당 월의 MonthlySchedule이 있으면 반환, 없으면 기본 WorkSchedule 반환
        
        POST /api/labor/employees/<id>/monthly-schedule-override/
        {
            "year": 2025,
            "month": 3,
            "schedules": [
                {"weekday": 0, "start_time": "09:00", "end_time": "18:00", "enabled": true},
                {"weekday": 1, "start_time": "09:00", "end_time": "18:00", "enabled": true},
                ...
            ]
        }
        - 해당 월의 모든 근무 스케줄을 일괄 저장/업데이트
        - 해당 월의 기존 MonthlySchedule을 모두 삭제하고 새로 생성
        """
        from .models import MonthlySchedule
        from .serializers import MonthlyScheduleSerializer
        
        job = self.get_object()
        
        if request.method == 'GET':
            year = request.query_params.get('year')
            month = request.query_params.get('month')
            
            if not year or not month:
                return Response({'error': 'year and month parameters required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                year = int(year)
                month = int(month)
            except ValueError:
                return Response({'error': 'year and month must be integers'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 해당 월의 MonthlySchedule 조회
            monthly_schedules = MonthlySchedule.objects.filter(
                employee=job,
                year=year,
                month=month
            ).order_by('weekday')
            
            if monthly_schedules.exists():
                # 월별 스케줄이 있으면 반환
                serializer = MonthlyScheduleSerializer(monthly_schedules, many=True)
                return Response({
                    'has_override': True,
                    'schedules': serializer.data
                })
            else:
                # 월별 스케줄이 없으면 기본 주간 스케줄 반환
                from .serializers import WorkScheduleSerializer
                default_schedules = job.schedules.all().order_by('weekday')
                serializer = WorkScheduleSerializer(default_schedules, many=True)
                return Response({
                    'has_override': False,
                    'schedules': serializer.data
                })
        
        else:  # POST
            data = request.data
            year = data.get('year')
            month = data.get('month')
            schedules_data = data.get('schedules', [])
            default_break_map = data.get('default_break_minutes_by_weekday')
            weekly_rest_day = data.get('weekly_rest_day')
            
            if not year or not month:
                return Response({'error': 'year and month required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                year = int(year)
                month = int(month)
            except ValueError:
                return Response({'error': 'year and month must be integers'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 해당 월의 기존 MonthlySchedule 모두 삭제
            MonthlySchedule.objects.filter(
                employee=job,
                year=year,
                month=month
            ).delete()
            
            # 새 스케줄 생성
            from datetime import datetime as dt
            created_schedules = []
            schedule_map = {}  # weekday -> schedule 매핑
            
            for schedule_data in schedules_data:
                weekday = schedule_data.get('weekday')
                start_time_str = schedule_data.get('start_time')
                end_time_str = schedule_data.get('end_time')
                enabled = schedule_data.get('enabled', True)
                
                # 시간 문자열을 time 객체로 변환
                start_time_obj = None
                end_time_obj = None
                
                if enabled and start_time_str:
                    try:
                        start_time_obj = dt.strptime(start_time_str, '%H:%M').time()
                    except ValueError:
                        pass
                
                if enabled and end_time_str:
                    try:
                        end_time_obj = dt.strptime(end_time_str, '%H:%M').time()
                    except ValueError:
                        pass
                
                # enabled가 False이거나 시간이 없으면 비활성 상태로 저장
                monthly_schedule = MonthlySchedule.objects.create(
                    employee=job,
                    year=year,
                    month=month,
                    weekday=weekday,
                    start_time=start_time_obj,
                    end_time=end_time_obj,
                    enabled=enabled,
                    default_break_minutes_by_weekday=default_break_map if isinstance(default_break_map, dict) else None,
                    weekly_rest_day=weekly_rest_day if isinstance(weekly_rest_day, int) else None
                )
                created_schedules.append(monthly_schedule)
                
                # enabled된 스케줄만 매핑에 추가
                if enabled and start_time_obj and end_time_obj:
                    schedule_map[weekday] = monthly_schedule
            
            # 해당 월의 모든 날짜에 대해 근로기록 자동 생성
            import calendar as pycal
            today = timezone.now().date()
            _, last_day = pycal.monthrange(year, month)
            created_records_count = 0
            
            for day in range(1, last_day + 1):
                work_date = date(year, month, day)
                
                # 미래 날짜는 건너뛰기 (오늘까지만)
                if work_date > today:
                    continue
                
                weekday = work_date.weekday()
                
                # 해당 요일의 스케줄이 있으면 근로기록 생성/업데이트
                if weekday in schedule_map:
                    schedule = schedule_map[weekday]
                    
                    # 기존 근로기록 확인
                    existing_record = WorkRecord.objects.filter(
                        employee=job,
                        work_date=work_date
                    ).first()
                    
                    if not existing_record:
                        # 스케줄의 시간 객체는 이미 time 타입
                        # DateTime 객체 생성 (날짜 + 시간)
                        time_in_dt = datetime.combine(work_date, schedule.start_time)
                        time_out_dt = datetime.combine(work_date, schedule.end_time)
                        # 기본 휴게(분) 적용 (있으면)
                        base_break = None
                        try:
                            if schedule.default_break_minutes_by_weekday and isinstance(schedule.default_break_minutes_by_weekday, dict):
                                base_break = schedule.default_break_minutes_by_weekday.get(str(weekday))
                                if base_break is None:
                                    base_break = schedule.default_break_minutes_by_weekday.get(weekday)
                        except Exception:
                            base_break = None
                        
                        # 새 근로기록 생성
                        WorkRecord.objects.create(
                            employee=job,
                            work_date=work_date,
                            time_in=time_in_dt,
                            time_out=time_out_dt,
                            break_minutes=base_break if isinstance(base_break, int) else 0  # 기본값 또는 지정값
                        )
                        created_records_count += 1
                    else:
                        # 기존 기록이 0시간이라면 스케줄 시간으로 업데이트하여 복구
                        try:
                            if (not existing_record.time_in or not existing_record.time_out) or float(existing_record.get_total_hours()) == 0.0:
                                existing_record.time_in = datetime.combine(work_date, schedule.start_time)
                                existing_record.time_out = datetime.combine(work_date, schedule.end_time)
                                # 기본 휴게 적용
                                if isinstance(base_break, int):
                                    existing_record.break_minutes = base_break
                                elif existing_record.break_minutes is None:
                                    existing_record.break_minutes = 0
                                existing_record.save()
                                updated_empty_records_count += 1
                        except Exception:
                            pass
            
            # 최신 통계 및 캘린더 데이터 계산
            from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
            stats = compute_monthly_schedule_stats(job, year, month)
            dates = monthly_scheduled_dates(job, year, month)
            
            # 누적 통계도 함께 계산
            cumulative_stats = self.get_cumulative_stats_data(job)
            
            serializer = MonthlyScheduleSerializer(created_schedules, many=True)
            return Response({
                'message': f'{year}년 {month}월 근무 스케줄이 저장되었습니다. ({created_records_count}건의 근로기록 생성)',
                'schedules': serializer.data,
                'created_records': created_records_count,
                'updated_empty_records': updated_empty_records_count,
                'stats': stats,
                'dates': dates,
                'cumulative_stats': cumulative_stats
            })

    @action(detail=True, methods=['get'], url_path='cumulative-stats')
    def cumulative_stats(self, request, pk=None):
        """해당 알바의 전체 누적 통계 반환
        
        계산 기준 (v3 - 실제 근로기록만 집계):
        - 근로 시작일(start_date)부터 **오늘(현재 날짜)**까지의 **실제 근로기록만** 집계
        - **중요 변경**: 스케줄 기반 예상 근로는 제외 (실제로 일한 시간만 카운트)
        - 삭제 후 즉시 반영되도록 개선
        
        데이터 반영:
        - 실제 근로기록(WorkRecord)만 집계
        - 월별/주간 스케줄은 집계에서 제외
        
        GET /api/labor/jobs/<id>/cumulative-stats/
        응답: {
            'total_hours': 72.0,         # 실제 근무한 누적 시간
            'total_earnings': 864000,    # 실제 급여 (실제 시간 × 시급)
            'total_work_days': 8,        # 실제 근무한 일수
            'start_date': '2024-11-01'   # 근로 시작일
        }
        """
        job = self.get_object()
        
        # get_cumulative_stats_data 헬퍼 메소드 사용
        result = self.get_cumulative_stats_data(job)
        return Response(result)

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
            
            # 미래 날짜 입력 차단
            work_date_str = self.request.data.get('work_date')
            if work_date_str:
                from datetime import datetime
                work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
                today = timezone.now().date()
                if work_date > today:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError("미래 날짜에는 근로 기록을 입력할 수 없습니다.")
            
            serializer.save()
        except Employee.DoesNotExist:
            raise PermissionError("이 Job에 접근할 권한이 없습니다.")

    def create(self, request, *args, **kwargs):
        """근로기록 생성 후 최신 통계 반환"""
        response = super().create(request, *args, **kwargs)
        
        # 생성된 기록의 employee와 날짜 정보로 최신 통계 계산
        work_record = WorkRecord.objects.get(id=response.data['id'])
        employee = work_record.employee
        year = work_record.work_date.year
        month = work_record.work_date.month
        
        from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
        
        # 최신 통계 계산
        stats = compute_monthly_schedule_stats(employee, year, month)
        dates = monthly_scheduled_dates(employee, year, month)
        
        # 응답 데이터 구성
        result = dict(response.data)
        result['stats'] = stats
        result['dates'] = dates
        
        return Response(result, status=response.status_code)

    def perform_update(self, serializer):
        # ensure user owns this record
        instance = serializer.instance
        if instance.employee.user != self.request.user:
            raise PermissionError("이 작업을 수행할 권한이 없습니다.")
        
        # 미래 날짜 수정 차단
        work_date_str = self.request.data.get('work_date')
        if work_date_str:
            from datetime import datetime
            work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
            today = timezone.now().date()
            if work_date > today:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("미래 날짜의 근로 기록은 수정할 수 없습니다.")
        
        serializer.save()

    def update(self, request, *args, **kwargs):
        """근로기록 수정 후 최신 통계 반환"""
        response = super().update(request, *args, **kwargs)
        
        # 수정된 기록의 employee와 날짜 정보로 최신 통계 계산
        work_record = WorkRecord.objects.get(id=response.data['id'])
        employee = work_record.employee
        year = work_record.work_date.year
        month = work_record.work_date.month
        
        from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
        
        # 최신 통계 계산
        stats = compute_monthly_schedule_stats(employee, year, month)
        dates = monthly_scheduled_dates(employee, year, month)
        
        # 응답 데이터 구성
        result = dict(response.data)
        result['stats'] = stats
        result['dates'] = dates
        
        return Response(result, status=response.status_code)

    def perform_destroy(self, instance):
        if instance.employee.user != self.request.user:
            raise PermissionError("이 작업을 수행할 권한이 없습니다.")
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        """근로기록 삭제 전 정보 저장 후 최신 통계 반환"""
        instance = self.get_object()
        employee = instance.employee
        year = instance.work_date.year
        month = instance.work_date.month
        
        # 삭제 실행
        self.perform_destroy(instance)
        
        from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
        
        # 최신 통계 계산
        stats = compute_monthly_schedule_stats(employee, year, month)
        dates = monthly_scheduled_dates(employee, year, month)
        
        # 삭제 성공 응답에 통계 추가
        return Response({
            'message': '근로기록이 삭제되었습니다.',
            'stats': stats,
            'dates': dates
        }, status=status.HTTP_200_OK)


class CalculationResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CalculationResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CalculationResult.objects.filter(employee__user=self.request.user)


from .serializers import AnnualLeaveSummarySerializer


@api_view(['GET'])
@drf_permission_classes([IsAuthenticated])
def holidays(request):
    """월 단위 한국 공휴일 정보 반환

    GET /api/labor/holidays/?month=YYYY-MM
    응답: [{"date": "2025-10-03", "name": "개천절", "type": "LEGAL"}, ...]
    type 필드는 LEGAL 또는 OBSERVANCE 값을 가집니다.
    """
    month_param = request.query_params.get('month')
    if not month_param:
        return Response({'error': 'month parameter required (YYYY-MM)'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        year_str, month_str = month_param.split('-')
        year = int(year_str)
        month = int(month_str)
        if month < 1 or month > 12:
            raise ValueError
    except ValueError:
        return Response({'error': 'month must be formatted as YYYY-MM'}, status=status.HTTP_400_BAD_REQUEST)

    data = get_holidays_for_month(year, month)
    return Response(data)


@api_view(['GET'])
@drf_permission_classes([IsAuthenticated])
def annual_leave_summary(request):
    """연차 요약 정보 조회
    
    GET /api/leave/annual/summary/?workplace_id=<employee_id>
    
    Response:
    {
        "as_of": "2025-01-15",
        "earned_days": 5.0,
        "used_days": 2.0,
        "remaining_days": 3.0,
        "rule_version": "simplified",
        "is_eligible": true,
        "reason": ""
    }
    """
    workplace_id = request.query_params.get('workplace_id')
    
    if not workplace_id:
        return Response(
            {'error': 'workplace_id 파라미터가 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        employee = Employee.objects.get(id=workplace_id, user=request.user)
    except Employee.DoesNotExist:
        return Response(
            {'error': '해당 근로정보를 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 기준일: 오늘
    as_of = date.today()
    
    # 1. 주당 근무시간 확인 (15시간 이상이어야 연차 발생 대상)
    schedules = WorkSchedule.objects.filter(employee=employee, enabled=True)
    weekly_hours = sum(
        (datetime.combine(date.min, s.end_time) - datetime.combine(date.min, s.start_time)).total_seconds() / 3600
        for s in schedules
    )
    
    if weekly_hours < 15:
        return Response({
            'as_of': as_of,
            'earned_days': 0,
            'used_days': 0,
            'remaining_days': 0,
            'rule_version': 'simplified',
            'is_eligible': False,
            'reason': '주당 근무시간이 15시간 미만입니다.'
        })
    
    # 2. 근무 기간 계산
    employment_start = employee.start_date
    months_employed = relativedelta(as_of, employment_start).months + \
                     relativedelta(as_of, employment_start).years * 12
    
    # 3. 발생 연차 계산
    earned_days = Decimal('0')
    
    if months_employed < 12:
        # 1년 미만: 개근한 월마다 1일 (최대 11일)
        # 개근 확인: 각 월의 스케줄된 날짜 수와 실제 근무 기록 수 비교
        perfect_months = 0
        current_month = employment_start.replace(day=1)
        
        while current_month < as_of:
            # 해당 월의 예정 근무일 수 계산
            from .services import monthly_scheduled_dates
            scheduled_dates = monthly_scheduled_dates(employee, current_month.year, current_month.month)
            
            # 실제 근무 기록 수
            work_records = WorkRecord.objects.filter(
                employee=employee,
                work_date__year=current_month.year,
                work_date__month=current_month.month
            ).count()
            
            if len(scheduled_dates) > 0 and work_records >= len(scheduled_dates):
                perfect_months += 1
            
            # 다음 달로 이동
            if current_month.month == 12:
                current_month = current_month.replace(year=current_month.year + 1, month=1)
            else:
                current_month = current_month.replace(month=current_month.month + 1)
        
        earned_days = min(Decimal(perfect_months), Decimal('11'))
    
    else:
        # 1년 이상: 지난 1년간 출근율 80% 이상이면 15일
        attendance_rate = employee.attendance_rate_last_year or 0
        
        if attendance_rate >= 80:
            earned_days = Decimal('15')
        else:
            earned_days = Decimal('0')
    
    # 4. 사용 연차 계산
    used_days = LeaveUsage.objects.filter(
        employee=employee,
        leave_type='annual',
        leave_date__lte=as_of
    ).aggregate(total=models.Sum('days'))['total'] or Decimal('0')
    
    # 5. 잔여 연차
    remaining_days = earned_days - used_days
    
    serializer = AnnualLeaveSummarySerializer({
        'as_of': as_of,
        'earned_days': earned_days,
        'used_days': used_days,
        'remaining_days': remaining_days,
        'rule_version': 'simplified',
        'is_eligible': True,
        'reason': ''
    })
    
    return Response(serializer.data)

