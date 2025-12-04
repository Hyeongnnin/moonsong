# labor/serializers.py
from rest_framework import serializers
from datetime import datetime, timedelta
from decimal import Decimal
from .models import Employee, WorkRecord, CalculationResult, WorkSchedule


class WorkRecordSerializer(serializers.ModelSerializer):
    total_hours = serializers.SerializerMethodField()

    class Meta:
        model = WorkRecord
        fields = [
            'id', 'work_date', 'time_in', 'time_out', 'break_minutes',
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


class EmployeeSerializer(serializers.ModelSerializer):
    work_records = WorkRecordSerializer(many=True, read_only=True)
    schedules = WorkScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Employee
        fields = [
            'id', 'workplace_name', 'workplace_address', 'workplace_reg_no',
            'industry', 'employment_type', 'start_date', 'end_date',
            'hourly_rate', 'weekly_hours', 'daily_hours',
            'has_paid_weekly_holiday', 'is_severance_eligible', 'is_current',
            'work_days_per_week', 'attendance_rate_last_year', 'total_wage_last_3m', 'total_days_last_3m',
            'work_records', 'schedules'
        ]
        read_only_fields = ['id']


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Employee 근로정보 수정용 Serializer (PATCH/PUT)"""

    class Meta:
        model = Employee
        fields = [
            'workplace_name', 'workplace_address', 'workplace_reg_no',
            'industry', 'employment_type', 'start_date', 'end_date',
            'hourly_rate', 'weekly_hours', 'daily_hours',
            'has_paid_weekly_holiday', 'is_severance_eligible', 'is_current',
            'work_days_per_week', 'attendance_rate_last_year', 'total_wage_last_3m', 'total_days_last_3m'
        ]

    def validate_hourly_rate(self, value):
        """시급은 0 이상이어야 함"""
        if value < 0:
            raise serializers.ValidationError("시급은 0 이상이어야 합니다.")
        return value

    def validate_weekly_hours(self, value):
        """주당 근로시간은 0 이상 168 이하여야 함"""
        if value < 0 or value > 168:
            raise serializers.ValidationError("주당 근로시간은 0 이상 168 이하여야 합니다.")
        return value

    def validate(self, data):
        """전체 유효성 검사"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        # 인스턴스가 있으면 기존 값 사용
        if self.instance:
            start_date = start_date or self.instance.start_date
            end_date = end_date or self.instance.end_date

        # end_date가 start_date보다 이전이면 안됨
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                {"end_date": "종료일은 시작일 이후여야 합니다."}
            )

        return data


class CalculationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalculationResult
        fields = "__all__"
