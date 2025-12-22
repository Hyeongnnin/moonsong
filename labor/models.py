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

    employment_type = models.CharField(max_length=50, blank=True)  # 정규직/알바 등
    start_date = models.DateField()
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # 추가 필드 (노동법 평가용) - 단순화된 참고 계산을 위한 데이터
    attendance_rate_last_year = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="작년 출근율 0~1")
    total_wage_last_3m = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="최근 3개월 총임금")
    total_days_last_3m = models.IntegerField(null=True, blank=True, help_text="최근 3개월 총일수")

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


class WorkRecord(models.Model):
    """근로 기록 (날짜별)"""
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="work_records")
    work_date = models.DateField()
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)
    break_minutes = models.IntegerField(default=0)
    # 선택: 휴게 구간 입력 (단일 또는 복수)
    break_start = models.DateTimeField(null=True, blank=True)
    break_end = models.DateTimeField(null=True, blank=True)
    break_intervals = models.JSONField(null=True, blank=True, help_text="[{'start': ISO8601, 'end': ISO8601}, ...]")

    DAY_TYPE_CHOICES = [
        ('NORMAL', '일반근무'),
        ('HOLIDAY_WORK', '휴일근무'),
    ]
    day_type = models.CharField(max_length=20, choices=DAY_TYPE_CHOICES, default='NORMAL')

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
        """실제 근로시간 (break 제외)"""
        if not self.time_in or not self.time_out:
            return Decimal('0')

        duration = self.time_out - self.time_in
        total_minutes = duration.total_seconds() / 60.0

        # 휴게 시간 계산: 우선순위 (1) break_intervals (2) break_start/break_end (3) break_minutes
        break_total = 0.0

        try:
            if self.break_intervals:
                for itv in self.break_intervals or []:
                    try:
                        s_raw = itv.get('start')
                        e_raw = itv.get('end')
                        if not s_raw or not e_raw:
                            continue
                        s_dt = datetime.fromisoformat(s_raw)
                        e_dt = datetime.fromisoformat(e_raw)
                        if e_dt <= s_dt:
                            continue
                        # 윈도우 클리핑 (근무시간내)
                        s = max(s_dt, self.time_in)
                        e = min(e_dt, self.time_out)
                        if e > s:
                            break_total += (e - s).total_seconds() / 60.0
                    except Exception:
                        continue
            elif self.break_start and self.break_end:
                s = max(self.break_start, self.time_in)
                e = min(self.break_end, self.time_out)
                if e > s:
                    break_total += (e - s).total_seconds() / 60.0
            else:
                break_total += float(self.break_minutes or 0)
        except Exception:
            break_total += float(self.break_minutes or 0)

        work_minutes = max(0.0, total_minutes - break_total)
        return Decimal(str(work_minutes / 60.0))


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
    enabled = models.BooleanField(default=True)
    # 월별 메타: 요일별 기본 휴게(분) 및 주휴일(기준 요일)
    default_break_minutes_by_weekday = models.JSONField(null=True, blank=True, help_text="{0: 60, 1: 30, ...}")
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
