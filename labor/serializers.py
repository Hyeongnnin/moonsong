# labor/serializers.py
from rest_framework import serializers
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Employee, WorkRecord, CalculationResult, WorkSchedule, MonthlySchedule


class AnnualLeaveSummarySerializer(serializers.Serializer):
    """연차 요약 정보"""
    as_of = serializers.DateField(help_text="기준일")
    earned_days = serializers.DecimalField(max_digits=4, decimal_places=1, help_text="발생 연차")
    used_days = serializers.DecimalField(max_digits=4, decimal_places=1, help_text="사용 연차")
    remaining_days = serializers.DecimalField(max_digits=4, decimal_places=1, help_text="잔여 연차")
    rule_version = serializers.CharField(help_text="적용 규칙 버전")
    is_eligible = serializers.BooleanField(help_text="연차 발생 대상 여부")
    reason = serializers.CharField(help_text="부적격 사유 (적격시 빈 문자열)", allow_blank=True)


class WorkRecordSerializer(serializers.ModelSerializer):
    total_hours = serializers.SerializerMethodField()
    is_scheduled_workday = serializers.SerializerMethodField()
    schedule_info = serializers.SerializerMethodField()

    class Meta:
        model = WorkRecord
        fields = [
            'id', 'employee', 'work_date', 'time_in', 'time_out', 
            'is_overnight', 'next_day_work_minutes', 'break_minutes',
            'day_type', 'attendance_type', 'attendance_status',
            'total_hours', 'is_overtime', 'is_night', 'is_holiday',
            'is_scheduled_workday', 'schedule_info'
        ]

    def get_total_hours(self, obj):
        """실제 근로시간 계산 (익일 근무 포함)"""
        return float(obj.get_total_hours())
    
    def get_is_scheduled_workday(self, obj):
        """해당 날짜가 소정근로일인지 여부"""
        return obj.employee.is_scheduled_workday(obj.work_date)
    
    def get_schedule_info(self, obj):
        """해당 날짜의 스케줄 정보 (기본값 참조용)"""
        return obj.employee.get_schedule_for_date(obj.work_date)


class JobSummarySerializer(serializers.Serializer):
    """특정 월의 근로 요약 정보"""
    job_id = serializers.IntegerField()
    job_name = serializers.CharField()
    workplace_name = serializers.CharField()
    hourly_wage = serializers.DecimalField(max_digits=10, decimal_places=2)
    month = serializers.CharField()  # YYYY-MM 형식
    total_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_days = serializers.IntegerField()
    estimated_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    week_stats = serializers.ListField()  # 주별 통계


class WorkScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.SerializerMethodField()

    class Meta:
        model = WorkSchedule
        fields = [
            'id', 'weekday', 'weekday_display', 'start_time', 'end_time', 
            'is_overnight', 'next_day_work_minutes', 'break_minutes', 'enabled'
        ]

    def get_weekday_display(self, obj):
        return obj.get_weekday_display()


class MonthlyScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.SerializerMethodField()

    class Meta:
        model = MonthlySchedule
        fields = [
            'id', 'year', 'month', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'is_overnight', 'next_day_work_minutes', 
            'break_minutes', 'enabled'
        ]

    def get_weekday_display(self, obj):
        return obj.get_weekday_display()


class EmployeeSerializer(serializers.ModelSerializer):
    work_records = WorkRecordSerializer(many=True, read_only=True)
    schedules = WorkScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'workplace_name', 'workplace_reg_no',
            'employment_type', 'is_workplace_over_5', 'start_date',
            'hourly_rate', 'contract_weekly_hours', 'deduction_type',
            'attendance_rate_last_year', 'total_wage_last_3m', 'total_days_last_3m',
            'work_records', 'schedules'
        ]
        read_only_fields = ['id']


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Employee 근로정보 수정용 Serializer (PATCH/PUT)"""

    class Meta:
        model = Employee
        fields = [
            'workplace_name', 'workplace_reg_no',
            'employment_type', 'is_workplace_over_5', 'start_date',
            'hourly_rate', 'contract_weekly_hours', 'deduction_type',
            'attendance_rate_last_year', 'total_wage_last_3m', 'total_days_last_3m'
        ]

    def validate_hourly_rate(self, value):
        """시급은 0 이상이어야 함"""
        if value < 0:
            raise serializers.ValidationError("시급은 0 이상이어야 합니다.")
        return value


class CalculationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationResult
        fields = "__all__"

class PayrollBreakdownSerializer(serializers.Serializer):
    """일별 급여 상세 내역"""
    date = serializers.DateField()
    source = serializers.CharField()  # actual | scheduled | none
    hours = serializers.FloatField()
    is_holiday = serializers.BooleanField()
    holiday_type = serializers.CharField(allow_null=True)
    day_pay = serializers.IntegerField()
    holiday_bonus = serializers.IntegerField()
    night_hours = serializers.FloatField(required=False, default=0)
    night_bonus = serializers.IntegerField(required=False, default=0)
    is_future = serializers.BooleanField(required=False, default=False)


class PayrollSummaryNestedSerializer(serializers.Serializer):
    """급여 요약 핵심 정보"""
    base_pay = serializers.IntegerField()
    night_extra = serializers.IntegerField()
    holiday_extra = serializers.IntegerField()
    weekly_holiday_pay = serializers.IntegerField(required=False, default=0)
    total = serializers.IntegerField()
    total_hours = serializers.FloatField()
    total = serializers.IntegerField()
    total_hours = serializers.FloatField()
    scheduled_hours = serializers.FloatField()
    deduction = serializers.DictField(required=False)


class PayrollSummarySerializer(serializers.Serializer):
    """월별 급여 집계 및 요약"""
    month = serializers.CharField()
    hourly_wage = serializers.IntegerField()
    workplace_size = serializers.CharField()
    contract_weekly_hours = serializers.FloatField(allow_null=True)
    
    # Top level fields for backward compatibility, now optional
    total_hours = serializers.FloatField(required=False, default=0)
    actual_hours = serializers.FloatField(required=False, default=0)
    scheduled_hours = serializers.FloatField(required=False, default=0)
    
    base_pay = serializers.IntegerField(required=False, default=0)
    holiday_hours = serializers.FloatField(required=False, default=0)
    holiday_bonus = serializers.IntegerField(required=False, default=0)
    night_hours = serializers.FloatField(required=False, default=0)
    night_bonus = serializers.IntegerField(required=False, default=0)
    estimated_monthly_pay = serializers.IntegerField(required=False, default=0)
    net_pay = serializers.IntegerField(required=False, default=0)
    
    summary = PayrollSummaryNestedSerializer()
    rows = PayrollBreakdownSerializer(many=True) # breakdown -> rows
    notes = serializers.ListField(child=serializers.CharField())
