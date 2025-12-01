# 근로정보 수정 기능 - 완벽 가이드

## 📋 개요

"근로정보 수정" 탭에서 사용자가 알바 정보(시급, 주당 근로시간, 고용형태 등)를 수정하면, 자동으로 "근로관리" 탭의 모든 통계가 실시간으로 갱신되는 기능입니다.

---

## 🎯 주요 기능

### 1. 근로정보 수정 폼 (LaborEdit.vue)
- **12개 필드**: 사업장명, 주소, 업종, 고용형태, 시급, 주당/일 근로시간, 근로 시작/종료일, 주휴수당/퇴직금/현재재직 여부
- **자동 검증**: 백엔드 유효성 검사 + 프론트엔드 HTML5 검증
- **에러 처리**: 유효성 검사 오류 시 명확한 메시지 표시
- **성공 피드백**: 저장 완료 시 3초 토스트 알림

### 2. 자동 데이터 갱신 (Cascading Update)
저장 → 폼 닫기 후 근로관리 탭 이동 → **자동으로 모든 통계 갱신**

데이터 흐름:
```
사용자: "저장하기" 클릭
    ↓
PATCH /api/labor/employees/{id}/ ← formData 전송
    ↓
Backend: Serializer 유효성 검사 → DB 저장
    ↓
Frontend: fetchJobs() ← 최신 Employee 정보 로드
    ↓
jobStore.activeJob 자동 업데이트
    ↓
RightSidebar가 activeJob.id 변화 감지
    ↓
fetchJobSummary() ← 월별 통계 재계산
    ↓
RightSidebar 통계 카드 자동 갱신 ✅
WorkCalendar 자동 갱신 (시급 변경 반영)
```

---

## 🔧 기술 구현

### 백엔드 (Django REST Framework)

#### 1. serializers.py - EmployeeUpdateSerializer
```python
class EmployeeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            'workplace_name', 'workplace_address', 'workplace_reg_no',
            'industry', 'employment_type', 'start_date', 'end_date',
            'hourly_rate', 'weekly_hours', 'daily_hours',
            'has_paid_weekly_holiday', 'is_severance_eligible', 'is_current'
        ]
    
    def validate_hourly_rate(self, value):
        if value < 0:
            raise ValidationError("시급은 0 이상이어야 합니다.")
        return value
    
    def validate_weekly_hours(self, value):
        if value < 0 or value > 168:
            raise ValidationError("주당 근로시간은 0 이상 168 이하여야 합니다.")
        return value
    
    def validate(self, data):
        # end_date > start_date 검증
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if self.instance:
            start_date = start_date or self.instance.start_date
            end_date = end_date or self.instance.end_date
        
        if end_date and start_date and end_date < start_date:
            raise ValidationError(
                {"end_date": "종료일은 시작일 이후여야 합니다."}
            )
        return data
```

**핵심**: GET(read) vs PATCH(update) 시 다른 Serializer 사용 → 필요한 검증만 실행

#### 2. views.py - EmployeeViewSet
```python
class EmployeeViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        """액션에 따라 다른 Serializer 선택"""
        if self.action in ['update', 'partial_update']:
            return EmployeeUpdateSerializer  # PATCH/PUT 시
        return EmployeeSerializer  # GET/POST/DELETE 시
    
    def perform_update(self, serializer):
        """저장 로직"""
        serializer.save()  # 유효성 검사는 이미 실행됨
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """월별 요약 통계 계산 (시급 변경 후 재계산됨)"""
        # 시급을 포함한 월별 통계 계산
        # week_stats = [{hours, pay}, ...]
        # 시급이 변경되면 pay 값이 다시 계산됨
```

**엔드포인트**:
- `GET /api/labor/jobs/` - 모든 알바 목록
- `GET /api/labor/jobs/{id}/` - 상세 정보
- `PATCH /api/labor/jobs/{id}/` - ⭐️ 부분 수정 (근로정보 수정)
- `GET /api/labor/jobs/{id}/summary/?month=2025-11` - 월별 통계

#### 3. 유효성 검사 규칙
| 필드 | 규칙 | 에러 메시지 |
|------|------|-----------|
| hourly_rate | ≥ 0 | "시급은 0 이상이어야 합니다." |
| weekly_hours | 0 ≤ value ≤ 168 | "주당 근로시간은 0 이상 168 이하여야 합니다." |
| start_date | Required | "필수 항목입니다." |
| end_date | end_date > start_date | "종료일은 시작일 이후여야 합니다." |

---

### 프론트엔드 (Vue 3 + TypeScript)

#### 1. LaborEdit.vue - 근로정보 수정 폼
```typescript
// 1. 폼 데이터 로드
async function loadFormData() {
  const response = await apiClient.get(`/labor/employees/${activeJob.value.id}/`)
  // 12개 필드에 데이터 채우기
  Object.assign(formData, response.data)
}

// 2. 폼 제출 (PATCH)
async function submitForm() {
  await apiClient.patch(`/labor/employees/${activeJob.value.id}/`, formData)
  
  // 3. 자동 갱신 (cascading)
  await fetchJobs()  // ← 중요! activeJob 업데이트
  
  // 4. RightSidebar 통계도 갱신
  const month = getMonthString()
  await fetchJobSummary(activeJob.value.id, month)
  
  // 5. 사용자 피드백
  showSuccessToast.value = true
}
```

**상태 관리**:
```typescript
formData = reactive({...})      // 폼 필드 값
formLoading = ref(false)        // 초기 로드 중
isSubmitting = ref(false)       // PATCH 요청 중
formError = ref(null)           // 로드 오류
submitError = ref(null)         // 저장 오류
showSuccessToast = ref(false)   // 성공 알림
```

#### 2. jobStore.ts - 전역 상태 관리
```typescript
// 1. fetchJobs() 호출 시 최신 Employee 데이터 로드
async function fetchJobs() {
  const response = await apiClient.get('/labor/jobs/')
  jobs.value = response.data  // 모든 필드 업데이트 (hourly_rate 포함)
}

// 2. activeJob computed는 jobs 배열 변경 감지
const activeJob = computed(() => {
  return jobs.value.find((job) => job.id === activeJobId.value) || null
})
```

#### 3. RightSidebar.vue - 통계 자동 갱신
```typescript
// 1. activeJob.id 변화 감지
watch(
  () => activeJob.value?.id,
  () => {
    loadJobSummary()  // 월별 통계 재조회
  }
)

// 2. loadJobSummary() - 새로운 시급으로 급여 재계산
async function loadJobSummary() {
  const month = getMonthString()
  const summary = await fetchJobSummary(activeJob.value.id, month)
  jobSummary.value = summary  // 이번 달 통계 갱신
}

// 3. 통계 카드에 반영
<div>총 급여 예상액: {{ formatSalary(jobSummary.estimated_salary) }}</div>
```

---

## 📱 UI 흐름

### 1. 근로정보 수정 탭 열기
```
MainLayout.vue
  → "근로정보 수정" 탭 클릭
  → LaborEdit.vue 마운트
  → onMounted() → loadFormData() → 폼 채우기
```

### 2. 폼 필드 입력
```
사용자: 시급 11500 → 13000으로 변경
폼에 입력됨 (v-model 바인딩)
저장하기 버튼 활성화
```

### 3. 저장하기 클릭
```
submitForm() 호출
  ↓
isSubmitting = true (버튼 로딩 상태)
  ↓
PATCH /api/labor/employees/{id}/ ← formData 전송
  ↓
Backend 유효성 검사 통과
  ↓
DB: Employee.hourly_rate = 13000 저장
  ↓
Frontend: Response 수신
  ↓
fetchJobs() ← 최신 정보 로드
  ↓
jobStore.activeJob.hourly_rate = 13000 (자동 업데이트)
  ↓
RightSidebar 감지 → loadJobSummary()
  ↓
GET /api/labor/jobs/{id}/summary/?month=2025-11
  ↓
Backend: 새로운 시급(13000)으로 총급여 재계산
    estimated_salary = 근로시간 × 13000
  ↓
jobSummary.value = 새로운 통계
  ↓
화면 업데이트 ✅
  ↓
showSuccessToast = true (3초 표시)
```

---

## 🧪 테스트 체크리스트

### 필수 테스트
- [ ] 폼 로드: 현재 알바 정보가 정확히 표시되는가?
- [ ] 시급 수정: 시급 변경 후 저장 → RightSidebar "총 급여" 자동 변경?
- [ ] 주당시간 수정: 주당 시간 변경 후 저장 → WorkCalendar 업데이트?
- [ ] 검증: 음수 시급 입력 → 에러 메시지 표시?
- [ ] 검증: end_date < start_date → 에러 메시지 표시?
- [ ] 성공 토스트: 저장 완료 시 토스트 3초 표시 후 사라짐?
- [ ] 탭 전환: 근로정보 수정 저장 → 근로관리 탭으로 이동 → 통계 갱신되어 있음?

### 엣지 케이스
- [ ] 여러 알바가 있을 때: 각 알바별로 독립적으로 수정 가능?
- [ ] 네트워크 지연: PATCH 요청 중 "저장 중..." 표시?
- [ ] 에러 응답: 400 에러 시 submitError 표시?
- [ ] 취소: 저장하지 않고 취소 버튼 → 원래 데이터 복원?

---

## 🔗 파일 구조

### 백엔드
```
labor/
├── models.py          # Employee 모델
├── serializers.py     # EmployeeUpdateSerializer (NEW)
├── views.py           # EmployeeViewSet with get_serializer_class()
└── urls.py            # /api/labor/jobs/ 라우팅
```

### 프론트엔드
```
src/
├── pages/
│   └── LaborEdit.vue        # 근로정보 수정 폼 (NEW)
├── components/
│   ├── MainLayout.vue       # "근로정보 수정" 탭 통합
│   ├── DashboardContent.vue # activeJob 감시
│   ├── RightSidebar.vue     # 통계 자동 갱신
│   └── WorkCalendar.vue     # activeJob.hourly_rate 기반 계산
├── stores/
│   └── jobStore.ts          # fetchJobs() 메서드
└── composables/
    └── useLabor.ts          # fetchJobSummary() 메서드
```

---

## 🚀 배포 확인사항

### 1. 백엔드 마이그레이션
```bash
python manage.py migrate  # Employee 모델 최신 상태 확인
```

### 2. API 테스트
```bash
# 폼 로드
GET /api/labor/employees/1/ 

# 폼 저장
PATCH /api/labor/employees/1/
Content-Type: application/json
{
  "hourly_rate": 13000,
  "weekly_hours": 30
}

# 통계 갱신
GET /api/labor/employees/1/summary/?month=2025-11
```

### 3. 프론트엔드 빌드
```bash
npm run build  # 또는 vite build
```

---

## 💡 주요 설계 패턴

### 1. Serializer 선택 패턴 (get_serializer_class)
```python
def get_serializer_class(self):
    if self.action in ['update', 'partial_update']:
        return EmployeeUpdateSerializer  # 검증 있음
    return EmployeeSerializer  # 검증 없음 (read-only)
```
**이점**: GET 성능 ↑, PATCH 안정성 ↑

### 2. Cascading Update 패턴
```typescript
await fetchJobs()  // 1. activeJob 업데이트
await fetchJobSummary()  // 2. 통계 재계산
// RightSidebar watch가 자동 감지
```
**이점**: 명시적 데이터 흐름, 의존성 명확함

### 3. 반응형 상태 동기화 (Reactive Sync)
```
Backend DB 변경
    ↓
Frontend fetchJobs() (GET)
    ↓
jobStore.jobs 배열 업데이트
    ↓
activeJob computed 자동 재계산
    ↓
RightSidebar watch 감지
    ↓
UI 자동 갱신
```
**이점**: 단방향 데이터 흐름, 상태 일관성 보장

---

## 📊 성능 고려사항

| 작업 | API 호출 | 시간 |
|------|---------|------|
| 폼 로드 | GET /employees/{id}/ | ~100ms |
| 폼 저장 | PATCH /employees/{id}/ | ~150ms |
| Job 목록 갱신 | GET /jobs/ | ~100ms |
| 통계 재계산 | GET /summary/ | ~200ms |
| **총소요시간** | **3개** | **~550ms** |

**최적화 방법**:
- 병렬 요청: `Promise.all([fetchJobs(), fetchJobSummary()])`
- 캐싱: localStorage에 마지막 요청 결과 저장
- 디바운싱: 폼 입력 중 유효성 검사 지연

---

## 🐛 디버깅 팁

### 1. 데이터가 갱신되지 않을 때
```javascript
// 1. fetchJobs() 호출 확인
console.log('fetchJobs() 호출됨')

// 2. activeJob 변경 확인
watch(() => activeJob.value?.id, (newId) => {
  console.log('activeJob.id 변경:', newId)
})

// 3. fetchJobSummary() 호출 확인
console.log('jobSummary:', jobSummary.value)
```

### 2. 검증 오류가 표시되지 않을 때
```python
# serializers.py에서 ValidationError 확인
raise ValidationError("메시지")  # 객체 오류
raise ValidationError({"field": "메시지"})  # 필드별 오류
```

### 3. PATCH 요청 실패
```typescript
try {
  await apiClient.patch(...)
} catch (err) {
  console.log('Response:', err.response.data)  // 상세 오류 확인
  // 예: {"hourly_rate": ["시급은 0 이상이어야 합니다."]}
}
```

---

## 📚 참고 자료

- Django REST Framework: https://www.django-rest-framework.org/
- Vue 3 Composition API: https://vuejs.org/guide/extras/composition-api-faq.html
- Reactive Programming Pattern: https://www.patterns.dev/posts/reactivity/

---

**마지막 업데이트**: 2025-11-21
**상태**: ✅ 완성 및 테스트 준비 완료
