# labor/models.py
from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta

User = settings.AUTH_USER_MODEL

class Employee(models.Model):
    """Job(알바) 정보를 저장하는 모델"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="employees")
    workplace_name = models.CharField(max_length=200)
    workplace_reg_no = models.CharField(max_length=50, blank=True)

    employment_type = models.CharField(max_length=50, default='알바', blank=True)  # 알바로 고정
    is_workplace_over_5 = models.BooleanField(default=False, help_text="5인 이상 사업장 여부")
    start_date = models.DateField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # 추가 필드 (노동법 평가용) - 단순화된 참고 계산을 위한 데이터
    attendance_rate_last_year = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="작년 출근율 0~1")
    total_wage_last_3m = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="최근 3개월 총임금")
    total_days_last_3m = models.IntegerField(null=True, blank=True, help_text="최근 3개월 총일수")
    contract_weekly_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="계약상 주 소정근로시간")

    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"

    def __str__(self):
        return f"{self.workplace_name} ({self.user.username})"

    def get_total_hours_for_period(self, start_date, end_date):
        """기간 내 근로시간 합계 (분 단위 break 제외)"""
        records = self.work_records.filter(work_date__range=[start_date, end_date])
        total = Decimal('0')
        for record in records:
            total += record.get_total_hours()
        return total

    def get_estimated_pay_for_period(self, start_date, end_date):
        """기간 내 예상 급여 (시급 * 근로시간)"""
        total_hours = self.get_total_hours_for_period(start_date, end_date)
        return total_hours * self.hourly_rate

    def is_scheduled_workday(self, target_date):
        """특정 날짜가 소정근로일인지 판정
        
        판정 기준 (우선순위 순):
        1. 해당 월의 MonthlySchedule이 있으면 그것 기준
        2. 없으면 WorkSchedule(주간 스케줄) 기준
        
        Returns:
            bool: 소정근로일 여부
        """
        from .models import MonthlySchedule, WorkSchedule
        
        year = target_date.year
        month = target_date.month
        weekday = target_date.weekday()
        
        # 1. 월별 스케줄 확인 (최우선)
        monthly_schedule = MonthlySchedule.objects.filter(
            employee=self,
            year=year,
            month=month,
            weekday=weekday,
            enabled=True
        ).first()
        
        if monthly_schedule:
            # 월별 스케줄이 있으면 그것으로 판정 (시작일 이후여야 함)
            if target_date < self.start_date:
                return False
            return monthly_schedule.start_time is not None and monthly_schedule.end_time is not None
        
        # 2. 주간 스케줄 확인
        weekly_schedule = WorkSchedule.objects.filter(
            employee=self,
            weekday=weekday,
            enabled=True
        ).first()
        
        if weekly_schedule:
            # 시작일 이후여야 함
            if target_date < self.start_date:
                return False
            return weekly_schedule.start_time is not None and weekly_schedule.end_time is not None
        
        # 스케줄이 없으면 소정근로일이 아님
        return False
    
    def get_schedule_for_date(self, target_date):
        """특정 날짜의 스케줄 정보 반환 (시간 포함)
        
        Returns:
            dict: {'is_scheduled': bool, 'start_time': time, 'end_time': time, 'break_minutes': int}
        """
        from .models import MonthlySchedule, WorkSchedule
        
        year = target_date.year
        month = target_date.month
        weekday = target_date.weekday()
        
        # 1. 월별 스케줄 우선
        monthly_schedule = MonthlySchedule.objects.filter(
            employee=self,
            year=year,
            month=month,
            weekday=weekday,
            enabled=True
        ).first()
        
        # 시작일 이전이면 예외 없이 스케줄 없음 처리
        if target_date < self.start_date:
            return {
                'is_scheduled': False,
                'start_time': None,
                'end_time': None,
                'break_minutes': 0,
                'is_overnight': False,
                'next_day_work_minutes': 0,
            }

        if monthly_schedule:
            return {
                'is_scheduled': monthly_schedule.start_time is not None and monthly_schedule.end_time is not None,
                'start_time': monthly_schedule.start_time,
                'end_time': monthly_schedule.end_time,
                'break_minutes': monthly_schedule.break_minutes,
                'is_overnight': monthly_schedule.is_overnight,
                'next_day_work_minutes': monthly_schedule.next_day_work_minutes,
            }
        
        # 2. 주간 스케줄
        weekly_schedule = WorkSchedule.objects.filter(
            employee=self,
            weekday=weekday,
            enabled=True
        ).first()
        
        if weekly_schedule:
            return {
                'is_scheduled': weekly_schedule.start_time is not None and weekly_schedule.end_time is not None,
                'start_time': weekly_schedule.start_time,
                'end_time': weekly_schedule.end_time,
                'break_minutes': weekly_schedule.break_minutes,
                'is_overnight': weekly_schedule.is_overnight,
                'next_day_work_minutes': weekly_schedule.next_day_work_minutes,
            }
        
        # 스케줄 없음
        return {
            'is_scheduled': False,
            'start_time': None,
            'end_time': None,
            'break_minutes': 0,
            'is_overnight': False,
            'next_day_work_minutes': 0,
        }


class WorkRecord(models.Model):
    """근로 기록 (날짜별)"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="work_records")
    work_date = models.DateField()
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)
    is_overnight = models.BooleanField(default=False, help_text="퇴근 시간이 자정(24:00)을 넘는 경우")
    next_day_work_minutes = models.IntegerField(default=0, help_text="익일 추가 근무 시간 (0~360분, 24:00~06:00 구간)")
    break_minutes = models.IntegerField(default=0)

    DAY_TYPE_CHOICES = [
        ('NORMAL', '일반근무'),
        ('HOLIDAY_WORK', '휴일근무'),
    ]
    day_type = models.CharField(max_length=20, choices=DAY_TYPE_CHOICES, default='NORMAL')

    # 소정근로일 중심 구조: 출결 상태 확장
    ATTENDANCE_STATUS_CHOICES = [
        ('REGULAR_WORK', '근무(소정근로)'),  # 소정근로일에 정상 출근
        ('EXTRA_WORK', '추가근무'),  # 대타, 보충근무 등 비소정근로일 근무
        ('ANNUAL_LEAVE', '연차사용'),  # 유급휴가
        ('ABSENT', '결근'),  # 무단 결근
        ('SICK_LEAVE', '병가'),  # 병가
    ]
    attendance_status = models.CharField(
        max_length=20, 
        choices=ATTENDANCE_STATUS_CHOICES, 
        default='REGULAR_WORK',
        help_text="출결 상태 (소정근로/추가근무/연차/결근/병가)"
    )
    
    # 하위 호환성을 위한 기존 필드 유지 (deprecated)
    ATTENDANCE_TYPE_CHOICES = [
        ('WORKED', '근무'),
        ('APPROVED_LEAVE', '승인된 휴무'),
        ('ABSENT', '결근'),
    ]
    attendance_type = models.CharField(max_length=20, choices=ATTENDANCE_TYPE_CHOICES, default='WORKED')
    is_overtime = models.BooleanField(default=False)
    is_night = models.BooleanField(default=False)
    is_holiday = models.BooleanField(default=False)

    class Meta:
        ordering = ['-work_date']
        unique_together = [['employee', 'work_date']]

    def __str__(self):
        return f"{self.employee} - {self.work_date}"

    def get_total_hours(self):
        """실제 근로시간 (break 제외, 익일 근무 포함)"""
        total_work_minutes = 0.0

        if self.time_in and self.time_out:
            dt_in = self.time_in
            dt_out = self.time_out
            
            # [Fix] 오직 퇴근 시간이 출근 시간보다 앞선 경우에만 익일로 간주하여 24시간 더함.
            # is_overnight 플래그만으로 24시간을 더하면 일반 근무일 때 중복 합산될 우려가 있음.
            if dt_out < dt_in:
                if dt_out.date() == dt_in.date():
                    dt_out += timedelta(days=1)
                
            duration = dt_out - dt_in
            total_minutes = duration.total_seconds() / 60.0
            # 휴게 시간 계산: break_minutes만 사용
            break_total = float(self.break_minutes or 0)
            total_work_minutes = max(0.0, total_minutes - break_total)
        
        # 익일 추가 근무 시간 합산 (24:00~06:00 구간) - 이건 별도 필드이므로 그대로 합산
        next_day_minutes = float(self.next_day_work_minutes or 0)
        total_work_minutes += next_day_minutes
        
        return Decimal(str(total_work_minutes / 60.0))

    def get_night_hours(self):
        """야간 수당 대상 시간 계산 (22:00 ~ 익일 06:00)"""
        night_minutes = 0.0
        
        # 1. 출퇴근 시간 기반 야간 근로 계산
        if self.time_in and self.time_out:
            t_in = self.time_in
            t_out = self.time_out
            if t_out < t_in:
                t_out += timedelta(days=1)
            
            # 시간대별 야간 구간 판별 함수
            def get_night_overlap_minutes(start, end):
                overlap = 0.0
                curr = start
                # 1분 단위로 체크 (간단하지만 정확함, 성능 문제시 최적화 가능)
                # 실제로는 22:00-06:00 구간을 구하는 수학적 계산이 더 효율적임.
                
                # 수학적 계산 방식:
                while curr < end:
                    # 야간 기준: 22:00 ~ 06:00
                    if curr.hour >= 22 or curr.hour < 6:
                        overlap += 1
                    curr += timedelta(minutes=1)
                return overlap

            # [Optimized] 수학적 계산 방식
            # 근로 시작~종료 구간에서 [22:00~06:00] 구간과 겹치는 시간 산출
            night_minutes += self._calculate_range_overlap_minutes(t_in, t_out, 22, 6)

        # 2. 익일 추가 근무 시간 (24:00~06:00)은 전액 야간수당 대상
        next_day_minutes = float(self.next_day_work_minutes or 0)
        night_minutes += next_day_minutes
        
        # 휴게 시간 차감 (야간 근무 중 휴게가 포함된 경우 비례 차감하거나 
        # 사용자의 단순 입력을 고려하여 전액 인정할 수 있으나, 여기선 단순 합산 유지)
        
        return Decimal(str(night_minutes / 60.0))

    def _calculate_range_overlap_minutes(self, start, end, night_start_hour, night_end_hour):
        """두 시간대 사이에서 야간 시간과 겹치는 분(minutes)을 계산합니다."""
        from django.utils import timezone
        overlap = 0
        curr = start.replace(second=0, microsecond=0)
        end_clean = end.replace(second=0, microsecond=0)
        
        while curr < end_clean:
            # [Fix] timezone.localtime()을 사용하여 KST 기준으로 시(hour) 판단
            local_curr = timezone.localtime(curr)
            if local_curr.hour >= night_start_hour or local_curr.hour < night_end_hour:
                overlap += 1
            curr += timedelta(minutes=1)
        return overlap


class CalculationResult(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="calculation_results")
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    calculation_type = models.CharField(max_length=50)  # '월급', '주휴수당', '전체권리요약'

    input_data_json = models.JSONField(null=True, blank=True)

    total_annual_leave = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    used_annual_leave = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    remaining_annual_leave = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    expected_base_wage = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_overtime_pay = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_total_pay = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    detail_json = models.JSONField(null=True, blank=True)
    calculated_at = models.DateTimeField(auto_now_add=True)
    law_version_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.employee} / {self.calculation_type} ({self.period_start}~{self.period_end})"


WEEKDAY_CHOICES = [
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
]

class WorkSchedule(models.Model):
    """Weekly recurring schedule for an Employee: which weekdays and times."""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_overnight = models.BooleanField(default=False, help_text="퇴근 시간이 자정(24:00)을 넘는 경우")
    next_day_work_minutes = models.IntegerField(default=0, help_text="익일 추가 근무 시간 (0~360분)")
    break_minutes = models.IntegerField(default=0, help_text="휴게 시간 (분)")
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = [['employee', 'weekday']]

    def __str__(self):
        return f"{self.employee} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class MonthlySchedule(models.Model):
    """특정 월의 근무 스케줄 오버라이드
    
    이 모델은 특정 년월에 대해 기본 주간 스케줄(WorkSchedule)과 다른 
    근무 패턴을 적용하고 싶을 때 사용합니다.
    
    예: 2025년 3월에만 화요일 근무 시간이 달랐던 경우
    """
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='monthly_schedules')
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_overnight = models.BooleanField(default=False, help_text="퇴근 시간이 자정(24:00)을 넘는 경우")
    next_day_work_minutes = models.IntegerField(default=0, help_text="익일 추가 근무 시간 (0~360분)")
    break_minutes = models.IntegerField(default=0, help_text="휴게 시간 (분)")
    enabled = models.BooleanField(default=True)
    # 월별 메타: 주휴일(기준 요일)
    weekly_rest_day = models.IntegerField(null=True, blank=True, choices=WEEKDAY_CHOICES)
    
    class Meta:
        unique_together = [['employee', 'year', 'month', 'weekday']]
        indexes = [
            models.Index(fields=['employee', 'year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.employee} - {self.year}-{self.month:02d} {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class LeaveUsage(models.Model):
    """연차 사용 기록"""
    LEAVE_TYPE_CHOICES = [
        ('annual', '연차'),
        ('sick', '병가'),
        ('personal', '개인사유'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_usages')
    leave_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, default='annual')
    days = models.DecimalField(max_digits=3, decimal_places=1, default=1.0, help_text="사용 일수 (0.5=반차, 1=연차)")
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-leave_date']
        unique_together = [['employee', 'leave_date', 'leave_type']]
    
    def __str__(self):
        return f"{self.employee} - {self.leave_date} ({self.get_leave_type_display()} {self.days}일)"
