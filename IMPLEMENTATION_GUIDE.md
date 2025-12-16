# 근로 관리 시스템 기능 구현 완료 문서

## 📋 구현 개요

주간 근무 스케줄을 기반으로 캘린더에 자동 표시하고, 개별 날짜의 근로기록 추가/수정/삭제 시 실시간으로 통계가 업데이트되는 시스템을 구현했습니다.

---

## 🎯 구현된 주요 기능

### 1. 날짜별 근로기록 추가/변경 시 즉시 반영 + 통계 갱신

**동작 방식:**
- 캘린더에서 날짜 클릭 → 근로기록 모달 표시
- 출근/퇴근시간 입력 후 "저장" 클릭
- **현재 페이지(근로관리)에 그대로 유지**
- 저장한 날짜가 주황색으로 즉시 표시
- 오른쪽 통계 카드(총 근로시간, 급여 예상액, 이번 주 근로시간) 즉시 갱신

**구현 위치:**

#### 백엔드 (Django)
- **파일:** `labor/views.py`
- **클래스:** `WorkRecordViewSet`
- **메서드:**
  - `create()`: 근로기록 생성 후 최신 통계 반환
  - `update()`: 근로기록 수정 후 최신 통계 반환
  - `destroy()`: 근로기록 삭제 후 최신 통계 반환

```python
def create(self, request, *args, **kwargs):
    """근로기록 생성 후 최신 통계 반환"""
    response = super().create(request, *args, **kwargs)
    
    work_record = WorkRecord.objects.get(id=response.data['id'])
    employee = work_record.employee
    year = work_record.work_date.year
    month = work_record.work_date.month
    
    from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
    
    # 최신 통계 계산
    stats = compute_monthly_schedule_stats(employee, year, month)
    dates = monthly_scheduled_dates(employee, year, month)
    
    # 응답에 통계 추가
    response.data['stats'] = stats
    response.data['dates'] = dates
    
    return response
```

- **파일:** `labor/services.py`
- **함수:** `compute_monthly_schedule_stats(employee, year, month)`
  - 실제 근로기록과 스케줄을 모두 계산하여 통합 통계 반환
  - 실제 근로기록이 있는 날은 스케줄 대신 실제 기록 우선 사용
  - 야간 근무(overnight shifts) 처리 로직 포함

```python
def compute_monthly_schedule_stats(employee, year, month):
    """
    월별 근무 스케줄 통계 계산
    - 실제 근로기록 우선 반영
    - 스케줄은 실제 근로일을 제외한 날짜에만 적용
    """
    # ... 실제 근무 기록 조회
    work_records = WorkRecord.objects.filter(...)
    worked_dates = {wr.work_date for wr in work_records}
    
    # 실제 근무 시간
    actual_hours_worked = sum(float(wr.get_total_hours()) for wr in work_records)
    
    # 스케줄 기반 예상 시간 (실제 근무일 제외)
    for date in month_dates:
        if date not in worked_dates and has_schedule(date):
            total_scheduled_hours += calculate_hours(schedule)
    
    return {
        'scheduled_total_hours': actual_hours + scheduled_hours,
        'scheduled_estimated_salary': total_hours * hourly_rate,
        ...
    }
```

#### 프론트엔드 (Vue 3)
- **파일:** `frontend/src/components/WorkDayModal.vue`
- **변경사항:**
  - `onSave()` 함수 수정: 응답 데이터를 emit으로 전달
  - 저장 성공 시 `emit('saved', response.data)` 호출

```typescript
async function onSave() {
  // ... 저장 로직
  
  let response
  if (props.record && props.record.id) {
    response = await apiClient.patch(`/labor/work-records/${props.record.id}/`, payload)
  } else {
    response = await apiClient.post('/labor/work-records/', payload)
  }
  
  // 응답에서 최신 통계 데이터를 받아서 emit
  emit('saved', response.data)
  close()
}
```

- **파일:** `frontend/src/components/WorkCalendar.vue`
- **변경사항:**
  - `onModalSaved()` 함수: 응답 데이터로 캘린더 즉시 갱신
  - 부모 컴포넌트에 통계 업데이트 이벤트 emit

```typescript
function onModalSaved(responseData?: any) {
  modalVisible.value = false;
  modalRecord.value = null;
  
  // 응답 데이터에 최신 통계가 있으면 사용
  if (responseData && responseData.dates && responseData.stats) {
    calendarData.value = responseData.dates;  // 캘린더 즉시 갱신
    emit('statsUpdated', responseData.stats);  // 통계 업데이트
  } else {
    loadCalendar();
    emit('statsUpdated');
  }
}
```

- **파일:** `frontend/src/components/WorkSummaryCard.vue`
- **변경사항:**
  - `updateStats()` 메서드 추가: 외부에서 통계 갱신 호출 가능
  - `defineExpose({ updateStats })` 로 메서드 노출

```typescript
function updateStats(stats?: any) {
  if (stats) {
    monthlyTotalHours.value = stats.scheduled_total_hours || 0;
    monthlyEstimatedSalary.value = stats.scheduled_estimated_salary || 0;
    weeklyHours.value = stats.scheduled_this_week_hours || 0;
    // ... 통계 값 즉시 업데이트
  } else {
    loadJobSummary();  // API 재호출
  }
}

defineExpose({ updateStats });
```

- **파일:** `frontend/src/components/DashboardContent.vue`
- **변경사항:**
  - `WorkCalendar`의 `@statsUpdated` 이벤트 리스닝
  - `WorkSummaryCard` ref로 접근하여 `updateStats()` 호출

```typescript
<WorkCalendar :activeJob="activeJob" @statsUpdated="handleStatsUpdate" />
<WorkSummaryCard ref="summaryCardRef" :activeJob="activeJob" />

function handleStatsUpdate(stats?: any) {
  if (summaryCardRef.value) {
    summaryCardRef.value.updateStats(stats);
  }
}
```

---

### 2. 주황색 근로일의 기본 출퇴근 시간 자동 세팅

**동작 방식:**
- 주간 근무 스케줄에 설정된 요일(예: 매주 목요일 13:00~19:00)
- 해당 요일의 날짜 클릭 시 모달에 기본값 자동 입력
- 사용자가 원하면 수정 가능 (입력 편의용 프리셋)

**구현 위치:**

#### 백엔드
- **파일:** `labor/views.py`
- **클래스:** `EmployeeViewSet`
- **메서드:** `date_schedule()` - 새로운 API 엔드포인트

```python
@action(detail=True, methods=['get'], url_path='date-schedule')
def date_schedule(self, request, pk=None):
    """특정 날짜의 기본 스케줄 정보 반환"""
    job = self.get_object()
    date_str = request.query_params.get('date')
    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    # 해당 날짜의 요일 확인
    weekday = target_date.weekday()  # 0=월요일
    
    # 해당 요일의 스케줄 조회
    schedule = job.schedules.filter(weekday=weekday, enabled=True).first()
    
    # 실제 근로기록 조회
    work_record = job.work_records.filter(work_date=target_date).first()
    
    return Response({
        'has_schedule': schedule is not None,
        'start_time': schedule.start_time.strftime('%H:%M') if schedule else None,
        'end_time': schedule.end_time.strftime('%H:%M') if schedule else None,
        'work_record': WorkRecordSerializer(work_record).data if work_record else None,
    })
```

**API 엔드포인트:**
```
GET /api/labor/jobs/<id>/date-schedule/?date=YYYY-MM-DD

응답:
{
  "has_schedule": true,
  "start_time": "13:00",
  "end_time": "19:00",
  "work_record": { ... } or null
}
```

#### 프론트엔드
- **파일:** `frontend/src/components/WorkDayModal.vue`
- **변경사항:**
  - `loadDefaultSchedule()` 함수 추가
  - 모달이 열릴 때 자동으로 기본 스케줄 로드
  - 실제 근로기록이 없고 스케줄만 있는 경우에만 기본값 설정

```typescript
async function loadDefaultSchedule() {
  if (!props.employeeId || !props.dateIso) return
  
  try {
    const res = await apiClient.get(`/labor/jobs/${props.employeeId}/date-schedule/`, {
      params: { date: props.dateIso }
    })
    
    hasSchedule.value = res.data.has_schedule
    
    // 실제 근로기록이 없고 스케줄만 있는 경우에만 기본값 설정
    if (!props.record && res.data.has_schedule) {
      timeIn.value = res.data.start_time      // "13:00"
      timeOut.value = res.data.end_time       // "19:00"
      breakMinutes.value = 60                 // 기본 휴게시간 60분
    }
  } catch (e) {
    console.error('Failed to load default schedule', e)
  }
}

// 모달이 열릴 때 자동 로드
watch(() => props.visible, async (isVisible) => {
  if (isVisible && props.employeeId) {
    await loadDefaultSchedule()
  }
}, { immediate: true })
```

---

### 3. 근로날짜 취소 기능 ("근로날짜 취소" 버튼)

**동작 방식:**
- 주황색 근로일 클릭 → 모달에 "근로날짜 취소" 버튼 표시
- 버튼 클릭 → confirm 팝업으로 확인
- 실제 근로기록 삭제 → 캘린더에서 주황색 제거
- 통계 카드에서 해당 날짜의 근로시간 제외하여 재계산

**구현 위치:**

#### 백엔드
- **파일:** `labor/views.py`
- **클래스:** `WorkRecordViewSet`
- **메서드:** `destroy()` 오버라이드

```python
def destroy(self, request, *args, **kwargs):
    """근로기록 삭제 후 최신 통계 반환"""
    instance = self.get_object()
    employee = instance.employee
    year = instance.work_date.year
    month = instance.work_date.month
    
    # 삭제 실행
    self.perform_destroy(instance)
    
    from .services import compute_monthly_schedule_stats, monthly_scheduled_dates
    
    # 최신 통계 계산 (해당 날짜 제외된 상태)
    stats = compute_monthly_schedule_stats(employee, year, month)
    dates = monthly_scheduled_dates(employee, year, month)
    
    return Response({
        'message': '근로기록이 삭제되었습니다.',
        'stats': stats,
        'dates': dates
    }, status=status.HTTP_200_OK)
```

#### 프론트엔드
- **파일:** `frontend/src/components/WorkDayModal.vue`
- **변경사항:**
  - UI에 "근로날짜 취소" 버튼 추가
  - `onCancelWorkDay()` 함수 추가

```vue
<template>
  <!-- ... -->
  <div class="mt-6 flex items-center justify-between gap-2">
    <button 
      @click="onCancelWorkDay" 
      v-if="hasWorkRecord || hasSchedule"
      class="px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
    >
      근로날짜 취소
    </button>
    <div class="flex gap-2 ml-auto">
      <button @click="close">취소</button>
      <button @click="onSave">저장</button>
    </div>
  </div>
</template>

<script setup lang="ts">
async function onCancelWorkDay() {
  // 실수 방지를 위한 confirm 팝업
  if (!confirm('정말 이 날짜의 근로를 취소하시겠습니까?\n실제 근로기록이 있다면 삭제됩니다.')) {
    return
  }
  
  try {
    if (props.record && props.record.id) {
      // 실제 근로기록이 있는 경우 삭제
      const response = await apiClient.delete(`/labor/work-records/${props.record.id}/`)
      emit('deleted', response.data)  // 최신 통계 전달
      close()
    } else {
      // 스케줄만 있고 실제 기록이 없는 경우
      alert('실제 근로기록이 없습니다. 주간 스케줄을 변경하려면 알바 편집 페이지에서 수정하세요.')
      close()
    }
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '취소 중 오류가 발생했습니다.'
  }
}
</script>
```

- **파일:** `frontend/src/components/WorkCalendar.vue`
- **변경사항:**
  - `onModalDeleted()` 함수: 삭제 응답 처리

```typescript
function onModalDeleted(responseData?: any) {
  modalVisible.value = false;
  modalRecord.value = null;
  
  // 응답 데이터에 최신 통계가 있으면 사용
  if (responseData && responseData.dates && responseData.stats) {
    calendarData.value = responseData.dates;  // 캘린더 갱신 (주황색 제거)
    emit('statsUpdated', responseData.stats);  // 통계 갱신
  } else {
    loadCalendar();
    emit('statsUpdated');
  }
}
```

---

## 🔄 데이터 흐름 (Data Flow)

### 근로기록 저장 시

```
사용자 입력 (WorkDayModal)
    ↓
POST /api/labor/work-records/
    ↓
Django: WorkRecordViewSet.create()
    ↓
근로기록 DB 저장
    ↓
compute_monthly_schedule_stats() 호출
    ↓
최신 통계 계산 (실제 기록 + 스케줄)
    ↓
Response { id, stats, dates }
    ↓
WorkDayModal.onSave() → emit('saved', response.data)
    ↓
WorkCalendar.onModalSaved() 
    ├─ calendarData.value = response.dates  (캘린더 갱신)
    └─ emit('statsUpdated', response.stats)
        ↓
DashboardContent.handleStatsUpdate()
    ↓
WorkSummaryCard.updateStats(stats)
    ↓
UI 즉시 업데이트 완료!
```

### 근로기록 삭제 시

```
사용자 클릭 (근로날짜 취소 버튼)
    ↓
confirm() 확인
    ↓
DELETE /api/labor/work-records/<id>/
    ↓
Django: WorkRecordViewSet.destroy()
    ↓
근로기록 DB 삭제
    ↓
compute_monthly_schedule_stats() 호출
    ↓
최신 통계 계산 (삭제된 날짜 제외)
    ↓
Response { message, stats, dates }
    ↓
(위와 동일한 흐름으로 UI 갱신)
```

---

## 📊 통계 계산 로직

### `compute_monthly_schedule_stats()` 핵심 로직

```python
def compute_monthly_schedule_stats(employee, year, month):
    # 1. 실제 근무 기록 조회
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )
    worked_dates = {wr.work_date for wr in work_records}
    
    # 2. 실제 근무 시간 계산
    actual_hours_worked = sum(float(wr.get_total_hours()) for wr in work_records)
    actual_work_days = len(worked_dates)
    
    # 3. 스케줄 기반 예상 시간 계산 (실제 근무일 제외)
    schedule_map = {s.weekday: s for s in schedules}
    total_scheduled_hours = 0
    scheduled_work_days = 0
    
    current_date = start_of_month
    while current_date <= end_of_month:
        # 실제 근무 기록이 없는 날만 스케줄 적용
        if current_date not in worked_dates and current_date.weekday() in schedule_map:
            schedule = schedule_map[current_date.weekday()]
            if schedule.start_time and schedule.end_time:
                # 시간 계산 (야간 근무 처리 포함)
                start_hour = schedule.start_time.hour + schedule.start_time.minute / 60
                end_hour = schedule.end_time.hour + schedule.end_time.minute / 60
                
                if end_hour <= start_hour:  # 야간 근무 (예: 23:00-06:00)
                    end_hour += 24
                
                duration_hours = end_hour - start_hour
                total_scheduled_hours += duration_hours
                scheduled_work_days += 1
        
        current_date += timedelta(days=1)
    
    # 4. 합산
    total_hours = actual_hours_worked + total_scheduled_hours
    total_days = actual_work_days + scheduled_work_days
    
    return {
        'scheduled_total_hours': total_hours,
        'scheduled_estimated_salary': total_hours * hourly_rate,
        'scheduled_work_days': total_days,
        'scheduled_this_week_hours': this_week_hours,
        'scheduled_this_week_estimated_salary': this_week_salary,
    }
```

### `monthly_scheduled_dates()` 핵심 로직

```python
def monthly_scheduled_dates(employee, year, month):
    schedules = WorkSchedule.objects.filter(employee=employee, enabled=True)
    
    # 실제 근무 기록 가져오기
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )
    worked_dates = {wr.work_date for wr in work_records}
    
    schedule_map = {s.weekday: s for s in schedules if s.start_time and s.end_time}
    
    scheduled_dates_data = []
    for dt in month_dates:
        if dt.month != month:
            continue
        
        # 실제 근무 기록이 있거나 스케줄에 있으면 표시
        is_scheduled = dt in worked_dates or dt.weekday() in schedule_map
        
        scheduled_dates_data.append({
            "date": dt.isoformat(),
            "is_scheduled": is_scheduled,
        })
    
    return scheduled_dates_data
```

---

## 🐛 버그 수정 내역

### 1. 날짜 시간대 이슈 (UTC vs 로컬 시간)
**문제:** `Date.toISOString()`이 UTC로 변환하면서 날짜가 하루 밀리는 현상
**해결:** 로컬 날짜 문자열 직접 생성

```typescript
// 기존 (버그)
const date = new Date(year, month, i);
days.push({ day: i, dateIso: date.toISOString().split('T')[0] });
// → 한국 시간대에서 "2025-12-04"가 "2025-12-03"로 변환됨

// 수정 후
const dateIso = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
days.push({ day: i, dateIso });
// → 정확한 로컬 날짜 문자열 생성
```

### 2. 임시 폴백 로직 제거
**문제:** 디버깅용 폴백 로직이 실제 데이터를 무시하고 월/화를 무조건 표시
**해결:** 실제 데이터만 사용하도록 수정

```typescript
// 기존 (버그)
const isMonOrTue = dayOfWeek === 1 || dayOfWeek === 2;
const result = fromData || isMonOrTue;  // 항상 월/화 표시

// 수정 후
const result = mapEntry?.is_scheduled === true;  // 실제 데이터만 사용
```

---

## 📝 API 엔드포인트 요약

### 기존 API
```
GET  /api/labor/jobs/<id>/monthly-schedule/?month=YYYY-MM
     → 월간 스케줄 날짜 목록 반환

GET  /api/labor/jobs/<id>/monthly-summary/?month=YYYY-MM
     → 월간 통계 (총 근로시간, 급여 등) 반환

POST /api/labor/work-records/
     → 근로기록 생성

PATCH /api/labor/work-records/<id>/
      → 근로기록 수정

DELETE /api/labor/work-records/<id>/
       → 근로기록 삭제
```

### 새로 추가된 API
```
GET  /api/labor/jobs/<id>/date-schedule/?date=YYYY-MM-DD
     → 특정 날짜의 기본 스케줄 정보 반환
     
     응답:
     {
       "has_schedule": true,
       "start_time": "13:00",
       "end_time": "19:00",
       "work_record": { ... } or null
     }
```

### 수정된 API (응답 형식 확장)
```
POST /api/labor/work-records/
     → 응답에 stats, dates 추가

PATCH /api/labor/work-records/<id>/
      → 응답에 stats, dates 추가

DELETE /api/labor/work-records/<id>/
       → 응답에 message, stats, dates 추가
```

---

## 🎨 UI/UX 개선사항

1. **"근로날짜 취소" 버튼 추가**
   - 위치: 모달 하단 왼쪽
   - 스타일: 빨간색 계열 (경고 의미)
   - Confirm 팝업으로 실수 방지

2. **통계 카드 재구성**
   - "이번 달 통계" 섹션: 총 근로시간, 급여 예상액, 총 근로일수
   - "이번 주 근로시간" 섹션: 주간 진행도 바, 이번 주 예상 급여
   - 기존의 "오늘 근무현황" 제거 (더 유용한 정보로 대체)

3. **실시간 업데이트**
   - 저장/삭제 즉시 캘린더 주황색 갱신
   - 페이지 리다이렉트 없이 현재 화면 유지
   - 통계 숫자 즉시 변경 (로딩 없이 부드러운 업데이트)

---

## ✅ 테스트 시나리오

### 시나리오 1: 근로기록 추가
1. 주간 스케줄에 "목요일 13:00-19:00" 설정
2. 캘린더에서 12월 12일(목) 클릭
3. 모달 열림 → 출근 13:00, 퇴근 19:00 자동 입력 확인
4. 퇴근시간을 20:00으로 수정
5. "저장" 클릭
6. **확인사항:**
   - 모달 닫힘, 페이지 유지
   - 12월 12일이 주황색으로 표시
   - "이번 달 총 근로시간" 증가
   - "이번 주 근로시간" 증가

### 시나리오 2: 근로기록 수정
1. 이미 저장된 12월 12일 클릭
2. 모달 열림 → 기존 데이터(13:00-20:00) 표시 확인
3. 퇴근시간을 21:00으로 수정
4. "저장" 클릭
5. **확인사항:**
   - 통계에서 1시간 추가 반영
   - 캘린더는 여전히 주황색 유지

### 시나리오 3: 근로날짜 취소
1. 12월 12일(근로기록 있음) 클릭
2. 모달에서 "근로날짜 취소" 버튼 표시 확인
3. 버튼 클릭 → confirm 팝업 표시
4. "확인" 클릭
5. **확인사항:**
   - 12월 12일 주황색 제거
   - "이번 달 총 근로시간" 감소
   - "이번 주 근로시간" 감소

### 시나리오 4: 스케줄만 있고 기록 없는 날
1. 12월 19일(목, 스케줄만 있음) 클릭
2. 모달 열림 → 기본값 13:00-19:00 확인
3. "근로날짜 취소" 버튼 클릭
4. **확인사항:**
   - "실제 근로기록이 없습니다" 알림 표시
   - 주황색 유지 (스케줄은 주간 편집에서 변경해야 함)

---

## 🚀 향후 개선 가능 사항

1. **실시간 동기화**
   - WebSocket으로 여러 디바이스 간 동기화

2. **일괄 처리**
   - 여러 날짜를 한 번에 추가/삭제

3. **통계 확장**
   - 주별/월별 차트 시각화
   - 전월 대비 증감률 표시
   - 연간 누적 통계

4. **알림 기능**
   - 출근 시간 알림
   - 주간 근로시간 40시간 초과 경고

5. **내보내기**
   - 월간 근로기록 PDF 출력
   - Excel 내보내기

---

## 📚 참고 자료

- Django REST Framework: https://www.django-rest-framework.org/
- Vue 3 Composition API: https://vuejs.org/guide/extras/composition-api-faq.html
- Python datetime 모듈: https://docs.python.org/3/library/datetime.html
- JavaScript Date 객체: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Date

---

**작성일:** 2025년 12월 8일  
**작성자:** GitHub Copilot  
**버전:** 1.0.0
