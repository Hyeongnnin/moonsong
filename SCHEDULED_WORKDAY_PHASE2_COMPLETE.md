# 소정근로일 중심 구조 개편 Phase 2 완료 보고서

## 📋 개요

Phase 1에서 구축한 데이터 구조를 기반으로, Phase 2에서는 **주휴수당과 연차 계산 로직을 소정근로일 개근 기준으로 전면 개편**했습니다.

## ✅ 완료된 작업

### 1. holiday_pay() 엔드포인트 개편

#### 변경 사항
**기존 (Phase 1):**
- 실제 근무 시간 15시간 기준으로만 판단
- 개근 여부는 체크하지 않음
- 실제 일한 시간만 집계

**개선 (Phase 2):**
- ✅ 소정근로일 개근 여부 확인
- ✅ `REGULAR_WORK` + `ANNUAL_LEAVE`만 출근 인정
- ✅ `EXTRA_WORK`, `ABSENT`, `SICK_LEAVE`는 개근 판단에서 제외
- ✅ 주 15시간 + 개근 모두 만족해야 지급

#### 계산 로직
```python
# 1. 해당 주의 소정근로일 목록 수집
scheduled_dates = [date for date in week_dates if is_scheduled_workday(date)]

# 2. 개근 여부 확인
perfect_attendance = True
for date in scheduled_dates:
    record = get_work_record(date)
    if not record:
        perfect_attendance = False  # 기록 없음 = 결근
        break
    if record.attendance_status not in ['REGULAR_WORK', 'ANNUAL_LEAVE']:
        perfect_attendance = False  # 추가근무/결근/병가는 불인정
        break

# 3. 조건 확인
if weekly_scheduled_hours >= 15 and perfect_attendance:
    holiday_pay = daily_avg_hours × hourly_rate
else:
    holiday_pay = 0
```

#### API 응답 변경
```json
// Phase 2 응답
{
  "amount": 12000,
  "hours": 8.0,
  "reason": "eligible",
  "weekly_scheduled_hours": 40.0,
  "scheduled_days_count": 5,
  "perfect_attendance": true,  // 새로 추가
  "attendance_details": [  // 새로 추가
    {
      "date": "2025-12-15",
      "is_scheduled": true,
      "attendance_status": "REGULAR_WORK",
      "is_attended": true,
      "hours": 8.0
    },
    {
      "date": "2025-12-16",
      "is_scheduled": true,
      "attendance_status": "ANNUAL_LEAVE",
      "is_attended": true,
      "hours": 0
    },
    {
      "date": "2025-12-17",
      "is_scheduled": true,
      "attendance_status": "ABSENT",
      "is_attended": false,  // 결근으로 주휴수당 미지급
      "hours": 0
    }
  ]
}
```

#### 사용 예시
```javascript
// 프론트엔드에서 사용
const holidayPayResponse = await fetch('/api/labor/employees/1/holiday-pay/?date=2025-12-20')
const data = await holidayPayResponse.json()

if (data.reason === 'not_perfect_attendance') {
  alert('이번 주는 개근하지 못해 주휴수당이 지급되지 않습니다.')
  console.log('결근/병가 날짜:', data.attendance_details.filter(d => !d.is_attended))
}
```

---

### 2. annual_leave_summary() 엔드포인트 개편

#### 변경 사항
**기존 (Phase 1):**
- 실제 근무 기록 수와 예정 근무일 수 비교
- 단순 카운트 방식

**개선 (Phase 2):**
- ✅ 소정근로일별 출결 상태 확인
- ✅ `REGULAR_WORK` + `ANNUAL_LEAVE`만 출근 인정
- ✅ 월별 개근 여부를 정확히 판단

#### 계산 로직 (1년 미만 근로자)
```python
perfect_months = 0

for month in range(start_month, current_month):
    # 1. 해당 월의 소정근로일 목록
    scheduled_dates = [date for date in month_dates if is_scheduled_workday(date)]
    
    # 2. 개근 여부 확인
    perfect_attendance = True
    for date in scheduled_dates:
        record = get_work_record(date)
        if not record or record.attendance_status not in ['REGULAR_WORK', 'ANNUAL_LEAVE']:
            perfect_attendance = False
            break
    
    # 3. 개근한 달만 카운트
    if perfect_attendance:
        perfect_months += 1

# 4. 발생 연차 (최대 11일)
earned_days = min(perfect_months, 11)
```

#### 예시 시나리오
```
근로 시작일: 2025-01-01
기준일: 2025-12-20

1월: 소정근로일 20일 → 20일 모두 REGULAR_WORK → 개근 ✅ (1일 발생)
2월: 소정근로일 18일 → 17일 REGULAR_WORK, 1일 ABSENT → 불인정 ❌
3월: 소정근로일 20일 → 18일 REGULAR_WORK, 2일 ANNUAL_LEAVE → 개근 ✅ (1일 발생)
4월: 소정근로일 19일 → 17일 REGULAR_WORK, 2일 EXTRA_WORK → 불인정 ❌ (추가근무는 개근 불인정)
...

총 개근 월수: 8개월
발생 연차: 8일
```

---

### 3. calendar() 엔드포인트 개선

#### 추가된 필드
```json
{
  "dates": [
    {
      "date": "2025-12-15",
      "day": 15,
      
      // Phase 1 기존 필드
      "is_scheduled": true,
      "record": {...},
      
      // Phase 2 추가 필드
      "is_scheduled_workday": true,  // 소정근로일 여부 (명시적)
      "attendance_status": "REGULAR_WORK",  // 출결 상태
      "is_worked": true  // 실제 근무 여부
    },
    {
      "date": "2025-12-16",
      "day": 16,
      "is_scheduled": true,
      "is_scheduled_workday": true,
      "attendance_status": "ANNUAL_LEAVE",
      "is_worked": false,  // 연차는 근무 아님
      "record": {...}
    },
    {
      "date": "2025-12-17",
      "day": 17,
      "is_scheduled": false,
      "is_scheduled_workday": false,
      "attendance_status": "EXTRA_WORK",  // 추가근무
      "is_worked": true,
      "record": {...}
    }
  ]
}
```

#### 프론트엔드 시각화 가이드
```vue
<template>
  <div 
    v-for="date in dates" 
    :key="date.date"
    :class="getDateClass(date)"
  >
    {{ date.day }}
  </div>
</template>

<script>
function getDateClass(date) {
  // 소정근로일 + 실제 근무 → 주황색 채움
  if (date.is_scheduled_workday && date.is_worked && date.attendance_status === 'REGULAR_WORK') {
    return 'bg-orange-400'
  }
  
  // 소정근로일이지만 미출근 (결근/병가/연차) → 주황색 테두리만
  if (date.is_scheduled_workday && !date.is_worked) {
    return 'border-2 border-orange-400 bg-white'
  }
  
  // 비소정근로일인데 실제 근로 (추가근무) → 녹색
  if (!date.is_scheduled_workday && date.is_worked && date.attendance_status === 'EXTRA_WORK') {
    return 'bg-green-200'
  }
  
  // 그 외 → 기본
  return 'bg-white'
}
</script>
```

---

### 4. get_cumulative_stats_data() 메소드 개선

#### 추가된 통계 항목
```python
{
    # 기존 통계
    'total_hours': 160.0,
    'total_earnings': 1600000,
    'total_work_days': 20,
    'start_date': '2024-11-01',
    
    # Phase 2 추가: 소정근로 vs 추가근무 구분
    'regular_work_hours': 144.0,  # 소정근로 시간
    'regular_work_days': 18,  # 소정근로 일수
    'regular_work_earnings': 1440000,  # 소정근로 급여
    
    'extra_work_hours': 16.0,  # 추가근무 시간
    'extra_work_days': 2,  # 추가근무 일수
    'extra_work_earnings': 160000,  # 추가근무 급여
    
    # Phase 2 추가: 출결 상태별 카운트
    'annual_leave_days': 1,  # 연차 사용 일수
    'absent_days': 0,  # 결근 일수
    'sick_leave_days': 0  # 병가 일수
}
```

#### 사용 예시
```vue
<template>
  <div class="stats-card">
    <h3>누적 근로 통계</h3>
    
    <div class="stat-item">
      <span>총 근무시간</span>
      <span>{{ stats.total_hours }}시간</span>
    </div>
    
    <div class="stat-breakdown">
      <div class="regular">
        <span>소정근로</span>
        <span>{{ stats.regular_work_hours }}시간 ({{ stats.regular_work_days }}일)</span>
      </div>
      <div class="extra">
        <span>추가근무</span>
        <span>{{ stats.extra_work_hours }}시간 ({{ stats.extra_work_days }}일)</span>
      </div>
    </div>
    
    <div class="stat-item">
      <span>총 급여</span>
      <span>{{ stats.total_earnings.toLocaleString() }}원</span>
    </div>
    
    <div class="leave-summary">
      <span>연차 {{ stats.annual_leave_days }}일</span>
      <span>결근 {{ stats.absent_days }}일</span>
      <span>병가 {{ stats.sick_leave_days }}일</span>
    </div>
  </div>
</template>
```

---

## 🔍 핵심 변경 원칙

### 1. 소정근로일 판정
- **기준**: 근무표 (WorkSchedule / MonthlySchedule)
- **시점**: 사전에 확정된 스케줄
- **사용자 입력**: 불필요 (시스템 자동 판정)

### 2. 개근 판정
- **기준**: 실제 근로 상태 (WorkRecord.attendance_status)
- **출근 인정**:
  - ✅ `REGULAR_WORK` (소정근로)
  - ✅ `ANNUAL_LEAVE` (연차 - 유급)
- **출근 불인정**:
  - ❌ `EXTRA_WORK` (추가근무 - 소정근로일 아님)
  - ❌ `ABSENT` (결근)
  - ❌ `SICK_LEAVE` (병가)

### 3. 급여 계산
- **기준**: 실제 근로시간 (모든 attendance_status 합산)
- **포함**:
  - ✅ `REGULAR_WORK` 시간
  - ✅ `EXTRA_WORK` 시간
- **제외**:
  - ❌ `ANNUAL_LEAVE` (시간 없음, 별도 유급휴가 처리)

---

## 📊 실전 예시

### 시나리오: 주휴수당 계산

```
직원: 김OO
주간 스케줄: 월~금 09:00~18:00 (주 40시간)
시급: 10,000원

이번 주 (12/16~12/22):
- 12/16(월): 소정근로일, REGULAR_WORK, 8시간 → ✅ 출근
- 12/17(화): 소정근로일, ANNUAL_LEAVE → ✅ 출근 (연차)
- 12/18(수): 소정근로일, REGULAR_WORK, 8시간 → ✅ 출근
- 12/19(목): 소정근로일, ABSENT → ❌ 결근
- 12/20(금): 소정근로일, REGULAR_WORK, 8시간 → ✅ 출근
- 12/21(토): 비소정근로일, EXTRA_WORK, 4시간 → 추가근무 (개근 판단 무관)
- 12/22(일): 비소정근로일, 기록 없음 → 무관

소정근로일: 월~금 (5일)
개근 여부: ❌ (목요일 결근)
주휴수당: 0원

만약 목요일도 출근했다면:
- 개근: ✅
- 주 40시간 이상: ✅
- 1일 소정근로시간: 40 ÷ 5 = 8시간
- 주휴수당: 8시간 × 10,000원 = 80,000원
```

### 시나리오: 연차 발생

```
직원: 이OO
입사일: 2025-01-01
기준일: 2025-12-20
주간 스케줄: 월, 수, 금 13:00~22:00 (주 27시간 → 연차 발생 대상)

1월 (소정근로일: 13일):
- 13일 모두 REGULAR_WORK → 개근 ✅ → 1일 발생

2월 (소정근로일: 12일):
- 11일 REGULAR_WORK, 1일 ABSENT → 불인정 ❌

3월 (소정근로일: 13일):
- 10일 REGULAR_WORK, 3일 ANNUAL_LEAVE → 개근 ✅ → 1일 발생

4월 (소정근로일: 13일):
- 12일 REGULAR_WORK, 1일 EXTRA_WORK (토요일 대타) → 불인정 ❌
  (토요일은 소정근로일이 아니므로 개근 판단에 포함 안 됨)

5월 (소정근로일: 14일):
- 14일 모두 REGULAR_WORK → 개근 ✅ → 1일 발생

...

11월까지 개근 월수: 8개월
발생 연차: 8일
사용 연차: 3일 (3월에 사용한 3일)
잔여 연차: 5일
```

---

## ⚠️ 주의사항

### 1. 기존 데이터 처리
- 기존 WorkRecord의 `attendance_status`는 기본값 `REGULAR_WORK`로 설정됨
- 과거 데이터는 수동으로 재분류 필요 (선택사항)

### 2. EXTRA_WORK의 의미
- **급여**: 정상 지급 (실제 근로시간 × 시급)
- **개근**: 불인정 (소정근로일이 아니므로)
- **주휴수당**: 영향 없음 (개근 판단에서 제외)
- **연차 발생**: 영향 없음 (개근 판단에서 제외)

### 3. ANNUAL_LEAVE의 의미
- **급여**: 0원 (근로시간 없음, 별도 유급휴가 처리)
- **개근**: 인정 ✅ (유급휴가)
- **주휴수당**: 출근 인정
- **연차 발생**: 출근 인정

---

## 🎯 다음 단계 (Phase 3)

Phase 2에서 백엔드 계산 로직은 완료되었습니다. 다음은 프론트엔드 작업입니다:

### 필수 작업
1. **WorkDayModal.vue 개선**
   - "근무표 수정" / "실제 근로 수정" 두 가지 경로 분리
   - 출결 상태 선택 UI (5가지 선택지)
   - 소정근로일 안내 문구

2. **WorkCalendar.vue 개선**
   - 소정근로일 시각적 구분 (테두리)
   - 출결 상태별 색상 구분
   - 호버 시 상세 정보 표시

3. **통계 화면 개선**
   - 소정근로 vs 추가근무 구분 표시
   - 출결 상태별 집계 표시

---

**작업 완료일**: 2025-12-20  
**Phase**: 2 (계산 로직 업데이트)  
**작성자**: GitHub Copilot
