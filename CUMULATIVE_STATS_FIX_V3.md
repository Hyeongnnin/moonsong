# 누적 통계 계산 로직 변경 (v3)

## 문제점
월별 근로기록 삭제 후에도 알바 업적(누적 통계)이 변하지 않는 문제 발생.

### 원인
기존 누적 통계 계산 방식:
```python
# 실제 근로기록 + 월별 스케줄 + 주간 스케줄 모두 집계
if 실제_근로기록:
    시간 += 실제_기록_시간
elif 월별_스케줄:
    시간 += 월별_스케줄_시간
elif 주간_스케줄:
    시간 += 주간_스케줄_시간  # ← 이게 문제!
```

**문제**: 실제 근로기록을 삭제해도 주간 스케줄이 남아있어 "예상 근로시간"이 계속 집계됨.

### 예시
- 11월에 실제로 72시간 일함 → 삭제
- 하지만 주간 스케줄(목, 금, 토 6시간씩)이 설정되어 있음
- 삭제 전: 101시간 (실제 기록 + 스케줄 시간)
- 삭제 후: 101시간 (스케줄 시간이 남아있음) ← **변하지 않음!**

---

## 해결 방법 (v3)

### 변경된 계산 방식
```python
# 실제 근로기록(WorkRecord)만 집계
for record in work_records:
    if record.get_total_hours() > 0:
        total_hours += record.hours
        total_work_days += 1

# 스케줄은 집계하지 않음!
```

### 효과
- ✅ **실제로 일한 시간만** 카운트
- ✅ 삭제 시 **즉시 반영**
- ✅ 정확한 업적 계산

### 결과
- 11월 72시간 삭제 전: 101시간
- 11월 72시간 삭제 후: 29시간 ← **정상 반영!**

---

## 영향 받는 API

### 1. `/api/labor/jobs/{id}/cumulative-stats/`
**변경 전**: 실제 기록 + 월별 스케줄 + 주간 스케줄
**변경 후**: 실제 기록만

### 2. `delete_monthly_work_records()` 응답의 `cumulative_stats`
**변경 전**: 스케줄 포함
**변경 후**: 실제 기록만

### 3. `monthly_scheduled_dates()` - 캘린더 표시 (v3 추가)
**변경 전**: 실제 기록 + 월별 스케줄 + 주간 스케줄 (주황색 표시)
**변경 후**: 실제 기록만 (주황색 표시)

**효과**:
- ✅ 삭제 후 주황색 날짜 즉시 사라짐
- ✅ 스케줄만 설정하고 실제 일하지 않으면 흰색으로 표시
- ✅ 일관된 UI/UX

---

## 비교표

| 항목 | 변경 전 (v2) | 변경 후 (v3) |
|------|-------------|-------------|
| 실제 근로기록 | ✅ 집계 | ✅ 집계 |
| 월별 스케줄 | ✅ 집계 (예상) | ❌ 제외 |
| 주간 스케줄 | ✅ 집계 (예상) | ❌ 제외 |
| 삭제 반영 | ❌ 느림 | ✅ 즉시 |
| 정확도 | 낮음 (예상 포함) | 높음 (실제만) |

---

## 사용자 관점

### 변경 전
- "근로기록 삭제했는데 알바 업적이 안 바뀌네요?"
- "스케줄만 설정했는데 시간이 올라가요?"

### 변경 후
- ✅ 삭제하면 즉시 업적 감소
- ✅ 실제로 일한 시간만 표시
- ✅ 정확한 통계

---

## 기술 상세

### 수정된 파일
- `labor/views.py`
  - `get_cumulative_stats_data()`: 실제 기록만 집계
  - `cumulative_stats()`: 헬퍼 메소드 사용
- `labor/services.py` **(v3 추가)**
  - `monthly_scheduled_dates()`: 실제 기록만 주황색 표시

### 주요 코드

#### 1. 누적 통계 계산 (views.py)
```python
def get_cumulative_stats_data(self, job):
    """누적 통계 계산 - 실제 근로기록만 집계"""
    
    # 실제 근로기록만 조회
    work_records = WorkRecord.objects.filter(
        employee=job,
        work_date__gte=start_date,
        work_date__lte=today
    )
    
    total_hours = Decimal('0.0')
    total_work_days = 0
    
    # 실제 근로기록만 집계 (스케줄 제외)
    for record in work_records:
        hours = record.get_total_hours()
        if hours > 0:
            total_hours += hours
            total_work_days += 1
    
    return {
        'total_hours': float(total_hours),
        'total_earnings': float(total_hours * job.hourly_rate),
        'total_work_days': total_work_days,
        'start_date': start_date.isoformat()
    }
```

#### 2. 캘린더 날짜 표시 (services.py)
```python
def monthly_scheduled_dates(employee, year, month):
    """실제 근로기록만 표시 (v3)"""
    
    # 실제 근무 기록만 가져오기
    work_records = WorkRecord.objects.filter(
        employee=employee,
        work_date__year=year,
        work_date__month=month
    )
    
    worked_records_map = {wr.work_date: wr for wr in work_records}
    
    for dt in month_dates:
        is_scheduled = False
        
        # 실제 근로기록만 확인
        if dt in worked_records_map:
            record = worked_records_map[dt]
            if record.get_total_hours() > 0:
                is_scheduled = True  # 주황색으로 표시
        
        scheduled_dates_data.append({
            "date": dt.isoformat(),
            "is_scheduled": is_scheduled,
        })
    
    return scheduled_dates_data
```

---

## 테스트 시나리오

### 삭제 전
```
알바 업적:
- 총 근로시간: 101시간
- 총 누적 급여: 1,212,000원
- 총 근무 일수: 11일
```

### 11월 데이터 삭제 (72시간, 8일)
```
2025년 11월의 근로기록 8건이 삭제되었습니다.
```

### 삭제 후 (새로고침 없이 즉시 반영)
```
알바 업적:
- 총 근로시간: 29시간 ← (101 - 72 = 29)
- 총 누적 급여: 348,000원
- 총 근무 일수: 3일 ← (11 - 8 = 3)
```

✅ **정상 동작!**

---

## 업데이트 날짜
2025년 12월 17일 (v3)
