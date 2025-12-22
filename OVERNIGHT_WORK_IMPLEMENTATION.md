# 자정 넘김 및 익일 근무 기능 구현 완료

## 📝 구현 개요

**목표**: 24:00 시간 입력 지원 및 익일 새벽(24:00~06:00) 근무 기록 기능 추가

**날짜**: 2025년 12월 20일

---

## ✅ 구현 완료 사항

### 1. Backend (Django)

#### 1.1 Models (`labor/models.py`)
**추가된 필드**:
- `WorkRecord.is_overnight`: Boolean - 퇴근 시간이 자정을 넘는지 표시
- `WorkRecord.next_day_work_minutes`: Integer (0~360) - 익일 추가 근무 시간(분)
- `WorkSchedule.is_overnight`: Boolean - 스케줄의 자정 넘김 여부
- `WorkSchedule.next_day_work_minutes`: Integer (0~360) - 스케줄의 익일 근무 시간
- `MonthlySchedule.is_overnight`: Boolean - 월별 스케줄의 자정 넘김 여부
- `MonthlySchedule.next_day_work_minutes`: Integer (0~360) - 월별 스케줄의 익일 근무 시간

**수정된 메소드**:
- `WorkRecord.get_total_hours()`: 익일 근무 시간을 포함하여 계산
  ```python
  total_work_minutes = work_minutes + next_day_minutes
  return Decimal(str(total_work_minutes / 60.0))
  ```

#### 1.2 Serializers (`labor/serializers.py`)
- `WorkRecordSerializer`: `is_overnight`, `next_day_work_minutes` 필드 추가
- `WorkScheduleSerializer`: `is_overnight`, `next_day_work_minutes` 필드 추가
- `MonthlyScheduleSerializer`: `is_overnight`, `next_day_work_minutes` 필드 추가

#### 1.3 Views (`labor/views.py`)
**수정된 엔드포인트**:
- `POST /api/labor/employees/<id>/schedules/`
  - `is_overnight`, `next_day_work_minutes` 파라미터 수신
  - 24:00 입력 시 다음날 00:00으로 저장하고 `is_overnight=True` 설정
  - 과거 근로기록 자동 생성 시 자정 넘김 정보 반영

#### 1.4 Migrations
**생성된 마이그레이션**: `labor/migrations/0012_monthlyschedule_is_overnight_and_more.py`
- 6개 필드 추가 (각 모델에 2개씩)
- 기본값: `is_overnight=False`, `next_day_work_minutes=0`

---

### 2. Frontend (Vue.js)

#### 2.1 WorkDayModal.vue (근로기록 입력)
**UI 변경사항**:
- 시간 선택 범위: `00:00 ~ 24:00` (기존 23:30 → 24:00으로 확장)
- 새 섹션 추가: "익일 근무 있음 (24:00~06:00)" 체크박스
- 체크 시 "익일 근무 시간(분)" 입력 필드 표시 (0~360분)
- 도움말 메시지: "💡 당일 24:00부터 다음날 06:00 사이의 추가 근로시간을 입력하세요."

**로직 변경사항**:
- `timeOptions`: 24:00 옵션 추가
- `hasNextDayWork`, `nextDayWorkMinutes` 상태 추가
- `validateTimes()`: 24:00 형식 허용 및 익일 근무 시간 범위 검증
- 저장 시 24:00을 다음날 00:00으로 변환하고 `is_overnight=true` 전송

#### 2.2 WeeklyScheduleEditor.vue (주간 스케줄)
**UI 변경사항**:
- 시간 선택 범위: `00:00 ~ 24:00`으로 확장

**로직 변경사항**:
- `timeOptions`: 24:00 옵션 추가
- `saveSchedules()`: 24:00 입력 시 00:00으로 변환하고 `is_overnight=true` 전송

---

## 🧪 테스트

### 테스트 파일: `labor/tests_overnight.py`

**테스트 케이스** (6개, 모두 통과 ✅):
1. ✅ `test_24_00_end_time_creates_overnight_record`: 24:00 퇴근 시 자정 넘김 기록 생성
2. ✅ `test_next_day_work_minutes_included_in_total`: 익일 근무 시간이 총 근로시간에 포함
3. ✅ `test_overnight_schedule_creates_correct_records`: 자정 넘김 스케줄의 정확성
4. ✅ `test_next_day_work_minutes_validation`: 익일 근무 시간 범위 검증 (0~360분)
5. ✅ `test_normal_work_without_overnight`: 일반 근무(자정 넘김 없음) 정상 동작
6. ✅ `test_multiple_overnight_calculations`: 여러 자정 넘김 근무의 통계 계산

**실행 방법**:
```bash
python manage.py test labor.tests_overnight -v 2
```

**결과**:
```
Ran 6 tests in 0.968s
OK
```

---

## 📐 설계 결정사항

### 24:00 저장 방식
**선택한 방식**: 방식 A
- UI에는 "24:00"으로 표시
- 저장 시 다음날 "00:00:00"으로 변환
- `is_overnight` 플래그로 자정 넘김 구분

**이유**:
- 데이터베이스의 `TimeField`는 24:00을 지원하지 않음
- `is_overnight` 플래그로 명확한 의도 표현
- UI 재표시 시 간단한 변환으로 24:00 복원 가능

### 익일 근무 시간 처리
**방식**: 별도 필드 `next_day_work_minutes` 사용

**이유**:
- 출퇴근 시간(`time_in`, `time_out`)은 당일 내 근무만 표현
- 24:00 이후 근무는 별도로 기록하여 중복 계산 방지
- 명확한 범위 제한 (0~360분 = 최대 6시간)

---

## 🔄 데이터 흐름

### 근로기록 입력 (캘린더 날짜 클릭)
1. 사용자가 퇴근 시간에 "24:00" 선택
2. "익일 근무 있음" 체크 및 "120"(분) 입력
3. 저장 버튼 클릭
4. Frontend: 24:00 → 다음날 00:00으로 변환, `is_overnight: true` 전송
5. Backend: `time_out`에 다음날 00:00 저장, 플래그 저장
6. `get_total_hours()` 호출 시 익일 근무 시간 자동 합산

### 스케줄 저장 (주간 근무 스케줄)
1. 사용자가 월요일 퇴근을 "24:00"로 설정
2. 저장 클릭
3. Frontend: `end_time: "00:00"`, `is_overnight: true` 전송
4. Backend: 스케줄 저장 및 과거 근로기록 자동 생성 시 플래그 반영

---

## 📊 계산 예시

### 예시 1: 18:00 ~ 24:00 근무 (휴게 30분, 익일 근무 없음)
```
time_in: 2025-01-15 18:00:00
time_out: 2025-01-16 00:00:00
is_overnight: true
break_minutes: 30
next_day_work_minutes: 0

계산:
- 기본 근무: (24:00 - 18:00) = 6시간 = 360분
- 휴게: 30분
- 익일 근무: 0분
- 총 근무: (360 - 30 + 0) / 60 = 5.5시간
```

### 예시 2: 18:00 ~ 24:00 근무 + 익일 02:00까지 (총 8시간)
```
time_in: 2025-01-15 18:00:00
time_out: 2025-01-16 00:00:00
is_overnight: true
break_minutes: 0
next_day_work_minutes: 120  # 24:00 ~ 02:00 = 2시간

계산:
- 기본 근무: 360분
- 휴게: 0분
- 익일 근무: 120분
- 총 근무: (360 - 0 + 120) / 60 = 8.0시간
```

---

## 🎯 사용자 시나리오

### 시나리오 1: 편의점 야간 근무
**상황**: 오후 6시 출근 → 다음날 새벽 2시 퇴근
**입력**:
- 출근: 18:00
- 퇴근: 24:00
- 익일 근무: ✅ 체크, 120분 입력
- 휴게: 60분

**결과**: 7시간 근무 기록 (6시간 - 1시간 + 2시간)

### 시나리오 2: 레스토랑 마감 근무
**상황**: 오후 5시 출근 → 자정까지 근무
**입력**:
- 출근: 17:00
- 퇴근: 24:00
- 익일 근무: ❌ 체크 안 함
- 휴게: 30분

**결과**: 6.5시간 근무 기록 (7시간 - 0.5시간)

---

## 🔧 향후 개선 가능 사항

### 1. UI 개선
- [ ] 익일 근무 시간을 시:분 형식으로도 입력 가능하게
- [ ] 자정 넘김 근무 시각적 표시 (캘린더에 특수 아이콘)
- [ ] 야간 근로 수당 자동 계산 (22:00~06:00 구간 1.5배)

### 2. 기능 확장
- [ ] 월별 스케줄 편집에도 익일 근무 입력 UI 추가
- [ ] 익일 근무 통계 별도 집계 (야간 근무 시간 추이)
- [ ] 연속 근무 경고 (24시간 내 재출근 알림)

### 3. 검증 강화
- [ ] 익일 근무가 다음 날 출근과 겹치는지 체크
- [ ] 주 52시간 제한 계산에 익일 근무 포함
- [ ] 연속 근무 시간 제한 준수 검증

---

## 📚 API 변경사항

### WorkRecord 생성/수정
```json
POST /api/labor/work-records/
{
  "employee": 1,
  "work_date": "2025-01-15",
  "time_in": "2025-01-15T18:00:00",
  "time_out": "2025-01-16T00:00:00",
  "is_overnight": true,
  "next_day_work_minutes": 120,
  "break_minutes": 60
}
```

### WorkSchedule 저장
```json
POST /api/labor/employees/1/schedules/
{
  "weekday": 0,
  "start_time": "18:00",
  "end_time": "00:00",
  "is_overnight": true,
  "next_day_work_minutes": 0,
  "enabled": true
}
```

---

## 🐛 알려진 제한사항

1. **익일 근무 범위**: 현재 24:00~06:00 (최대 6시간)으로 하드코딩
   - 06:00 이후 근무는 별도 기록으로 입력해야 함

2. **스케줄 자동 생성**: 익일 근무 정보는 스케줄에 저장되지만, UI에서 편집 불가
   - WeeklyScheduleEditor에 익일 근무 UI 미구현

3. **시간대 처리**: 모든 시간은 서버 타임존 기준
   - 다른 타임존 지원 필요 시 추가 구현 필요

---

## 📖 관련 문서

- 마이그레이션: `labor/migrations/0012_monthlyschedule_is_overnight_and_more.py`
- 테스트: `labor/tests_overnight.py`
- 모델: `labor/models.py`
- 뷰: `labor/views.py`
- 프론트엔드: `frontend/src/components/WorkDayModal.vue`

---

## ✨ 요약

이번 업데이트로 다음이 가능해졌습니다:

1. ✅ **24:00 시간 입력**: UI에서 24:00 선택 가능
2. ✅ **자정 넘김 근무**: 18:00 ~ 24:00 같은 근무 정확히 기록
3. ✅ **익일 새벽 근무**: 24:00~06:00 구간 추가 근로시간 입력
4. ✅ **정확한 계산**: 모든 통계 및 급여 계산에 자동 반영
5. ✅ **테스트 검증**: 6개 테스트 케이스 모두 통과

이제 야간 근무와 자정을 넘기는 근무를 정확하게 기록하고 계산할 수 있습니다! 🎉
