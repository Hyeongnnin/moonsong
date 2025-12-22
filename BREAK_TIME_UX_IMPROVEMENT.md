# 휴게시간 입력 UX 개선 및 급여 계산 반영

## 📋 개요

주간 스케줄과 월별 스케줄 변경 화면의 휴게시간 입력 UX를 개선하여 각 요일 행에서 근무시간과 함께 휴게시간을 직관적으로 입력할 수 있도록 변경했습니다.

### 개선 전 문제점
- 월별 스케줄: 휴게시간이 별도 섹션에 입력 (요일별 0~6 입력 박스)
- 근무시간 입력 영역과 분리되어 혼란 야기
- 실수로 입력 누락 가능성 높음
- 주간 스케줄: 휴게시간 입력 기능 없음

### 개선 후
- ✅ 각 요일 행에서 시간 입력 옆에 휴게시간 입력 필드 배치
- ✅ 근무시간과 휴게시간을 한 눈에 확인 가능
- ✅ 주간/월별 스케줄 모두 동일한 UX 적용
- ✅ 스케줄 저장 시 WorkRecord에 자동 반영
- ✅ 급여/통계 계산에 정확히 반영

## 📂 변경된 파일

### 데이터베이스 (마이그레이션)
**`labor/migrations/0013_remove_monthlyschedule_default_break_minutes_by_weekday_and_more.py`**
```python
operations = [
    migrations.RemoveField(
        model_name='monthlyschedule',
        name='default_break_minutes_by_weekday',
    ),
    migrations.AddField(
        model_name='monthlyschedule',
        name='break_minutes',
        field=models.IntegerField(default=0, help_text='휴게 시간 (분)'),
    ),
    migrations.AddField(
        model_name='workschedule',
        name='break_minutes',
        field=models.IntegerField(default=0, help_text='휴게 시간 (분)'),
    ),
]
```

### 백엔드 모델 (3개 파일)

#### 1. `labor/models.py`
**변경 내용:**
- `WorkSchedule` 모델에 `break_minutes` 필드 추가
- `MonthlySchedule` 모델에 `break_minutes` 필드 추가
- `default_break_minutes_by_weekday` JSON 필드 제거 (더 이상 불필요)

```python
class WorkSchedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_overnight = models.BooleanField(default=False)
    next_day_work_minutes = models.IntegerField(default=0)
    break_minutes = models.IntegerField(default=0, help_text="휴게 시간 (분)")  # 추가
    enabled = models.BooleanField(default=True)

class MonthlySchedule(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='monthly_schedules')
    year = models.IntegerField()
    month = models.IntegerField()
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    is_overnight = models.BooleanField(default=False)
    next_day_work_minutes = models.IntegerField(default=0)
    break_minutes = models.IntegerField(default=0, help_text="휴게 시간 (분)")  # 추가
    enabled = models.BooleanField(default=True)
    weekly_rest_day = models.IntegerField(null=True, blank=True, choices=WEEKDAY_CHOICES)
    # default_break_minutes_by_weekday 필드 제거됨
```

#### 2. `labor/serializers.py`
**변경 내용:**
- `WorkScheduleSerializer`에 `break_minutes` 필드 추가
- `MonthlyScheduleSerializer`에 `break_minutes` 필드 추가
- `default_break_minutes_by_weekday` 필드 제거

```python
class WorkScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkSchedule
        fields = [
            'id', 'weekday', 'weekday_display', 'start_time', 'end_time', 
            'is_overnight', 'next_day_work_minutes', 'break_minutes', 'enabled'
        ]

class MonthlyScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlySchedule
        fields = [
            'id', 'year', 'month', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'is_overnight', 'next_day_work_minutes', 
            'break_minutes', 'enabled', 'weekly_rest_day'
        ]
```

#### 3. `labor/views.py`
**변경 내용:**

**schedules() 엔드포인트 (주간 스케줄):**
```python
# POST 요청 처리
data = request.data
weekday = int(data.get('weekday'))
start_time = data.get('start_time')
end_time = data.get('end_time')
is_overnight = data.get('is_overnight', False)
next_day_work_minutes = int(data.get('next_day_work_minutes', 0))
break_minutes = int(data.get('break_minutes', 0))  # 추가
enabled = data.get('enabled', 'true') in ['1', 'true', True, 'True']

# WorkSchedule 생성/업데이트
schedule, created = job.schedules.get_or_create(weekday=weekday, defaults={
    'start_time': start_time or None,
    'end_time': end_time or None,
    'is_overnight': is_overnight,
    'next_day_work_minutes': next_day_work_minutes,
    'break_minutes': break_minutes,  # 추가
    'enabled': enabled,
})

# WorkRecord 자동 생성 시 반영
WorkRecord.objects.create(
    employee=job,
    work_date=current_date,
    time_in=time_in_dt,
    time_out=time_out_dt,
    is_overnight=schedule.is_overnight,
    next_day_work_minutes=schedule.next_day_work_minutes,
    break_minutes=schedule.break_minutes  # 스케줄의 휴게시간 반영
)
```

**monthly_schedule_override() 엔드포인트:**
```python
# POST 요청 처리
for schedule_data in schedules_data:
    weekday = schedule_data.get('weekday')
    start_time_str = schedule_data.get('start_time')
    end_time_str = schedule_data.get('end_time')
    enabled = schedule_data.get('enabled', True)
    is_overnight = schedule_data.get('is_overnight', False)
    next_day_work_minutes = int(schedule_data.get('next_day_work_minutes', 0))
    break_minutes = int(schedule_data.get('break_minutes', 0))  # 추가

    # MonthlySchedule 생성
    monthly_schedule = MonthlySchedule.objects.create(
        employee=job,
        year=year,
        month=month,
        weekday=weekday,
        start_time=start_time_obj,
        end_time=end_time_obj,
        is_overnight=is_overnight,
        next_day_work_minutes=next_day_work_minutes,
        break_minutes=break_minutes,  # 추가
        enabled=enabled,
        weekly_rest_day=weekly_rest_day
    )

    # WorkRecord 자동 생성 시 반영
    WorkRecord.objects.create(
        employee=job,
        work_date=work_date,
        time_in=time_in_dt,
        time_out=time_out_dt,
        is_overnight=schedule.is_overnight,
        next_day_work_minutes=schedule.next_day_work_minutes,
        break_minutes=schedule.break_minutes  # 월별 스케줄의 휴게시간 반영
    )
```

### 프론트엔드 (2개 파일)

#### 1. `frontend/src/components/WeeklyScheduleEditor.vue`
**변경 내용:**
- 각 요일 행에 휴게시간 입력 필드 추가
- `localSchedules` 타입에 `break_minutes` 필드 추가
- `loadSchedules()`: 스케줄 로드 시 break_minutes 포함
- `saveSchedules()`: 저장 시 break_minutes 전송 및 밸리데이션 (0~480분)

**UI 구조:**
```vue
<template>
  <div v-for="d in weekdays" :key="d.value" class="border rounded-lg p-3 bg-gray-50">
    <div class="flex items-center gap-3 mb-2">
      <div class="w-20 text-sm font-medium">{{ d.label }}</div>
      
      <!-- 시작 시간 -->
      <TimeSelect v-model="localSchedules[d.value].start_time" />
      
      <span class="text-xs text-gray-400">~</span>
      
      <!-- 종료 시간 -->
      <TimeSelect v-model="localSchedules[d.value].end_time" />
      
      <!-- 휴게시간 입력 (NEW) -->
      <div class="flex items-center gap-1">
        <span class="text-xs text-gray-500">휴게</span>
        <input
          type="number"
          v-model.number="localSchedules[d.value].break_minutes"
          min="0"
          max="480"
          :disabled="!localSchedules[d.value].enabled"
          class="w-16 px-2 py-1 text-sm border rounded"
          placeholder="0"
        />
        <span class="text-xs text-gray-500">분</span>
      </div>
      
      <label class="ml-2">
        <input type="checkbox" v-model="localSchedules[d.value].enabled" />
        일하는 날
      </label>
    </div>
    
    <!-- 익일 근무 섹션은 그대로 유지 -->
    <div v-if="localSchedules[d.value].enabled">
      <!-- 익일 근무 입력 -->
    </div>
  </div>
</template>

<script setup lang="ts">
// 타입 정의
const localSchedules = reactive<Record<number, { 
  start_time: string | null, 
  end_time: string | null, 
  enabled: boolean,
  has_next_day_work: boolean,
  next_day_work_minutes: number,
  break_minutes: number  // 추가
}>>({
  0: { start_time: null, end_time: null, enabled: false, 
       has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  // ... 나머지 요일
})

// 로드 시 break_minutes 포함
async function loadSchedules() {
  const res = await apiClient.get(`/labor/jobs/${props.employeeId}/schedules/`)
  for (const s of res.data) {
    const idx = parseInt(s.weekday)
    localSchedules[idx] = { 
      start_time: roundToNearest30(s.start_time), 
      end_time: roundToNearest30(s.end_time), 
      enabled: !!s.enabled,
      has_next_day_work: (s.next_day_work_minutes || 0) > 0,
      next_day_work_minutes: s.next_day_work_minutes || 0,
      break_minutes: s.break_minutes || 0  // 추가
    }
  }
}

// 저장 시 밸리데이션 및 전송
async function saveSchedules() {
  const requests = weekdays.map(w => {
    const schedule = localSchedules[w.value]
    const breakMinutes = schedule.break_minutes || 0
    
    // 밸리데이션: 0~480분 (8시간)
    if (breakMinutes < 0 || breakMinutes > 480) {
      throw new Error(`휴게시간은 0~480분 사이여야 합니다. (현재: ${breakMinutes}분)`)
    }
    
    const payload = {
      weekday: w.value,
      start_time: schedule.enabled ? schedule.start_time : null,
      end_time: schedule.enabled ? schedule.end_time : null,
      is_overnight: isOvernight,
      next_day_work_minutes: nextDayMinutes,
      break_minutes: breakMinutes,  // 추가
      enabled: schedule.enabled,
    }
    return apiClient.post(`/labor/jobs/${targetEmployeeId}/schedules/`, payload)
  })
  
  await Promise.all(requests)
}
</script>
```

#### 2. `frontend/src/components/MonthlyScheduleModal.vue`
**변경 내용:**
- 별도 휴게시간 입력 섹션 제거 (`defaultBreaks` reactive 객체 삭제)
- 각 요일 행에 휴게시간 입력 필드 추가
- 안내 문구 변경: "각 요일의 휴게시간은 아래 근무시간 입력란에서 개별 설정할 수 있습니다."

**UI 구조 (WeeklyScheduleEditor와 동일):**
```vue
<template>
  <!-- 주휴일 설정 섹션 -->
  <div class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
    <div>
      <label>주휴일 요일</label>
      <select v-model="weeklyRestDay">
        <option :value="null">선택 없음</option>
        <option v-for="d in weekdays">{{ d.label }}</option>
      </select>
    </div>
    <div class="text-sm text-gray-600 flex items-center">
      각 요일의 휴게시간은 아래 근무시간 입력란에서 개별 설정할 수 있습니다.
    </div>
  </div>

  <!-- 스케줄 입력 (요일별) -->
  <div class="space-y-3">
    <div v-for="d in weekdays" :key="d.value" class="border rounded-lg p-3 bg-white">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-16 text-sm font-medium">{{ d.label }}</div>
        
        <TimeSelect v-model="localSchedules[d.value].start_time" />
        <span>~</span>
        <TimeSelect v-model="localSchedules[d.value].end_time" />
        
        <!-- 휴게시간 입력 -->
        <div class="flex items-center gap-1">
          <span class="text-xs text-gray-500">휴게</span>
          <input
            type="number"
            v-model.number="localSchedules[d.value].break_minutes"
            min="0"
            max="480"
            :disabled="!localSchedules[d.value].enabled"
            class="w-16 px-2 py-1 text-sm border rounded"
            placeholder="0"
          />
          <span class="text-xs text-gray-500">분</span>
        </div>
        
        <label><input type="checkbox" v-model="localSchedules[d.value].enabled" /> 활성</label>
      </div>
      
      <!-- 익일 근무 섹션 -->
    </div>
  </div>
</template>

<script setup lang="ts">
// 타입 정의 (break_minutes 추가)
interface ScheduleData {
  enabled: boolean
  start_time: string
  end_time: string
  has_next_day_work: boolean
  next_day_work_minutes: number
  break_minutes: number  // 추가
}

// defaultBreaks reactive 객체 제거됨

// 로드 시 break_minutes 포함
async function loadSchedules() {
  const response = await apiClient.get(
    `/labor/employees/${props.employeeId}/monthly-schedule-override/`,
    { params: { year: props.year, month: props.month } }
  )
  
  const schedules = response.data.schedules || []
  schedules.forEach((schedule: any) => {
    const weekday = schedule.weekday
    localSchedules[weekday] = {
      enabled: schedule.enabled ?? false,
      start_time: schedule.start_time || '09:00',
      end_time: schedule.end_time || '18:00',
      has_next_day_work: (schedule.next_day_work_minutes || 0) > 0,
      next_day_work_minutes: schedule.next_day_work_minutes || 0,
      break_minutes: schedule.break_minutes || 0  // 추가
    }
  })
}

// 저장 시 밸리데이션 및 전송
async function saveSchedules() {
  const schedulesArray = Object.entries(localSchedules).map(([weekday, data]) => {
    const breakMinutes = data.break_minutes || 0
    
    // 밸리데이션
    if (breakMinutes < 0 || breakMinutes > 480) {
      throw new Error(`휴게시간은 0~480분 사이여야 합니다. (현재: ${breakMinutes}분)`)
    }
    
    return {
      weekday: parseInt(weekday),
      start_time: data.enabled ? data.start_time : null,
      end_time: data.enabled ? endTime : null,
      is_overnight: isOvernight,
      next_day_work_minutes: nextDayMinutes,
      break_minutes: breakMinutes,  // 추가
      enabled: data.enabled
    }
  })
  
  const response = await apiClient.post(
    `/labor/employees/${props.employeeId}/monthly-schedule-override/`,
    {
      year: props.year,
      month: props.month,
      schedules: schedulesArray,
      weekly_rest_day: weeklyRestDay.value
      // default_break_minutes_by_weekday 제거됨
    }
  )
}
</script>
```

## 🔄 데이터 흐름

### 1. 주간 스케줄 저장 흐름
```
사용자 입력 (WeeklyScheduleEditor)
  ↓
월요일: 09:00 ~ 18:00, 휴게 60분
  ↓
API 요청: POST /api/labor/jobs/{id}/schedules/
{
  weekday: 0,
  start_time: "09:00",
  end_time: "18:00",
  break_minutes: 60,
  enabled: true
}
  ↓
WorkSchedule 모델 저장
  ↓
과거 날짜 WorkRecord 자동 생성/업데이트
  - break_minutes: 60 포함
  ↓
총 근로시간 계산:
  (18:00 - 09:00) - 60분 = 8시간
  ↓
급여 계산: 8시간 × 시급
```

### 2. 월별 스케줄 저장 흐름
```
사용자 입력 (MonthlyScheduleModal)
  ↓
2025년 1월 화요일: 10:00 ~ 19:00, 휴게 90분
  ↓
API 요청: POST /api/labor/employees/{id}/monthly-schedule-override/
{
  year: 2025,
  month: 1,
  schedules: [
    {
      weekday: 1,
      start_time: "10:00",
      end_time: "19:00",
      break_minutes: 90,
      enabled: true
    }
  ]
}
  ↓
MonthlySchedule 모델 저장
  ↓
해당 월의 WorkRecord 자동 생성/업데이트
  - break_minutes: 90 포함
  ↓
총 근로시간 계산:
  (19:00 - 10:00) - 90분 = 7.5시간
  ↓
급여 계산: 7.5시간 × 시급
```

### 3. 급여 계산 로직

**WorkRecord.get_total_hours() 메소드**는 이미 break_minutes를 정확히 반영합니다:

```python
def get_total_hours(self):
    """실제 근로시간 (break 제외, 익일 근무 포함)"""
    if not self.time_in or not self.time_out:
        return Decimal('0')

    # 1. 기본 근로 시간 계산
    duration = self.time_out - self.time_in
    total_minutes = duration.total_seconds() / 60.0

    # 2. 휴게 시간 제외 (스케줄에서 자동 반영됨)
    break_total = float(self.break_minutes or 0)
    work_minutes = max(0.0, total_minutes - break_total)
    
    # 3. 익일 추가 근무 시간 합산
    next_day_minutes = float(self.next_day_work_minutes or 0)
    total_work_minutes = work_minutes + next_day_minutes
    
    return Decimal(str(total_work_minutes / 60.0))
```

**계산 예시:**
```
근무 시간: 09:00 ~ 18:00 (9시간 = 540분)
휴게 시간: 60분 (스케줄에서 설정)
익일 근무: 0분

계산:
- 기본 근로: 540분
- 휴게 제외: 540분 - 60분 = 480분
- 익일 근무 추가: 480분 + 0분 = 480분
- 최종 근로시간: 480분 ÷ 60 = 8시간

급여 계산:
- 시급: 10,000원
- 일 급여: 8시간 × 10,000원 = 80,000원
```

## ✅ 개선 사항 요약

### UI/UX 개선
1. **직관성 향상**
   - 근무시간과 휴게시간을 한 줄에 입력
   - 시각적으로 연관성 명확

2. **일관성**
   - 주간 스케줄과 월별 스케줄 동일한 UI
   - 학습 비용 감소

3. **실수 방지**
   - 별도 섹션 제거로 입력 누락 방지
   - 요일별 휴게시간 한 번에 확인 가능

### 데이터 정확성
1. **자동 반영**
   - 스케줄 저장 시 과거 WorkRecord에 자동 반영
   - 수동 입력 필요 없음

2. **우선순위 명확**
   - 일별 기록 > 월별 스케줄 > 주간 스케줄
   - break_minutes도 동일한 우선순위 적용

3. **급여 계산 정확성**
   - WorkRecord.get_total_hours()에서 자동 차감
   - 모든 통계/급여 계산에 즉시 반영

### 개발 효율성
1. **데이터 모델 단순화**
   - `default_break_minutes_by_weekday` JSON 필드 제거
   - 각 스케줄 모델에 직접 `break_minutes` 필드 사용

2. **유지보수 용이**
   - 프론트엔드 코드 간소화
   - 백엔드 로직 단순화

## 🧪 테스트 시나리오

### 1. 주간 스케줄 휴게시간 설정
```
1. 근로정보 수정 화면 진입
2. 주간 근무 스케줄 탭 선택
3. 월요일 설정:
   - 시작: 09:00
   - 종료: 18:00
   - 휴게: 60분
   - 일하는 날: 체크
4. 저장 버튼 클릭
5. 확인:
   - 과거 월요일 WorkRecord에 break_minutes=60 반영
   - 총 근로시간: 8시간 (9시간 - 1시간)
   - 급여: 8시간 × 시급
```

### 2. 월별 스케줄 휴게시간 변경
```
1. 캘린더에서 "이달만 스케줄 변경" 클릭
2. 2025년 1월 선택
3. 화요일 설정:
   - 시작: 10:00
   - 종료: 19:00
   - 휴게: 90분
   - 활성: 체크
4. 저장 버튼 클릭
5. 확인:
   - 1월의 모든 화요일에 break_minutes=90 반영
   - 총 근로시간: 7.5시간 (9시간 - 1.5시간)
   - 다른 월에는 영향 없음
```

### 3. 휴게시간 밸리데이션
```
1. 주간/월별 스케줄에서 휴게시간 입력
2. 테스트:
   - -10분 입력 → "휴게시간은 0~480분 사이여야 합니다" 에러
   - 500분 입력 → 동일 에러
   - 0분 입력 → 정상 저장 (휴게 없음)
   - 480분 입력 → 정상 저장 (최대 8시간)
```

### 4. 급여 계산 정확성
```
시나리오: 다양한 휴게시간 패턴

월요일: 09:00~18:00, 휴게 60분 → 8시간
화요일: 10:00~20:00, 휴게 90분 → 8.5시간
수요일: 13:00~22:00, 휴게 120분 → 7시간

월 총 근로시간: 23.5시간
시급 10,000원일 경우 월급: 235,000원
```

## 📝 주의사항

### 개발 시 유의사항
1. **마이그레이션 순서**
   - 반드시 마이그레이션 적용 후 프론트엔드 배포
   - 기존 스케줄의 break_minutes는 0으로 초기화됨

2. **기존 데이터**
   - 기존 WorkRecord의 break_minutes는 유지됨
   - 스케줄 재저장 시에만 새 값으로 업데이트됨

3. **밸리데이션**
   - 프론트: 0~480분 (입력 시)
   - 백엔드: 동일한 범위 체크 (향후 추가 가능)

### 운영 시 유의사항
1. **스케줄 변경 영향**
   - 주간 스케줄 변경 시 과거 모든 WorkRecord 업데이트
   - 월별 스케줄 변경 시 해당 월만 업데이트

2. **일별 기록 우선**
   - 특정 날짜만 다르면 캘린더에서 직접 수정 권장
   - 일별 수정은 스케줄에 영향받지 않음

3. **휴게시간 입력 권장**
   - 근로기준법상 4시간당 30분 이상 휴게 권장
   - 8시간 근무 시 60분 이상 입력 권장

## 🔗 관련 문서
- [OVERNIGHT_WORK_SCHEDULE_FEATURE.md](./OVERNIGHT_WORK_SCHEDULE_FEATURE.md) - 익일 근무 기능
- [SCHEDULE_VS_WORKRECORD_FIX.md](./SCHEDULE_VS_WORKRECORD_FIX.md) - 스케줄/기록 우선순위
- [FEATURE_GUIDE.md](./FEATURE_GUIDE.md) - 전체 기능 가이드

---

**작업 완료일**: 2025-12-20  
**버전**: 1.0.0  
**작성자**: GitHub Copilot
