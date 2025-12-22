# 익일 근무 입력 기능 - 주간/월별 스케줄 확장

## 📋 개요

이 문서는 **주간 근무 스케줄**과 **월별 스케줄 변경 모달**에 익일 근무(24:00~06:00) 입력 기능을 추가한 작업을 설명합니다.

### 변경 범위
- ✅ **일별 근로기록 모달** (WorkDayModal.vue) - 이미 구현됨
- ✅ **주간 근무 스케줄** (WeeklyScheduleEditor.vue) - 이번 작업에서 추가
- ✅ **월별 스케줄 변경** (MonthlyScheduleModal.vue) - 이번 작업에서 추가

## 🎯 기능 요구사항

### 1. UI 요구사항
- 각 요일 행에 "익일 근무 있음 (24:00~06:00)" 체크박스 표시
- 체크박스 선택 시에만 익일 근무 시간 입력 필드 노출
- 입력 범위: 0~360분 (6시간)
- 밸리데이션: 범위 초과 시 에러 메시지 표시

### 2. 데이터 처리
- 주간 스케줄: `WorkSchedule` 모델의 `next_day_work_minutes` 필드에 저장
- 월별 스케줄: `MonthlySchedule` 모델의 `next_day_work_minutes` 필드에 저장
- 일별 기록: `WorkRecord` 모델의 `next_day_work_minutes` 필드에 저장

### 3. 우선순위 로직
근로시간 계산 시:
1. **일별 WorkRecord 값**이 있으면 우선 사용
2. 없으면 **월별 MonthlySchedule 값** 사용
3. 없으면 **주간 WorkSchedule 값** 사용

## 📂 변경된 파일

### 프론트엔드 (3개 파일)

#### 1. `frontend/src/components/WeeklyScheduleEditor.vue`
**변경 내용:**
- 각 요일 행을 카드 형태로 변경 (border + padding)
- 익일 근무 체크박스 및 시간 입력 필드 추가
- `localSchedules` 타입에 `has_next_day_work`, `next_day_work_minutes` 필드 추가
- `loadSchedules()`: 백엔드에서 익일 근무 데이터 로드
- `saveSchedules()`: 익일 근무 데이터 저장 및 밸리데이션 (0~360분)
- `timeOptions`: 24:00 옵션 추가

**주요 코드:**
```vue
<!-- 템플릿 -->
<div v-if="localSchedules[d.value].enabled" class="ml-24 flex items-center gap-3">
  <label class="inline-flex items-center gap-2 text-sm cursor-pointer select-ne">
    <input 
      type="checkbox" 
      v-model="localSchedules[d.value].has_next_day_work"
      class="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
    />
    <span class="text-gray-700">익일 근무 있음 (24:00~06:00)</span>
  </label>
  
  <div v-if="localSchedules[d.value].has_next_day_work" class="flex items-center gap-2">
    <input
      type="number"
      v-model.number="localSchedules[d.value].next_day_work_minutes"
      min="0"
      max="360"
      class="w-20 px-2 py-1 text-sm border rounded"
      placeholder="0"
    />
    <span class="text-xs text-gray-600">분 (0~360)</span>
  </div>
</div>

// 스크립트
const nextDayMinutes = schedule.has_next_day_work ? (schedule.next_day_work_minutes || 0) : 0;

// 밸리데이션
if (nextDayMinutes < 0 || nextDayMinutes > 360) {
  throw new Error(`익일 근무 시간은 0~360분 사이여야 합니다.`);
}

const payload = {
  weekday: w.value,
  start_time: schedule.enabled ? startTime : null,
  end_time: schedule.enabled ? endTime : null,
  is_overnight: isOvernight,
  next_day_work_minutes: nextDayMinutes,
  enabled: schedule.enabled,
};
```

#### 2. `frontend/src/components/MonthlyScheduleModal.vue`
**변경 내용:**
- WeeklyScheduleEditor와 동일한 UI 구조 적용
- `localSchedules` 타입에 익일 근무 필드 추가
- 24:00 시간 옵션 추가 (48개 → 49개)
- `loadSchedules()`: 월별 스케줄 로드 시 익일 근무 데이터 포함
- `saveSchedules()`: 24:00 처리 및 익일 근무 데이터 저장

**주요 코드:**
```typescript
// 시간 옵션 (24:00 포함)
const timeOptions = Array.from({ length: 49 }, (_, i) => {
  if (i === 48) return '24:00'
  const hour = Math.floor(i / 2)
  const minute = (i % 2) * 30
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
})

// 데이터 타입
interface ScheduleData {
  enabled: boolean
  start_time: string
  end_time: string
  has_next_day_work: boolean
  next_day_work_minutes: number
}

// 저장 로직
const nextDayMinutes = data.has_next_day_work ? (data.next_day_work_minutes || 0) : 0

return {
  weekday: parseInt(weekday),
  start_time: data.enabled ? data.start_time : null,
  end_time: data.enabled ? endTime : null,
  is_overnight: isOvernight,
  next_day_work_minutes: nextDayMinutes,
  enabled: data.enabled
}
```

#### 3. `frontend/src/components/WorkDayModal.vue`
**변경 사항 없음** - 이미 익일 근무 기능이 구현되어 있음

### 백엔드 (1개 파일)

#### 4. `labor/views.py`
**변경 내용:**

**schedules() 엔드포인트 (주간 스케줄):**
- 이미 `next_day_work_minutes` 처리 로직 포함됨
- 변경 사항 없음

**monthly_schedule_override() 엔드포인트 (월별 스케줄):**
- POST 요청 처리 시 `is_overnight`, `next_day_work_minutes` 필드 추가
- MonthlySchedule 생성 시 익일 근무 필드 저장
- WorkRecord 자동 생성 시 익일 근무 필드 포함

**주요 코드:**
```python
# MonthlySchedule 생성
for schedule_data in schedules_data:
    weekday = schedule_data.get('weekday')
    start_time_str = schedule_data.get('start_time')
    end_time_str = schedule_data.get('end_time')
    enabled = schedule_data.get('enabled', True)
    is_overnight = schedule_data.get('is_overnight', False)
    next_day_work_minutes = int(schedule_data.get('next_day_work_minutes', 0))
    
    monthly_schedule = MonthlySchedule.objects.create(
        employee=job,
        year=year,
        month=month,
        weekday=weekday,
        start_time=start_time_obj,
        end_time=end_time_obj,
        is_overnight=is_overnight,
        next_day_work_minutes=next_day_work_minutes,
        enabled=enabled,
        # ...
    )

# WorkRecord 자동 생성
if schedule.is_overnight:
    next_date = work_date + timedelta(days=1)
    time_out_dt = datetime.combine(next_date, schedule.end_time)
else:
    time_out_dt = datetime.combine(work_date, schedule.end_time)

WorkRecord.objects.create(
    employee=job,
    work_date=work_date,
    time_in=time_in_dt,
    time_out=time_out_dt,
    is_overnight=schedule.is_overnight,
    next_day_work_minutes=schedule.next_day_work_minutes,
    break_minutes=base_break if isinstance(base_break, int) else 0
)
```

### 데이터베이스
**마이그레이션 불필요** - `WorkSchedule`와 `MonthlySchedule` 모델에 이미 필드가 존재함
- `is_overnight` (BooleanField, default=False)
- `next_day_work_minutes` (IntegerField, default=0)

## 🔄 데이터 흐름

### 1. 주간 스케줄 저장 흐름
```
사용자 입력 (WeeklyScheduleEditor)
  ↓
체크박스 선택 → has_next_day_work = true
시간 입력 → next_day_work_minutes = 120 (예시)
  ↓
saveSchedules() 호출
  ↓
밸리데이션 (0~360 범위 체크)
  ↓
API 요청: POST /api/labor/jobs/{id}/schedules/
  weekday: 0
  start_time: "18:00"
  end_time: "00:00"
  is_overnight: true (24:00 입력 시)
  next_day_work_minutes: 120
  enabled: true
  ↓
백엔드: WorkSchedule 모델 저장
  ↓
과거 날짜 WorkRecord 자동 생성/업데이트
  (next_day_work_minutes 포함)
  ↓
통계 계산 및 응답
  ↓
프론트: labor-updated 이벤트 발생
  ↓
캘린더/통계 자동 갱신
```

### 2. 월별 스케줄 저장 흐름
```
사용자 입력 (MonthlyScheduleModal)
  ↓
체크박스 선택 → has_next_day_work = true
시간 입력 → next_day_work_minutes = 180 (예시)
  ↓
saveSchedules() 호출
  ↓
밸리데이션 (0~360 범위 체크)
  ↓
API 요청: POST /api/labor/employees/{id}/monthly-schedule-override/
  year: 2025
  month: 1
  schedules: [
    {
      weekday: 0,
      start_time: "18:00",
      end_time: "00:00",
      is_overnight: true,
      next_day_work_minutes: 180,
      enabled: true
    },
    ...
  ]
  ↓
백엔드: MonthlySchedule 모델 저장
  ↓
해당 월의 WorkRecord 자동 생성/업데이트
  (next_day_work_minutes 포함)
  ↓
통계 계산 및 응답
  ↓
프론트: saved 이벤트 발생 (stats 포함)
  ↓
부모 컴포넌트에서 캘린더/통계 갱신
```

### 3. 일별 기록 조회 흐름
```
캘린더 날짜 클릭
  ↓
WorkDayModal 열림
  ↓
GET /api/labor/jobs/{id}/date-schedule/?date=2025-01-15
  ↓
백엔드 응답:
  {
    has_schedule: true,
    start_time: "18:00",
    end_time: "00:00",
    work_record: {
      time_in: "2025-01-15T18:00:00",
      time_out: "2025-01-16T00:00:00",
      is_overnight: true,
      next_day_work_minutes: 120,
      break_minutes: 0
    }
  }
  ↓
모달에 데이터 표시
  - 기본 시간: 18:00 ~ 24:00 (is_overnight=true인 경우)
  - 익일 근무: 체크됨, 120분 표시
```

## 🧮 근로시간 계산 로직

### WorkRecord.get_total_hours() 메소드
```python
def get_total_hours(self):
    """실제 근로시간 (break 제외, 익일 근무 포함)"""
    if not self.time_in or not self.time_out:
        return Decimal('0')

    # 1. 기본 근로 시간 계산
    duration = self.time_out - self.time_in
    total_minutes = duration.total_seconds() / 60.0

    # 2. 휴게 시간 제외
    break_total = float(self.break_minutes or 0)
    work_minutes = max(0.0, total_minutes - break_total)
    
    # 3. 익일 추가 근무 시간 합산 (24:00~06:00 구간)
    next_day_minutes = float(self.next_day_work_minutes or 0)
    total_work_minutes = work_minutes + next_day_minutes
    
    # 4. 시간 단위로 변환
    return Decimal(str(total_work_minutes / 60.0))
```

### 계산 예시
```
근무 시간: 18:00 ~ 24:00 (6시간)
휴게 시간: 30분
익일 근무: 120분 (2시간, 24:00~02:00)

계산:
- 기본 근로: (24:00 - 18:00) = 6시간 = 360분
- 휴게 제외: 360분 - 30분 = 330분
- 익일 근무 추가: 330분 + 120분 = 450분
- 최종 근로시간: 450분 ÷ 60 = 7.5시간

급여 계산:
- 시급: 10,000원
- 일 급여: 7.5시간 × 10,000원 = 75,000원
```

## ✅ 테스트 시나리오

### 1. 주간 스케줄 익일 근무 설정
```
1. 주간 스케줄 편집 화면 진입
2. 월요일 선택
   - 시작: 18:00
   - 종료: 24:00
   - "일하는 날" 체크
3. "익일 근무 있음" 체크
4. 익일 근무 시간: 120분 입력
5. 저장 버튼 클릭
6. 확인:
   - 과거 월요일 날짜에 근로기록 자동 생성
   - 각 기록에 next_day_work_minutes=120 포함
   - 총 근로시간에 2시간 추가 반영
```

### 2. 월별 스케줄 익일 근무 변경
```
1. 캘린더에서 "이달만 스케줄 변경" 클릭
2. 특정 요일 선택 (예: 화요일)
   - 시작: 20:00
   - 종료: 24:00
   - "활성" 체크
3. "익일 근무 있음" 체크
4. 익일 근무 시간: 180분 입력
5. 저장 버튼 클릭
6. 확인:
   - 해당 월의 화요일에만 익일 근무 반영
   - 다른 월에는 영향 없음
   - 월별 통계에 익일 근무 시간 포함
```

### 3. 밸리데이션 테스트
```
1. 주간/월별 스케줄에서 익일 근무 체크
2. 시간 입력:
   - -10분 입력 → 에러 메시지 표시
   - 500분 입력 → 에러 메시지 표시
   - 0분 입력 → 정상 저장 (익일 근무 없음)
   - 360분 입력 → 정상 저장 (최대 6시간)
```

### 4. 우선순위 로직 테스트
```
시나리오 A: 주간 스케줄만 설정
- 주간 스케줄: 익일 근무 120분
- 월별 스케줄: 없음
- 일별 기록: 자동 생성
- 결과: 120분 적용

시나리오 B: 월별 스케줄로 덮어쓰기
- 주간 스케줄: 익일 근무 120분
- 월별 스케줄: 익일 근무 180분 (특정 월에만)
- 일별 기록: 자동 생성
- 결과: 해당 월은 180분, 다른 월은 120분

시나리오 C: 일별 기록 직접 수정
- 주간 스케줄: 익일 근무 120분
- 월별 스케줄: 익일 근무 180분
- 일별 기록: 익일 근무 60분 (직접 수정)
- 결과: 60분 적용 (일별이 최우선)
```

## 🎨 UI/UX 개선사항

### 기존 문제점
- 일별 기록에서만 익일 근무 입력 가능
- 매일 반복 입력해야 하는 불편함
- 스케줄 변경 시 과거 기록 일괄 수정 불가

### 개선된 점
- ✅ 주간 스케줄에서 반복 패턴으로 설정 가능
- ✅ 월별 스케줄로 특정 달만 변경 가능
- ✅ 과거 기록 자동 생성/업데이트
- ✅ 3단계 우선순위로 유연한 관리
- ✅ 통일된 UI/UX (3곳 모두 동일한 디자인)

### 사용자 가이드 표시
```
WeeklyScheduleEditor.vue:
"저장 시 캘린더 전체 근로시간이 변경돼요!"

MonthlyScheduleModal.vue:
"이 달의 근무 스케줄만 변경됩니다. 다른 달의 스케줄에는 영향을 주지 않습니다."

익일 근무 입력 옆:
"분 (0~360)" - 범위 안내
```

## 🚀 향후 개선 방향

### 1. 야간 가산수당 자동 계산
```python
# 향후 구현 예정
def calculate_night_premium(work_record):
    """22:00~06:00 구간 1.5배 가산"""
    # 기본 근로시간과 익일 근로시간을 분석하여
    # 야간 구간(22:00~06:00)에 해당하는 시간 계산
    # 해당 시간 × 시급 × 0.5 = 야간 가산수당
    pass
```

### 2. 스케줄 복사 기능
```
# 기능 아이디어
- 특정 월의 스케줄을 다른 달로 복사
- 주간 스케줄을 월별 스케줄로 일괄 적용
- 여러 달 선택하여 한 번에 적용
```

### 3. 시각적 표시 개선
```
# 캘린더에 익일 근무 표시
- 아이콘 추가: 🌙 (야간 근무 표시)
- 색상 구분: 익일 근무가 있는 날은 다른 색상
- 툴팁: 마우스 오버 시 익일 근무 시간 표시
```

### 4. 통계 분리 표시
```
# 월별 통계 화면
- 기본 근무시간: 80시간
- 익일 근무시간: +10시간
- 총 근무시간: 90시간
- 기본 급여: 800,000원
- 익일 추가 급여: +100,000원
```

## 📝 주의사항

### 개발 시 유의사항
1. **타임존 처리**: 모든 시간 계산은 서버 타임존 기준
2. **밸리데이션**: 프론트와 백엔드 양쪽에서 0~360 범위 체크
3. **기존 데이터**: 기존 WorkRecord는 next_day_work_minutes=0 (영향 없음)
4. **NULL 처리**: next_day_work_minutes가 NULL이면 0으로 처리

### 운영 시 유의사항
1. **스케줄 변경 영향**: 과거 기록이 자동으로 변경됨 (확인 필요)
2. **월별 우선순위**: 월별 스케줄이 주간 스케줄을 덮어씀
3. **일별 수정 권장**: 특정 날짜만 다르면 일별 기록 직접 수정
4. **급여 계산**: 익일 근무 시간도 총 근로시간에 포함됨

## 🔗 관련 문서
- [OVERNIGHT_WORK_IMPLEMENTATION.md](./OVERNIGHT_WORK_IMPLEMENTATION.md) - 익일 근무 기능 초기 구현
- [CALENDAR_STATS_SYNC_FEATURE.md](./CALENDAR_STATS_SYNC_FEATURE.md) - 통계 동기화
- [FEATURE_GUIDE.md](./FEATURE_GUIDE.md) - 전체 기능 가이드

---

**작업 완료일**: 2025-12-20  
**버전**: 1.0.0  
**작성자**: GitHub Copilot
