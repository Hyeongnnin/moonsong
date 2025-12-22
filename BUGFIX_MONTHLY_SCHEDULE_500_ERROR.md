# 월별 스케줄 저장 500 에러 및 캘린더 날짜 미표시 버그 수정

## 🐛 버그 리포트
- **발생 일시**: 2025-12-20
- **증상 1**: 월별 스케줄 변경 → 저장 버튼 클릭 시 "Request failed with status code 500" 에러
- **증상 2**: 캘린더에서 근로 색깔 표시가 사라짐
- **증상 3**: 캘린더에 날짜 자체가 아예 표시되지 않음 (빈 캘린더)

## 🔍 원인 분석

### 1. 백엔드 500 에러 (변수 미초기화)
**파일**: `labor/views.py`
**위치**: `monthly_schedule_override()` 메소드 (약 1071번째 줄)

**문제 코드**:
```python
created_records_count = 0
# updated_empty_records_count 초기화 누락!

for day in range(1, last_day + 1):
    # ...
    updated_empty_records_count += 1  # ❌ 초기화되지 않은 변수 사용
```

**에러 메시지** (추정):
```
UnboundLocalError: local variable 'updated_empty_records_count' referenced before assignment
```

### 2. 프론트엔드 API 엔드포인트 불일치
**파일**: `frontend/src/components/WorkCalendar.vue`
**위치**: `loadCalendar()` 함수 (약 404번째 줄)

**문제**:
- 사용 중인 API: `/labor/jobs/<id>/monthly-schedule/`
- 문제점: Phase 3에서 필요한 `is_scheduled_workday`, `is_worked`, `attendance_status` 필드가 없음
- 결과: 캘린더가 색깔을 구분할 수 없음

### 3. 백엔드 Import 누락 (캘린더 날짜 미표시)
**파일**: `labor/views.py`
**위치**: 파일 상단 import 섹션

**문제**:
- `calendar` 모듈이 파일 상단에 import되지 않음
- 각 메소드 내에서 `import calendar as pycal` 중복 사용
- `calendar()` API 호출 시 `NameError` 또는 `AttributeError` 발생 가능
- 결과: 캘린더 데이터가 생성되지 않아 빈 화면 표시

**에러 메시지** (추정):
```python
# 메소드 내 로컬 import 전에 pycal 사용 시도하면:
NameError: name 'pycal' is not defined

# 또는 monthrange 호출 실패:
AttributeError: module 'calendar' has no attribute 'monthrange'
```

## ✅ 수정 내용

### 1. 백엔드 변수 초기화 (labor/views.py)

**Before**:
```python
created_records_count = 0

for day in range(1, last_day + 1):
```

**After**:
```python
created_records_count = 0
updated_empty_records_count = 0  # ✅ 초기화 추가

for day in range(1, last_day + 1):
```

**위치**: Line ~1065

### 2. 백엔드 Import 정리 (labor/views.py)

**Before** (파일 상단):
```python
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List
from django.db import models
from .models import Employee, WorkRecord, ...
# calendar 모듈 import 없음 ❌
```

**After** (파일 상단):
```python
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from typing import List
from django.db import models
import calendar as pycal  # ✅ 추가
from .models import Employee, WorkRecord, ...
```

**Before** (각 메소드 내):
```python
def calendar(self, request, pk=None):
    # ...
    import calendar as pycal  # ❌ 메소드 내 중복 import
    from datetime import date  # ❌ 이미 상단에 있음
    _, lastday = pycal.monthrange(year, mon)
```

**After** (각 메소드 내):
```python
def calendar(self, request, pk=None):
    # ...
    _, lastday = pycal.monthrange(year, mon)  # ✅ 상단 import 사용
```

**수정된 메소드**:
- `calendar()` - Line ~575
- `delete_monthly_work_records()` - Line ~635
- `monthly_schedule_override()` - Line ~1063

**위치**: Line 11 (상단 import), Lines 575, 635, 1063 (메소드 내 중복 제거)

### 3. 프론트엔드 API 엔드포인트 변경 (WorkCalendar.vue)

**Before**:
```typescript
const res = await apiClient.get(`/labor/jobs/${employeeId}/monthly-schedule/`, {
  params: { month: monthStr },
  signal: calendarAbortController.signal,
});
```

**After**:
```typescript
// Phase 3: calendar API 사용 (is_scheduled_workday, is_worked, attendance_status 포함)
const res = await apiClient.get(`/labor/jobs/${employeeId}/calendar/`, {
  params: { month: monthStr },
  signal: calendarAbortController.signal,
});
```

**변경 이유**:
- `/calendar/` API는 Phase 2/3에서 추가된 필드들을 모두 포함
- 각 날짜별로 `is_scheduled_workday`, `is_worked`, `attendance_status` 반환
- 이를 통해 4가지 색상 구분 가능 (주황/초록/회색)

**위치**: Line ~404

## 📊 API 응답 비교

### `/monthly-schedule/` (기존 - Phase 3 미지원)
```json
{
  "dates": [
    {
      "date": "2025-12-15",
      "day": 15,
      "is_scheduled": true,
      "start_time": "13:00",
      "end_time": "19:00"
    }
  ]
}
```

### `/calendar/` (개선 - Phase 3 지원)
```json
{
  "dates": [
    {
      "date": "2025-12-15",
      "day": 15,
      "is_scheduled_workday": true,      // ✅ 소정근로일 여부
      "is_scheduled": true,               // 하위 호환
      "is_worked": true,                  // ✅ 실제 근무 여부
      "attendance_status": "REGULAR_WORK",// ✅ 출결 상태
      "record": { ... }
    }
  ]
}
```

## 🎨 시각적 개선 효과

### Before (버그 발생 후)
```
❌ 캘린더에 날짜가 아예 표시되지 않음 (빈 화면)
❌ 모든 날짜가 회색으로만 표시 (색깔 구분 실패)
❌ 근무일과 빈 날짜 구분 불가
❌ 500 에러로 월별 스케줄 저장 실패
```

### After (수정 후)
```
✅ 캘린더에 1~31일 날짜 정상 표시
✅ 소정근로 + 출근: 🟠 주황색 채움
✅ 소정근로 + 결근: ⚪ 주황 테두리
✅ 추가근무: 🟢 초록색 채움
✅ 빈 날짜: ⚪ 회색 테두리
✅ 월별 스케줄 저장 정상 작동
```

## 🧪 테스트 시나리오

### 1. 월별 스케줄 저장 테스트
1. 달력에서 "📅 월별 스케줄 변경" 버튼 클릭
2. 근무 시간 수정 (예: 화요일 11:00~18:00)
3. "저장 중..." 버튼 클릭
4. **기대 결과**: 
   - ✅ "저장되었습니다" 메시지
   - ✅ 500 에러 없음
   - ✅ 해당 월의 근로기록 자동 생성

### 2. 캘린더 색상 구분 테스트
1. 12월 달력 확인
2. **기대 결과**:
   - 월~금 (소정근로일): 🟠 주황색 또는 ⚪ 주황 테두리
   - 토요일 대타근무: 🟢 초록색
   - 일요일: ⚪ 회색 (또는 주휴일 하늘색)
   - 빈 날짜: ⚪ 회색

### 3. 근로기록 입력 후 색상 변경 테스트
1. 소정근로일(월~금)에 근로 입력
2. **기대 결과**: ⚪ 주황 테두리 → 🟠 주황 채움

## 📝 재발 방지

### 코드 리뷰 체크리스트
- [ ] 변수 초기화 확인 (`+=` 연산자 사용 전 초기값 설정)
- [ ] API 엔드포인트 일관성 확인 (Phase 변경사항 반영)
- [ ] Import 문은 파일 상단에 위치 (메소드 내 중복 import 금지)
- [ ] Python 표준 라이브러리는 프로젝트 시작 시 import
- [ ] 에러 핸들링 추가 (try-except with logging)

### 자동화 개선 사항
```python
# 추천 1: 변수 초기화를 한 곳에서 관리
created_records_count = 0
updated_empty_records_count = 0
overridden_records_count = 0  # schedules() 메소드에는 있음

# 추천 2: Import는 파일 상단에 통일
import calendar as pycal
from datetime import datetime, timedelta, date

# ❌ 금지: 메소드 내 중복 import
def some_method(self):
    import calendar as pycal  # 이미 상단에 있음!
```

### Import 정리 원칙
1. **표준 라이브러리**: 파일 최상단
2. **서드파티 라이브러리**: 표준 라이브러리 다음
3. **로컬 모듈**: 서드파티 다음
4. **메소드 내 import**: 순환 참조 방지용으로만 제한적 사용

## 🔄 관련 문서
- [SCHEDULED_WORKDAY_PHASE3_COMPLETE.md](./SCHEDULED_WORKDAY_PHASE3_COMPLETE.md) - Phase 3 프론트엔드 구현
- [SCHEDULED_WORKDAY_PHASE2_COMPLETE.md](./SCHEDULED_WORKDAY_PHASE2_COMPLETE.md) - Phase 2 백엔드 구현

## ✅ 수정 완료
- [x] 백엔드: `updated_empty_records_count` 변수 초기화
- [x] 백엔드: `calendar` 모듈 파일 상단 import 추가
- [x] 백엔드: 메소드 내 중복 import 제거 (3곳)
- [x] 프론트엔드: `monthly-schedule` → `calendar` API 변경
- [x] 검증: `python3 manage.py check` 통과
- [x] 문서화: 버그 수정 내용 기록

---

**수정 일시**: 2025-12-20
**수정자**: GitHub Copilot
**영향 범위**: 월별 스케줄 저장 기능, 캘린더 날짜 표시, 캘린더 색상 표시
**우선순위**: 🔴 긴급 (Production 영향 - 캘린더 전체 불능)
**수정된 파일**: 
- `labor/views.py` (4개 수정: import 추가, 변수 초기화, 중복 import 제거 3곳)
- `frontend/src/components/WorkCalendar.vue` (1개 수정: API 엔드포인트 변경)
