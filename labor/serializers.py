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

    class Meta:
        model = WorkRecord
        fields = [
            'id', 'employee', 'work_date', 'time_in', 'time_out', 'break_minutes',
            'break_start', 'break_end', 'break_intervals',
            'day_type', 'attendance_type',
            'total_hours', 'is_overtime', 'is_night', 'is_holiday'
        ]

    def get_total_hours(self, obj):
        """실제 근로시간 계산"""
        return float(obj.get_total_hours())


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
        fields = ['id', 'weekday', 'weekday_display', 'start_time', 'end_time', 'enabled']

    def get_weekday_display(self, obj):
        return obj.get_weekday_display()


class MonthlyScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.SerializerMethodField()

    class Meta:
        model = MonthlySchedule
        fields = [
            'id', 'year', 'month', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'enabled',
            'default_break_minutes_by_weekday', 'weekly_rest_day'
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
            'employment_type', 'start_date',
            'hourly_rate',
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
            'employment_type', 'start_date',
            'hourly_rate',
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
