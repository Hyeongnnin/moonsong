"""labor/services.py

노동법 관련 근로조건 평가 서비스 (단순화된 참고용 계산 로직)
본 로직은 실제 법률 자문이 아닌 교육/참고 목적의 계산 예시입니다.
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from decimal import Decimal
from math import floor
from typing import Optional, Dict, Any, List


MIN_WAGE_2025 = 10030  # 2025년 최저임금 (시급)


@dataclass
class JobInputs:
    hourly_rate: float
    employment_type: str
    start_date: date
    is_current: bool
    has_paid_weekly_holiday: bool
    attendance_rate_last_year: Optional[float]
    total_wage_last_3m: Optional[float]
    total_days_last_3m: Optional[int]
    # 계약상 주 소정근로시간
    contract_weekly_hours: Optional[float] = None
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


def calc_weekly_holiday_pay(weekly_hours: float, hourly_rate: float, work_days_per_week: Optional[int], contract_weekly_hours: Optional[float] = None) -> int:
    """주휴수당 계산 (계약상 시간 또는 스케줄 기반)
    
    Args:
        weekly_hours: 주간 총 근로시간 (스케줄 기반으로 계산된 값)
        hourly_rate: 시급
        work_days_per_week: 주당 근무일수
        contract_weekly_hours: 계약상 주 소정근로시간 (최우선)
    """
    total_weekly_hours = contract_weekly_hours if contract_weekly_hours is not None else weekly_hours
    
    if not total_weekly_hours or total_weekly_hours < 15:
        return 0
    
    days = work_days_per_week
    if not days or days <= 0:
        # 스케줄에서 계산된 근무일수가 없으면 기본 추정
        estimated_daily_hours = total_weekly_hours if total_weekly_hours < 24 else total_weekly_hours / 5
        days = max(1, int(round(total_weekly_hours / max(estimated_daily_hours, 1))))
    
    weekly_holiday_hours = total_weekly_hours / days
    pay = weekly_holiday_hours * hourly_rate
    return int(round(pay))


def calculate_weekly_holiday_pay_v2(employee, target_date: date) -> Dict[str, Any]:
    """주휴수당 계산 v2 (사용자 요청 로직)
    
    - 계약상 주 소정근로시간 >= 15시간
    - 해당 주의 소정근로일 개근 (REGULAR_WORK, ANNUAL_LEAVE 인정)
    - 주휴시간 = 계약상 주 소정근로시간 / 해당 주의 소정근로일 수
    - 주휴수당 = 주휴시간 * 시급
    """
    from .models import WorkRecord
    from .policy_manager import PolicyManager
    
    rules = PolicyManager.get_holiday_pay_rules()
    min_weekly_hours = Decimal(str(rules.get('min_weekly_hours', 15)))
    
    # 기준 날짜가 속한 주 범위 (월~일)
    start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # 주간 소정근로일 및 시간 정보 수집
    # 소정근로일 목록 수집 및 개근 체크
    scheduled_dates = []
    weekly_scheduled_hours = Decimal('0')
    
    current_date = start_of_week
    while current_date <= end_of_week:
        if employee.is_scheduled_workday(current_date):
            scheduled_dates.append(current_date)
            # 스케줄 기반 예정 시간
            s_info = employee.get_schedule_for_date(current_date)
            if s_info['start_time'] and s_info['end_time']:
                dummy_date = date(2000, 1, 1)
                dt_start = datetime.combine(dummy_date, s_info['start_time'])
                dt_end = datetime.combine(dummy_date, s_info['end_time'])
                if dt_end < dt_start:
                    dt_end += timedelta(days=1)
                
                duration = dt_end - dt_start
                total_mins = (duration.total_seconds() / 60.0) + float(s_info.get('next_day_work_minutes', 0))
                break_mins = float(s_info.get('break_minutes', 0))
                weekly_scheduled_hours += Decimal(str(max(0.0, total_mins - break_mins) / 60.0))
        current_date += timedelta(days=1)
    
    # 실제 근로 (추가근무 포함) 확인을 위해 레코드 조회
    records = WorkRecord.objects.filter(employee=employee, work_date__range=[start_of_week, end_of_week])
    record_map = {r.work_date: r for r in records}
    
    # 실제 근로시간 합계
    actual_worked_hours = Decimal('0')
    for r in records:
        actual_worked_hours += r.get_total_hours()

    # 총 주간 근로시간 결정 (views.py의 holiday_pay 로직과 동일하게 맞춤)
    # 계약상 시간 우선, 단 실제 근로시간이 더 많아 15시간을 넘기면 그것을 인정
    is_estimated = employee.contract_weekly_hours is None
    
    if not is_estimated:
        contract_hours = Decimal(str(employee.contract_weekly_hours))
        # 계약 15시간 미만이나 실제 15시간 이상이면 인정
        if contract_hours < min_weekly_hours and actual_worked_hours >= min_weekly_hours:
            total_weekly_hours = actual_worked_hours
        else:
            total_weekly_hours = contract_hours
    else:
        # 스케줄 vs 실제 중 큰 값
        total_weekly_hours = max(weekly_scheduled_hours, actual_worked_hours)
    
    # 조건 1: 15시간 
    if total_weekly_hours < min_weekly_hours:
        return {
            'amount': 0, 'hours': 0, 'reason': 'less_than_threshold', 
            'week_start': start_of_week, 'week_end': end_of_week, 'is_eligible': False
        }
    
    # 조건 2: 소정근로일 개근 여부
    is_perfect = True
    for sd in scheduled_dates:
        record = record_map.get(sd)
        # REGULAR_WORK, ANNUAL_LEAVE, EXTRA_WORK 모두 출근으로 인정
        if not record or record.attendance_status not in ['REGULAR_WORK', 'ANNUAL_LEAVE', 'EXTRA_WORK']:
            is_perfect = False
            break
            
    if not is_perfect:
        return {
            'amount': 0, 'hours': 0, 'reason': 'not_perfect_attendance', 
            'week_start': start_of_week, 'week_end': end_of_week, 'is_eligible': False
        }
        
    # 주휴시간 및 금액 계산
    # 주휴시간 계산 (비례 원칙 적용)
    # 단시간 근로자 주휴수당 = (1주 소정근로시간 / 40시간) × 8시간
    # 즉, 주간 근로시간 / 5 (단, 최대 8시간 한도)
    holiday_hours = total_weekly_hours / Decimal('5')
    if holiday_hours > 8:
        holiday_hours = Decimal('8')
        
    amount = int(holiday_hours * employee.hourly_rate)
    
    return {
        'amount': amount,
        'hours': float(holiday_hours),
        'reason': 'eligible',
        'week_start': start_of_week,
        'week_end': end_of_week,
        'is_eligible': True
    }


def get_monthly_holiday_pay_info(employee, year: int, month: int) -> Dict[str, Any]:
    """월별 주휴수당 정보 요약 (확정분 vs 예정분 구분)"""
    from django.utils import timezone
    today = timezone.localdate()
    
    start_date = date(year, month, 1)
    # 월의 모든 날짜를 포함하는 주들을 찾기 위해 월의 첫날부터 마지막날까지 순회
    
    weeks = []
    current_week_start = start_date - timedelta(days=start_date.weekday()) # 해당 월의 첫 날이 포함된 주의 월요일
    
    import calendar
    _, last_day = calendar.monthrange(year, month)
    end_of_month = date(year, month, last_day)
    
    while current_week_start <= end_of_month:
        week_end = current_week_start + timedelta(days=6)
        
        # 해당 주가 선택한 월에 포함되는지 체크 (Week End Date 기준)
        if current_week_start.month == month or week_end.month == month:
            # [Fix] 만약 해당 주의 '주휴일(일요일)'이 소정근로일이 아니라고 판정되면(예: 월별 스케줄 삭제로 인해),
            #       주휴수당 발생 자체가 불가능하므로 제외합니다.
            #       (사용자가 월별 기록을 삭제했을 때, 이전에 걸친 주의 수당이 남지 않도록 함)
            #       단, 원래 스케줄이 없는 날이면 상관없으나 'MonthlySchedule'로 명시적 삭제된 경우엔 False가 나옴.
            #       일반적인 주휴일은 '비근무'지만 '소정근로일'의 일환으로 관리될 수 있음.
            #       여기서는 'MonthlySchedule'이 존재하고 start_time이 None인 경우를 체크해야 함.
            
            # 더 강력한 체크: 해당 주에 '유효한 계획된 근로일'이 하루라도 있는가?
            # 삭제된 달이라면 모든 요일이 MonthlySchedule(start=None)이므로 is_scheduled_workday가 모두 False임.
            has_scheduled_day = False
            temp_date = current_week_start
            while temp_date <= week_end:
                if employee.is_scheduled_workday(temp_date):
                    has_scheduled_day = True
                    break
                temp_date += timedelta(days=1)
            
            if has_scheduled_day:
                res = calculate_weekly_holiday_pay_v2(employee, current_week_start)
                
                # 확정 여부: 주의 일요일(week_end)이 오늘 이전이면 확정
                is_finished = week_end < today
                
                weeks.append({
                    'start': current_week_start,
                    'end': week_end,
                    'amount': res['amount'],
                    'is_finished': is_finished,
                    'is_eligible': res['is_eligible'],
                    'reason': res['reason']
                })
            
        current_week_start += timedelta(days=7)
        
    confirmed_total = sum(w['amount'] for w in weeks if w['is_finished'])
    estimated_total = sum(w['amount'] for w in weeks)
    
    return {
        'weeks': weeks,
        'confirmed_total': confirmed_total,
        'estimated_total': estimated_total
    }


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


def calc_severance(service_years: int, weekly_hours: Optional[float], total_wage_last_3m: Optional[float], total_days_last_3m: Optional[int], contract_weekly_hours: Optional[float] = None) -> int:
    """퇴직금 계산 (계약상 시간 또는 스케줄 기반)
    
    Args:
        service_years: 근속 연수
        weekly_hours: 주간 총 근로시간 (스케줄 기반으로 계산된 값, None일 수 있음)
        total_wage_last_3m: 최근 3개월 총 임금
        total_days_last_3m: 최근 3개월 총 일수
        contract_weekly_hours: 계약상 주 소정근로시간 (최우선)
    """
    total_weekly_hours = contract_weekly_hours if contract_weekly_hours is not None else weekly_hours
    
    if service_years < 1 or not total_weekly_hours or total_weekly_hours < 15:
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
    weekly_holiday_pay = calc_weekly_holiday_pay(weekly_hours, job.hourly_rate, job.work_days_per_week, job.contract_weekly_hours)
    annual_leave_days = calc_annual_leave(job.start_date, job.attendance_rate_last_year, today)
    severance_estimate = calc_severance(service_years, weekly_hours, job.total_wage_last_3m, job.total_days_last_3m, job.contract_weekly_hours)

    warnings: List[str] = []
    if not min_wage["min_wage_ok"]:
        warnings.append("최저임금(10,030원) 미달 가능성이 있습니다.")
    total_weekly_hours = job.contract_weekly_hours if job.contract_weekly_hours is not None else weekly_hours
    if total_weekly_hours >= 15 and weekly_holiday_pay == 0:
        warnings.append("주 15시간 이상 근무 시 주휴수당 지급이 필요합니다.")
    if service_years >= 1 and total_weekly_hours >= 15 and severance_estimate == 0:
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
    단, 이번 달(오늘 기준)에 MonthlySchedule이 있다면 그것을 우선 반영합니다.
    """
    from datetime import datetime
    from django.utils import timezone
    from .models import WorkSchedule, MonthlySchedule
    
    today = timezone.localdate()
    year = today.year
    month = today.month
    
    # 1. 월별 스케줄이 있는지 확인 (해당 월의 아무 요일이나)
    #    (하나라도 있으면 월별 스케줄 모드로 간주)
    #    정확히는 7일 전체를 봐야 하지만, '이번 달 근로조건'을 평가하는 것이므로
    #    이번 달에 MonthlySchedule이 존재하면 그것을 기준으로 주당 시간을 산출
    monthly_schedules = MonthlySchedule.objects.filter(
        employee=employee,
        year=year,
        month=month,
        enabled=True
    )
    
    weekly_hours = 0.0
    work_days_per_week = 0
    
    if monthly_schedules.exists():
        # 월별 스케줄 사용
        for schedule in monthly_schedules:
            if schedule.start_time and schedule.end_time:
                dummy_date = datetime(2000, 1, 1)
                dt_start = datetime.combine(dummy_date.date(), schedule.start_time)
                dt_end = datetime.combine(dummy_date.date(), schedule.end_time)
                diff = dt_end - dt_start
                hours = diff.total_seconds() / 3600
                weekly_hours += hours
                work_days_per_week += 1
    else:
        # 주간 스케줄 사용 (fallback)
        schedules = WorkSchedule.objects.filter(employee=employee, enabled=True)
        for schedule in schedules:
            if schedule.start_time and schedule.end_time:
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
        is_current=True,
        has_paid_weekly_holiday=True,
        contract_weekly_hours=float(employee.contract_weekly_hours) if employee.contract_weekly_hours is not None else None,
        attendance_rate_last_year=float(employee.attendance_rate_last_year)
        if employee.attendance_rate_last_year is not None
        else None,
        total_wage_last_3m=float(employee.total_wage_last_3m)
        if employee.total_wage_last_3m is not None
        else None,
        total_days_last_3m=employee.total_days_last_3m,
    )


# ... (calculate_annual_leave_v2, etc stay same) ...
# ... (calculate_annual_leave) ...

# ... (We need to jump to calculate_retirement_pay to apply fix) ...




def calculate_annual_leave_v2(employee, year: int) -> Dict[str, Any]:
    """연차휴가 예상액 계산 (연도 기준 단순/안전 버전)
    
    1. 대상: 5인 이상 사업장 AND 주 15시간 이상
    2. 발생: 
       - 1년 미만: 월 단위 개근 시 1일 (최대 11일)
       - 1년 이상: 해당 연도 15일 고정
    3. 사용: 해당 연도 내 ANNUAL_LEAVE 일수
    """
    from datetime import date, timedelta
    from django.db.models import Count
    from django.utils import timezone
    from .models import WorkRecord
    import calendar

    today = timezone.localdate()
    start_date = employee.start_date
    
    # 1. 자격 확인
    eligible = True
    reason = None
    
    if not employee.is_workplace_over_5:
        eligible = False
        reason = "5인 미만 사업장은 연차 의무 적용 대상이 아닙니다."
    elif (employee.contract_weekly_hours or 0) < 15:
        eligible = False
        reason = "주당 근로시간이 15시간 미만입니다."
    elif not start_date:
        eligible = False
        reason = "근로 시작일 정보가 없습니다."
    elif start_date > today:
        eligible = False
        reason = "근로 시작일 이전입니다."

    if not eligible:
        return {
            "eligible": False,
            "accrued_days": 0,
            "used_days": 0,
            "remaining_days": 0,
            "reason": reason
        }

    # 2. 발생 연차(accrued_days) 계산
    accrued_days = 0.0
    
    # 입사 1주년 날짜
    one_year_anniversary = start_date + timedelta(days=365)
    
    # 해당 연도 범위
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    # 1년 이상자 여부 판정 (단순화: 오늘 기준 1년 이상이면 15일)
    if today >= one_year_anniversary:
        accrued_days = 15.0
    else:
        # 1년 미만자: 입사 후 1달마다 개근 시 1일 (최대 11개월)
        # i=0 (1개월차), i=1 (2개월차) ... i=10 (11개월차)
        for i in range(11):
            m_start = start_date + timedelta(days=i*30)
            m_end = m_start + timedelta(days=29)
            
            # 이 개근 판정 기간이 오늘을 완전히 지났거나 오늘을 포함하는 경우
            # (오늘 진행 중인 달도 일단 개근 중이면 1일로 쳐줌 - "결근 명시 안되면 개근")
            if m_start > today:
                break
                
            # 해당 기간(m_start~m_end) 중 소정근로일인데 ABSENT인 기록이 있는지 확인
            # is_scheduled_workday 체크 로직 포함
            absent_records = WorkRecord.objects.filter(
                employee=employee,
                work_date__range=[m_start, m_end],
                attendance_status='ABSENT'
            )
            
            has_absent = False
            for r in absent_records:
                if employee.is_scheduled_workday(r.work_date):
                    has_absent = True
                    break
            
            if not has_absent:
                # [Fix] "개근"의 전제는 "소정근로일이 존재함"입니다.
                # 해당 기간 내에 소정근로일이 하루라도 있었는지 확인합니다.
                # 아예 스케줄이 없는(삭제된) 달에는 연차가 발생하지 않아야 합니다.
                has_any_schedule = False
                temp_date = m_start
                while temp_date <= m_end:
                    if employee.is_scheduled_workday(temp_date):
                        has_any_schedule = True
                        break
                    temp_date += timedelta(days=1)
                
                if has_any_schedule:
                    accrued_days += 1.0

    # 3. 사용 연차(used_days) 계산
    # 해당 연도 내의 ANNUAL_LEAVE 개수
    used_days = WorkRecord.objects.filter(
        employee=employee,
        work_date__range=[year_start, year_end],
        attendance_status='ANNUAL_LEAVE'
    ).count()

    # 4. 잔여 연차(remaining_days)
    remaining_days = max(0.0, accrued_days - used_days)

    return {
        "eligible": True,
        "accrued_days": float(accrued_days),
        "used_days": float(used_days),
        "remaining_days": float(remaining_days),
        "reason": None
    }


def calculate_annual_leave(job: JobInputs, today: Optional[date] = None) -> Dict[str, float]:
    """
    연차휴가 요약 계산 (단순화 규칙)
    - 주 15시간 미만: 0일 처리
    - 1년 미만: 월 1일 발생 (개근 가정)
    - 1년 이상: 출근율 0.8 미만 0일, 그 외 15일 + (2년마다 1일) 최대 25일
    - 사용 연차는 현재 0일로 가정 (추후 실제 데이터로 대체)
    """
    today = today or date.today()

    weekly_hours = job.contract_weekly_hours if job.contract_weekly_hours is not None else (job.weekly_hours or 0)
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
    주어진 월의 각 날짜에 대해 스케줄 여부를 표시하고, 실제 근로기록이 있으면 함께 반환합니다.

    표시 규칙:
    - is_scheduled_workday: 월별 오버라이드(MonthlySchedule)가 있으면 그것, 없으면 주간 스케줄(WorkSchedule)을 기준으로 소정근로일 여부 판정
    - is_worked: 실제 WorkRecord가 존재하고 시간이 0보다 크면 True
    - schedule_source: "monthly" | "weekly" | None
    - 캘린더 API와 동일한 형식으로 반환하여 프론트엔드에서 일관성 있게 처리
    """
    # 실제 근무 기록 맵
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )
    records_map = {wr.work_date: wr for wr in work_records}

    cal = calendar.Calendar()
    month_dates = cal.itermonthdates(year, month)
    scheduled_dates_data = []
    
    # Serializer import (circular import 방지 위해 함수 내부 import 권장)
    from .serializers import WorkRecordSerializer

    for dt in month_dates:
        if dt.month != month:
            continue

        record = records_map.get(dt)
        weekday = dt.weekday()
        
        # 1. 소정근로일 여부 및 스케줄 소스 판정 (근무 시작일 이후여야 함)
        is_scheduled_workday = False
        schedule_source = None  # "monthly" | "weekly" | None
        scheduled_start_time = None
        scheduled_end_time = None
        scheduled_break_minutes = 0
        scheduled_is_overnight = False
        scheduled_next_day_minutes = 0
        
        # 시작일 이전이면 스케줄링 건너뜀
        if dt >= employee.start_date:
            # 월별 스케줄 확인 (최우선)
            monthly_schedule = MonthlySchedule.objects.filter(
                employee=employee,
                year=year,
                month=month,
                weekday=weekday,
                enabled=True
            ).first()
            
            if monthly_schedule:
                # 월별 스케줄이 존재하면, 시간이 있든 없든 이것을 최종 스케줄로 간주 (fallback 하지 않음)
                schedule_source = "monthly"
                if monthly_schedule.start_time and monthly_schedule.end_time:
                    is_scheduled_workday = True
                    scheduled_start_time = monthly_schedule.start_time.strftime('%H:%M')
                    scheduled_end_time = monthly_schedule.end_time.strftime('%H:%M')
                    scheduled_break_minutes = monthly_schedule.break_minutes
                    scheduled_is_overnight = monthly_schedule.is_overnight
                    scheduled_next_day_minutes = monthly_schedule.next_day_work_minutes
                else:
                    # 시간이 없는 월별 스케줄 = 명시적 근무 없음
                    is_scheduled_workday = False
            else:
                # 월별 스케줄이 없을 때만 주간 스케줄 확인 (fallback)
                weekly_schedule = WorkSchedule.objects.filter(
                    employee=employee,
                    weekday=weekday,
                    enabled=True
                ).first()
                
                if weekly_schedule and weekly_schedule.start_time and weekly_schedule.end_time:
                    is_scheduled_workday = True
                    schedule_source = "weekly"
                    scheduled_start_time = weekly_schedule.start_time.strftime('%H:%M')
                    scheduled_end_time = weekly_schedule.end_time.strftime('%H:%M')
                    scheduled_break_minutes = weekly_schedule.break_minutes
                    scheduled_is_overnight = weekly_schedule.is_overnight
                    scheduled_next_day_minutes = weekly_schedule.next_day_work_minutes
        
        # 2. 출결 상태 및 실제 근무 여부
        attendance_status = None
        is_worked = False
        if record:
            attendance_status = record.attendance_status
            # REGULAR_WORK 또는 EXTRA_WORK는 실제 근무로 간주
            is_worked = attendance_status in ['REGULAR_WORK', 'EXTRA_WORK'] and record.get_total_hours() > 0

        scheduled_dates_data.append({
            "date": dt.isoformat(),
            "day": dt.day,
            "is_scheduled_workday": is_scheduled_workday,  # 소정근로일 여부
            "is_scheduled": is_scheduled_workday,  # 하위 호환성
            "schedule_source": schedule_source,  # "monthly" | "weekly" | None
            "scheduled_start_time": scheduled_start_time,
            "scheduled_end_time": scheduled_end_time,
            "scheduled_break_minutes": scheduled_break_minutes,
            "scheduled_is_overnight": scheduled_is_overnight,
            "scheduled_next_day_minutes": scheduled_next_day_minutes,
            "is_worked": is_worked,
            "attendance_status": attendance_status,
            "record": WorkRecordSerializer(record).data if record else None,
        })

    return scheduled_dates_data


def compute_monthly_schedule_stats(employee, year, month):
    """
    월별 근무 통계를 계산합니다.
    - 과거(~어제): 실제 근무 기록(WorkRecord) 기준
    - 오늘: 실제 근무 기록이 있으면 그것, 없으면 스케줄(WorkSchedule/MonthlySchedule) 기준
    - 미래(내일~):
        - WorkRecord가 있고 attendance_status가 'ABSENT' 등인 경우: 0시간 (결근 확정)
        - WorkRecord가 없는 경우: 스케줄 기준 근무 예정으로 계산
    
    v5 (2025-01-15): 미래 예정된 근무도 포함하도록 변경
    """
    from django.utils import timezone
    import calendar
    
    # 오늘 날짜
    today = timezone.localdate()
    
    hourly_rate = float(employee.hourly_rate)
    
    # 해당 월의 마지막 날 계산
    _, last_day = calendar.monthrange(year, month)
    month_start = date(year, month, 1)
    month_end = date(year, month, last_day)
    
    # 해당 월의 모든 WorkRecord 조회 (한 번에 쿼리)
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )
    records_map = {wr.work_date: wr for wr in work_records}
    
    total_hours = 0.0
    total_days = 0
    total_salary = Decimal('0')
    
    # 1일부터 말일까지 순회
    current = month_start
    while current <= month_end:
        record = records_map.get(current)
        daily_hours = 0.0
        is_paid_day = False # 근무일 수 산정용 (유급 인정일)
        
        # 1. 실제 기록이 있는 경우 (가장 확실)
        if record:
            # 출결 상태에 따른 처리
            status = record.attendance_status
            
            # 결근/병가/무급휴가는 0시간
            if status in ['ABSENT', 'SICK_LEAVE', 'UNPAID_LEAVE']:
                daily_hours = 0.0
            
            # 근무/연차/추가근무 등은 시간 인정
            else:
                # 실제 시간 입력이 있으면 그것을 사용
                if record.time_in and record.time_out:
                    daily_hours = float(record.get_total_hours())
                    is_paid_day = True
                
                # 시간 입력은 없지만(아직 미입력 등) 스케줄상 근무일이면 스케줄 시간 적용 (미래이거나 오늘인데 아직 입력 안한 경우)
                # 단, 'EXTRA_WORK'인데 시간 없으면 0으로 둬야 함 (추가근무는 스케줄이 없으므로)
                elif status == 'REGULAR_WORK' or status == 'ANNUAL_LEAVE':
                    # 스케줄 정보 가져오기
                    s_info = employee.get_schedule_for_date(current)
                    if s_info['is_scheduled']:
                        dummy_date = date(2000, 1, 1)
                        if s_info['start_time'] and s_info['end_time']:
                            dt_start = datetime.combine(dummy_date, s_info['start_time'])
                            dt_end = datetime.combine(dummy_date, s_info['end_time'])
                            if dt_end < dt_start:
                                dt_end += timedelta(days=1)
                            
                            duration = dt_end - dt_start
                            total_mins = (duration.total_seconds() / 60.0) + float(s_info.get('next_day_work_minutes', 0))
                            break_mins = float(s_info.get('break_minutes', 0))
                            daily_hours = max(0.0, (total_mins - break_mins) / 60.0)
                            is_paid_day = True
        
        # 2. 기록이 없는 경우
        else:
            # 과거(~어제)인데 기록이 없다 -> 근무 안 한 것으로 간주 (0시간)
            if current < today:
                daily_hours = 0.0
            
            # 오늘 또는 미래 -> 스케줄이 있으면 근무 예정으로 계산
            else:
                s_info = employee.get_schedule_for_date(current)
                if s_info['is_scheduled']:
                    dummy_date = date(2000, 1, 1)
                    if s_info['start_time'] and s_info['end_time']:
                        dt_start = datetime.combine(dummy_date, s_info['start_time'])
                        dt_end = datetime.combine(dummy_date, s_info['end_time'])
                        if dt_end < dt_start:
                            dt_end += timedelta(days=1)
                        
                        duration = dt_end - dt_start
                        total_mins = (duration.total_seconds() / 60.0) + float(s_info.get('next_day_work_minutes', 0))
                        break_mins = float(s_info.get('break_minutes', 0))
                        daily_hours = max(0.0, (total_mins - break_mins) / 60.0)
                        is_paid_day = True

        if daily_hours > 0:
            total_hours += daily_hours
            total_salary += Decimal(str(daily_hours)) * Decimal(str(hourly_rate))
        
        if is_paid_day:
            total_days += 1
            
        current += timedelta(days=1)


    # ============================================================
    # 이번 주 통계 계산 (주휴수당 계산용 + 미래 예정 포함)
    # ============================================================
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    week_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__range=[start_of_week, end_of_week]
    )
    week_records_map = {wr.work_date: wr for wr in week_records}
    
    total_this_week_hours = 0.0
    
    curr_week = start_of_week
    while curr_week <= end_of_week:
        # 이번 달 통계와 동일한 로직 적용 (함수화하면 좋겠지만 일단 인라인)
        d_hours = 0.0
        w_record = week_records_map.get(curr_week)
        
        if w_record:
            if w_record.attendance_status in ['ABSENT', 'SICK_LEAVE', 'UNPAID_LEAVE']:
                d_hours = 0.0
            else:
                if w_record.time_in and w_record.time_out:
                    d_hours = float(w_record.get_total_hours())
                elif w_record.attendance_status in ['REGULAR_WORK', 'ANNUAL_LEAVE']:
                    s_info = employee.get_schedule_for_date(curr_week)
                    if s_info['is_scheduled']:
                        # (스케줄 시간 계산 생략... 간단히 처리위해 같은 로직)
                        # 여기서는 정확성을 위해 위와 동일하게 계산
                         dummy_date = date(2000, 1, 1)
                         if s_info['start_time'] and s_info['end_time']:
                            dt_start = datetime.combine(dummy_date, s_info['start_time'])
                            dt_end = datetime.combine(dummy_date, s_info['end_time'])
                            if dt_end < dt_start:
                                dt_end += timedelta(days=1)
                            dur = (dt_end - dt_start).total_seconds() / 60.0 + float(s_info.get('next_day_work_minutes', 0))
                            brk = float(s_info.get('break_minutes', 0))
                            d_hours = max(0.0, (dur - brk) / 60.0)
        else:
            if curr_week < today:
                d_hours = 0.0
            else:
                s_info = employee.get_schedule_for_date(curr_week)
                if s_info['is_scheduled']:
                     dummy_date = date(2000, 1, 1)
                     if s_info['start_time'] and s_info['end_time']:
                        dt_start = datetime.combine(dummy_date, s_info['start_time'])
                        dt_end = datetime.combine(dummy_date, s_info['end_time'])
                        if dt_end < dt_start:
                            dt_end += timedelta(days=1)
                        dur = (dt_end - dt_start).total_seconds() / 60.0 + float(s_info.get('next_day_work_minutes', 0))
                        brk = float(s_info.get('break_minutes', 0))
                        d_hours = max(0.0, (dur - brk) / 60.0)
        
        total_this_week_hours += d_hours
        curr_week += timedelta(days=1)

    return {
        "scheduled_total_hours": total_hours,
        "scheduled_estimated_salary": float(total_salary),
        "scheduled_work_days": total_days,
        "scheduled_this_week_hours": float(total_this_week_hours),
        "scheduled_this_week_estimated_salary": float(Decimal(str(total_this_week_hours)) * Decimal(str(hourly_rate))),
    }


def _overlap_hours(start_dt, end_dt, window_start_time, window_end_time):
    """주어진 날짜의 시각 구간과 특정 시간창 사이 겹치는 시간을 시간(float)으로 반환.

    window_end_time가 다음날(예: 22:00~06:00)로 넘어가는 경우를 지원합니다.
    """
    from datetime import datetime, timedelta
    if not start_dt or not end_dt:
        return 0.0
    if end_dt <= start_dt:
        return 0.0

    day = start_dt.date()
    w_start = datetime.combine(day, window_start_time)
    w_end = datetime.combine(day, window_end_time)

    # start/end가 tz-aware인 경우, 비교를 위해 window도 동일 tz로 맞춤
    tzinfo = getattr(start_dt, 'tzinfo', None)
    if tzinfo is not None and w_start.tzinfo is None:
        w_start = w_start.replace(tzinfo=tzinfo)
        w_end = w_end.replace(tzinfo=tzinfo)

    if window_end_time <= window_start_time:
        # 다음날로 넘어가는 창 (예: 22:00~06:00)
        w_end = w_end + timedelta(days=1)

    # 교집합 계산
    s = max(start_dt, w_start)
    e = min(end_dt, w_end)
    if e <= s:
        return 0.0
    return (e - s).total_seconds() / 3600.0


def compute_monthly_payroll(employee, year, month):
    """월 단위 급여 최소 계산 (우선 카드 표시용)

    - 실근로시간: 각 WorkRecord의 `get_total_hours()` 합
    - 근로일수: `get_total_hours() > 0` 인 레코드 수
    - 급여: 시급 × 실근로시간

    추가 반영:
    - 휴게구간(break_intervals, break_start/break_end) 우선 적용 (WorkRecord.get_total_hours 내부 반영)
    - 휴일근무(`day_type=HOLIDAY_WORK`) 총 시간 및 금액 집계 (월별 부가 정보 제공)
    TODO: 야간/연장/주휴 가산은 추후 단계에서 추가
    """
    hourly_rate = float(employee.hourly_rate or 0)

    records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month,
    )

    total_hours = 0.0
    total_work_days = 0
    holiday_hours = 0.0
    night_hours = 0.0  # [Fix] Initialize night_hours
    for r in records:
        hours = float(r.get_total_hours())
        if hours > 0:
            total_hours += hours
            total_work_days += 1
            if getattr(r, 'day_type', 'NORMAL') == 'HOLIDAY_WORK':
                holiday_hours += hours
            
            # 야간 시간 합산 (v4)
            night_hours += float(r.get_night_hours())

    base_hours = max(total_hours - holiday_hours, 0.0)
    overtime_hours = 0.0
    weekly_holiday_hours = 0.0

    is_over_5 = getattr(employee, 'is_workplace_over_5', False)
    
    base_pay = base_hours * hourly_rate
    overtime_pay = overtime_hours * hourly_rate * 0.5 if is_over_5 else 0
    night_pay = night_hours * hourly_rate * 0.5 if is_over_5 else 0
    holiday_pay = holiday_hours * hourly_rate
    if is_over_5 and holiday_hours > 0:
        holiday_pay += holiday_hours * hourly_rate * 0.5
    
    weekly_holiday_pay = weekly_holiday_hours * hourly_rate
    
    estimated_salary = base_pay + overtime_pay + night_pay + holiday_pay + weekly_holiday_pay

    breakdown = {
        "base_hours": round(base_hours, 2),
        "overtime_hours": round(overtime_hours, 2),
        "night_hours": round(night_hours, 2),
        "holiday_hours": round(holiday_hours, 2),
        "weekly_holiday_hours": round(weekly_holiday_hours, 2),
        "base_pay": round(base_pay, 2),
        "overtime_pay": round(overtime_pay, 2),
        "night_pay": round(night_pay, 2),
        "holiday_pay": round(holiday_pay, 2),
        "weekly_holiday_pay": round(weekly_holiday_pay, 2),
    }

    return {
        "month": f"{year}-{str(month).zfill(2)}",
        "total_hours": round(total_hours, 2),
        "total_work_days": total_work_days,
        "hourly_wage": round(hourly_rate, 2),
        "estimated_salary": round(estimated_salary, 2),
        "holiday_hours": round(holiday_hours, 2),
        "holiday_pay": round(holiday_pay, 2),
        "breakdown": breakdown,
    }


def calculate_severance_v2(employee) -> Dict[str, Any]:
    """퇴직금 예상액 계산 (MVP v2)
    
    1순위: ROLLING_90D_ACTUAL (최근 90일 실제 임금 / 90)
    2순위: CONTRACT_ESTIMATE (계약 시간 기반 추정)
    """
    from datetime import date, timedelta
    from decimal import Decimal
    from django.utils import timezone
    from .models import WorkRecord
    
    today = timezone.localdate()
    start_date = employee.start_date
    if not start_date:
        return {
            'eligible': False, 'severance_pay': 0, 'reason': 'start_date_missing',
            'service_days': 0, 'service_months': 0, 'avg_daily_wage': 0, 'method': 'NONE'
        }
        
    service_days = (today - start_date).days
    service_months = round(service_days / 30.41, 1) # 근사치
    
    # 지급 대상 조건
    # 1) 재직 365일 이상
    # 2) 주 소정근로시간 15시간 이상
    contract_hours = Decimal(str(employee.contract_weekly_hours)) if employee.contract_weekly_hours is not None else Decimal('0')
    
    eligible = True
    reason = ''
    if service_days < 365:
        eligible = False
        reason = 'service_period_under_1y'
    elif contract_hours < 15:
        eligible = False
        reason = 'hours_under_15'
        
    hourly_rate = Decimal(str(employee.hourly_rate))
    
    # --- 평균임금 산정 ---
    method = 'ROLLING_90D_ACTUAL'
    # 최근 90일 (오늘 제외 어제부터 90일간)
    end_90 = today - timedelta(days=1)
    start_90 = today - timedelta(days=90)
    
    # 1. 실제 근로 기반 임금 (기본 + 야간/휴일 가산)
    records = WorkRecord.objects.filter(employee=employee, work_date__range=[start_90, end_90])
    
    total_earnings_90 = Decimal('0')
    is_over_5 = employee.is_workplace_over_5
    
    for r in records:
        if r.attendance_status in ['REGULAR_WORK', 'EXTRA_WORK']:
            h = r.get_total_hours()
            if h > 0:
                # 기본급
                total_earnings_90 += h * hourly_rate
                if is_over_5:
                    # 야간 가산
                    nh = r.get_night_hours()
                    if nh > 0:
                        total_earnings_90 += nh * hourly_rate * Decimal('0.5')
                    # 휴일 가산 (단순화: 일요일이면 휴일로 간주)
                    if r.work_date.weekday() == 6:
                        total_earnings_90 += h * hourly_rate * Decimal('0.5')
                        
    # 2. 확정 주휴수당 합산
    from .services import calculate_weekly_holiday_pay_v2
    total_holiday_pay_90 = Decimal('0')
    
    # 90일 기간에 '종료'된 주들을 찾음
    # start_90이 포함된 주의 일요일부터 end_90이 포함된 주의 일요일까지
    curr_week_start = start_90 - timedelta(days=start_90.weekday())
    while curr_week_start <= end_90:
        week_end = curr_week_start + timedelta(days=6)
        # 주의 종료일이 90일 기간 내에 있고, 오늘보다 이전(종료된 주)인 경우
        if start_90 <= week_end <= end_90:
            h_res = calculate_weekly_holiday_pay_v2(employee, curr_week_start)
            total_holiday_pay_90 += Decimal(str(h_res['amount']))
        curr_week_start += timedelta(days=7)
        
    total_wage_90 = total_earnings_90 + total_holiday_pay_90
    avg_daily_wage = total_wage_90 / Decimal('90')
    
    # Fallback 조건: 임금 데이터가 거의 없거나 0인 경우
    if total_wage_90 == 0:
        method = 'CONTRACT_ESTIMATE'
        # 평균임금(일급) = (contract_weekly_hours / 7) × hourly_wage
        avg_daily_wage = (contract_hours / Decimal('7')) * hourly_rate
        
    # --- 퇴직금 계산 ---
    # 퇴직금 = 평균임금(일급) × 30 × (재직일수 / 365)
    severance_pay = avg_daily_wage * Decimal('30') * (Decimal(str(service_days)) / Decimal('365'))
    
    # [v2.1 Refinement] 지급 비대상인 경우 금액을 무조건 0으로 반환
    final_severance_pay = int(severance_pay) if eligible else 0
    
    return {
        'eligible': eligible,
        'severance_pay': final_severance_pay,
        'avg_daily_wage': int(avg_daily_wage),
        'service_days': service_days,
        'service_months': service_months,
        'method': method,
        'reason': reason,
        'total_wage_last_90d': int(total_wage_90),
        'contract_weekly_hours': float(contract_hours),
        'hourly_rate': int(hourly_rate)
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
    
    today = timezone.localdate()
    
    # 1. 재직기간 계산
    start_date = employee.start_date
    end_date = today  # 현재 날짜 기준으로 계산
    
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
    
    # 2. 계약상 주 소정근로시간 또는 스케줄 합계 확인 (15시간 미만이면 자격 없음)
    weekly_hours = Decimal('0')
    if employee.contract_weekly_hours is not None:
        weekly_hours = Decimal(str(employee.contract_weekly_hours))
    else:
        # [Fix] 이번 달 월별 스케줄이 있으면 그것을 우선 반영 (삭제된 경우 0시간)
        # 365, today 등은 함수 상단에 있음
        month_schedules = WorkSchedule.objects.none() # dummy
        
        from .models import MonthlySchedule
        monthly_schedules = MonthlySchedule.objects.filter(
            employee=employee,
            year=today.year,
            month=today.month,
            enabled=True
        )
        
        if monthly_schedules.exists():
             # 월별 스케줄 사용
             for schedule in monthly_schedules:
                if schedule.start_time and schedule.end_time:
                    from datetime import datetime
                    dummy_date = datetime(2000, 1, 1)
                    dt_start = datetime.combine(dummy_date.date(), schedule.start_time)
                    dt_end = datetime.combine(dummy_date.date(), schedule.end_time)
                    
                    if dt_end < dt_start:
                        dt_end += timedelta(days=1)
                    
                    diff = dt_end - dt_start
                    extra_mins = float(getattr(schedule, 'next_day_work_minutes', 0))
                    total_mins = (diff.total_seconds() / 60.0) + extra_mins
                    break_mins = float(getattr(schedule, 'break_minutes', 0))
                    
                    weekly_hours += Decimal(str(max(0.0, total_mins - break_mins) / 60.0))
        else:
            # 주간 스케줄 사용 (fallback)
            schedules = WorkSchedule.objects.filter(employee=employee, enabled=True)
            for schedule in schedules:
                if schedule.start_time and schedule.end_time:
                    from datetime import datetime
                    dummy_date = datetime(2000, 1, 1)
                    dt_start = datetime.combine(dummy_date.date(), schedule.start_time)
                    dt_end = datetime.combine(dummy_date.date(), schedule.end_time)
                    
                    if dt_end < dt_start:
                        dt_end += timedelta(days=1)
                    
                    diff = dt_end - dt_start
                    extra_mins = float(getattr(schedule, 'next_day_work_minutes', 0))
                    total_mins = (diff.total_seconds() / 60.0) + extra_mins
                    break_mins = float(getattr(schedule, 'break_minutes', 0))
                    
                    weekly_hours += Decimal(str(max(0.0, total_mins - break_mins) / 60.0))
    
    if weekly_hours < 15:
        return {
            "retirement_pay": 0,
            "average_wage": 0,
            "regular_wage": 0,
            "service_days": service_days,
            "service_months": service_months,
            "eligible": False,
            "calculation_details": f"주 소정근로시간 {float(weekly_hours)}시간 (15시간 미만은 퇴직금 지급 대상 아님)"
        }

    # 3. 1년 미만 근로자는 퇴직금 0원
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
    
    # 4. 통상임금 계산 (시급 기준)
    # 통상임금 = (시급 × 주간 근로시간 × 52주) / 365일
    
    hourly_rate = Decimal(str(employee.hourly_rate))
    
    # 스케줄이 없으면 기본값 40시간 사용
    if weekly_hours == 0:
        weekly_hours = Decimal('40')
    
    annual_wage = hourly_rate * weekly_hours * Decimal('52')
    regular_daily_wage = annual_wage / Decimal('365')
    
    # 5. 평균임금 계산 (최근 3개월 실제 임금 기준)
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

def compute_payroll_summary(employee, year, month):
    """월별 급여 집계 및 요약 서비스 (v3 - 복구 및 교정)
    
    계산 로직:
    - 해당 월의 모든 날짜에 대해:
        1. 실제 근로기록(WorkRecord)이 있으면 우선 사용.
        2. 없으면 스케줄 기반 예정 시간 사용.
    - 인정 기준:
        - '오늘' 이전(오늘 포함)의 기록만 '총 인정 시간' 및 '실제 근로 시간'에 포함.
        - '오늘' 이후의 예정 기록은 '예정 근로 시간' 및 '급여 예상액'에만 합산.
    """
    from .holidays import get_holidays_for_month
    from .models import WorkRecord
    from datetime import date, datetime, timedelta
    from django.utils import timezone
    import calendar
    
    today = timezone.localdate()
    
    # 해당 월의 시작일과 종료일 계산
    start_date = date(year, month, 1)
    _, last_day = calendar.monthrange(year, month)
    end_date = date(year, month, last_day)
        
    holidays = get_holidays_for_month(year, month)
    holiday_dates = {h['date'] for h in holidays if h['type'] == 'LEGAL'}
    
    # 1. 실제 근로기록 가져오기
    work_records_queryset = employee.work_records.filter(work_date__range=[start_date, end_date])
    work_record_map = {wr.work_date: wr for wr in work_records_queryset}
    
    total_hours = 0.0
    actual_hours = 0.0
    scheduled_hours = 0.0
    base_pay = 0
    holiday_bonus = 0
    holiday_hours = 0
    night_hours = 0.0
    night_bonus = 0
    
    hourly_wage = int(employee.hourly_rate)
    breakdown = []
    notes = []  # Initialize notes early
    
    # 야간 수당 계산을 위한 헬퍼 함수 (Scheduled 용)
    def calculate_scheduled_night_hours(st, et, is_overnight, next_day_mins):
        """스케줄 기반 야간 근로 시간 계산"""
        dummy_date = date(2000, 1, 1)
        dt_start = datetime.combine(dummy_date, st)
        dt_end = datetime.combine(dummy_date, et)
        if dt_end < dt_start or is_overnight:
             dt_end += timedelta(days=1)
        
        overlap_mins = 0
        curr = dt_start
        while curr < dt_end:
            if curr.hour >= 22 or curr.hour < 6:
                overlap_mins += 1
            curr += timedelta(minutes=1)
        
        total_night_mins = overlap_mins + next_day_mins
        return total_night_mins / 60.0

    # 해당 월의 모든 날짜 순회
    curr = start_date
    while curr <= end_date:
        hours = 0.0
        day_night_hours = 0.0
        source = 'none'
        is_holiday = False
        holiday_type = None
        record = work_record_map.get(curr)
        
        # 주휴일(일요일) 또는 공휴일 체크
        if curr.weekday() == 6: # Sunday
            is_holiday = True
            holiday_type = 'WEEKLY_REST'
        elif curr.isoformat() in holiday_dates:
            is_holiday = True
            holiday_type = 'LEGAL'
            
        if record:
            # 실제 기록이 있는 경우 (출결 상태가 근로인 경우만)
            if record.attendance_status in ['REGULAR_WORK', 'EXTRA_WORK']:
                hours = float(record.get_total_hours())
                day_night_hours = float(record.get_night_hours())
                source = 'actual'
        else:
            # 실제 기록이 없는 경우 스케줄 확인
            if employee.is_scheduled_workday(curr):
                source = 'scheduled'
                schedule_info = employee.get_schedule_for_date(curr)
                if schedule_info and schedule_info['is_scheduled']:
                    # 시간 계산
                    st = schedule_info['start_time']
                    et = schedule_info['end_time']
                    br = schedule_info['break_minutes']
                    is_ov = schedule_info.get('is_overnight', False)
                    nm = schedule_info.get('next_day_work_minutes', 0)
                    
                    if st and et:
                        dummy_date = date(2000, 1, 1)
                        dt_start = datetime.combine(dummy_date, st)
                        dt_end = datetime.combine(dummy_date, et)
                        if dt_end < dt_start or is_ov:
                             dt_end += timedelta(days=1)
                        
                        diff = (dt_end - dt_start).total_seconds() / 3600.0
                        hours = max(0.0, diff - (br / 60.0))
                        
                        # 야간 시간 계산
                        day_night_hours = calculate_scheduled_night_hours(st, et, is_ov, nm)
        
        # 통계 합산 (인정 기준 적용)
        if hours > 0:
            day_pay = int(hours * hourly_wage)
            day_holiday_bonus = 0
            day_night_bonus = 0
            
            # 5인 이상 사업장인 경우 가산수당 적용
            if employee.is_workplace_over_5:
                # 휴일 가산수당 50%
                if is_holiday:
                    day_holiday_bonus = int(hours * hourly_wage * 0.5)
                # 야간 가산수당 50%
                if day_night_hours > 0:
                    day_night_bonus = int(day_night_hours * hourly_wage * 0.5)
            
            # 미래 날짜도 집계에 포함 (사용자 요청: 예정된 근무도 통계 및 예상 급여에 반영)
            # if curr <= today:  <-- 조건 제거
            total_hours += hours
            if source == 'actual':
                actual_hours += hours
            else:
                scheduled_hours += hours
            
            # 급여 및 수당도 합산
            base_pay += day_pay
            holiday_bonus += day_holiday_bonus
            night_hours += day_night_hours
            night_bonus += day_night_bonus
            if is_holiday:
                holiday_hours += hours
            
            # 내역(breakdown)에는 포함하되 미래 여부 표시
            breakdown.append({
                "date": curr.isoformat(),
                "source": source,
                "hours": round(hours, 1),
                "night_hours": round(day_night_hours, 1),
                "is_holiday": is_holiday,
                "holiday_type": holiday_type,
                "day_pay": day_pay,
                "holiday_bonus": day_holiday_bonus,
                "night_bonus": day_night_bonus,
                "is_future": curr > today
            })
            
        curr += timedelta(days=1)
        
    # 합계 계산
    
    # 주휴수당 계산 (이번 달 전체 예상)
    from .services import get_monthly_holiday_pay_info
    holiday_pay_info = get_monthly_holiday_pay_info(employee, year, month)
    monthly_weekly_holiday_pay = int(holiday_pay_info['estimated_total'])
    
    total_extra = holiday_bonus + night_bonus
    # 최종 예상 급여 = 기본급 + 추가수당(야간/휴일) + 주휴수당
    estimated_monthly_pay = base_pay + total_extra + monthly_weekly_holiday_pay
    
    # 공제 계산 (v2.1)
    import math

    gross_pay = estimated_monthly_pay
    deduction_summary = {
        'type': employee.deduction_type, # NONE, FOUR_INSURANCE, FREELANCE
        'total_deduction': 0,
        'net_pay': gross_pay,
        'details': []
    }

    if employee.deduction_type == 'FOUR_INSURANCE':
        # 국민연금 4.5%
        pension = math.floor((gross_pay * 0.045) / 10) * 10
        # 건강보험 3.545%
        health = math.floor((gross_pay * 0.03545) / 10) * 10
        # 장기요양보험 (건강보험의 12.95%)
        care = math.floor((health * 0.1295) / 10) * 10
        # 고용보험 0.9%
        employment = math.floor((gross_pay * 0.009) / 10) * 10
        
        total_deduction = pension + health + care + employment
        deduction_summary['total_deduction'] = total_deduction
        deduction_summary['net_pay'] = gross_pay - total_deduction
        deduction_summary['details'] = [
            {'label': '국민연금 (4.5%)', 'amount': pension},
            {'label': '건강보험 (3.545%)', 'amount': health},
            {'label': '장기요양 (건보의 12.95%)', 'amount': care},
            {'label': '고용보험 (0.9%)', 'amount': employment},
        ]
        notes.append("4대보험료는 예상 요율(2025년 기준)로 계산되었으며 실제와 다를 수 있습니다.")
        
    elif employee.deduction_type == 'FREELANCE':
        # 3.3%
        tax = math.floor((gross_pay * 0.033) / 10) * 10
        deduction_summary['total_deduction'] = tax
        deduction_summary['net_pay'] = gross_pay - tax
        deduction_summary['details'] = [
            {'label': '사업소득세 (3.3%)', 'amount': tax}
        ]
        notes.append("프리랜서(사업소득) 3.3% 원천징수 기준으로 계산되었습니다.")
        
    else:
        # 미선택
        notes.append("현재 공제 방식이 선택되지 않아 세전 기준 급여로 계산되었습니다.")
        notes.append("정확한 실수령액을 알고 싶다면 근로정보 수정에서 공제 방식을 선택해주세요.")

    # 사용자 요구사항에 맞춘 summary 구조 (v2)
    summary = {
        "base_pay": base_pay,
        "night_extra": night_bonus,
        "holiday_extra": holiday_bonus,
        "weekly_holiday_pay": monthly_weekly_holiday_pay, 
        "total": estimated_monthly_pay, # 세전 총액
        "total_hours": round(total_hours, 1),
        "scheduled_hours": round(scheduled_hours, 1),
        "deduction": deduction_summary # 공제 정보 추가
    }
    
    notes.extend([
        "실제 근로기록이 있으면 실제시간을, 없으면 스케줄 기반 예정시간을 사용합니다.",
        f"오늘({today.isoformat()}) 이후의 근로 예정분도 통계 및 예상 급여에 포함됩니다.",
        "예상 주휴수당이 포함된 금액입니다. (주 15시간 이상 & 개근 시 발생)"
    ])
    
    if employee.is_workplace_over_5:
        notes.append("본 급여는 근로기준법(5인 이상 사업장)에 따라 야간근로 및 휴일근로 가산수당이 반영되었습니다.")
    else:
        notes.append("본 사업장은 5인 미만 사업장으로 야간·휴일 근로에 대한 가산수당이 적용되지 않습니다. (근로기준법 제11조)")
    
    notes.append("모든 공제 계산은 '예상 계산'이며 실제 급여 및 공제는 사업장/세무 처리 기준에 따라 달라질 수 있습니다.")

    return {
        "month": f"{year}-{month:02d}",
        "hourly_wage": hourly_wage,
        "workplace_size": "GE_5" if employee.is_workplace_over_5 else "LT_5",
        "contract_weekly_hours": float(employee.contract_weekly_hours) if employee.contract_weekly_hours else None,
        "total_hours": round(total_hours, 1),
        "actual_hours": round(actual_hours, 1),
        "scheduled_hours": round(scheduled_hours, 1),
        "holiday_hours": round(holiday_hours, 1),
        "night_hours": round(night_hours, 1),
        "base_pay": base_pay,
        "holiday_bonus": holiday_bonus,
        "night_bonus": night_bonus,
        "monthly_weekly_holiday_pay": monthly_weekly_holiday_pay, 
        "estimated_monthly_pay": estimated_monthly_pay, # 세전
        "net_pay": deduction_summary['net_pay'], # 세후 (최상위에도 노출)
        "summary": summary,
        "rows": breakdown, 
        "notes": notes
    }
