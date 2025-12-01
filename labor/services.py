"""labor/services.py

노동법 관련 근로조건 평가 서비스 (단순화된 참고용 계산 로직)
본 로직은 실제 법률 자문이 아닌 교육/참고 목적의 계산 예시입니다.
"""

from dataclasses import dataclass
from datetime import date
from math import floor
from typing import Optional, Dict, Any, List


MIN_WAGE_2025 = 10030  # 2025년 최저임금 (시급)


@dataclass
class JobInputs:
    hourly_rate: float
    weekly_hours: float
    daily_hours: float
    work_days_per_week: Optional[int]
    employment_type: str
    start_date: date
    end_date: Optional[date]
    is_current: bool
    has_paid_weekly_holiday: bool
    attendance_rate_last_year: Optional[float]
    total_wage_last_3m: Optional[float]
    total_days_last_3m: Optional[int]


def calc_service_days(start: date, today: date) -> int:
    return (today - start).days


def check_minimum_wage(hourly_rate: float) -> Dict[str, Any]:
    return {
        "min_wage_ok": hourly_rate >= MIN_WAGE_2025,
        "min_wage_required": MIN_WAGE_2025,
    }


def calc_weekly_holiday_pay(weekly_hours: float, hourly_rate: float, work_days_per_week: Optional[int]) -> int:
    if weekly_hours < 15:
        return 0
    days = work_days_per_week
    if not days or days <= 0:
        # 추정: daily_hours로 나누어 근로일수 예측 (daily_hours가 0이면 1로 가정)
        # 실제 환경에서는 더 정교한 로직 필요
        estimated_daily_hours = weekly_hours if weekly_hours < 24 else weekly_hours / 5
        days = max(1, int(round(weekly_hours / max(estimated_daily_hours, 1))))
    weekly_holiday_hours = weekly_hours / days
    pay = weekly_holiday_hours * hourly_rate
    return int(round(pay))


def calc_annual_leave(start_date: date, attendance_rate_last_year: Optional[float], today: date) -> float:
    service_days = calc_service_days(start_date, today)
    service_years = floor(service_days / 365)

    if service_years < 1:
        months = floor(service_days / 30)
        return float(months)

    # 1년 이상
    if attendance_rate_last_year is not None and attendance_rate_last_year < 0.8:
        return 0.0

    base = 15
    if service_years >= 3:
        extra_years = service_years - 1
        extra_days = extra_years // 2
        return float(min(25, base + extra_days))
    return float(base)


def calc_severance(service_years: int, weekly_hours: float, total_wage_last_3m: Optional[float], total_days_last_3m: Optional[int]) -> int:
    if service_years < 1 or weekly_hours < 15:
        return 0
    if not total_wage_last_3m or not total_days_last_3m or total_days_last_3m <= 0:
        return 0
    avg_daily_wage = total_wage_last_3m / total_days_last_3m
    severance = avg_daily_wage * 30 * service_years
    return int(round(severance))


def evaluate_labor(job: JobInputs, today: Optional[date] = None) -> Dict[str, Any]:
    today = today or date.today()
    service_days = calc_service_days(job.start_date, today)
    service_years = floor(service_days / 365)

    min_wage = check_minimum_wage(job.hourly_rate)
    weekly_holiday_pay = calc_weekly_holiday_pay(job.weekly_hours, job.hourly_rate, job.work_days_per_week)
    annual_leave_days = calc_annual_leave(job.start_date, job.attendance_rate_last_year, today)
    severance_estimate = calc_severance(service_years, job.weekly_hours, job.total_wage_last_3m, job.total_days_last_3m)

    warnings: List[str] = []
    if not min_wage["min_wage_ok"]:
        warnings.append("최저임금(10,030원) 미달 가능성이 있습니다.")
    if job.weekly_hours >= 15 and weekly_holiday_pay == 0:
        warnings.append("주 15시간 이상인데 주휴수당이 반영되지 않았을 수 있습니다.")
    if service_days >= 365 and severance_estimate == 0:
        warnings.append("1년 이상 근속인데 퇴직금 계산 정보(최근 3개월 임금 등)가 부족합니다.")

    return {
        **min_wage,
        "weekly_holiday_pay": weekly_holiday_pay,
        "annual_leave_days": annual_leave_days,
        "severance_estimate": severance_estimate,
        "warnings": warnings,
    }


def job_to_inputs(employee) -> JobInputs:
    """Employee 모델 인스턴스를 평가 입력 구조로 변환"""
    return JobInputs(
        hourly_rate=float(employee.hourly_rate),
        weekly_hours=float(employee.weekly_hours),
        daily_hours=float(employee.daily_hours),
        work_days_per_week=employee.work_days_per_week,
        employment_type=employee.employment_type,
        start_date=employee.start_date,
        end_date=employee.end_date,
        is_current=employee.is_current,
        has_paid_weekly_holiday=employee.has_paid_weekly_holiday,
        attendance_rate_last_year=float(employee.attendance_rate_last_year) if employee.attendance_rate_last_year is not None else None,
        total_wage_last_3m=float(employee.total_wage_last_3m) if employee.total_wage_last_3m is not None else None,
        total_days_last_3m=employee.total_days_last_3m,
    )


def calculate_annual_leave(job: JobInputs, today: Optional[date] = None) -> Dict[str, float]:
    """
    연차휴가 요약 계산 (단순화 규칙)
    - 주 15시간 미만: 0일 처리
    - 1년 미만: 월 1일 발생 (개근 가정)
    - 1년 이상: 출근율 0.8 미만 0일, 그 외 15일 + (2년마다 1일) 최대 25일
    - 사용 연차는 현재 0일로 가정 (추후 실제 데이터로 대체)
    """
    today = today or date.today()

    if job.weekly_hours < 15:
        total = 0.0
    else:
        total = calc_annual_leave(job.start_date, job.attendance_rate_last_year, today)

    used = 0.0  # placeholder, 추후 실제 사용 연차 집계로 대체 예정
    available = max(0.0, float(total) - float(used))
    return {
        "total": float(total),
        "used": float(used),
        "available": float(available),
    }
