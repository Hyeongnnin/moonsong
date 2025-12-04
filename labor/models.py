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
    workplace_address = models.CharField(max_length=255, blank=True)
    workplace_reg_no = models.CharField(max_length=50, blank=True)
    industry = models.CharField(max_length=100, blank=True)

    employment_type = models.CharField(max_length=50, blank=True)  # 정규직/알바 등
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weekly_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    daily_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    has_paid_weekly_holiday = models.BooleanField(default=True)
    is_severance_eligible = models.BooleanField(default=False)
    is_current = models.BooleanField(default=True)
    # 추가 필드 (노동법 평가용) - 단순화된 참고 계산을 위한 데이터
    work_days_per_week = models.IntegerField(null=True, blank=True, help_text="주 근로일수 (없으면 weekly_hours/daily_hours로 추정)")
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
        total_seconds = duration.total_seconds()
        total_minutes = total_seconds / 60
        work_minutes = total_minutes - self.break_minutes
        
        return Decimal(str(work_minutes / 60))  # 시간 단위로 변환


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
