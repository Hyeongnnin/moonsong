# 소정근로일 중심 구조 개편 (Phase 1)

## 📋 개요

기존 시스템은 주간/월별/일별 근로기록이 모두 "근로시간을 캘린더에 기록하는" 동일한 역할로 동작하여, 소정근로일과 추가근무를 구분할 수 없었습니다. 이로 인해 주휴수당·연차유급휴가 계산이 법적으로 불안정한 상태였습니다.

이번 개편에서는 **소정근로일 개념을 도입**하되, 사용자가 복잡한 체크나 법 개념을 직접 입력하지 않도록 하고, 스타벅스처럼 주/월 단위로 근무일이 유동적인 형태도 자연스럽게 지원합니다.

## 🎯 핵심 원칙

### 1. 소정근로일은 시스템이 자동 판정
- ❌ 사용자가 체크박스로 "소정근로일입니다" 선택하지 않음
- ✅ 사전에 확정된 스케줄(주간/월별)로부터 시스템이 자동 판정

### 2. 근로의 성격만 최소한으로 구분
- 기존 근로시간 입력 방식(주간/월별/일별) 유지
- 출결 상태만 확장: 근무(소정근로), 추가근무, 연차사용, 결근, 병가

### 3. 스케줄 우선순위
1. **월별 스케줄 변경** (최우선) - 해당 월의 '확정된 근무표'
2. **주간근무스케줄** (기본) - 기본 근무 패턴(템플릿, 선택사항)

## 📐 개념 정의

### 소정근로일 (Scheduled Workday)
해당 날짜가 다음 조건을 만족하는 경우:
1. 월별 스케줄에서 활성화되어 있거나
2. (월별 스케줄이 없을 경우) 주간근무스케줄에서 '일하는 날'로 설정된 경우

**※ 중요: 실제 출근 여부와 무관하며, 근무표 기준으로만 결정됩니다.**

### 출결 상태 (Attendance Status)
```python
ATTENDANCE_STATUS_CHOICES = [
    ('REGULAR_WORK', '근무(소정근로)'),    # 소정근로일에 정상 출근
    ('EXTRA_WORK', '추가근무'),            # 대타, 보충근무 등 비소정근로일 근무
    ('ANNUAL_LEAVE', '연차사용'),          # 유급휴가
    ('ABSENT', '결근'),                    # 무단 결근
    ('SICK_LEAVE', '병가'),                # 병가
]
```

## 🏗️ 구현 내용

### 1. 데이터베이스 변경

#### WorkRecord 모델에 필드 추가
```python
# labor/models.py

class WorkRecord(models.Model):
    # ... 기존 필드 ...
    
    # 소정근로일 중심 구조: 출결 상태 확장
    ATTENDANCE_STATUS_CHOICES = [
        ('REGULAR_WORK', '근무(소정근로)'),
        ('EXTRA_WORK', '추가근무'),
        ('ANNUAL_LEAVE', '연차사용'),
        ('ABSENT', '결근'),
        ('SICK_LEAVE', '병가'),
    ]
    attendance_status = models.CharField(
        max_length=20, 
        choices=ATTENDANCE_STATUS_CHOICES, 
        default='REGULAR_WORK',
        help_text="출결 상태 (소정근로/추가근무/연차/결근/병가)"
    )
    
    # 기존 attendance_type은 하위 호환성을 위해 유지 (deprecated)
```

#### 마이그레이션
```bash
python3 manage.py makemigrations labor --name add_attendance_status_field
python3 manage.py migrate labor
```

### 2. Employee 모델에 헬퍼 메소드 추가

#### is_scheduled_workday(target_date)
특정 날짜가 소정근로일인지 판정합니다.

```python
# labor/models.py

def is_scheduled_workday(self, target_date):
    """특정 날짜가 소정근로일인지 판정
    
    판정 기준 (우선순위 순):
    1. 해당 월의 MonthlySchedule이 있으면 그것 기준
    2. 없으면 WorkSchedule(주간 스케줄) 기준
    
    Returns:
        bool: 소정근로일 여부
    """
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
        return monthly_schedule.start_time is not None and monthly_schedule.end_time is not None
    
    # 2. 주간 스케줄 확인
    weekly_schedule = WorkSchedule.objects.filter(
        employee=self,
        weekday=weekday,
        enabled=True
    ).first()
    
    if weekly_schedule:
        return weekly_schedule.start_time is not None and weekly_schedule.end_time is not None
    
    return False
```

#### get_schedule_for_date(target_date)
특정 날짜의 스케줄 정보(시간 포함)를 반환합니다.

```python
def get_schedule_for_date(self, target_date):
    """특정 날짜의 스케줄 정보 반환 (시간 포함)
    
    Returns:
        dict: {
            'is_scheduled': bool,
            'start_time': time,
            'end_time': time,
            'break_minutes': int,
            'is_overnight': bool,
            'next_day_work_minutes': int
        }
    """
    # 1. 월별 스케줄 우선
    # 2. 주간 스케줄
    # 3. 스케줄 없음
```

### 3. API 변경

#### WorkRecordSerializer에 소정근로일 정보 추가

```python
# labor/serializers.py

class WorkRecordSerializer(serializers.ModelSerializer):
    total_hours = serializers.SerializerMethodField()
    is_scheduled_workday = serializers.SerializerMethodField()  # 추가
    schedule_info = serializers.SerializerMethodField()          # 추가

    class Meta:
        model = WorkRecord
        fields = [
            'id', 'employee', 'work_date', 'time_in', 'time_out', 
            'is_overnight', 'next_day_work_minutes', 'break_minutes',
            'day_type', 'attendance_type', 'attendance_status',  # attendance_status 추가
            'total_hours', 'is_overtime', 'is_night', 'is_holiday',
            'is_scheduled_workday', 'schedule_info'  # 추가
        ]

    def get_is_scheduled_workday(self, obj):
        """해당 날짜가 소정근로일인지 여부"""
        return obj.employee.is_scheduled_workday(obj.work_date)
    
    def get_schedule_info(self, obj):
        """해당 날짜의 스케줄 정보 (기본값 참조용)"""
        return obj.employee.get_schedule_for_date(obj.work_date)
```

#### date-schedule 엔드포인트 개선

**기존:**
```python
GET /api/labor/jobs/<id>/date-schedule/?date=YYYY-MM-DD
응답: {
    'has_schedule': true/false,
    'start_time': "13:00",
    'end_time': "19:00",
    'work_record': {...}
}
```

**개선 후:**
```python
GET /api/labor/jobs/<id>/date-schedule/?date=YYYY-MM-DD
응답: {
    'is_scheduled_workday': true,              # 소정근로일 여부 (추가)
    'has_schedule': true,
    'start_time': "13:00",
    'end_time': "19:00",
    'break_minutes': 60,
    'is_overnight': false,
    'next_day_work_minutes': 0,
    'work_record': {...},
    'suggested_attendance_status': "REGULAR_WORK"  # 기본값 제안 (추가)
}
```

#### WorkRecord 생성 시 자동 설정

```python
# labor/views.py - WorkRecordViewSet.perform_create()

# attendance_status가 없으면 소정근로일 여부에 따라 자동 설정
if 'attendance_status' not in self.request.data:
    is_scheduled = employee.is_scheduled_workday(work_date)
    default_status = 'REGULAR_WORK' if is_scheduled else 'EXTRA_WORK'
    serializer.validated_data['attendance_status'] = default_status
```

## 🎨 프론트엔드 요구사항

### 1. 캘린더 날짜 클릭 시 두 가지 수정 경로 제공

#### (1) 근무표 수정하기 (예정 변경)
- **의미**: 소정근로일 / 소정근로시간 변경
- **영향**: 
  - 월별 스케줄(근무표) 데이터 수정
  - 주휴수당·연차유급휴가 판단 기준에 직접 영향
- **수정 항목**:
  - 해당 날짜의 출근/퇴근 시간
  - 근무 여부 자체 (활성/비활성)

#### (2) 실제 근로 수정하기 (결과 기록)
- **의미**: 근무표는 유지한 채, 실제 근로 결과만 수정
- **포함 항목**:
  - **A) 근로 상태 (출결 상태)**:
    - 근무(소정근로)
    - 추가근무(대타/보충근무)
    - 연차사용
    - 결근
    - 병가
  - **B) 실제 근로시간**:
    - 실제 출근 시간
    - 실제 퇴근 시간
    - 휴게시간(분)
    - 익일 근무시간 (24:00~06:00)
- **기본값**: 근무표의 시간으로 자동 세팅
- **계산**: 연장/야간/추가근무 판단은 실제 근로시간 기준

### 2. 소정근로일 안내 문구

❌ **하지 말 것:**
```html
<input type="checkbox" v-model="isScheduledWorkday"> 소정근로일입니다
```

✅ **해야 할 것:**
```html
<div v-if="scheduleInfo.is_scheduled_workday" class="text-sm text-blue-600">
  ℹ️ 이 날짜는 소정근로일입니다 (근무표에 등록된 날)
</div>
<div v-else class="text-sm text-gray-500">
  ℹ️ 이 날짜는 소정근로일이 아닙니다 (추가근무로 기록됩니다)
</div>
```

### 3. 출결 유형 선택 기본값

```javascript
// 소정근로일 → 근무(소정근로)
// 비소정근로일 → 추가근무
const defaultAttendanceStatus = computed(() => {
  return scheduleInfo.value.is_scheduled_workday ? 'REGULAR_WORK' : 'EXTRA_WORK'
})
```

### 4. 캘린더 UI 시각적 표현

| 상태 | 시각적 표현 | 설명 |
|------|------------|------|
| 소정근로일 + 실제 출근 | 주황색 채움 | 기존과 동일 |
| 소정근로일이지만 미출근 (결근/병가/연차) | 주황색 테두리만 | 날짜 숫자 하단에 상태 텍스트 표시 |
| 비소정근로일인데 실제 근로 (추가근무/대타) | 별도 색상 (예: 연한 녹색) | 기존 주황색과 구분 |
| 소정근로일도 아니고 근로도 없음 | 기본 스타일 | 회색 또는 흰색 |

**예시 구현:**
```vue
<div 
  :class="{
    'bg-orange-400': record && isWorked(record),
    'border-2 border-orange-400': !record && isScheduledWorkday,
    'bg-green-200': record && !isScheduledWorkday && isWorked(record),
    'bg-white': !record && !isScheduledWorkday
  }"
>
  <span class="text-lg">{{ day }}</span>
  <div v-if="!record && isScheduledWorkday" class="text-xs text-gray-500">
    {{ getStatusText(record) }}
  </div>
</div>
```

## 🧮 백엔드 계산 로직 분리 원칙

### 1. 소정근로일 여부
**기준**: 근무표 (WorkSchedule / MonthlySchedule)
```python
is_scheduled = employee.is_scheduled_workday(target_date)
```

### 2. 개근/출근율 판단
**기준**: 실제 근로 상태 (WorkRecord.attendance_status)

```python
# 출근 인정: REGULAR_WORK + ANNUAL_LEAVE만
def is_attendance(work_record):
    return work_record.attendance_status in ['REGULAR_WORK', 'ANNUAL_LEAVE']

# 개근 판단
perfect_attendance = all(
    is_attendance(record) 
    for date in scheduled_dates 
    if (record := get_work_record(date))
)
```

**중요**: 
- ✅ `REGULAR_WORK` (근무) → 출근 인정
- ✅ `ANNUAL_LEAVE` (연차사용) → 출근 인정
- ❌ `EXTRA_WORK` (추가근무) → 개근 판단에서 제외
- ❌ `ABSENT` (결근) → 개근 판단에서 제외
- ❌ `SICK_LEAVE` (병가) → 개근 판단에서 제외

### 3. 근로시간 합산 / 급여 / 통계
**기준**: 실제 근로시간 (WorkRecord.get_total_hours())

```python
# 모든 근로 유형 합산 (REGULAR_WORK + EXTRA_WORK)
total_hours = sum(
    record.get_total_hours() 
    for record in work_records 
    if record.attendance_status in ['REGULAR_WORK', 'EXTRA_WORK']
)

total_pay = total_hours * hourly_rate
```

### 4. 주휴수당 계산

**기존 (변경 전):**
```python
# 실제 근무 시간 기준
if actual_worked_hours >= 15:
    holiday_pay = daily_avg_hours * hourly_rate
```

**변경 후 (소정근로일 개근 기준):**
```python
# 1. 해당 주의 소정근로일 목록 확인
scheduled_dates = [
    date for date in week_dates 
    if employee.is_scheduled_workday(date)
]

# 2. 소정근로일 개근 여부 확인
perfect_attendance = all(
    work_record and work_record.attendance_status in ['REGULAR_WORK', 'ANNUAL_LEAVE']
    for date in scheduled_dates
    if (work_record := get_work_record(date))
)

# 3. 주 15시간 이상 + 개근 시에만 지급
if perfect_attendance and weekly_hours >= 15:
    holiday_pay = daily_avg_hours * hourly_rate
else:
    holiday_pay = 0
```

### 5. 연차유급휴가 계산 (1년 미만)

**기존 (변경 전):**
```python
# 실제 근무 기록 수로 판단
if work_records_count >= len(scheduled_dates):
    perfect_months += 1
```

**변경 후 (소정근로일 개근 기준):**
```python
# 해당 월의 소정근로일 목록
scheduled_dates = [
    date for date in month_dates
    if employee.is_scheduled_workday(date)
]

# 개근 여부 확인 (REGULAR_WORK + ANNUAL_LEAVE만 인정)
perfect_attendance = all(
    work_record and work_record.attendance_status in ['REGULAR_WORK', 'ANNUAL_LEAVE']
    for date in scheduled_dates
    if (work_record := get_work_record(date))
)

if perfect_attendance:
    earned_days += 1  # 개근한 월마다 1일 발생
```

## 📊 데이터 흐름 예시

### 시나리오: 월요일 출근 기록

#### 1. 스케줄 설정 (근무표)
```
주간 스케줄: 월요일 09:00~18:00 (휴게 60분)
→ 모든 월요일이 소정근로일로 자동 판정
```

#### 2. 실제 근로 기록
```
2025-01-06 (월):
  - 출결 상태: REGULAR_WORK (근무)
  - 출근: 09:00
  - 퇴근: 18:00
  - 휴게: 60분
  → 총 근로시간: 8시간
  → 급여 반영: 8시간 × 시급
  → 개근 판단: ✅ 출근 인정
```

#### 3. 추가근무 (대타) 기록
```
2025-01-07 (화):
  - 스케줄: 없음 (소정근로일 아님)
  - 출결 상태: EXTRA_WORK (추가근무)
  - 출근: 14:00
  - 퇴근: 20:00
  - 휴게: 30분
  → 총 근로시간: 5.5시간
  → 급여 반영: 5.5시간 × 시급
  → 개근 판단: ❌ 소정근로일이 아니므로 판단 대상 아님
```

#### 4. 연차 사용
```
2025-01-08 (수):
  - 스케줄: 수요일 09:00~18:00 (소정근로일)
  - 출결 상태: ANNUAL_LEAVE (연차사용)
  - 시간: 입력 안 함
  → 총 근로시간: 0시간
  → 급여 반영: 0원 (연차는 별도 계산)
  → 개근 판단: ✅ 출근 인정 (유급휴가)
```

#### 5. 결근
```
2025-01-09 (목):
  - 스케줄: 목요일 09:00~18:00 (소정근로일)
  - 출결 상태: ABSENT (결근)
  - 시간: 입력 안 함
  → 총 근로시간: 0시간
  → 급여 반영: 0원
  → 개근 판단: ❌ 출근 불인정
  → 주휴수당: 이번 주는 미지급
```

## 🎯 스타벅스형(유동 스케줄) 지원

### 매주 근무 요일이 다른 경우
```
1주차: 월, 수, 금 근무
2주차: 화, 목, 토 근무
3주차: 월, 목, 일 근무
```

**해결 방법:**
- 주간 스케줄을 사용하지 않음
- 매주 월별 스케줄로 근무표를 사전 등록
- 각 주의 소정근로일이 자동으로 다르게 판정됨

### 월별로 근무 패턴이 변경되는 경우
```
1월: 월~금 09:00~18:00
2월: 화~토 13:00~22:00
3월: 월, 수, 금 14:00~20:00
```

**해결 방법:**
- 각 월에 대해 "이달만 스케줄 변경" 사용
- MonthlySchedule이 주간 스케줄보다 우선순위가 높음
- 법적 계산(주휴수당, 연차)도 월별 스케줄 기준으로 정확히 계산됨

## ⚠️ 주의사항

### 1. 마이그레이션 순서
1. 백엔드 마이그레이션 적용 (`python3 manage.py migrate labor`)
2. 프론트엔드 배포
3. 기존 WorkRecord의 `attendance_status`는 기본값 `REGULAR_WORK`로 초기화됨

### 2. 기존 데이터 호환성
- `attendance_type` 필드는 하위 호환성을 위해 유지 (deprecated)
- 새로운 코드는 `attendance_status` 필드 사용 권장
- 기존 API는 정상 동작 (신규 필드는 optional)

### 3. 개근 판단 기준 변경
- **기존**: 실제 근무 기록 존재 여부
- **변경 후**: 소정근로일 기준 + attendance_status 확인
- 주휴수당·연차 계산 로직도 이에 따라 업데이트 필요

## 🚀 Phase 2 완료 내역

### 1. 백엔드 계산 로직 업데이트 ✅

#### holiday_pay() 엔드포인트
**변경 전:**
```python
# 실제 근무 시간 15시간 기준
if actual_worked_hours >= 15:
    holiday_pay = daily_avg_hours * hourly_rate
```

**변경 후:**
```python
# 소정근로일 개근 + 주 15시간 기준
scheduled_dates = [날짜 for 날짜 in 해당주 if is_scheduled_workday(날짜)]
perfect_attendance = all(
    record.attendance_status in ['REGULAR_WORK', 'ANNUAL_LEAVE']
    for 날짜 in scheduled_dates
)

if perfect_attendance and weekly_scheduled_hours >= 15:
    holiday_pay = daily_avg_hours * hourly_rate
else:
    holiday_pay = 0
```

**응답 데이터:**
```json
{
  "amount": 12000,
  "hours": 8.0,
  "reason": "eligible",
  "weekly_scheduled_hours": 40.0,
  "scheduled_days_count": 5,
  "perfect_attendance": true,
  "attendance_details": [
    {
      "date": "2025-12-15",
      "is_scheduled": true,
      "attendance_status": "REGULAR_WORK",
      "is_attended": true,
      "hours": 8.0
    }
  ]
}
```

#### annual_leave_summary() 엔드포인트
**변경 전:**
```python
# 실제 근무 기록 수로 개근 판단
if work_records_count >= scheduled_dates_count:
    perfect_months += 1
```

**변경 후:**
```python
# 소정근로일별 출결 상태 확인
scheduled_dates = [날짜 for 날짜 in 해당월 if is_scheduled_workday(날짜)]
perfect_attendance = all(
    record and record.attendance_status in ['REGULAR_WORK', 'ANNUAL_LEAVE']
    for 날짜 in scheduled_dates
)

if perfect_attendance:
    earned_days += 1
```

#### calendar() 엔드포인트
**추가된 필드:**
```json
{
  "dates": [
    {
      "date": "2025-12-15",
      "day": 15,
      "is_scheduled_workday": true,  // 새로 추가
      "attendance_status": "REGULAR_WORK",  // 새로 추가
      "is_worked": true,  // 새로 추가
      "record": {...}
    }
  ]
}
```

#### get_cumulative_stats_data() 메소드
**추가된 통계:**
```json
{
  "total_hours": 160.0,
  "total_earnings": 1600000,
  "total_work_days": 20,
  "regular_work_hours": 144.0,  // 새로 추가
  "regular_work_days": 18,  // 새로 추가
  "regular_work_earnings": 1440000,  // 새로 추가
  "extra_work_hours": 16.0,  // 새로 추가
  "extra_work_days": 2,  // 새로 추가
  "extra_work_earnings": 160000,  // 새로 추가
  "annual_leave_days": 1,  // 새로 추가
  "absent_days": 0,  // 새로 추가
  "sick_leave_days": 0  // 새로 추가
}
```

### 2. 프론트엔드 작업 (향후 작업)

Phase 2에서 백엔드는 완료되었으나, 프론트엔드 UI는 아직 구현되지 않았습니다.

#### 필요한 작업:
- [ ] WorkDayModal.vue 개선 (두 가지 수정 경로 분리)
- [ ] 출결 상태 선택 UI
- [ ] 소정근로일 안내 문구
- [ ] 캘린더 시각적 구분

---

## 🚀 Phase 3 계획 (향후 작업)

현재 Phase 1에서는 데이터 구조와 기본 로직만 구현했습니다. 다음 단계에서는:

### 1. 프론트엔드 UI 개선
- [ ] WorkDayModal에 "근무표 수정" / "실제 근로 수정" 경로 분리
- [ ] 출결 상태 선택 UI (REGULAR_WORK / EXTRA_WORK / ANNUAL_LEAVE / ABSENT / SICK_LEAVE)
- [ ] 소정근로일 안내 문구 표시
- [ ] 캘린더 시각적 구분 (소정근로일 테두리, 추가근무 색상)

### 2. 계산 로직 업데이트
- [x] ~~holiday_pay() 엔드포인트 - 소정근로일 개근 기준으로 변경~~ ✅ Phase 2 완료
- [x] ~~annual_leave_summary() 엔드포인트 - 소정근로일 개근 기준으로 변경~~ ✅ Phase 2 완료
- [x] ~~compute_monthly_schedule_stats() - 소정근로일 vs 추가근무 구분 통계~~ ✅ Phase 2 완료

### 3. 테스트 및 검증
- [ ] 소정근로일 판정 로직 단위 테스트
- [ ] 주휴수당 계산 통합 테스트
- [ ] 연차 발생 계산 통합 테스트
- [ ] 유동 스케줄 시나리오 테스트

## 📝 관련 문서
- [BREAK_TIME_UX_IMPROVEMENT.md](./BREAK_TIME_UX_IMPROVEMENT.md) - 휴게시간 입력 UX 개선
- [OVERNIGHT_WORK_SCHEDULE_FEATURE.md](./OVERNIGHT_WORK_SCHEDULE_FEATURE.md) - 익일 근무 기능
- [SCHEDULE_VS_WORKRECORD_FIX.md](./SCHEDULE_VS_WORKRECORD_FIX.md) - 스케줄/기록 우선순위
- [FEATURE_GUIDE.md](./FEATURE_GUIDE.md) - 전체 기능 가이드

---

**작업 완료일**: 2025-12-20  
**Phase**: 1 (데이터 구조 및 기본 로직)  
**작성자**: GitHub Copilot
