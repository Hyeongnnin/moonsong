# 스케줄 소스 표시 기능 구현 완료

## 📋 요구사항
**문제점**: 주간 근무스케줄(템플릿)만 입력하면 캘린더에 아무 날짜도 표시되지 않고, 월별 스케줄/월별 기록을 추가해야만 소정근로일이 표시되는 문제

**해결 목표**: 
- 월별 스케줄이 없는 달에는 주간 근무스케줄을 fallback으로 사용하여 소정근로일 자동 판정
- 월별/주간 스케줄 중 어떤 것이 적용되었는지 시각적으로 구분 표시

## ✅ 구현 내용

### 1. 백엔드 API 개선 (`labor/views.py`)

#### `calendar()` 메소드 수정 (Line ~565)
```python
@action(detail=True, methods=['get'], url_path='calendar')
def calendar(self, request, pk=None):
    """월별 캘린더 데이터 반환 (소정근로일 정보 포함)
    
    Phase 3: 소정근로일 판정 시 월별/주간 스케줄 구분 정보 추가
    - 월별 스케줄이 없으면 주간 스케줄을 fallback으로 사용
    - source 필드로 "monthly" | "weekly" 구분
    - 스케줄 기반 기본 시간 정보 제공
    """
```

**주요 변경사항**:
1. **우선순위 기반 스케줄 판정**:
   ```python
   # 1순위: 월별 스케줄 확인
   monthly_schedule = MonthlySchedule.objects.filter(
       employee=job, year=year, month=mon, 
       weekday=weekday, enabled=True
   ).first()
   
   # 2순위: 주간 스케줄 확인 (fallback)
   weekly_schedule = WorkSchedule.objects.filter(
       employee=job, weekday=weekday, enabled=True
   ).first()
   ```

2. **응답 필드 추가**:
   - `is_scheduled_workday`: 소정근로일 여부 (boolean)
   - `schedule_source`: "monthly" | "weekly" | null (스케줄 출처)
   - `scheduled_start_time`: 스케줄 기반 시작 시간 (HH:MM)
   - `scheduled_end_time`: 스케줄 기반 종료 시간 (HH:MM)
   - `scheduled_break_minutes`: 스케줄 기반 휴게 시간 (분)
   - `scheduled_is_overnight`: 익일 근무 여부
   - `scheduled_next_day_minutes`: 익일 근무 시간

### 2. 프론트엔드 개선 (`WorkCalendar.vue`)

#### TypeScript 인터페이스 업데이트 (Line ~168)
```typescript
interface CalendarDateItem {
  date: string;
  day: number;
  is_scheduled_workday?: boolean;  // 소정근로일 여부
  is_scheduled?: boolean;           // 하위 호환
  schedule_source?: 'monthly' | 'weekly' | null;  // 스케줄 소스
  scheduled_start_time?: string | null;
  scheduled_end_time?: string | null;
  scheduled_break_minutes?: number;
  scheduled_is_overnight?: boolean;
  scheduled_next_day_minutes?: number;
  is_worked?: boolean;
  attendance_status?: string | null;
  record?: any;
}
```

#### 스케줄 소스 뱃지 표시 (Line ~112)
```vue
<!-- 스케줄 소스 뱃지 (Phase 3) -->
<span
  v-if="dayObj.day !== 0 && getScheduleSource(dayObj.dateIso) && 
        !isHoliday(dayObj.dateIso) && !isWeeklyRest(dayObj.dateIso)"
  :class="[
    'absolute top-1 right-1 text-[8px] font-bold px-1 py-0.5 rounded',
    getScheduleSource(dayObj.dateIso) === 'monthly' 
      ? 'bg-purple-500 text-white'  // 월별 = 보라색 M
      : 'bg-blue-500 text-white'     // 주간 = 파란색 W
  ]"
  :title="getScheduleSource(dayObj.dateIso) === 'monthly' 
    ? '월별 스케줄 기반' 
    : '주간 스케줄 기반'"
>
  {{ getScheduleSource(dayObj.dateIso) === 'monthly' ? 'M' : 'W' }}
</span>
```

#### 헬퍼 함수 추가 (Line ~342)
```typescript
// Phase 3: 스케줄 소스 확인
const getScheduleSource = (dateIso?: string): 'monthly' | 'weekly' | null => {
  if (!dateIso) return null;
  const dayData = calendarData.value.find(d => d.date === dateIso);
  return dayData?.schedule_source || null;
};
```

## 🎨 시각적 표시

### 캘린더 날짜 타일 색상 규칙
1. **주황색 채우기**: 소정근로일 + 실제 근무 (is_scheduled_workday=true && is_worked=true)
2. **주황색 테두리**: 소정근로일 + 미근무 (is_scheduled_workday=true && is_worked=false)
3. **초록색 채우기**: 추가근무 (is_scheduled_workday=false && is_worked=true)
4. **회색 테두리**: 근무/스케줄 없음

### 스케줄 소스 뱃지
- **보라색 "M"**: 월별 스케줄 기반 소정근로일
- **파란색 "W"**: 주간 스케줄 기반 소정근로일 (fallback)
- 뱃지 위치: 날짜 타일 우측 상단
- 뱃지 크기: 8px, 굵은 글씨

## 🔄 동작 순서

### 1. 주간 스케줄만 입력한 경우
```
사용자 액션: 근로정보 수정 → 주간 근무스케줄 입력 (예: 월/수/금 09:00-18:00)
         ↓
백엔드 처리: WorkSchedule 생성/업데이트
         ↓
캘린더 API 호출: /api/labor/employees/{id}/calendar/?month=2025-12
         ↓
백엔드 응답: 
  - 월별 스케줄 없음 → 주간 스케줄 fallback
  - schedule_source: "weekly"
  - is_scheduled_workday: true (월/수/금)
         ↓
프론트엔드 렌더링:
  - 월/수/금 날짜에 파란색 "W" 뱃지 표시
  - 주황색 테두리로 소정근로일 표시 (미근무 상태)
```

### 2. 월별 스케줄로 변경한 경우
```
사용자 액션: 월별 스케줄 변경 버튼 클릭 → 특정 요일 시간 수정
         ↓
백엔드 처리: MonthlySchedule 생성/업데이트
         ↓
캘린더 API 호출: /api/labor/employees/{id}/calendar/?month=2025-12
         ↓
백엔드 응답:
  - 월별 스케줄 우선 적용
  - schedule_source: "monthly"
  - is_scheduled_workday: true
         ↓
프론트엔드 렌더링:
  - 해당 날짜에 보라색 "M" 뱃지 표시
  - 월별 스케줄이 없는 요일은 여전히 파란색 "W" 표시
```

## 📊 API 응답 예시

### GET /api/labor/employees/23/calendar/?month=2025-12

**주간 스케줄만 있는 경우**:
```json
{
  "dates": [
    {
      "date": "2025-12-01",
      "day": 1,
      "is_scheduled_workday": true,
      "schedule_source": "weekly",
      "scheduled_start_time": "09:00",
      "scheduled_end_time": "18:00",
      "scheduled_break_minutes": 60,
      "scheduled_is_overnight": false,
      "scheduled_next_day_minutes": 0,
      "is_worked": false,
      "attendance_status": null,
      "record": null
    },
    {
      "date": "2025-12-02",
      "day": 2,
      "is_scheduled_workday": false,
      "schedule_source": null,
      "scheduled_start_time": null,
      "scheduled_end_time": null,
      "scheduled_break_minutes": 0,
      "is_worked": false,
      "attendance_status": null,
      "record": null
    }
  ]
}
```

**월별 스케줄이 추가된 경우** (12월 1일만 월별 스케줄로 변경):
```json
{
  "dates": [
    {
      "date": "2025-12-01",
      "day": 1,
      "is_scheduled_workday": true,
      "schedule_source": "monthly",  // 월별 스케줄 우선
      "scheduled_start_time": "10:00",
      "scheduled_end_time": "19:00",
      "scheduled_break_minutes": 60,
      "is_worked": false,
      "attendance_status": null,
      "record": null
    },
    {
      "date": "2025-12-03",
      "day": 3,
      "is_scheduled_workday": true,
      "schedule_source": "weekly",  // 주간 스케줄 fallback
      "scheduled_start_time": "09:00",
      "scheduled_end_time": "18:00",
      "scheduled_break_minutes": 60,
      "is_worked": false,
      "attendance_status": null,
      "record": null
    }
  ]
}
```

## ✅ 검증 결과

### 백엔드 검증
```bash
$ python3 manage.py check
System check identified no issues (0 silenced).
```

### 프론트엔드 검증
- ✅ TypeScript 컴파일 오류 없음
- ✅ ESLint 오류 없음
- ✅ 모든 타입 정의 일치

## 🎯 사용자 시나리오

### 시나리오 1: 신규 알바 등록
1. 근로정보 수정 → 주간 근무스케줄만 입력 (월/수/금 13:00-19:00)
2. 캘린더 확인 → **즉시 월/수/금에 파란색 "W" 뱃지 + 주황색 테두리 표시**
3. 클릭하여 근로 기록 추가 가능

### 시나리오 2: 특정 월만 스케줄 변경
1. 캘린더에서 "월별 스케줄 변경" 버튼 클릭
2. 12월의 화요일만 14:00-20:00로 변경
3. 캘린더 확인 → 화요일은 **보라색 "M" 뱃지**, 나머지는 **파란색 "W" 뱃지**

### 시나리오 3: 월별 스케줄 삭제
1. 월별 스케줄 삭제 (DB에서 MonthlySchedule 제거)
2. 캘린더 자동 갱신 → **자동으로 주간 스케줄 fallback 적용**
3. 모든 날짜가 다시 파란색 "W" 뱃지로 변경

## 🔍 기술적 세부사항

### 우선순위 로직 (`Employee.is_scheduled_workday()`)
```python
def is_scheduled_workday(self, target_date):
    """특정 날짜가 소정근로일인지 판정
    
    판정 기준 (우선순위 순):
    1. 해당 월의 MonthlySchedule이 있으면 그것 기준
    2. 없으면 WorkSchedule(주간 스케줄) 기준
    """
    # 1순위: 월별 스케줄
    monthly_schedule = MonthlySchedule.objects.filter(...).first()
    if monthly_schedule:
        return monthly_schedule.start_time is not None
    
    # 2순위: 주간 스케줄
    weekly_schedule = WorkSchedule.objects.filter(...).first()
    if weekly_schedule:
        return weekly_schedule.start_time is not None
    
    return False
```

### 성능 최적화
- 날짜별 개별 쿼리 없음
- 월별로 한 번에 조회: `filter(year=year, month=mon)`
- 프론트엔드에서 메모이제이션: `computed()` 사용

## 📝 후속 작업 (선택사항)

1. **범례(Legend) 추가**: 캘린더 하단에 색상/뱃지 의미 설명
2. **필터 기능**: "주간 스케줄만", "월별 스케줄만" 필터
3. **통계 분리**: 월별/주간 기반 소정근로일 통계 별도 표시
4. **알림 기능**: 월별 스케줄이 비어있을 때 "주간 스케줄 기반으로 표시 중" 안내

## 🎉 결과
✅ **주간 근무스케줄만 입력해도 캘린더에 소정근로일이 즉시 표시됩니다!**
✅ **월별/주간 스케줄 구분을 시각적으로 확인할 수 있습니다!**

---

**구현 완료일**: 2025-12-20  
**관련 파일**:
- `/labor/views.py` (calendar 메소드)
- `/frontend/src/components/WorkCalendar.vue`
