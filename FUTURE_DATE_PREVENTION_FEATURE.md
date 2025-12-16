# 미래 월 데이터 입력 차단 및 계산 방어 기능

## 개요

캘린더에서 무한히 미래로 이동하여 아직 발생하지 않은 날짜에 근로시간을 입력하고, 그 데이터가 통계/업적 계산에 반영되어 값이 비정상적으로 커지는 문제를 해결하기 위한 방어 기능입니다.

## 문제 상황

### 변경 전
❌ **문제점**:
- 캘린더 ▶ 버튼으로 무한히 미래로 이동 가능 (예: 2026년 6월, 2027년 1월 등)
- 미래 월의 날짜에도 근로시간 입력 가능
- 미래 날짜의 데이터가 통계/업적/주휴수당/퇴직금 계산에 포함됨
- 실제로는 근로하지 않은 시간이 누적되어 비정상적으로 큰 값 표시

### 예시
```
현재: 2025년 12월
사용자가 2026년 6월까지 이동하여 근로시간 입력
→ 아직 발생하지 않은 6개월치 근로시간이 누적 통계에 반영
→ 급여 예상액이 실제보다 훨씬 크게 표시됨
```

## 해결 방법

### 1. 캘린더 월 이동 범위 제한

#### 상한 설정: 현재 월 + 6개월
- **현재**: 2025년 12월
- **이동 가능 범위**: 2025년 12월 ~ 2026년 6월 (총 7개월)
- **2026년 6월**: ▶ 버튼 비활성화
- **하한**: 기존 정책 유지 (근로 시작일 이전으로는 이동 불가)

#### 구현 (WorkCalendar.vue)

```typescript
// 미래 월 이동 제한: 현재 월 + 6개월까지만 허용
const canGoNext = computed(() => {
  const today = new Date();
  const todayYear = today.getFullYear();
  const todayMonth = today.getMonth() + 1; // 1-12
  
  // 현재 월 + 6개월 계산
  const maxDate = new Date(todayYear, todayMonth - 1 + 6, 1);
  const maxYear = maxDate.getFullYear();
  const maxMonth = maxDate.getMonth() + 1;
  
  // 현재 보고 있는 달이 최대 허용 월보다 이전이면 true
  if (currentYear.value < maxYear) return true;
  if (currentYear.value === maxYear && currentMonth.value < maxMonth) return true;
  
  return false;
});
```

#### UI 변경
```vue
<button 
  @click="nextMonth"
  :disabled="!canGoNext"
  :class="[
    'p-2 rounded-lg transition-colors',
    canGoNext 
      ? 'text-gray-600 hover:bg-gray-100 cursor-pointer' 
      : 'text-gray-300 cursor-not-allowed opacity-50'
  ]"
  :title="!canGoNext ? '현재 월로부터 6개월 이후는 볼 수 없습니다' : '다음 달'"
>
  ▶
</button>
```

### 2. 미래 월 근로시간 입력/수정 금지

#### 미래 월 여부 확인
```typescript
// 미래 월 여부 확인 (현재 월보다 이후인지)
const isFutureMonth = computed(() => {
  const today = new Date();
  const todayYear = today.getFullYear();
  const todayMonth = today.getMonth() + 1; // 1-12
  
  if (currentYear.value > todayYear) return true;
  if (currentYear.value === todayYear && currentMonth.value > todayMonth) return true;
  
  return false;
});
```

#### 날짜 클릭 차단
```typescript
function selectDate(day: number) {
  if (day === 0) return;
  const employeeId = activeJob?.value?.id;
  if (!employeeId) return;

  // 미래 월의 날짜는 클릭 불가
  if (isFutureMonth.value) {
    alert('미래 날짜에는 근로 기록을 입력할 수 없습니다.');
    return;
  }
  
  // ...기존 로직
}
```

#### 시각적 구분
```vue
<!-- 미래 월의 날짜는 회색으로 표시되고 클릭 불가 -->
<button
  :disabled="dayObj.day === 0 || isFutureMonth"
  :class="[
    'aspect-square flex items-center justify-center text-sm rounded-lg',
    {
      'text-gray-400 bg-gray-100 cursor-not-allowed border border-gray-300': 
        dayObj.day !== 0 && isFutureMonth
    }
  ]"
>
```

#### 월별 스케줄 변경 버튼 비활성화
```vue
<button 
  v-if="activeJob"
  @click="openMonthlyScheduleModal"
  :disabled="isFutureMonth"
  :class="[
    'px-3 py-2 text-sm font-medium rounded-lg transition-colors',
    isFutureMonth
      ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
      : 'text-brand-600 bg-brand-50 hover:bg-brand-100'
  ]"
  :title="isFutureMonth ? '미래 월의 스케줄은 변경할 수 없습니다' : '이 달의 근무 스케줄을 변경합니다'"
>
  📅 월별 스케줄 변경
</button>
```

### 3. Backend 안전장치 (다중 방어선)

#### A. WorkRecord 생성 시 미래 날짜 차단

```python
def perform_create(self, serializer):
    employee_id = self.request.data.get('employee')
    try:
        employee = Employee.objects.get(id=employee_id, user=self.request.user)
        
        # 미래 날짜 입력 차단
        work_date_str = self.request.data.get('work_date')
        if work_date_str:
            from datetime import datetime
            work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
            today = timezone.now().date()
            if work_date > today:
                from rest_framework.exceptions import ValidationError
                raise ValidationError("미래 날짜에는 근로 기록을 입력할 수 없습니다.")
        
        serializer.save()
    except Employee.DoesNotExist:
        raise PermissionError("이 Job에 접근할 권한이 없습니다.")
```

#### B. WorkRecord 수정 시 미래 날짜 차단

```python
def perform_update(self, serializer):
    instance = serializer.instance
    if instance.employee.user != self.request.user:
        raise PermissionError("이 작업을 수행할 권한이 없습니다.")
    
    # 미래 날짜 수정 차단
    work_date_str = self.request.data.get('work_date')
    if work_date_str:
        from datetime import datetime
        work_date = datetime.strptime(work_date_str, '%Y-%m-%d').date()
        today = timezone.now().date()
        if work_date > today:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("미래 날짜의 근로 기록은 수정할 수 없습니다.")
    
    serializer.save()
```

#### C. cumulative_stats: 오늘까지만 계산

```python
@action(detail=True, methods=['get'], url_path='cumulative-stats')
def cumulative_stats(self, request, pk=None):
    """
    안전장치:
    - work_date <= today 조건으로 필터링
    - while 루프에서 current_date <= today 조건으로 제한
    - 미래 데이터가 DB에 있어도 계산에서 제외됨
    """
    # 현재 날짜 (오늘)
    today = timezone.now().date()
    
    # 모든 실제 근로기록 조회 (시작일 ~ 오늘)
    work_records = WorkRecord.objects.filter(
        employee=job,
        work_date__gte=start_date,
        work_date__lte=today  # ⭐ 오늘까지만
    )
    
    # 시작일부터 오늘까지 날짜별로 순회
    current_date = start_date
    while current_date <= today:  # ⭐ 오늘까지만
        # ... 통계 계산
        current_date += timedelta(days=1)
```

#### D. monthly_summary: 미래 월 표시

```python
@action(detail=True, methods=['get'], url_path='monthly-summary')
def monthly_summary(self, request, pk=None):
    """
    미래 월의 경우 is_future_month: true를 반환하여
    프론트엔드에서 적절히 처리할 수 있도록 함
    """
    # 미래 월 여부 확인
    today = timezone.now().date()
    today_year = today.year
    today_month = today.month
    is_future = (year > today_year) or (year == today_year and mon > today_month)
    
    stats = compute_monthly_schedule_stats(job, year, mon)
    stats['is_future_month'] = is_future  # ⭐ 미래 월 플래그
    
    return Response(stats)
```

## 방어선 요약

```
┌─────────────────────────────────────────────────┐
│ 1차 방어: 프론트엔드 UI 차단                      │
│   - 캘린더 월 이동 제한 (현재 + 6개월)            │
│   - 미래 월 날짜 클릭 불가                        │
│   - 미래 월 스케줄 변경 버튼 비활성화              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 2차 방어: 백엔드 API 검증                        │
│   - WorkRecord 생성 시 미래 날짜 거부             │
│   - WorkRecord 수정 시 미래 날짜 거부             │
│   - ValidationError 반환                        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│ 3차 방어: 계산 로직 필터링                        │
│   - cumulative_stats: work_date <= today        │
│   - 루프 조건: current_date <= today             │
│   - 미래 데이터가 있어도 계산에서 제외             │
└─────────────────────────────────────────────────┘
```

## 사용자 경험

### 시나리오 1: 현재 월에서 미래로 이동
```
1. 사용자가 2025년 12월 캘린더를 보고 있음
2. ▶ 버튼 클릭하여 2026년 1월로 이동
3. ▶ 버튼 클릭하여 2026년 2월, 3월, 4월, 5월, 6월으로 이동 가능
4. 2026년 6월에서 ▶ 버튼이 비활성화됨
   - 툴팁: "현재 월로부터 6개월 이후는 볼 수 없습니다"
```

### 시나리오 2: 미래 월에서 날짜 클릭 시도
```
1. 캘린더가 2026년 3월을 표시 중 (미래 월)
2. 모든 날짜 셀이 회색으로 표시되고 클릭 불가 상태
3. 날짜에 마우스 오버: "미래 월에는 근로 기록을 입력할 수 없습니다"
4. 클릭 시: alert 창 표시 "미래 날짜에는 근로 기록을 입력할 수 없습니다."
```

### 시나리오 3: API로 직접 미래 날짜 입력 시도
```
POST /api/labor/work-records/
{
  "employee": 1,
  "work_date": "2026-06-15",
  "start_time": "09:00",
  "end_time": "18:00"
}

응답: 400 Bad Request
{
  "work_date": ["미래 날짜에는 근로 기록을 입력할 수 없습니다."]
}
```

### 시나리오 4: 통계 계산 (미래 데이터 제외)
```
상황: DB에 실수로 미래 날짜 데이터가 들어간 경우

GET /api/labor/jobs/1/cumulative-stats/

계산 과정:
- 2024-01-01 ~ 2025-12-15 (오늘): 포함 ✅
- 2025-12-16 ~ 2026-12-31: 제외 ❌

결과: 오늘까지의 데이터만 정확히 집계됨
```

## 기술적 세부사항

### 날짜 계산 로직

#### 현재 월 + 6개월 계산
```typescript
const today = new Date();
const todayMonth = today.getMonth(); // 0-based (0=1월)

// 6개월 후
const maxDate = new Date(today.getFullYear(), todayMonth + 6, 1);
const maxYear = maxDate.getFullYear();
const maxMonth = maxDate.getMonth() + 1; // 1-based (1=1월)

// 예: 2025-12 → 2026-06
```

#### 미래 월 판별
```typescript
const isFutureMonth = computed(() => {
  const today = new Date();
  const todayYear = today.getFullYear();
  const todayMonth = today.getMonth() + 1; // 1-based
  
  // year > todayYear or (year == todayYear and month > todayMonth)
  if (currentYear.value > todayYear) return true;
  if (currentYear.value === todayYear && currentMonth.value > todayMonth) return true;
  
  return false;
});
```

### API 에러 처리

#### ValidationError 발생
```python
from rest_framework.exceptions import ValidationError

if work_date > today:
    raise ValidationError("미래 날짜에는 근로 기록을 입력할 수 없습니다.")
```

#### 프론트엔드에서 처리
```typescript
try {
  await apiClient.post('/labor/work-records/', data);
} catch (error) {
  if (error.response?.status === 400) {
    alert(error.response.data.work_date[0]);
    // "미래 날짜에는 근로 기록을 입력할 수 없습니다."
  }
}
```

## 테스트 방법

### 1. 캘린더 월 이동 제한 테스트
```
1. 근로관리 페이지 접속
2. 현재 월(2025년 12월)에서 시작
3. ▶ 버튼을 6번 클릭하여 2026년 6월까지 이동
4. 2026년 6월에서 ▶ 버튼이 비활성화되는지 확인
5. 툴팁이 올바르게 표시되는지 확인
```

### 2. 미래 월 입력 차단 테스트
```
1. 캘린더를 2026년 3월로 이동
2. 모든 날짜가 회색으로 표시되는지 확인
3. 날짜 클릭 시 alert가 표시되는지 확인
4. "월별 스케줄 변경" 버튼이 비활성화되는지 확인
```

### 3. API 직접 호출 테스트
```bash
# 미래 날짜 입력 시도
curl -X POST http://localhost:8000/api/labor/work-records/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee": 1,
    "work_date": "2026-06-15",
    "start_time": "09:00",
    "end_time": "18:00"
  }'

# 예상 응답: 400 Bad Request
# {"work_date": ["미래 날짜에는 근로 기록을 입력할 수 없습니다."]}
```

### 4. 통계 계산 정확성 테스트
```
1. 과거 날짜(2024년 10월)에 근로기록 입력
2. 현재 날짜(2025년 12월)에 근로기록 입력
3. DB에 직접 미래 날짜(2026년 6월) 데이터 삽입 (테스트용)
4. 누적 통계 API 호출
5. 미래 날짜 데이터가 계산에서 제외되는지 확인
```

## 제한사항 및 고려사항

### 현재 제한
- **6개월 상한**: 하드코딩된 값 (필요시 설정으로 변경 가능)
- **현재 월 기준**: 서버 시간 기준 (사용자 타임존 고려 안 함)

### 향후 개선 가능 사항
- 관리자 설정에서 월 이동 상한 조정 가능
- 사용자 타임존 고려한 날짜 계산
- 미래 월 스케줄 "예정" 모드 추가 (조회만 가능)
- 계절별 근무 패턴 미리 설정 기능

## 관련 파일

### Frontend
- `frontend/src/components/WorkCalendar.vue`
  - `canGoNext` computed: 미래 월 이동 제한
  - `isFutureMonth` computed: 미래 월 여부 확인
  - `selectDate()`: 미래 월 클릭 차단
  - UI 스타일링: 미래 월 시각적 구분

### Backend
- `labor/views.py`
  - `WorkRecordViewSet.perform_create()`: 생성 시 미래 날짜 차단
  - `WorkRecordViewSet.perform_update()`: 수정 시 미래 날짜 차단
  - `EmployeeViewSet.cumulative_stats()`: 오늘까지만 계산
  - `EmployeeViewSet.monthly_summary()`: 미래 월 플래그 추가

## 이전 문서와의 관계

이 기능은 다음 문서들과 함께 작동합니다:
- `MONTHLY_SCHEDULE_FEATURE.md`: 월별 스케줄 오버라이드 (미래 월은 변경 불가)
- `CUMULATIVE_STATS_FIX.md`: 누적 통계 정확한 계산 (오늘까지만)
- `CALENDAR_STATS_SYNC_FEATURE.md`: 캘린더-통계 동기화

이 네 가지 기능이 함께 작동하여:
1. 정확한 시간 범위 내에서만 데이터 입력 가능
2. 통계는 항상 실제 발생한 근로만 반영
3. 사용자에게 직관적이고 정확한 정보 제공
