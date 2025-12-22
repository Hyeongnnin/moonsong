<template>
  <div class="max-w-2xl mx-auto">
    <!-- 헤더 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">근로정보 수정</h1>
      <p class="text-sm text-gray-600">현재 선택된 알바의 근로조건을 수정할 수 있습니다.</p>
    </div>

    <!-- 안내: 활성 알바가 없으면 새 알바 등록 모드로 동작 -->
    <div v-if="!activeJob" class="mb-4 p-4 bg-brand-50 border border-brand-200 rounded-lg text-sm text-brand-700">
      현재 선택된 알바가 없습니다. 아래 폼을 작성하면 새 알바가 등록되고 자동으로 선택됩니다.
    </div>

    <!-- 폼: 항상 렌더링 -->
    <div class="bg-white rounded-lg border border-gray-200 p-8 shadow-sm">
      <form @submit.prevent="submitForm">
        <!-- 사업장명 -->
        <div class="mb-6">
          <label for="workplace_name" class="block text-sm font-semibold text-gray-900 mb-2">
            사업장명 <span class="text-red-500">*</span>
          </label>
          <input
            id="workplace_name"
            v-model="formData.workplace_name"
            type="text"
            required
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
            placeholder="예: Starbucks 강남점">
        </div>

        <!-- 고용형태 -->
        <div class="mb-6">
          <label for="employment_type" class="block text-sm font-semibold text-gray-900 mb-2">
            고용형태 <span class="text-red-500">*</span>
          </label>
          <select
            id="employment_type"
            v-model="formData.employment_type"
            required
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition">
            <option value="">-- 선택하세요 --</option>
            <option value="알바">알바</option>
            <option value="정규직">정규직</option>
            <option value="계약직">계약직</option>
            <option value="프리랜서">프리랜서</option>
            <option value="기타">기타</option>
          </select>
        </div>

        <!-- 시급 -->
        <div class="mb-6">
          <label for="hourly_rate" class="block text-sm font-semibold text-gray-900 mb-2">
            시급 <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              id="hourly_rate"
              v-model.number="formData.hourly_rate"
              type="number"
              required
              min="0"
              step="100"
              class="w-full px-4 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              placeholder="2025년 최저시급은 10030원이에요">
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">원</span>
          </div>
        </div>

        <!-- 근로 시작일 -->
        <div class="mb-6">
          <label for="start_date" class="block text-sm font-semibold text-gray-900 mb-2">
            근로 시작일 <span class="text-red-500">*</span>
          </label>
          <input
            id="start_date"
            v-model="formData.start_date"
            type="date"
            required
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition">
        </div>

        <!-- 주간 스케줄 편집기 -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-2">주간 근무 스케줄</h2>
          <WeeklyScheduleEditor ref="weeklyScheduleEditorRef" :employeeId="activeJob?.id" />
        </div>

        <!-- 에러 메시지 표시 -->
        <div v-if="submitError" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-red-700 text-sm">{{ submitError }}</p>
        </div>

        <!-- 버튼 -->
        <div class="flex gap-3 justify-end">
          <button
            type="button"
            @click="cancelEdit"
            class="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
            취소
          </button>
          <button
            type="submit"
            :disabled="isSubmitting"
            class="px-6 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center gap-2">
            <span v-if="!isSubmitting">{{ activeJob ? '저장하기' : '등록하고 선택하기' }}</span>
            <span v-else>저장 중...</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useJob } from '../stores/jobStore'
import { useLabor } from '../composables/useLabor'
import { apiClient } from '../api'
import WeeklyScheduleEditor from '../components/WeeklyScheduleEditor.vue'

const router = useRouter()
const { activeJob, fetchJobs, setActiveJob } = useJob()
const { fetchJobSummary, getMonthString, fetchEvaluation } = useLabor()

// 폼 데이터
const formData = reactive({
  workplace_name: '',
  workplace_reg_no: '',
  employment_type: '',
  start_date: '',
  hourly_rate: 0,
  // 평가 추가 필드
  attendance_rate_last_year: null as number | null,
  total_wage_last_3m: null as number | null,
  total_days_last_3m: null as number | null,
})

// 상태 관리
const formLoading = ref(false)
const isSubmitting = ref(false)
const formError = ref<string | null>(null)
const submitError = ref<string | null>(null)

// WeeklyScheduleEditor 컴포넌트 참조
const weeklyScheduleEditorRef = ref<InstanceType<typeof WeeklyScheduleEditor> | null>(null)

/**
 * 폼 로드: activeJob의 현재 데이터를 폼에 채우기
 */
async function loadFormData() {
  formLoading.value = true
  try {
    // 활성 알바가 있으면 서버 최신값으로 폼 채우기
    if (activeJob.value) {
      const response = await apiClient.get(`/labor/employees/${activeJob.value.id}/`)
      const data = response.data
      formData.workplace_name = data.workplace_name || ''
      formData.workplace_reg_no = data.workplace_reg_no || ''
      formData.employment_type = data.employment_type || ''
      formData.start_date = data.start_date || ''
      formData.hourly_rate = parseFloat(data.hourly_rate) || 0
      formData.attendance_rate_last_year = data.attendance_rate_last_year ?? null
      formData.total_wage_last_3m = data.total_wage_last_3m ?? null
      formData.total_days_last_3m = data.total_days_last_3m ?? null
    } else {
      // 활성 알바가 없으면 기본값 유지 (새 알바 등록 모드)
      formError.value = null
    }
  } catch (err: any) {
    formError.value = err.response?.data?.detail || '근로정보를 불러올 수 없습니다.'
    console.error('Failed to load form data:', err)
  } finally {
    formLoading.value = false
  }
}

/**
 * helper: convert various displayed date formats to 'YYYY-MM-DD' for API
 */
function pad(n: string | number) {
  return String(n).padStart(2, '0')
}
function formatDateForApi(value: string | null | undefined) {
  if (!value) return null
  value = value.trim()
  // If already ISO-like YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value
  // Match patterns like '2025. 07. 27.' or '2025.07.27' or '2025. 7. 27.'
  const m = value.match(/(\d{4}).*?(\d{1,2}).*?(\d{1,2})/)
  if (m) {
    const y = m[1]
    const mo = pad(m[2])
    const d = pad(m[3])
    return `${y}-${mo}-${d}`
  }
  // As a fallback, try Date parsing and format (avoid timezone issues)
  const dt = new Date(value)
  if (!isNaN(dt.getTime())) {
    const y = dt.getFullYear()
    const mo = pad(dt.getMonth() + 1)
    const d = pad(dt.getDate())
    return `${y}-${mo}-${d}`
  }
  return null
}

// helper: 시급 포맷팅 (표시용)
function formatWage(v: number) {
  return v.toLocaleString('ko-KR', { maximumFractionDigits: 0, minimumFractionDigits: 0 }) + '원'
}

/**
 * 폼 제출: PATCH 요청으로 데이터 저장
 */
async function submitForm() {
  // 저장 확인
  if (!confirm('근로정보를 저장하시겠습니까?')) {
    return
  }

  const scheduleSnapshot = weeklyScheduleEditorRef.value?.exportSchedules?.()
  submitError.value = null
  isSubmitting.value = true

  try {
    // Prepare payload by copying and normalizing date fields
    const payload: any = {
      workplace_name: formData.workplace_name,
      workplace_reg_no: formData.workplace_reg_no,
      employment_type: formData.employment_type,
      hourly_rate: formData.hourly_rate,
      attendance_rate_last_year: formData.attendance_rate_last_year,
      total_wage_last_3m: formData.total_wage_last_3m,
      total_days_last_3m: formData.total_days_last_3m,
    }

    // Normalize dates
    const sd = formatDateForApi(formData.start_date)
    // start_date is required
    payload.start_date = sd

    if (activeJob.value) {
      await apiClient.patch(`/labor/employees/${activeJob.value.id}/`, payload)
      
      // 스케줄 저장 시도
      try {
        if (weeklyScheduleEditorRef.value) {
          await weeklyScheduleEditorRef.value.saveSchedules()
        }
      } catch (schedErr) {
        console.warn('스케줄 저장 중 오류 발생:', schedErr)
      }
    } else {
      const response = await apiClient.post(`/labor/employees/`, payload)
      const created = response.data
      await fetchJobs()
      if (created?.id) {
        setActiveJob(created.id)
        
        // 새로 생성된 employee ID로 스케줄 저장 시도
        // 약간의 딜레이를 줘서 prop이 업데이트되도록 함
        try {
          if (weeklyScheduleEditorRef.value) {
            await weeklyScheduleEditorRef.value.saveSchedules({
              schedules: scheduleSnapshot || undefined,
              employeeId: created.id
            })
          }
        } catch (schedErr) {
          console.warn('스케줄 저장 중 오류 발생:', schedErr)
        }
      }
    }

    // 1. 전역 store의 activeJob 정보 갱신
    await fetchJobs()

    // 2. RightSidebar의 요약 데이터 다시 로드
    const month = getMonthString()
    if (activeJob.value) {
      await fetchJobSummary(activeJob.value.id, month)
    }

    // 3. 평가 결과 재조회 및 카드 갱신 트리거
    try {
      if (activeJob.value) {
        await fetchEvaluation(activeJob.value.id)
      }
    } catch (e) {
      console.warn('평가 결과 재조회 실패', e)
    }
    window.dispatchEvent(new CustomEvent('job-updated'))

    console.log('근로정보 저장 및 평가 갱신 완료')
    
    // 저장 성공 알림 표시
    alert('근로정보가 저장되었습니다.')
    
    // 근로관리 페이지로 이동 (이벤트 처리 시간을 위해 약간의 지연)
    setTimeout(() => {
      router.push('/dashboard?section=labor')
    }, 100)
  } catch (err: any) {
    console.error('Failed to save employee data:', err)
    const detail = err?.response?.data?.detail
    const fieldErrors = err?.response?.data && typeof err.response.data === 'object'
      ? Object.values(err.response.data).flat().join(', ')
      : ''
    submitError.value = detail || fieldErrors || '저장에 실패했습니다. 서버 연결 또는 인증을 확인해주세요.'
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 수정 취소
 */
function cancelEdit() {
  router.push('/dashboard?section=labor')
}

// 컴포넌트 마운트 시 폼 데이터 로드
onMounted(() => {
  loadFormData()
})

// Watch for changes in selected job and reload form accordingly
watch(activeJob, (newVal, oldVal) => {
  // Only reload when job selection actually changes
  if ((newVal && !oldVal) || (newVal && oldVal && newVal.id !== oldVal.id) || (!newVal && oldVal)) {
    loadFormData()
  }
})
</script>

<style scoped>
/* 시급 입력 스피너 제거 & 우측 단위와 겹침 방지 */
#hourly_rate::-webkit-outer-spin-button,
#hourly_rate::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}
#hourly_rate[type=number] {
  -moz-appearance: textfield; /* Firefox */
}
</style>
