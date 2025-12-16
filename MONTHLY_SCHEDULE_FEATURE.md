# 월별 근무 스케줄 개별 수정 기능

## 개요

이 기능은 특정 월의 근무 스케줄만 별도로 설정할 수 있게 하여, 과거 월과 현재 월의 근무 패턴이 다른 경우를 효율적으로 관리할 수 있도록 합니다.

## 구현 내용

### 1. Backend (Django)

#### 새로운 모델: `MonthlySchedule`
- **위치**: `labor/models.py`
- **목적**: 특정 년월에 대한 주간 스케줄 오버라이드
- **필드**:
  - `employee`: 근로자 (ForeignKey)
  - `year`: 년도
  - `month`: 월 (1-12)
  - `weekday`: 요일 (0-6, 월-일)
  - `start_time`: 시작 시간
  - `end_time`: 종료 시간
  - `enabled`: 활성화 여부

#### 새로운 API 엔드포인트
- **GET** `/api/labor/employees/<id>/monthly-schedule-override/?year=2025&month=3`
  - 해당 월의 MonthlySchedule 조회
  - 없으면 기본 WorkSchedule 반환
  - 응답: `{ has_override: boolean, schedules: [...] }`

- **POST** `/api/labor/employees/<id>/monthly-schedule-override/`
  - 해당 월의 근무 스케줄 일괄 저장
  - 요청 본문:
    ```json
    {
      "year": 2025,
      "month": 3,
      "schedules": [
        {"weekday": 0, "start_time": "09:00", "end_time": "18:00", "enabled": true},
        ...
      ]
    }
    ```

#### services.py 수정
- `monthly_scheduled_dates()`: MonthlySchedule 우선 적용
- `compute_monthly_schedule_stats()`: MonthlySchedule 우선 적용
- 우선순위: MonthlySchedule > WorkSchedule

### 2. Frontend (Vue 3)

#### 새로운 컴포넌트: `MonthlyScheduleModal.vue`
- **위치**: `frontend/src/components/MonthlyScheduleModal.vue`
- **기능**:
  - 특정 월의 근무 스케줄 조회 및 수정
  - WeeklyScheduleEditor와 동일한 UI (요일별 시간 선택)
  - 해당 월에만 적용되는 것을 명확히 표시
  - 기본 스케줄과 월별 오버라이드 구분

#### WorkCalendar.vue 수정
- "📅 월별 스케줄 변경" 버튼 추가
- 버튼 클릭 시 MonthlyScheduleModal 표시
- 스케줄 저장 후 캘린더 자동 갱신

### 3. Database Migration

- **Migration**: `labor/migrations/0006_monthlyschedule.py`
- MonthlySchedule 테이블 생성
- 인덱스: employee + year + month
- Unique constraint: employee + year + month + weekday

## 사용 방법

1. 근로관리 페이지의 캘린더에서 "📅 월별 스케줄 변경" 버튼 클릭
2. 모달에서 해당 월의 근무 스케줄 수정
3. "저장하기" 버튼 클릭
4. 해당 월의 캘린더에만 변경사항이 반영됨

## 주요 특징

✅ **월별 독립성**: 특정 월의 스케줄 변경이 다른 월에 영향을 주지 않음
✅ **기본 스케줄 유지**: 월별 오버라이드가 없는 경우 기본 주간 스케줄 사용
✅ **명확한 UI**: 현재 보고 있는 월의 스케줄만 변경할 수 있음을 명시
✅ **자동 갱신**: 스케줄 저장 시 캘린더 자동 갱신

## 기술적 세부사항

### 스케줄 우선순위 로직
```python
# services.py
if monthly_schedules.exists():
    schedule_map = {s.weekday: s for s in monthly_schedules}
else:
    schedule_map = {s.weekday: s for s in default_schedules}
```

### API 응답 예시
```json
{
  "has_override": true,
  "schedules": [
    {
      "id": 1,
      "year": 2025,
      "month": 3,
      "weekday": 0,
      "weekday_display": "Monday",
      "start_time": "09:00",
      "end_time": "18:00",
      "enabled": true
    }
  ]
}
```

## 테스트 방법

1. 근로정보 수정에서 기본 주간 스케줄 설정
2. 근로관리 페이지에서 특정 월로 이동
3. "월별 스케줄 변경" 버튼으로 해당 월만 다른 스케줄 설정
4. 캘린더에서 해당 월의 스케줄이 변경된 것 확인
5. 다른 월로 이동하여 기본 스케줄이 유지되는 것 확인

## 제한사항

- 월별 스케줄은 해당 월의 전체 주간 패턴을 오버라이드함
- 특정 날짜만 개별 수정하려면 캘린더에서 직접 근로기록 수정 필요
- 월별 스케줄 삭제 기능은 현재 미구현 (기본 스케줄로 돌아가려면 모든 요일을 비활성화)
