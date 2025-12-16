# 미래 날짜 스케줄 자동 반영 차단

## 개요

스케줄(예정)을 저장할 때 미래 날짜에 대해서만 자동 반영을 차단하여, 아직 발생하지 않은 근로시간이 통계에 포함되지 않도록 합니다.

**중요**: 과거 및 현재의 WorkRecord는 절대 삭제/수정하지 않으며, 오직 미래 날짜의 스케줄 반영만 차단합니다.

## 문제 상황

### 원래 동작 (변경 전)
```
주간 스케줄 저장 (월~금 09:00-18:00)
↓
미래 6개월까지 캘린더에 주황색 표시 (스케줄 기반)
↓
미래 6개월까지 통계 합산 (스케줄 기반)
↓
급여 예상액이 실제보다 훨씬 크게 표시됨
```

## 해결 방법

### 핵심 원칙

```
과거/현재(오늘 포함):
  - WorkRecord: 그대로 유지 ✓
  - Schedule: 오늘까지만 반영 ✓

미래(오늘 이후):
  - WorkRecord: 자동 생성 안 됨 ✓ (원래부터 없었음)
  - Schedule: 캘린더/통계에 반영 안 됨 ✓ (새로 차단)
```

### 1. 캘린더 표시 (monthly_scheduled_dates)

#### 수정 내용
```python
def monthly_scheduled_dates(employee, year, month):
    """
    우선순위:
    1. 실제 WorkRecord (가장 높음) - 과거/현재만
    2. MonthlySchedule - 오늘 이전만
    3. WorkSchedule - 오늘 이전만
    
    중요: 미래 날짜는 스케줄이 있어도 표시하지 않음
    """
    today = timezone.now().date()
    
    # 실제 근무 기록 조회 (모든 날짜)
    work_records = WorkRecord.objects.filter(...)
    worked_records_map = {wr.work_date: wr for wr in work_records}
    
    # 스케줄 조회
    schedule_map = ...  # MonthlySchedule 또는 WorkSchedule
    
    for dt in month_dates:
        is_scheduled = False
        
        # 1. 실제 기록 우선 (과거/현재/미래 모두)
        if dt in worked_records_map:
            if record.get_total_hours() > 0:
                is_scheduled = True
        # 2. 스케줄 (오늘 이전만)
        elif dt <= today and dt.weekday() in schedule_map:
            is_scheduled = True  # ← 오늘 이전만!
```

**효과**:
- ✅ 과거 WorkRecord: 그대로 주황색 표시
- ✅ 현재 WorkRecord: 그대로 주황색 표시
- ✅ 과거 스케줄: 주황색 표시 (WorkRecord 없는 경우)
- ❌ 미래 스케줄: 표시 안 됨

### 2. 월별 통계 계산 (compute_monthly_schedule_stats)

#### 수정 내용
```python
def compute_monthly_schedule_stats(employee, year, month):
    """
    우선순위:
    1. 실제 WorkRecord (가장 높음)
    2. MonthlySchedule - 오늘 이전만
    3. WorkSchedule - 오늘 이전만
    
    중요: 미래 날짜의 스케줄은 통계에 포함하지 않음
    """
    today = timezone.now().date()
    
    # 실제 근무 기록 (모든 날짜)
    work_records = WorkRecord.objects.filter(...)
    actual_hours_worked = sum(...)  # 과거/현재/미래 모두
    
    # 스케줄 기반 예상 시간 (오늘 이전만)
    current_date = start_of_month
    while current_date <= end_of_month and current_date <= today:  # ← 오늘까지만!
        if current_date not in worked_dates and current_date.weekday() in schedule_map:
            total_scheduled_hours += ...
        current_date += timedelta(days=1)
    
    # 총 시간 = 실제 + 스케줄 (오늘까지만)
    total_hours = actual_hours_worked + total_scheduled_hours
```

**효과**:
- ✅ 과거 WorkRecord: 통계에 포함
- ✅ 현재 WorkRecord: 통계에 포함
- ✅ 과거 스케줄: 통계에 포함 (WorkRecord 없는 경우)
- ❌ 미래 스케줄: 통계에서 제외

### 3. 이번 주 통계 (주휴수당 계산용)

#### 수정 내용
```python
# 이번 주 실제 근로기록 (오늘까지만)
actual_this_week_records = WorkRecord.objects.filter(
    work_date__gte=start_of_week,
    work_date__lte=min(end_of_week, today)  # ← 오늘까지만!
)

# 이번 주 스케줄 예상 시간 (오늘까지만)
while current_day <= min(end_of_week, today):  # ← 오늘까지만!
    if current_day not in actual_work_dates and current_day.weekday() in schedule_map:
        scheduled_this_week_hours += ...
```

## 데이터 보존 확인

### WorkRecord 삭제/수정 여부
```bash
# 시스템 전체 검색 결과:
grep -r "WorkRecord.objects.delete" labor/
grep -r "WorkRecord.objects.filter.*delete" labor/
grep -r "work_records.delete" labor/

# 결과: 0건
```

**확인**: 스케줄 저장 시 WorkRecord를 삭제/수정하는 로직이 **없습니다**. ✓

### WorkRecord 자동 생성 여부
```bash
# 시스템 전체 검색 결과:
grep -r "WorkRecord.objects.create" labor/
grep -r "WorkRecord.objects.bulk_create" labor/

# 결과: 0건
```

**확인**: 스케줄 저장 시 WorkRecord를 자동 생성하는 로직이 **없습니다**. ✓

## 사용자 시나리오

### 시나리오 1: 과거 기록 보존
```
상황: 2024년 11월에 이미 근로기록 입력 완료

1. 사용자가 2025년 12월에 주간 스케줄 변경
   
2. 2024년 11월 캘린더 확인
   ✓ 기존 주황색 그대로 유지
   ✓ 기존 시간 데이터 그대로 유지
   
3. 2024년 11월 통계 확인
   ✓ 기존 통계 그대로 유지
```

### 시나리오 2: 현재 월 동작
```
상황: 2025년 12월 (현재 월)

1. 사용자가 주간 스케줄 설정 (월~금 09:00-18:00)
   
2. 캘린더 확인
   - 12월 1일~15일 (과거): 스케줄 기반 주황색 표시 ✓
   - 12월 16일 (오늘): 스케줄 기반 주황색 표시 ✓
   - 12월 17일~31일 (미래): 회색 (표시 안 됨) ✓
   
3. 통계 확인
   - 총 근로시간: 12월 1일~16일 스케줄 합산 ✓
   - 미래 날짜는 제외 ✓
```

### 시나리오 3: 미래 월 동작
```
상황: 2026년 3월 (미래 월)

1. 사용자가 주간 스케줄 설정했어도
   
2. 캘린더 확인
   - 모든 날짜: 회색 ✓
   - 클릭 불가 ✓
   
3. 통계 확인
   - 모든 값: 0 ✓
```

### 시나리오 4: 실제 기록 추가
```
상황: 과거/현재/미래 어느 때든

1. 사용자가 캘린더에서 날짜 클릭 → 시간 입력 → 저장
   
2. 해당 날짜
   - WorkRecord 생성 ✓
   - 주황색 표시 ✓
   - 통계 반영 ✓
   
3. 스케줄보다 WorkRecord가 우선함 ✓
```

## 기술적 세부사항

### 날짜 비교 로직

```python
today = timezone.now().date()

# 과거/현재 판별
if dt <= today:
    # 스케줄 반영 가능
    
# 미래 판별  
if dt > today:
    # 스케줄 반영 불가
```

### 루프 제한

```python
# 변경 전
while current_date <= end_of_month:
    # 미래까지 계산됨 ✗
    
# 변경 후
while current_date <= end_of_month and current_date <= today:
    # 오늘까지만 계산 ✓
```

## 영향 범위

### 변경된 파일
- `labor/services.py`
  - `monthly_scheduled_dates()`: `dt <= today` 조건 추가
  - `compute_monthly_schedule_stats()`: `current_date <= today` 조건 추가

### 변경되지 않은 부분
- ✅ WorkRecord 모델
- ✅ WorkSchedule 모델  
- ✅ MonthlySchedule 모델
- ✅ API 엔드포인트
- ✅ 프론트엔드 코드
- ✅ WorkRecord 생성/수정/삭제 로직

## 테스트 방법

### 1. 과거 기록 보존 확인
```
1. 과거 월에 WorkRecord 입력
2. 주간 스케줄 변경
3. 과거 월 캘린더 확인
   ✓ 주황색 그대로 유지
4. 과거 월 통계 확인
   ✓ 값 그대로 유지
```

### 2. 현재 월 동작 확인
```
1. 주간 스케줄 설정
2. 현재 월 캘린더 확인
   ✓ 오늘까지: 주황색 (스케줄 기반)
   ✓ 내일부터: 회색
3. 현재 월 통계 확인
   ✓ 오늘까지만 합산
```

### 3. 미래 월 차단 확인
```
1. 캘린더를 미래 월로 이동
2. 모든 날짜가 회색인지 확인
3. 통계가 0인지 확인
```

## 관련 문서

- `FUTURE_DATE_PREVENTION_FEATURE.md`: 미래 날짜 입력 차단
- `CUMULATIVE_STATS_FIX.md`: 누적 통계 정확한 계산
- `CALENDAR_STATS_SYNC_FEATURE.md`: 캘린더-통계 동기화
- `MONTHLY_SCHEDULE_FEATURE.md`: 월별 스케줄 기능

이 수정으로 **과거 데이터는 완전히 보존**되며, **미래 날짜의 스케줄 반영만 차단**됩니다.

## 문제 상황

### 심각한 버그 발견
사용자가 **주간 근무 스케줄**을 저장하면:
1. 미래 달(예: 2026년 1~6월)까지 캘린더에 주황색 표시가 생김
2. 아직 발생하지 않은 미래 달의 통계(총 근로시간/급여/근로일수)가 계산됨
3. 실제로 근로하지 않은 시간이 누적되어 비정상적으로 큰 값이 표시됨

### 근본 원인
**스케줄(예정)**과 **실제 근로기록(WorkRecord)**을 혼동하는 로직:
- `monthly_scheduled_dates()`: 스케줄이 있으면 `is_scheduled: true` 반환
- `compute_monthly_schedule_stats()`: 스케줄 기반으로 미래 시간까지 합산
- 결과: 스케줄만 저장해도 "실제 근로한 것처럼" 캘린더 표시 및 통계 반영

### 예시
```
현재: 2025년 12월
사용자가 주간 스케줄 설정: 월~금 09:00-18:00

변경 전 (버그):
✗ 2026년 1월~6월 캘린더: 모든 월~금이 주황색
✗ 2026년 1월 통계: 총 176시간 (실제 근로 0시간인데!)
✗ 누적 통계: 미래 6개월치 포함되어 1000시간 이상

변경 후 (수정):
✓ 2026년 1월~6월 캘린더: 모두 회색 (기록 없음)
✓ 2026년 1월 통계: 0시간 (정확함)
✓ 누적 통계: 오늘까지만 포함되어 정확함
```

## 해결 방법

### 핵심 원칙

```
스케줄(Schedule) = 예정/계획 → 캘린더 표시 ✗, 통계 계산 ✗
실제 근로기록(WorkRecord) = 확정 → 캘린더 표시 ✓, 통계 계산 ✓
```

### 1. 캘린더 주황색 표시 (monthly_scheduled_dates)

#### 변경 전 (버그)
```python
def monthly_scheduled_dates(employee, year, month):
    # 스케줄 조회
    monthly_schedules = MonthlySchedule.objects.filter(...)
    default_schedules = WorkSchedule.objects.filter(...)
    
    # 문제: 스케줄이 있으면 is_scheduled = True
    if dt.weekday() in schedule_map:
        is_scheduled = True  # ← 버그!
```

#### 변경 후 (수정)
```python
def monthly_scheduled_dates(employee, year, month):
    """
    오직 실제 WorkRecord만 주황색으로 표시
    스케줄은 캘린더 표시에서 완전히 제외
    """
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # 실제 근무 기록만 가져오기
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )
    worked_records_map = {wr.work_date: wr for wr in work_records}
    
    for dt in month_dates:
        is_scheduled = False
        
        # 오직 실제 근로기록만 표시
        # 미래 날짜는 무조건 false
        if dt <= today and dt in worked_records_map:
            record = worked_records_map[dt]
            if record.get_total_hours() > 0:
                is_scheduled = True
```

### 2. 월별 통계 계산 (compute_monthly_schedule_stats)

#### 변경 전 (버그)
```python
def compute_monthly_schedule_stats(employee, year, month):
    # 실제 근로기록 시간
    actual_hours_worked = sum(...)
    
    # 문제: 스케줄 기반 예상 시간까지 합산
    total_scheduled_hours = 0
    for date in month_dates:
        if date.weekday() in schedule_map:
            total_scheduled_hours += schedule_hours  # ← 버그!
    
    # 문제: 실제 + 스케줄을 합산
    total_hours = actual_hours_worked + total_scheduled_hours  # ← 버그!
```

#### 변경 후 (수정)
```python
def compute_monthly_schedule_stats(employee, year, month):
    """
    오직 실제 WorkRecord만 통계에 반영
    스케줄은 통계 계산에서 완전히 제외
    """
    from django.utils import timezone
    
    today = timezone.now().date()
    start_of_month = date(year, month, 1)
    
    # 미래 월인 경우 모든 통계를 0으로 반환
    if start_of_month > today:
        return {
            'scheduled_total_hours': 0.0,
            'scheduled_estimated_salary': 0.0,
            'scheduled_work_days': 0,
            'scheduled_this_week_hours': 0.0,
        }
    
    # 실제 근무 기록만 가져오기 (오늘까지만)
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month,
        work_date__lte=today  # 오늘까지만
    )
    
    # 실제 근무 기록만 합산
    total_hours = sum(float(wr.get_total_hours()) for wr in work_records)
    total_work_days = sum(1 for wr in work_records if wr.get_total_hours() > 0)
    total_salary = total_hours * hourly_rate
    
    return {
        'scheduled_total_hours': total_hours,  # 실제 시간만
        'scheduled_estimated_salary': total_salary,  # 실제 급여만
        'scheduled_work_days': total_work_days,  # 실제 일수만
    }
```

### 3. 이번 주 통계 (주휴수당 계산용)

#### 변경 전 (버그)
```python
# 실제 근로기록 시간
actual_this_week_hours = sum(...)

# 문제: 스케줄 예상 시간까지 합산
scheduled_this_week_hours = 0
for day in week_dates:
    if day.weekday() in schedule_map:
        scheduled_this_week_hours += schedule_hours  # ← 버그!

# 문제: 실제 + 스케줄을 합산
total_this_week_hours = actual_this_week_hours + scheduled_this_week_hours  # ← 버그!
```

#### 변경 후 (수정)
```python
# 이번 주 실제 근로기록만 조회
actual_this_week_records = WorkRecord.objects.filter(
    employee=employee,
    work_date__gte=start_of_week, 
    work_date__lte=end_of_week
)

# 실제 근로시간만 합산
actual_this_week_hours = sum(wr.get_total_hours() for wr in actual_this_week_records)

return {
    'scheduled_this_week_hours': float(actual_this_week_hours),  # 실제만
}
```

## 데이터 흐름 비교

### 변경 전 (버그)
```
주간 스케줄 저장
    ↓
WorkSchedule 또는 MonthlySchedule 테이블에 저장
    ↓
monthly_scheduled_dates() 호출
    ↓
스케줄이 있는 모든 날짜를 is_scheduled: true로 반환
    ↓
캘린더: 미래 달까지 주황색 표시 ✗
    ↓
compute_monthly_schedule_stats() 호출
    ↓
실제 근로시간 + 스케줄 예상시간 합산
    ↓
통계: 미래 달까지 시간/급여 계산 ✗
```

### 변경 후 (수정)
```
주간 스케줄 저장
    ↓
WorkSchedule 또는 MonthlySchedule 테이블에 저장
(여기까지는 동일, 예정으로만 저장됨)
    ↓
monthly_scheduled_dates() 호출
    ↓
오직 WorkRecord만 조회
    ↓
캘린더: 실제 기록이 있는 날만 주황색 ✓
(미래 날짜는 회색)
    ↓
compute_monthly_schedule_stats() 호출
    ↓
오직 WorkRecord만 합산
    ↓
통계: 실제 근로시간/급여만 계산 ✓
(미래 월은 0)
```

## 스케줄의 역할

스케줄은 **참고용 예정**으로만 사용됩니다:

### WorkSchedule (주간 스케줄)
- 사용자가 근로정보 수정에서 설정
- 용도: 캘린더에서 근로기록 입력 시 기본값으로 사용
- **영향**: 캘린더 표시 ✗, 통계 계산 ✗

### MonthlySchedule (월별 스케줄)
- 사용자가 캘린더에서 "월별 스케줄 변경"으로 설정
- 용도: 특정 월만 다른 패턴일 때 기본값 변경
- **영향**: 캘린더 표시 ✗, 통계 계산 ✗

### WorkRecord (실제 근로기록)
- 사용자가 캘린더에서 날짜 클릭 → 시간 입력 → 저장
- 용도: **실제 근로한 시간 확정**
- **영향**: 캘린더 표시 ✓, 통계 계산 ✓

## 사용자 시나리오

### 시나리오 1: 스케줄만 설정
```
1. 사용자가 근로정보 수정에서 주간 스케줄 설정
   월~금: 09:00-18:00
   
2. 캘린더 확인
   - 과거 날짜: 회색 (기록 안 한 날)
   - 오늘: 회색 (아직 기록 안 함)
   - 미래: 회색 (기록할 수 없음)
   
3. 통계 확인
   - 총 근로시간: 0시간 ✓
   - 급여: 0원 ✓
   - 근로일수: 0일 ✓
```

### 시나리오 2: 스케줄 설정 + 실제 근로
```
1. 사용자가 주간 스케줄 설정
   월~금: 09:00-18:00
   
2. 12월 2일(월) 날짜 클릭 → 09:00-18:00 입력 → 저장
   
3. 캘린더 확인
   - 12월 2일: 주황색 ✓ (실제 기록)
   - 12월 3일: 회색 (아직 기록 안 함)
   - 12월 4일: 회색 (아직 기록 안 함)
   
4. 통계 확인
   - 총 근로시간: 8시간 ✓ (12월 2일만)
   - 급여: 96,000원 ✓ (시급 12,000원 × 8시간)
   - 근로일수: 1일 ✓
```

### 시나리오 3: 과거 월 기록
```
1. 사용자가 캘린더를 2024년 11월로 이동
   
2. 11월 1일~30일 중 실제 근로한 날만 클릭해서 기록
   
3. 캘린더 확인
   - 기록한 날: 주황색 ✓
   - 기록 안 한 날: 회색
   
4. 통계 확인 (2024년 11월)
   - 총 근로시간: 실제 기록한 시간만 합산 ✓
   - 급여: 실제 근로시간 × 시급 ✓
```

### 시나리오 4: 미래 월 조회
```
1. 사용자가 캘린더를 2026년 3월로 이동 (미래 월)
   
2. 캘린더 확인
   - 모든 날짜: 회색 + 클릭 불가 ✓
   - 알림: "미래 날짜에는 근로 기록을 입력할 수 없습니다"
   
3. 통계 확인 (2026년 3월)
   - 총 근로시간: 0시간 ✓
   - 급여: 0원 ✓
   - 근로일수: 0일 ✓
```

## 기술적 세부사항

### 데이터베이스 구조

```
WorkSchedule (주간 스케줄)
├─ employee_id
├─ weekday (0-6)
├─ start_time
├─ end_time
└─ enabled

MonthlySchedule (월별 스케줄)
├─ employee_id
├─ year
├─ month
├─ weekday (0-6)
├─ start_time
├─ end_time
└─ enabled

WorkRecord (실제 근로기록) ← 통계 계산에 사용
├─ employee_id
├─ work_date        ← 이 날짜가 <= today 인 것만
├─ start_time
├─ end_time
└─ notes
```

### 우선순위 시스템

#### 캘린더 표시
```python
# 오직 WorkRecord만 확인
if dt <= today and dt in worked_records_map:
    if record.get_total_hours() > 0:
        is_scheduled = True  # 주황색
```

#### 통계 계산
```python
# 오직 WorkRecord만 합산
work_records = WorkRecord.objects.filter(
    employee=employee,
    work_date__year=year,
    work_date__month=month,
    work_date__lte=today  # 오늘까지만
)

total_hours = sum(float(wr.get_total_hours()) for wr in work_records)
```

#### 근로기록 입력 시 기본값
```python
# 스케줄은 여기서만 사용 (기본값 제공)
# 1순위: MonthlySchedule
# 2순위: WorkSchedule
# 3순위: 빈 값

def date_schedule(request, pk=None):
    """특정 날짜의 기본 스케줄 정보 반환 (모달 기본값용)"""
    # MonthlySchedule 확인
    monthly_schedule = MonthlySchedule.objects.filter(
        employee=job,
        year=target_date.year,
        month=target_date.month,
        weekday=weekday,
        enabled=True
    ).first()
    
    if monthly_schedule:
        return {
            'start_time': monthly_schedule.start_time,
            'end_time': monthly_schedule.end_time,
        }
    
    # WorkSchedule 확인
    work_schedule = WorkSchedule.objects.filter(
        employee=job,
        weekday=weekday,
        enabled=True
    ).first()
    
    if work_schedule:
        return {
            'start_time': work_schedule.start_time,
            'end_time': work_schedule.end_time,
        }
    
    return {'start_time': None, 'end_time': None}
```

## 영향 범위

### 변경된 파일
- `labor/services.py`
  - `monthly_scheduled_dates()`: 스케줄 조회 로직 완전 제거
  - `compute_monthly_schedule_stats()`: 스케줄 합산 로직 완전 제거

### 변경되지 않은 파일
- `labor/views.py`: API 엔드포인트는 그대로 유지
- `labor/models.py`: 모델 구조는 변경 없음
- `frontend/`: 프론트엔드 코드는 변경 없음 (API 응답 구조 동일)

## 테스트 방법

### 1. 스케줄만 설정 테스트
```
1. 근로정보 수정에서 주간 스케줄 설정 (월~금 09:00-18:00)
2. 근로관리 페이지에서 캘린더 확인
   ✓ 모든 날짜가 회색인지 확인
3. 통계 카드 확인
   ✓ 총 근로시간: 0시간
   ✓ 급여: 0원
   ✓ 근로일수: 0일
```

### 2. 실제 근로기록 추가 테스트
```
1. 캘린더에서 오늘 날짜 클릭
2. 09:00-18:00 입력 후 저장
3. 캘린더 확인
   ✓ 오늘 날짜만 주황색
   ✓ 다른 날짜는 회색
4. 통계 확인
   ✓ 총 근로시간: 8시간 (오늘 것만)
   ✓ 급여: 시급 × 8시간
   ✓ 근로일수: 1일
```

### 3. 미래 월 테스트
```
1. 캘린더를 2026년 3월로 이동
2. 캘린더 확인
   ✓ 모든 날짜가 회색
   ✓ 날짜 클릭 시 "미래 날짜에는 근로 기록을 입력할 수 없습니다" alert
3. 통계 확인
   ✓ 모든 값이 0
```

### 4. 누적 통계 테스트
```
1. 여러 날짜에 근로기록 입력
2. 업적 카드 확인
   ✓ 누적 근로시간: 입력한 기록들의 합
   ✓ 누적 급여: 실제 근로시간 × 시급
   ✓ 총 근로일수: 기록 입력한 일수
```

## 이전 동작과의 비교

| 항목 | 변경 전 (버그) | 변경 후 (수정) |
|------|--------------|--------------|
| 스케줄 저장 시 캘린더 표시 | 미래까지 주황색 ✗ | 기록한 날만 주황색 ✓ |
| 스케줄 저장 시 통계 반영 | 미래까지 합산 ✗ | 기록한 것만 합산 ✓ |
| 미래 월 통계 | 스케줄 기반 계산 ✗ | 0 (기록 없음) ✓ |
| 실제 근로기록 생성 | 자동 생성 안 됨 ✓ | 자동 생성 안 됨 ✓ |
| 스케줄의 역할 | 캘린더/통계 반영 ✗ | 기본값만 제공 ✓ |

## 관련 문서

- `FUTURE_DATE_PREVENTION_FEATURE.md`: 미래 날짜 입력 차단
- `CUMULATIVE_STATS_FIX.md`: 누적 통계 정확한 계산
- `CALENDAR_STATS_SYNC_FEATURE.md`: 캘린더-통계 동기화
- `MONTHLY_SCHEDULE_FEATURE.md`: 월별 스케줄 기능

이 수정으로 시스템이 **스케줄(예정)**과 **실제 근로기록(확정)**을 명확히 구분하게 되었습니다.
