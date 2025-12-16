# 달력-통계 카드 동기화 기능

## 개요

캘린더에서 선택한 월과 통계 카드를 완전히 동기화하여, 사용자가 보고 있는 월의 통계를 직관적으로 확인할 수 있도록 개선했습니다.

## 변경 전 동작

❌ **문제점**:
- 캘린더에서 2024년 10월을 보고 있어도 통계는 항상 현재 월(2025년 12월) 기준으로만 표시
- 사용자가 "지금 보고 있는 달의 통계"인지 "현재 시점의 통계"인지 구분하기 어려움
- 캘린더와 통계 카드가 서로 다른 시간축을 사용

## 변경 후 동작

✅ **개선사항**:
1. **통계 기준 월 = 캘린더 선택 월**
   - 캘린더가 2024년 10월 → 통계도 2024년 10월 데이터
   - 캘린더가 2025년 12월 → 통계도 2025년 12월 데이터

2. **동적 제목**
   - 변경 전: "이번 달 통계" (고정)
   - 변경 후: "2024년 10월 통계", "2025년 12월 통계" (동적)

3. **완전한 동기화**
   - 캘린더 ◀/▶ 버튼으로 월 변경 시 통계도 자동 업데이트
   - 캘린더와 통계가 항상 같은 월을 기준으로 표시

## 구현 내용

### 1. WorkCalendar.vue

#### 이벤트 추가
```typescript
// monthChanged 이벤트 추가
const emit = defineEmits(['statsUpdated', 'monthChanged']);
```

#### 월 변경 감지 및 알림
```typescript
// currentYear, currentMonth가 변경될 때마다 부모 컴포넌트에 알림
watch([() => activeJob?.value?.id, currentYear, currentMonth], () => {
  loadCalendar();
  emit('monthChanged', { year: currentYear.value, month: currentMonth.value });
}, { immediate: true });
```

### 2. WorkSummaryCard.vue

#### Props 추가
```typescript
interface Props {
  activeJob?: Job | null;
  displayYear?: number;      // 새로 추가
  displayMonth?: number;     // 새로 추가
}
```

#### 동적 제목 및 레이블
```typescript
// 통계 카드 제목
const statsTitle = computed(() => {
  if (props.displayYear && props.displayMonth) {
    return `${props.displayYear}년 ${props.displayMonth}월 통계`;
  }
  return '이번 달 통계';
});

// 월 레이블
const monthLabel = computed(() => {
  if (props.displayYear && props.displayMonth) {
    return `${props.displayYear}년 ${props.displayMonth}월`;
  }
  return '이번 달';
});
```

#### 선택된 월 기준 데이터 로드
```typescript
async function loadJobSummary() {
  // displayYear/displayMonth가 제공되면 해당 월, 없으면 현재 월
  if (props.displayYear && props.displayMonth) {
    monthStr = `${props.displayYear}-${String(props.displayMonth).padStart(2, '0')}`;
  } else {
    const today = new Date();
    monthStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
  }
  
  const res = await apiClient.get(`/labor/jobs/${employeeId}/monthly-summary/`, {
    params: { month: monthStr }
  });
}
```

#### Props 변경 감지
```typescript
// displayYear, displayMonth 중 하나라도 변경되면 재로드
watch([() => props.activeJob?.id, () => props.displayYear, () => props.displayMonth], () => {
  if (props.activeJob) {
    loadJobSummary();
  }
}, { immediate: true });
```

### 3. MainDashboard.vue

#### 상태 추가
```typescript
// 캘린더에서 선택된 연/월을 추적
const selectedYear = ref<number | undefined>(undefined);
const selectedMonth = ref<number | undefined>(undefined);
```

#### 이벤트 핸들러
```typescript
// 캘린더에서 월이 변경될 때 호출
function handleMonthChanged(data: { year: number; month: number }) {
  selectedYear.value = data.year;
  selectedMonth.value = data.month;
}
```

#### Props 전달
```vue
<WorkCalendar 
  :activeJob="activeJob" 
  @statsUpdated="handleStatsUpdated"
  @monthChanged="handleMonthChanged" 
/>

<WorkSummaryCard 
  ref="workSummaryCardRef" 
  :activeJob="activeJob" 
  :displayYear="selectedYear"
  :displayMonth="selectedMonth"
/>
```

### 4. DashboardContent.vue

MainDashboard.vue와 동일한 방식으로 수정되었습니다.

## 데이터 흐름

```
┌─────────────────┐
│ WorkCalendar    │
│ (currentYear,   │
│  currentMonth)  │
└────────┬────────┘
         │ emit('monthChanged', { year, month })
         ▼
┌─────────────────┐
│ MainDashboard/  │
│ DashboardContent│
│ (selectedYear,  │
│  selectedMonth) │
└────────┬────────┘
         │ :displayYear, :displayMonth
         ▼
┌─────────────────┐
│ WorkSummaryCard │
│ - 동적 제목     │
│ - 선택된 월     │
│   기준 통계     │
└─────────────────┘
```

## 사용자 시나리오

### 시나리오 1: 과거 월 조회
1. 사용자가 캘린더 ◀ 버튼을 클릭하여 2024년 10월로 이동
2. 캘린더가 2024년 10월 표시
3. 통계 카드 제목이 "2024년 10월 통계"로 변경
4. 통계 카드에 2024년 10월 데이터 표시 (총 근로시간, 급여, 근로일수)

### 시나리오 2: 현재 월 조회
1. 사용자가 캘린더 ▶ 버튼을 클릭하여 현재 월(2025년 12월)로 이동
2. 캘린더가 2025년 12월 표시
3. 통계 카드 제목이 "2025년 12월 통계"로 변경
4. 통계 카드에 2025년 12월 데이터 표시

### 시나리오 3: 근로기록 수정
1. 사용자가 캘린더에서 특정 날짜 클릭하여 근로기록 수정
2. 근로기록 저장 시 `statsUpdated` 이벤트 발생
3. 통계 카드가 **현재 보고 있는 월** 기준으로 자동 갱신
4. 캘린더와 통계가 항상 동기화 유지

## 기술적 세부사항

### 이벤트 시스템
- `monthChanged`: 캘린더 월이 변경될 때 부모에게 알림
- `statsUpdated`: 근로기록이 변경될 때 통계 갱신 트리거

### Props Drilling
```
WorkCalendar → MainDashboard → WorkSummaryCard
(emit event)   (store state)   (receive props)
```

### Reactivity Chain
1. WorkCalendar의 `currentYear/currentMonth` 변경
2. `watch` 감지 → `emit('monthChanged')`
3. MainDashboard의 `selectedYear/selectedMonth` 업데이트
4. WorkSummaryCard의 `watch` 감지 → `loadJobSummary()` 호출
5. API 요청 → 통계 데이터 갱신

## 테스트 방법

1. **월 변경 테스트**
   - 캘린더에서 ◀/▶ 버튼으로 월 변경
   - 통계 카드 제목이 동적으로 변경되는지 확인
   - 통계 데이터가 해당 월 기준으로 표시되는지 확인

2. **근로기록 수정 테스트**
   - 특정 날짜의 근로기록 추가/수정/삭제
   - 통계 카드가 현재 보고 있는 월 기준으로 갱신되는지 확인

3. **여러 근로자 테스트**
   - 근로자 전환 시 통계가 올바르게 로드되는지 확인
   - 각 근로자마다 독립적인 통계가 표시되는지 확인

## 제한사항 및 고려사항

### 현재 구현
✅ 캘린더 선택 월 = 통계 기준 월 (완전 동기화)
✅ 동적 제목으로 현재 보는 월 명확히 표시
✅ 월 이동 시 자동 갱신

### 향후 개선 가능 사항
- 여러 월의 통계를 한눈에 비교하는 기능
- 월별 통계 그래프 시각화
- 연간 누적 통계 표시 옵션
- 통계 데이터 CSV 내보내기

## 관련 파일

- `frontend/src/components/WorkCalendar.vue`
- `frontend/src/components/WorkSummaryCard.vue`
- `frontend/src/components/MainDashboard.vue`
- `frontend/src/components/DashboardContent.vue`

## 이전 문서와의 관계

이 기능은 다음 문서들과 함께 작동합니다:
- `MONTHLY_SCHEDULE_FEATURE.md`: 월별 스케줄 오버라이드 기능
- `CUMULATIVE_STATS_FIX.md`: 누적 통계 계산 로직 개선

이 세 가지 기능이 함께 작동하여 사용자에게 정확하고 직관적인 근로 관리 경험을 제공합니다.
