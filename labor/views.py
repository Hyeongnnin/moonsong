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
import calendar as pycal  # calendar 모듈 import 추가
from .models import Employee, WorkRecord, CalculationResult, LeaveUsage, WorkSchedule
from .services import job_to_inputs, evaluate_labor, calculate_annual_leave, compute_monthly_schedule_stats, monthly_scheduled_dates, compute_payroll_summary
from .holidays import get_holidays_for_month
from .serializers import (
    EmployeeSerializer,
    EmployeeUpdateSerializer,
    WorkRecordSerializer,
    CalculationResultSerializer,
    JobSummarySerializer,
    PayrollSummarySerializer
)
from django.http import Http404
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

today = date.today()


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

    def destroy(self, request, *args, **kwargs):
        """알바 정보 삭제 후, 다음으로 선택할 알바 ID를 반환"""
        try:
            instance = self.get_object()
        except Http404:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # perform_destroy는 내부적으로 instance.delete()를 호출합니다.
        self.perform_destroy(instance)

        # 사용자의 나머지 알바 목록 조회 (최신순으로)
        remaining_employees = self.get_queryset().order_by('-id')
        next_employee_id = None
        if remaining_employees.exists():
            next_employee_id = remaining_employees.first().id

        return Response({
            'message': '근로정보가 삭제되었습니다.',
            'next_employee_id': next_employee_id
        }, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=['get'], url_path='payroll-summary')
    def payroll_summary(self, request, pk=None):
        """월별 급여 집계 및 요약 API"""
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
        
        summary_data = compute_payroll_summary(job, year, month)
        serializer = PayrollSummarySerializer(summary_data)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='holiday-pay')
    def holiday_pay(self, request, pk=None):
        """이번 주 주휴수당 계산 (소정근로일 개근 기준)

        Phase 2 변경사항:
        - 소정근로일 개근 여부로 자격 판단
        - REGULAR_WORK + ANNUAL_LEAVE만 출근 인정
        - 기준 날짜는 ?date=YYYY-MM-DD 쿼리 파라미터로 전달
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
        calc_method = rules.get('calculation_method', 'daily_average')

        # 기준 날짜가 속한 주 범위 (월~일)
        start_of_week = target_date - timedelta(days=target_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # 이번 주 근로기록
        records = job.work_records.filter(
            work_date__gte=start_of_week,
            work_date__lte=end_of_week
        )
        record_map = {r.work_date: r for r in records}

        # 디버깅 로그
        logger.info(f'=== Holiday Pay Debug v2 (Employee {job.id}) ===')
        logger.info(f'Week range: {start_of_week} ~ {end_of_week}')
        logger.info(f'Records count: {records.count()}')

        # 소정근로일 목록 수집 및 개근 체크
        scheduled_dates = []
        weekly_scheduled_hours = Decimal('0')
        perfect_attendance = True
        attendance_details = []

        current_date = start_of_week
        while current_date <= end_of_week:
            # 소정근로일 판정
            is_scheduled = job.is_scheduled_workday(current_date)
            
            if is_scheduled:
                scheduled_dates.append(current_date)
                
                # 스케줄 정보로 예정 시간 계산
                schedule_info = job.get_schedule_for_date(current_date)
                if schedule_info['start_time'] and schedule_info['end_time']:
                    dummy_date = date(2000, 1, 1)
                    dt_start = datetime.combine(dummy_date, schedule_info['start_time'])
                    dt_end = datetime.combine(dummy_date, schedule_info['end_time'])
                    
                    # [Fix] overnight and next_day_work handling
                    if dt_end < dt_start:
                        dt_end += timedelta(days=1)
                    
                    diff = dt_end - dt_start
                    total_mins = (diff.total_seconds() / 60.0) + float(schedule_info.get('next_day_work_minutes', 0))
                    break_mins = float(schedule_info.get('break_minutes', 0))
                    
                    hours = Decimal(str(max(0.0, total_mins - break_mins) / 60.0))
                    weekly_scheduled_hours += hours
                
                # 실제 근로기록 확인
                record = record_map.get(current_date)
                if record:
                    # REGULAR_WORK 또는 ANNUAL_LEAVE만 출근 인정
                    is_attended = record.attendance_status in ['REGULAR_WORK', 'ANNUAL_LEAVE']
                    attendance_details.append({
                        'date': current_date.isoformat(),
                        'is_scheduled': True,
                        'attendance_status': record.attendance_status,
                        'is_attended': is_attended,
                        'hours': float(record.get_total_hours())
                    })
                    if not is_attended:
                        perfect_attendance = False
                else:
                    # 근로기록 없음 = 결근
                    perfect_attendance = False
                    attendance_details.append({
                        'date': current_date.isoformat(),
                        'is_scheduled': True,
                        'attendance_status': None,
                        'is_attended': False,
                        'hours': 0
                    })
            
            current_date += timedelta(days=1)

        scheduled_days_count = len(scheduled_dates)
        
        # 주간 소정근로시간 결정: 계약상 시간 우선, 없으면 스케줄 합산
        is_estimated = job.contract_weekly_hours is None
        total_weekly_hours = Decimal(str(job.contract_weekly_hours)) if not is_estimated else weekly_scheduled_hours

        # 조건 1: 주 15시간 미만이면 0원
        if total_weekly_hours < min_weekly_hours:
            return Response({
                'amount': 0,
                'hours': 0,
                'reason': 'less_than_threshold',
                'weekly_scheduled_hours': float(total_weekly_hours),
                'scheduled_days_count': scheduled_days_count,
                'perfect_attendance': perfect_attendance,
                'attendance_details': attendance_details,
                'policy_threshold': float(min_weekly_hours),
                'week_start': start_of_week.isoformat(),
                'week_end': end_of_week.isoformat(),
                'is_estimated': is_estimated
            })

        # 조건 2: 소정근로일 개근하지 않으면 0원
        if not perfect_attendance:
            return Response({
                'amount': 0,
                'hours': 0,
                'reason': 'not_perfect_attendance',
                'weekly_scheduled_hours': float(total_weekly_hours),
                'scheduled_days_count': scheduled_days_count,
                'perfect_attendance': perfect_attendance,
                'attendance_details': attendance_details,
                'policy_threshold': float(min_weekly_hours),
                'week_start': start_of_week.isoformat(),
                'week_end': end_of_week.isoformat(),
                'is_estimated': is_estimated
            })

        # 1일 소정근로시간 (주휴시간) 계산
        if scheduled_days_count > 0:
            daily_avg_hours = total_weekly_hours / Decimal(str(scheduled_days_count))
        else:
            daily_avg_hours = Decimal('0')

        # 주휴수당 = 1일 소정근로시간 × 시급
        holiday_pay = daily_avg_hours * job.hourly_rate

        return Response({
            'amount': float(holiday_pay),
            'hours': float(daily_avg_hours),
            'reason': 'eligible',
            'weekly_scheduled_hours': float(total_weekly_hours),
            'scheduled_days_count': scheduled_days_count,
            'perfect_attendance': perfect_attendance,
            'attendance_details': attendance_details,
            'policy_threshold': float(min_weekly_hours),
            'week_start': start_of_week.isoformat(),
            'week_end': end_of_week.isoformat(),
            'is_estimated': is_estimated
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
            is_overnight = data.get('is_overnight', False)
            next_day_work_minutes = int(data.get('next_day_work_minutes', 0))
            break_minutes = int(data.get('break_minutes', 0))
            enabled = data.get('enabled', 'true') in ['1', 'true', True, 'True']
            
            # 스케줄 저장
            schedule, created = job.schedules.get_or_create(weekday=weekday, defaults={
                'start_time': start_time or None,
                'end_time': end_time or None,
                'is_overnight': is_overnight,
                'next_day_work_minutes': next_day_work_minutes,
                'break_minutes': break_minutes,
                'enabled': enabled,
            })
            if not created:
                schedule.start_time = start_time or None
                schedule.end_time = end_time or None
                schedule.is_overnight = is_overnight
                schedule.next_day_work_minutes = next_day_work_minutes
                schedule.break_minutes = break_minutes
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
                
                today = timezone.localdate()
                job_start_date = job.start_date
                
                # 반복 시작 날짜 설정: 근로 시작일이 있으면 그 날짜부터, 없으면 오늘부터
                # (단, 근로 시작일이 오늘보다 미래이면 안됨)
                start_loop_date = job_start_date if job_start_date and job_start_date <= today else today

                # 근로 시작일부터 오늘까지 순회
                if start_loop_date <= today:
                    current_date = start_loop_date
                    
                    # 시간 문자열을 time 객체로 변환
                    try:
                        start_time_obj = dt.strptime(start_time, '%H:%M').time()
                        end_time_obj = dt.strptime(end_time, '%H:%M').time()
                    except ValueError:
                        start_time_obj = schedule.start_time
                        end_time_obj = schedule.end_time
                    
                    while current_date <= today:
                        # 해당 요일이고, 근로 시작일 이후인 경우
                        if current_date.weekday() == weekday and (not job_start_date or current_date >= job_start_date):
                            # 기존 근로기록이 없으면 생성
                            existing_record = WorkRecord.objects.filter(
                                employee=job,
                                work_date=current_date
                            ).first()
                            
                            if not existing_record:
                                # DateTime 객체 생성 (날짜 + 시간)
                                time_in_dt = datetime.combine(current_date, start_time_obj)
                                
                                # is_overnight이면 퇴근시간을 다음날로 설정
                                if schedule.is_overnight:
                                    next_date = current_date + timedelta(days=1)
                                    time_out_dt = datetime.combine(next_date, end_time_obj)
                                else:
                                    time_out_dt = datetime.combine(current_date, end_time_obj)
                                
                                WorkRecord.objects.create(
                                    employee=job,
                                    work_date=current_date,
                                    time_in=time_in_dt,
                                    time_out=time_out_dt,
                                    is_overnight=schedule.is_overnight,
                                    next_day_work_minutes=schedule.next_day_work_minutes,
                                    break_minutes=schedule.break_minutes
                                )
                                created_records_count += 1
                            else:
                                # 기존 기록을 **무조건** 스케줄 시간으로 덮어쓰기
                                try:
                                    prev_hours = float(existing_record.get_total_hours()) if (existing_record.time_in and existing_record.time_out) else 0.0
                                    existing_record.time_in = datetime.combine(current_date, start_time_obj)
                                    
                                    # is_overnight이면 퇴근시간을 다음날로 설정
                                    if schedule.is_overnight:
                                        next_date = current_date + timedelta(days=1)
                                        existing_record.time_out = datetime.combine(next_date, end_time_obj)
                                    else:
                                        existing_record.time_out = datetime.combine(current_date, end_time_obj)
                                    
                                    existing_record.is_overnight = schedule.is_overnight
                                    existing_record.next_day_work_minutes = schedule.next_day_work_minutes
                                    existing_record.break_minutes = schedule.break_minutes
                                    existing_record.save()
                                    if prev_hours == 0.0:
                                        updated_empty_records_count += 1
                                    else:
                                        overridden_records_count += 1
                                except Exception:
                                    pass
                        
                        current_date += timedelta(days=1)
            
            # 스케줄 변경 후 최신 통계 계산
            today = timezone.localdate()
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
        """월별 캘린더 데이터 반환 (소정근로일 정보 포함)
        
        Phase 3: 소정근로일 판정 시 월별/주간 스케줄 구분 정보 추가
        - 월별 스케줄이 없으면 주간 스케줄을 fallback으로 사용
        - source 필드로 "monthly" | "weekly" 구분
        - 스케줄 기반 기본 시간 정보 제공
        """
        from .models import MonthlySchedule, WorkSchedule
        
        job = self.get_object()
        month = request.query_params.get('month')  # YYYY-MM
        
        logger.info(f'[calendar] API 호출됨 - job_id={job.id}, month={month}')
        
        if not month:
            return Response({'error': 'month parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, mon = map(int, month.split('-'))
        except Exception:
            return Response({'error': 'month format error'}, status=status.HTTP_400_BAD_REQUEST)
        
        _, lastday = pycal.monthrange(year, mon)
        logger.info(f'[calendar] {year}-{mon:02d} 처리 중, 총 {lastday}일')
        
        # 주간 스케줄 전체 조회 (디버깅용)
        all_schedules = WorkSchedule.objects.filter(employee=job)
        logger.info(f'[calendar] 주간 스케줄 총 {all_schedules.count()}개')
        for ws in all_schedules:
            logger.info(f'[calendar]   - weekday={ws.weekday}, enabled={ws.enabled}, '
                       f'start={ws.start_time}, end={ws.end_time}')
        
        # 1. 공통 서비스 함수를 사용하여 날짜별 데이터 생성 (중복 로직 제거)
        from .services import monthly_scheduled_dates
        dates = monthly_scheduled_dates(job, year, mon)
        
        # 2. 결과 반환
        logger.info(f'[calendar] 응답 데이터: {len(dates)}개 날짜, '
                   f'소정근로일={sum(1 for d in dates if d["is_scheduled_workday"])}일')
        
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

        Phase 2 변경점:
        - attendance_status별 통계 추가
        - 소정근로일 vs 추가근무 구분 통계
        """
        today = timezone.localdate()

        # 실제 근로기록만 조회 (스케줄 기반 예상 근로는 제외)
        work_records = WorkRecord.objects.filter(
            employee=job,
            work_date__lte=today
        ).order_by('work_date')

        from .holidays import get_holidays_for_month
        from .services import calculate_annual_leave_v2
        
        total_hours = Decimal('0.0')
        total_earnings = Decimal('0.0')
        total_work_days = 0
        record_ids = []
        records_debug = []
        
        # Phase 2: 출결 상태별 통계
        regular_work_hours = Decimal('0.0')
        extra_work_hours = Decimal('0.0')
        regular_work_days = 0
        extra_work_days = 0
        annual_leave_days = 0
        absent_days = 0
        sick_leave_days = 0

        # 연도별/월별로 공휴일 정보를 캐싱하여 반복적인 API/DB 조회를 방지할 수 있지만, 
        # 여기서는 단순함을 위해 각 기록의 날짜에 대해 체크하거나 월 단위로 묶어서 처리합니다.
        # 누적 통계는 기록이 많을 수 있으므로 최적화가 필요할 수 있습니다.
        
        hourly_rate = job.hourly_rate or Decimal('0.0')
        is_over_5 = job.is_workplace_over_5

        # 기록들의 연/월 범위를 구함
        if work_records.exists():
            dates = work_records.values_list('work_date', flat=True)
            min_date = min(dates)
            max_date = max(dates)
            
            # 모든 해당 월의 공휴일 수집
            all_holidays = {} # (year, month) -> set of holiday dates
            curr_y, curr_m = min_date.year, min_date.month
            while (curr_y, curr_m) <= (max_date.year, max_date.month):
                h_list = get_holidays_for_month(curr_y, curr_m)
                all_holidays[(curr_y, curr_m)] = {h['date'] for h in h_list if h['type'] == 'LEGAL'}
                if curr_m == 12:
                    curr_y += 1
                    curr_m = 1
                else:
                    curr_m += 1

            for record in work_records:
                hours = record.get_total_hours()
                attendance_status = record.attendance_status or 'REGULAR_WORK'
                dt = record.work_date
                
                # 휴일 여부 판정
                is_holiday = False
                if dt.weekday() == 6: # Sunday
                    is_holiday = True
                else:
                    h_set = all_holidays.get((dt.year, dt.month), set())
                    if dt.isoformat() in h_set:
                        is_holiday = True

                # 디버깅용 상세 내역 수집
                records_debug.append({
                    'id': record.id,
                    'date': dt.isoformat(),
                    'time_in': record.time_in.isoformat() if record.time_in else None,
                    'time_out': record.time_out.isoformat() if record.time_out else None,
                    'break_minutes': record.break_minutes,
                    'daily_work_minutes': float(hours) * 60.0 if hours else 0.0,
                    'attendance_status': attendance_status,
                    'is_holiday': is_holiday
                })
                
                if hours > 0:
                    total_hours += hours
                    record_ids.append(record.id)
                    
                    # 수당 계산
                    day_pay = hours * hourly_rate
                    if is_over_5:
                        # 1. 휴일 가산 수당 (50%)
                        if is_holiday:
                            day_pay += hours * hourly_rate * Decimal('0.5')
                        
                        # 2. 야간 가산 수당 (50%)
                        night_h = record.get_night_hours()
                        if night_h > 0:
                            day_pay += night_h * hourly_rate * Decimal('0.5')
                    
                    total_earnings += day_pay
                    
                    if attendance_status == 'REGULAR_WORK':
                        regular_work_hours += hours
                        regular_work_days += 1
                        total_work_days += 1
                    elif attendance_status == 'EXTRA_WORK':
                        extra_work_hours += hours
                        extra_work_days += 1
                        total_work_days += 1
                
                if attendance_status == 'ANNUAL_LEAVE':
                    annual_leave_days += 1
                elif attendance_status == 'ABSENT':
                    absent_days += 1
                elif attendance_status == 'SICK_LEAVE':
                    sick_leave_days += 1

        # Future Scheduled Work (Remainder of Current Month)
        # 사용자 요청: 현재 월의 남은 기간에 대한 예정된 근무도 누적 통계에 포함
        from calendar import monthrange
        if True: #Indent block preservation trick for readability if needed, but here we just dedent
            _, last_day_of_month = monthrange(today.year, today.month)
            month_end = date(today.year, today.month, last_day_of_month)
            
            curr_future = today + timedelta(days=1)
            while curr_future <= month_end:
                # 미래에 이미 WorkRecord가 존재할 수도 있음 (예: 미리 휴가 신청)
                # 이 경우 위 루프에서 처리되지 않았으므로(lte=today 필터 때문), 여기서 확인 필요
                # 하지만 get_cumulative_stats_data는 원래 '실적' 위주였음.
                # 편의상 미래의 WorkRecord는 아직 없다고 가정하거나, 있어도 스케줄대로 계산
                # (정확히 하려면 WorkRecord 조회 조건을 전체로 넓히고 loop에서 today 기준으로 분기하는게 낫지만,
                #  기존 로직 최소 침습을 위해 별도 루프로 처리)
                
                # 해당 날짜의 WorkRecord 확인
                future_record = WorkRecord.objects.filter(employee=job, work_date=curr_future).first()
                f_hours = 0.0
                f_pay = Decimal('0')
                is_f_worked = False
                
                if future_record:
                    # 기록이 있으면 기록 우선 (단, 결근 등 제외)
                    if future_record.attendance_status in ['REGULAR_WORK', 'EXTRA_WORK', 'ANNUAL_LEAVE']:
                        is_f_worked = True # 연차도 근무일수에는 포함 안하지만 급여는 줌? 위 로직엔 연차 급여 없음. 
                        # 위 로직(808)에 따르면 day_pay = hours * hourly_rate.
                        # 연차여도 시간 있으면 돈 줌.
                        if future_record.get_total_hours() > 0:
                            f_hours = float(future_record.get_total_hours())
                else:
                    # 기록 없으면 스케줄 확인
                    if job.is_scheduled_workday(curr_future):
                        s_info = job.get_schedule_for_date(curr_future)
                        if s_info['is_scheduled']:
                             dummy_date = date(2000, 1, 1)
                             if s_info['start_time'] and s_info['end_time']:
                                dt_start = datetime.combine(dummy_date, s_info['start_time'])
                                dt_end = datetime.combine(dummy_date, s_info['end_time'])
                                if dt_end < dt_start:
                                    dt_end += timedelta(days=1)
                                dur = (dt_end - dt_start).total_seconds() / 60.0 + float(s_info.get('next_day_work_minutes', 0))
                                brk = float(s_info.get('break_minutes', 0))
                                f_hours = max(0.0, (dur - brk) / 60.0)
                                is_f_worked = True
                
                if f_hours > 0:
                    total_hours += Decimal(str(f_hours))
                    # 수당 계산 (야간/휴일 등은 복잡하니 기본급만 추정하거나, 위와 동일 로직 적용)
                    # 여기선 일단 기본급만 적용 (단순화)
                    f_pay = Decimal(str(f_hours)) * hourly_rate
                    total_earnings += f_pay
                    
                    if is_f_worked:
                        total_work_days += 1
                        # 미래는 일단 'REGULAR_WORK'로 간주하여 카운트
                        regular_work_days += 1
                        regular_work_hours += Decimal(str(f_hours))
                
                curr_future += timedelta(days=1)

            total_earnings = total_earnings.quantize(Decimal('1')) # 원 단위 절사
            regular_work_earnings = regular_work_hours * hourly_rate
            extra_work_earnings = extra_work_hours * hourly_rate
        else:
            # 기록이 없는 경우 초기화
            hourly_rate = job.hourly_rate or Decimal('0.0')
            regular_work_earnings = Decimal('0.0')
            extra_work_earnings = Decimal('0.0')

        logger.info(
            f"[get_cumulative_stats_data] Job {job.id}: "
            f"records={work_records.count()}, hours={total_hours}, "
            f"days={total_work_days}, earnings={total_earnings}, "
            f"regular={regular_work_days}d/{regular_work_hours}h, "
            f"extra={extra_work_days}d/{extra_work_hours}h"
        )

        # 집계 시작일은 실제 기록 중 가장 이른 날짜로 설정 (없으면 None)
        earliest = work_records.first().work_date if work_records.exists() else None
        
        # Phase 3: 누적 확정 주휴수당 계산 (이미 종료된 주만 합산)
        total_confirmed_holiday_pay = 0
        if earliest:
            from .services import calculate_weekly_holiday_pay_v2
            # 근로 시작일부터 오늘까지 주 단위로 순회
            # 주의 시작인 월요일부터 계산 시작
            curr_week_start = earliest - timedelta(days=earliest.weekday())
            while curr_week_start <= today:
                week_end = curr_week_start + timedelta(days=6)
                # 주의 종료일이 오늘보다 이전이면 확정분으로 간주
                if week_end < today:
                    h_res = calculate_weekly_holiday_pay_v2(job, curr_week_start)
                    total_confirmed_holiday_pay += h_res['amount']
                curr_week_start += timedelta(days=7)

        # 공제 계산 (누적 업적용)
        import math
        gross_pay = float(total_earnings) + total_confirmed_holiday_pay
        total_deduction = 0

        if job.deduction_type == 'FOUR_INSURANCE':
            # 국민연금 4.5%
            pension = math.floor((gross_pay * 0.045) / 10) * 10
            # 건강보험 3.545%
            health = math.floor((gross_pay * 0.03545) / 10) * 10
            # 장기요양보험 (건강보험의 12.95%)
            care = math.floor((health * 0.1295) / 10) * 10
            # 고용보험 0.9%
            employment = math.floor((gross_pay * 0.009) / 10) * 10
            
            total_deduction = pension + health + care + employment
            
        elif job.deduction_type == 'FREELANCE':
            # 3.3%
            tax = math.floor((gross_pay * 0.033) / 10) * 10
            total_deduction = tax
        
        achievement_total = gross_pay - total_deduction

        return {
            'total_hours': float(total_hours),
            'total_earnings': float(total_earnings), # 순수 근로 기준
            'total_work_days': total_work_days,
            'total_confirmed_holiday_pay': total_confirmed_holiday_pay,
            'achievement_total': achievement_total, # 세후 (공제 반영)
            'total_gross_pay': gross_pay, # 세전
            'total_deduction': total_deduction, # 공제액
            'start_date': earliest.isoformat() if earliest else None,
            'record_ids': record_ids,
            'records_debug': records_debug,
            # Phase 2 추가: 출결 상태별 통계
            'regular_work_hours': float(regular_work_hours),
            'regular_work_days': regular_work_days,
            'regular_work_earnings': float(regular_work_earnings),
            'extra_work_hours': float(extra_work_hours),
            'extra_work_days': extra_work_days,
            'extra_work_earnings': float(extra_work_earnings),
            'annual_leave_days': annual_leave_days,
            'absent_days': absent_days,
            'sick_leave_days': sick_leave_days,
            'annual_leave_summary': calculate_annual_leave_v2(job, today.year),
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
        today = timezone.localdate()
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
        """특정 날짜의 스케줄 정보 및 소정근로일 여부 반환
        
        GET /api/labor/jobs/<id>/date-schedule/?date=YYYY-MM-DD
        응답: { 
            is_scheduled_workday: true/false,  # 소정근로일 여부
            has_schedule: true/false,
            start_time: "13:00",
            end_time: "19:00",
            break_minutes: 60,
            is_overnight: false,
            next_day_work_minutes: 0,
            work_record: { ... } or null,  # 실제 근로기록
            suggested_attendance_status: "REGULAR_WORK" or "EXTRA_WORK"  # 기본값 제안
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
        
        # 소정근로일 여부 및 스케줄 정보
        is_scheduled = job.is_scheduled_workday(target_date)
        schedule_info = job.get_schedule_for_date(target_date)
        
        # 실제 근로기록 조회
        work_record = job.work_records.filter(work_date=target_date).first()
        
        # 출결 상태 기본값 제안
        suggested_attendance_status = 'REGULAR_WORK' if is_scheduled else 'EXTRA_WORK'
        
        response_data = {
            'is_scheduled_workday': is_scheduled,
            'has_schedule': schedule_info['is_scheduled'],
            'start_time': schedule_info['start_time'].strftime('%H:%M') if schedule_info['start_time'] else None,
            'end_time': schedule_info['end_time'].strftime('%H:%M') if schedule_info['end_time'] else None,
            'break_minutes': schedule_info['break_minutes'],
            'is_overnight': schedule_info['is_overnight'],
            'next_day_work_minutes': schedule_info['next_day_work_minutes'],
            'work_record': WorkRecordSerializer(work_record).data if work_record else None,
            'suggested_attendance_status': suggested_attendance_status,
        }
        
        return Response(response_data)

    @action(detail=True, methods=['get'], url_path='monthly-holiday-pay')
    def monthly_holiday_pay(self, request, pk=None):
        """특정 월의 주휴수당 내역 (주별 상세 + 월 누적 확정분)"""
        job = self.get_object()
        month_str = request.query_params.get('month')
        if not month_str:
            return Response({'error': 'month parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year, month = map(int, month_str.split('-'))
        except ValueError:
            return Response({'error': 'Invalid month format'}, status=status.HTTP_400_BAD_REQUEST)
            
        from .services import get_monthly_holiday_pay_info
        info = get_monthly_holiday_pay_info(job, year, month)
        return Response(info)

    @action(detail=True, methods=['get'], url_path='holiday-pay-v2')
    def holiday_pay_v2(self, request, pk=None):
        """특정 날짜 기준 주휴수당 계산 v2"""
        job = self.get_object()
        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'date format error'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = date.today()
            
        from .services import calculate_weekly_holiday_pay_v2
        res = calculate_weekly_holiday_pay_v2(job, target_date)
        return Response(res)

    @action(detail=True, methods=['get'], url_path='severance')
    def severance(self, request, pk=None):
        """퇴직금 예상액 정보 조회 (MVP v2)"""
        job = self.get_object()
        from .services import calculate_severance_v2
        res = calculate_severance_v2(job)
        return Response(res)

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
                is_overnight = schedule_data.get('is_overnight', False)
                next_day_work_minutes = int(schedule_data.get('next_day_work_minutes', 0))
                break_minutes = int(schedule_data.get('break_minutes', 0))
                
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
                    is_overnight=is_overnight,
                    next_day_work_minutes=next_day_work_minutes,
                    break_minutes=break_minutes,
                    enabled=enabled,
                    weekly_rest_day=weekly_rest_day if isinstance(weekly_rest_day, int) else None
                )
                created_schedules.append(monthly_schedule)
                
                # enabled된 스케줄만 매핑에 추가
                if enabled and start_time_obj and end_time_obj:
                    schedule_map[weekday] = monthly_schedule
            
            # 해당 월의 모든 날짜에 대해 근로기록 자동 생성
            today = timezone.localdate()
            _, last_day = pycal.monthrange(year, month)
            created_records_count = 0
            updated_empty_records_count = 0  # 초기화 추가
            
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
                        
                        # is_overnight이면 퇴근시간을 다음날로 설정
                        if schedule.is_overnight:
                            next_date = work_date + timedelta(days=1)
                            time_out_dt = datetime.combine(next_date, schedule.end_time)
                        else:
                            time_out_dt = datetime.combine(work_date, schedule.end_time)
                        
                        # 새 근로기록 생성
                        WorkRecord.objects.create(
                            employee=job,
                            work_date=work_date,
                            time_in=time_in_dt,
                            time_out=time_out_dt,
                            is_overnight=schedule.is_overnight,
                            next_day_work_minutes=schedule.next_day_work_minutes,
                            break_minutes=schedule.break_minutes
                        )
                        created_records_count += 1
                    else:
                        # 기존 기록이 0시간이라면 스케줄 시간으로 업데이트하여 복구
                        try:
                            if (not existing_record.time_in or not existing_record.time_out) or float(existing_record.get_total_hours()) == 0.0:
                                existing_record.time_in = datetime.combine(work_date, schedule.start_time)
                                
                                # is_overnight이면 퇴근시간을 다음날로 설정
                                if schedule.is_overnight:
                                    next_date = work_date + timedelta(days=1)
                                    existing_record.time_out = datetime.combine(next_date, schedule.end_time)
                                else:
                                    existing_record.time_out = datetime.combine(work_date, schedule.end_time)
                                
                                existing_record.is_overnight = schedule.is_overnight
                                existing_record.next_day_work_minutes = schedule.next_day_work_minutes
                                existing_record.break_minutes = schedule.break_minutes
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

    # 이 ViewSet의 기본 destroy 메소드를 위에서 정의한 커스텀 destroy로 대체합니다.
    # 기존의 destroy 메소드는 삭제합니다.

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
                today = timezone.localdate()
                # 미래 날짜 입력 차단 로직 제거 (2025-12-23: 출결 상태 변경 허용을 위해 제거)
                # if work_date > today:
                #     from rest_framework.exceptions import ValidationError
                #     raise ValidationError("미래 날짜에는 근로 기록을 입력할 수 없습니다.")
                
                # attendance_status가 없으면 소정근로일 여부에 따라 자동 설정
                if 'attendance_status' not in self.request.data or not self.request.data.get('attendance_status'):
                    is_scheduled = employee.is_scheduled_workday(work_date)
                    default_status = 'REGULAR_WORK' if is_scheduled else 'EXTRA_WORK'
                    serializer.validated_data['attendance_status'] = default_status
            
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
            today = timezone.localdate()
            # 미래 날짜 수정 차단 로직 제거 (2025-12-23: 출결 상태 변경 허용을 위해 제거)
            # if work_date > today:
            #     from rest_framework.exceptions import ValidationError
            #     raise ValidationError("미래 날짜의 근로 기록은 수정할 수 없습니다.")
        
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
    """연차 요약 정보 조회 (연도 기준 단순/안전 버전)
    
    GET /api/leave/annual/summary/?workplace_id=<employee_id>
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
    
    from .services import calculate_annual_leave_v2
    today = date.today()
    res = calculate_annual_leave_v2(employee, today.year)
    
    return Response({
        "as_of": today.isoformat(),
        "earned_days": res["accrued_days"],
        "used_days": res["used_days"],
        "remaining_days": res["remaining_days"],
        "is_eligible": res["eligible"],
        "reason": res["reason"],
        "rule_version": "v2.0_year_based"
    })

