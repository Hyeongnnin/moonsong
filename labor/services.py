"""labor/services.py

노동법 관련 근로조건 평가 서비스 (단순화된 참고용 계산 로직)
본 로직은 실제 법률 자문이 아닌 교육/참고 목적의 계산 예시입니다.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from math import floor
from typing import Optional, Dict, Any, List


MIN_WAGE_2025 = 10030  # 2025년 최저임금 (시급)


@dataclass
class JobInputs:
    hourly_rate: float
    employment_type: str
    start_date: date
    end_date: Optional[date]
    is_current: bool
    has_paid_weekly_holiday: bool
    attendance_rate_last_year: Optional[float]
    total_wage_last_3m: Optional[float]
    total_days_last_3m: Optional[int]
    # 스케줄 기반 계산을 위한 필드 (동적으로 계산)
    weekly_hours: Optional[float] = None
    work_days_per_week: Optional[int] = None


def calc_service_days(start: date, today: date) -> int:
    return (today - start).days


def check_minimum_wage(hourly_rate: float) -> Dict[str, Any]:
    return {
        "min_wage_ok": hourly_rate >= MIN_WAGE_2025,
        "min_wage_required": MIN_WAGE_2025,
    }


def calc_weekly_holiday_pay(weekly_hours: float, hourly_rate: float, work_days_per_week: Optional[int]) -> int:
    """주휴수당 계산 (스케줄 기반)
    
    Args:
        weekly_hours: 주간 총 근로시간 (스케줄 기반으로 계산된 값)
        hourly_rate: 시급
        work_days_per_week: 주당 근무일수
    """
    if not weekly_hours or weekly_hours < 15:
        return 0
    
    days = work_days_per_week
    if not days or days <= 0:
        # 스케줄에서 계산된 근무일수가 없으면 기본 추정
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


def calc_severance(service_years: int, weekly_hours: Optional[float], total_wage_last_3m: Optional[float], total_days_last_3m: Optional[int]) -> int:
    """퇴직금 계산 (스케줄 기반)
    
    Args:
        service_years: 근속 연수
        weekly_hours: 주간 총 근로시간 (스케줄 기반으로 계산된 값, None일 수 있음)
        total_wage_last_3m: 최근 3개월 총 임금
        total_days_last_3m: 최근 3개월 총 일수
    """
    if service_years < 1 or not weekly_hours or weekly_hours < 15:
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
    weekly_hours = job.weekly_hours or 0
    weekly_holiday_pay = calc_weekly_holiday_pay(weekly_hours, job.hourly_rate, job.work_days_per_week)
    annual_leave_days = calc_annual_leave(job.start_date, job.attendance_rate_last_year, today)
    severance_estimate = calc_severance(service_years, weekly_hours, job.total_wage_last_3m, job.total_days_last_3m)

    warnings: List[str] = []
    if not min_wage["min_wage_ok"]:
        warnings.append("최저임금(10,030원) 미달 가능성이 있습니다.")
    if weekly_hours >= 15 and weekly_holiday_pay == 0:
        warnings.append("주 15시간 이상 근무 시 주휴수당 지급이 필요합니다.")
    if service_years >= 1 and weekly_hours >= 15 and severance_estimate == 0:
        warnings.append("1년 이상, 주 15시간 이상 근무 시 퇴직금 지급이 필요합니다.")

    return {
        "service_days": service_days,
        "service_years": service_years,
        "min_wage": min_wage,
        "weekly_holiday_pay": weekly_holiday_pay,
        "annual_leave_days": annual_leave_days,
        "severance_estimate": severance_estimate,
        "warnings": warnings,
    }


def job_to_inputs(employee) -> JobInputs:
    """Employee 모델 인스턴스를 평가 입력 구조로 변환
    
    주당 근로시간은 WorkSchedule에서 동적으로 계산합니다.
    """
    from datetime import datetime
    from .models import WorkSchedule
    
    # 활성화된 스케줄에서 주당 근로시간 계산
    schedules = WorkSchedule.objects.filter(employee=employee, enabled=True)
    weekly_hours = 0.0
    work_days_per_week = 0
    
    for schedule in schedules:
        if schedule.start_time and schedule.end_time:
            # 시간 차이 계산
            dummy_date = datetime(2000, 1, 1)
            dt_start = datetime.combine(dummy_date.date(), schedule.start_time)
            dt_end = datetime.combine(dummy_date.date(), schedule.end_time)
            diff = dt_end - dt_start
            hours = diff.total_seconds() / 3600
            weekly_hours += hours
            work_days_per_week += 1
    
    return JobInputs(
        hourly_rate=float(employee.hourly_rate),
        weekly_hours=weekly_hours if weekly_hours > 0 else None,
        work_days_per_week=work_days_per_week if work_days_per_week > 0 else None,
        employment_type=employee.employment_type,
        start_date=employee.start_date,
        end_date=employee.end_date,
        is_current=employee.is_current,
        has_paid_weekly_holiday=employee.has_paid_weekly_holiday,
        attendance_rate_last_year=float(employee.attendance_rate_last_year)
        if employee.attendance_rate_last_year is not None
        else None,
        total_wage_last_3m=float(employee.total_wage_last_3m)
        if employee.total_wage_last_3m is not None
        else None,
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

    weekly_hours = job.weekly_hours or 0
    if weekly_hours < 15:
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


import calendar
from datetime import date, timedelta, time
from django.utils import timezone
from .models import WorkSchedule, WorkRecord, MonthlySchedule

def monthly_scheduled_dates(employee, year, month):
    """
    주어진 월의 각 날짜에 대해 근무가 예정되어 있는지 또는 실제 근무했는지 여부를 반환합니다.
    
    우선순위:
    1. 실제 WorkRecord (가장 높음) - 과거/현재 날짜
    2. MonthlySchedule (월별 오버라이드) - 과거/현재 날짜만
    3. WorkSchedule (전역 주간 스케줄) - 과거/현재 날짜만
    
    중요: 미래 날짜(오늘 이후)는 스케줄이 있어도 표시하지 않음
    """
    from django.utils import timezone
    
    # 오늘 날짜
    today = timezone.now().date()
    
    # 1. 해당 월의 MonthlySchedule 조회
    monthly_schedules = MonthlySchedule.objects.filter(
        employee=employee,
        year=year,
        month=month,
        enabled=True
    )
    
    # 2. 기본 WorkSchedule 조회
    default_schedules = WorkSchedule.objects.filter(employee=employee, enabled=True)
    
    # 실제 근무 기록 가져오기
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )
    # 날짜별 기록 매핑
    worked_records_map = {wr.work_date: wr for wr in work_records}

    # MonthlySchedule이 있으면 우선 사용, 없으면 기본 스케줄 사용
    if monthly_schedules.exists():
        schedule_map = {}
        for s in monthly_schedules:
            if s.start_time and s.end_time:
                schedule_map[s.weekday] = s
    else:
        schedule_map = {}
        for s in default_schedules:
            if s.start_time and s.end_time:
                schedule_map[s.weekday] = s
    
    cal = calendar.Calendar()
    month_dates = cal.itermonthdates(year, month)
    
    scheduled_dates_data = []
    for dt in month_dates:
        if dt.month != month:
            continue
        
        is_scheduled = False
        
        # 1. 실제 기록 확인 (우선순위 가장 높음)
        if dt in worked_records_map:
            record = worked_records_map[dt]
            # 실제 기록이 있으면, 기록된 시간이 0보다 클 때만 '스케줄됨'으로 표시
            if record.get_total_hours() > 0:
                is_scheduled = True
            else:
                is_scheduled = False
        # 2. 스케줄 확인 (실제 기록이 없는 경우에만)
        # 중요: 미래 날짜는 스케줄이 있어도 표시하지 않음
        elif dt <= today and dt.weekday() in schedule_map:
            is_scheduled = True
            
        scheduled_dates_data.append({
            "date": dt.isoformat(),
            "is_scheduled": is_scheduled,
        })
    return scheduled_dates_data


def compute_monthly_schedule_stats(employee, year, month):
    """
    월별 근무 스케줄 통계(예상 총 근무시간, 예상 급여 등)를 계산합니다.
    실제 근무 기록이 있는 날은 스케줄 대신 실제 기록을 우선합니다.
    
    우선순위:
    1. 실제 WorkRecord (가장 높음)
    2. MonthlySchedule (월별 오버라이드) - 오늘 이전만
    3. WorkSchedule (전역 주간 스케줄) - 오늘 이전만
    
    중요: 미래 날짜(오늘 이후)의 스케줄은 통계에 포함하지 않음
    """
    from django.utils import timezone
    
    # 오늘 날짜
    today = timezone.now().date()
    
    # 1. 해당 월의 MonthlySchedule 조회
    monthly_schedules = MonthlySchedule.objects.filter(
        employee=employee,
        year=year,
        month=month,
        enabled=True
    )
    
    # 2. 기본 WorkSchedule 조회
    default_schedules = WorkSchedule.objects.filter(employee=employee, enabled=True)
    
    hourly_rate = float(employee.hourly_rate)

    total_scheduled_hours = 0
    scheduled_work_days = 0
    
    # 이번 달의 첫날과 마지막 날
    start_of_month = date(year, month, 1)
    end_of_month = date(year, month, calendar.monthrange(year, month)[1])

    # 이번 달의 실제 근무 기록 가져오기
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )

    # 실제 근무 기록이 있는 날짜 집합 (0시간 기록 포함 - 스케줄 오버라이드용)
    worked_dates = {wr.work_date for wr in work_records}

    # 실제 근무 기록 기반으로 시간 계산
    actual_hours_worked = sum(float(wr.get_total_hours()) for wr in work_records)
    
    # 실제 근무일 수 계산 (0시간 기록 제외)
    actual_work_days = sum(1 for wr in work_records if wr.get_total_hours() > 0)

    # MonthlySchedule이 있으면 우선 사용, 없으면 기본 스케줄 사용
    if monthly_schedules.exists():
        schedule_map = {s.weekday: s for s in monthly_schedules}
    else:
        schedule_map = {s.weekday: s for s in default_schedules}
    
    # 스케줄 기반으로 예상 시간 계산
    # 중요: 오늘 이전 날짜만 계산, 미래는 제외
    current_date = start_of_month
    while current_date <= end_of_month and current_date <= today:  # 오늘까지만
        # 실제 기록(취소 포함)이 있으면 스케줄 무시
        if current_date not in worked_dates and current_date.weekday() in schedule_map:
            schedule = schedule_map[current_date.weekday()]
            if schedule.start_time and schedule.end_time:
                # 시간 계산
                start_hour = schedule.start_time.hour + schedule.start_time.minute / 60
                end_hour = schedule.end_time.hour + schedule.end_time.minute / 60
                
                # 야간 근무 처리 (종료 시간이 시작 시간보다 빠른 경우)
                if end_hour <= start_hour:
                    end_hour += 24
                
                duration_hours = end_hour - start_hour
                total_scheduled_hours += duration_hours
                scheduled_work_days += 1
        current_date += timedelta(days=1)

    # 총 근무 시간 = 실제 근무 시간 + 예상 근무 시간 (오늘까지만)
    total_hours = actual_hours_worked + total_scheduled_hours
    total_days = actual_work_days + scheduled_work_days
    
    # 총 급여 계산
    total_salary = total_hours * hourly_rate

    # ============================================================
    # 이번 주 통계 계산 (주휴수당 계산용)
    # 중요: 오늘 이전 날짜만 계산, 미래는 제외
    # ============================================================
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'[compute_monthly_schedule_stats] Computing this week stats')
    logger.info(f'  Today: {today}')
    logger.info(f'  Week range: {start_of_week} ~ {end_of_week}')
    
    # 이번 주에 속한 모든 실제 근로기록 조회
    actual_this_week_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__gte=start_of_week, 
        work_date__lte=min(end_of_week, today)  # 오늘까지만
    )
    actual_this_week_hours = Decimal('0')
    for wr in actual_this_week_records:
        hours = wr.get_total_hours()
        actual_this_week_hours += Decimal(str(hours))
        logger.info(f'  Work record on {wr.work_date}: {hours} hours')
    
    logger.info(f'  Total actual hours this week: {actual_this_week_hours}')
    
    # 이번 주 스케줄 예상 시간 계산 (실제 근무 기록이 없는 날만, 오늘까지만)
    scheduled_this_week_hours = Decimal('0')
    current_day = start_of_week
    actual_work_dates = set(wr.work_date for wr in actual_this_week_records)
    
    while current_day <= min(end_of_week, today):  # 오늘까지만
        # 실제 근무 기록이 없고, 스케줄이 있는 날만 계산
        if current_day not in actual_work_dates and current_day.weekday() in schedule_map:
            schedule = schedule_map[current_day.weekday()]
            if schedule.start_time and schedule.end_time:
                start_hour = schedule.start_time.hour + schedule.start_time.minute / 60
                end_hour = schedule.end_time.hour + schedule.end_time.minute / 60
                if end_hour <= start_hour:
                    end_hour += 24
                hours = Decimal(str(end_hour - start_hour))
                scheduled_this_week_hours += hours
                logger.info(f'  Scheduled on {current_day} ({current_day.strftime("%A")}): {hours} hours')
        current_day += timedelta(days=1)
    
    logger.info(f'  Total scheduled hours this week: {scheduled_this_week_hours}')
    
    total_this_week_hours = actual_this_week_hours + scheduled_this_week_hours
    logger.info(f'  Total this week hours: {total_this_week_hours}')

    return {
        "scheduled_total_hours": total_hours,
        "scheduled_estimated_salary": total_salary,
        "scheduled_work_days": total_days,
        "scheduled_this_week_hours": float(total_this_week_hours),
        "scheduled_this_week_estimated_salary": float(total_this_week_hours * Decimal(str(hourly_rate))),
    }


def calculate_retirement_pay(employee) -> Dict[str, Any]:
    """퇴직금 계산 (근로기준법 제34조)
    
    법적 근거:
    - 근로기준법 제34조: 계속근로기간 1년에 대하여 30일분 이상의 평균임금을 퇴직금으로 지급
    - 퇴직금 = 평균임금 × 30일 × (재직일수 / 365)
    - 평균임금 = 퇴직 전 3개월간 임금총액 / 해당 기간의 총 일수(역일수)
    - 평균임금이 통상임금보다 낮을 경우 통상임금 사용
    
    Args:
        employee: Employee 모델 인스턴스
        
    Returns:
        {
            "retirement_pay": 퇴직금 예상액 (원),
            "average_wage": 평균임금 (일급),
            "regular_wage": 통상임금 (일급),
            "service_days": 재직일수,
            "service_months": 재직개월수,
            "eligible": 자격 여부 (1년 이상),
            "calculation_details": 계산 상세 정보
        }
    """
    from datetime import date, timedelta
    from decimal import Decimal
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # 1. 재직기간 계산
    start_date = employee.start_date
    end_date = employee.end_date if employee.end_date else today
    
    if not start_date:
        return {
            "retirement_pay": 0,
            "average_wage": 0,
            "regular_wage": 0,
            "service_days": 0,
            "service_months": 0,
            "eligible": False,
            "calculation_details": "입사일 정보가 없습니다."
        }
    
    service_days = (end_date - start_date).days
    service_months = round(service_days / 30.44, 1)  # 평균 월 일수
    
    # 2. 1년 미만 근로자는 퇴직금 0원
    if service_days < 365:
        return {
            "retirement_pay": 0,
            "average_wage": 0,
            "regular_wage": 0,
            "service_days": service_days,
            "service_months": service_months,
            "eligible": False,
            "calculation_details": f"재직기간 {service_months}개월 (1년 미만은 퇴직금 지급 대상 아님)"
        }
    
    # 3. 통상임금 계산 (시급 기준)
    # 통상임금 = (시급 × 주간 근로시간 × 52주) / 365일
    hourly_rate = Decimal(str(employee.hourly_rate))
    weekly_hours = Decimal(str(employee.weekly_hours)) if employee.weekly_hours else Decimal('40')
    
    annual_wage = hourly_rate * weekly_hours * Decimal('52')
    regular_daily_wage = annual_wage / Decimal('365')
    
    # 4. 평균임금 계산 (최근 3개월 실제 임금 기준)
    three_months_ago = end_date - timedelta(days=90)
    
    # 최근 3개월 근로기록 조회
    recent_records = employee.work_records.filter(
        work_date__gte=three_months_ago,
        work_date__lte=end_date
    )
    
    total_wage_3m = Decimal('0')
    for record in recent_records:
        hours = record.get_total_hours()
        if hours > 0:
            total_wage_3m += Decimal(str(hours)) * hourly_rate
    
    # 3개월 = 90일 (역일수)
    calendar_days_3m = Decimal('90')
    
    if total_wage_3m > 0:
        average_daily_wage = total_wage_3m / calendar_days_3m
    else:
        # 근로기록이 없으면 통상임금 사용
        average_daily_wage = regular_daily_wage
    
    # 5. 평균임금이 통상임금보다 낮으면 통상임금 사용
    final_average_wage = max(average_daily_wage, regular_daily_wage)
    
    # 6. 퇴직금 계산
    # 퇴직금 = 평균임금 × 30일 × (재직일수 / 365)
    retirement_pay = final_average_wage * Decimal('30') * (Decimal(str(service_days)) / Decimal('365'))
    
    calculation_details = (
        f"평균임금(일급): {int(average_daily_wage):,}원\n"
        f"통상임금(일급): {int(regular_daily_wage):,}원\n"
        f"적용 기준: {int(final_average_wage):,}원 (둘 중 높은 금액)\n"
        f"재직일수: {service_days}일 ({service_months}개월)\n"
        f"계산식: {int(final_average_wage):,}원 × 30일 × ({service_days}/365)"
    )
    
    return {
        "retirement_pay": int(retirement_pay),
        "average_wage": int(final_average_wage),
        "regular_wage": int(regular_daily_wage),
        "service_days": service_days,
        "service_months": service_months,
        "eligible": True,
        "calculation_details": calculation_details
    }
