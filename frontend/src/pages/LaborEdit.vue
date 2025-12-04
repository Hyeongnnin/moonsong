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

        <!-- 사업장 주소 -->
        <div class="mb-6">
          <label for="workplace_address" class="block text-sm font-semibold text-gray-900 mb-2">
            사업장 주소
          </label>
          <input
            id="workplace_address"
            v-model="formData.workplace_address"
            type="text"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
            placeholder="예: 서울시 강남구">
        </div>

        <!-- 업종 -->
        <div class="mb-6">
          <label for="industry" class="block text-sm font-semibold text-gray-900 mb-2">
            업종
          </label>
          <input
            id="industry"
            v-model="formData.industry"
            type="text"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
            placeholder="예: 음식료, 소매, 교육">
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
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              placeholder="예: 11500">
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">원</span>
          </div>
        </div>

        <!-- 주당 근로시간 -->
        <div class="mb-6">
          <label for="weekly_hours" class="block text-sm font-semibold text-gray-900 mb-2">
            주당 근로시간 <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              id="weekly_hours"
              v-model.number="formData.weekly_hours"
              type="number"
              required
              min="0"
              max="168"
              step="0.5"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              placeholder="예: 30">
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">시간</span>
          </div>
        </div>

        <!-- 1일 근로시간 -->
        <div class="mb-6">
          <label for="daily_hours" class="block text-sm font-semibold text-gray-900 mb-2">
            1일 근로시간
          </label>
          <div class="relative">
            <input
              id="daily_hours"
              v-model.number="formData.daily_hours"
              type="number"
              min="0"
              max="24"
              step="0.5"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              placeholder="예: 8">
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">시간</span>
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

        <!-- 근로 종료일 -->
        <div class="mb-6">
          <label for="end_date" class="block text-sm font-semibold text-gray-900 mb-2">
            근로 종료일
          </label>
          <input
            id="end_date"
            v-model="formData.end_date"
            type="date"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition">
          <p class="text-xs text-gray-500 mt-1">현재 재직 중인 경우 비워두세요.</p>
        </div>

        <!-- 주휴수당 대상 여부 -->
        <div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div class="flex items-center gap-3">
            <input
              id="has_paid_weekly_holiday"
              v-model="formData.has_paid_weekly_holiday"
              type="checkbox"
              class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-2 focus:ring-brand-500">
            <label for="has_paid_weekly_holiday" class="text-sm font-medium text-gray-900">
              주휴수당 대상
            </label>
            <p class="text-xs text-gray-500 ml-auto">주 1일 이상 근무 시 적용</p>
          </div>
        </div>

        <!-- 퇴직금 대상 여부 -->
        <div class="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div class="flex items-center gap-3">
            <input
              id="is_severance_eligible"
              v-model="formData.is_severance_eligible"
              type="checkbox"
              class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-2 focus:ring-brand-500">
            <label for="is_severance_eligible" class="text-sm font-medium text-gray-900">
              퇴직금 대상
            </label>
            <p class="text-xs text-gray-500 ml-auto">1년 이상 근무 시 적용</p>
          </div>
        </div>

        <!-- 현재 재직 중 여부 -->
        <div class="mb-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <div class="flex items-center gap-3">
            <input
              id="is_current"
              v-model="formData.is_current"
              type="checkbox"
              class="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-2 focus:ring-brand-500">
            <label for="is_current" class="text-sm font-medium text-gray-900">
              현재 재직 중
            </label>
          </div>
        </div>

        <!-- 주간 스케줄 편집기 -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-2">주간 근무 스케줄</h2>
          <WeeklyScheduleEditor :employeeId="activeJob?.id || 0" />
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

    <!-- 성공 토스트 알림 -->
    <transition name="fade">
      <div v-if="showSuccessToast" class="fixed bottom-6 right-6 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg">
        저장되었습니다!
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useJob } from '../stores/jobStore'
import { useLabor } from '../composables/useLabor'
import { apiClient } from '../api'
import WeeklyScheduleEditor from '../components/WeeklyScheduleEditor.vue'

const { activeJob, fetchJobs, setActiveJob } = useJob()
const { fetchJobSummary, getMonthString, fetchEvaluation } = useLabor()

// 폼 데이터
const formData = reactive({
  workplace_name: '',
  workplace_address: '',
  workplace_reg_no: '',
  industry: '',
  employment_type: '',
  start_date: '',
  end_date: '',
  hourly_rate: 0,
  weekly_hours: 0,
  daily_hours: 0,
  has_paid_weekly_holiday: true,
  is_severance_eligible: false,
  is_current: true,
  // 평가 추가 필드
  work_days_per_week: null as number | null,
  attendance_rate_last_year: null as number | null,
  total_wage_last_3m: null as number | null,
  total_days_last_3m: null as number | null,
})

// 상태 관리
const formLoading = ref(false)
const isSubmitting = ref(false)
const formError = ref<string | null>(null)
const submitError = ref<string | null>(null)
const showSuccessToast = ref(false)

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
      formData.workplace_address = data.workplace_address || ''
      formData.workplace_reg_no = data.workplace_reg_no || ''
      formData.industry = data.industry || ''
      formData.employment_type = data.employment_type || ''
      formData.start_date = data.start_date || ''
      formData.end_date = data.end_date || ''
      formData.hourly_rate = parseFloat(data.hourly_rate) || 0
      formData.weekly_hours = parseFloat(data.weekly_hours) || 0
      formData.daily_hours = parseFloat(data.daily_hours) || 0
      formData.has_paid_weekly_holiday = data.has_paid_weekly_holiday ?? true
      formData.is_severance_eligible = data.is_severance_eligible ?? false
      formData.is_current = data.is_current ?? true
      formData.work_days_per_week = data.work_days_per_week ?? null
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

/**
 * 폼 제출: PATCH 요청으로 데이터 저장
 */
async function submitForm() {

  submitError.value = null
  isSubmitting.value = true

  try {
    // Prepare payload by copying and normalizing date fields
    const payload: any = {
      workplace_name: formData.workplace_name,
      workplace_address: formData.workplace_address,
      workplace_reg_no: formData.workplace_reg_no,
      industry: formData.industry,
      employment_type: formData.employment_type,
      hourly_rate: formData.hourly_rate,
      weekly_hours: formData.weekly_hours,
      daily_hours: formData.daily_hours,
      has_paid_weekly_holiday: formData.has_paid_weekly_holiday,
      is_severance_eligible: formData.is_severance_eligible,
      is_current: formData.is_current,
      work_days_per_week: formData.work_days_per_week,
      attendance_rate_last_year: formData.attendance_rate_last_year,
      total_wage_last_3m: formData.total_wage_last_3m,
      total_days_last_3m: formData.total_days_last_3m,
    }

    // Normalize dates
    const sd = formatDateForApi(formData.start_date)
    const ed = formatDateForApi(formData.end_date)
    // start_date is required
    payload.start_date = sd
    // end_date: if empty/null -> send null
    payload.end_date = ed // ed will be null if empty or unparsable

    if (activeJob.value) {
      await apiClient.patch(`/labor/employees/${activeJob.value.id}/`, payload)
    } else {
      const response = await apiClient.post(`/labor/employees/`, payload)
      const created = response.data
      await fetchJobs()
      if (created?.id) setActiveJob(created.id)
    }

    // 저장 성공 → 상태 갱신
    showSuccessToast.value = true
    setTimeout(() => {
      showSuccessToast.value = false
    }, 3000)

    // 1. 전역 store의 activeJob 정보 갱신 (수정 시에도 목록 갱신)
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
  loadFormData()
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
/* 토스트 알림 애니메이션 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
