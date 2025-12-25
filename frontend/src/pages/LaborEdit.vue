<template>
  <div class="max-w-2xl mx-auto">
    <!-- 헤더 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">알바 근로정보 수정</h1>
      <p class="text-sm text-gray-600">현재 선택된 알바의 근로조건을 수정할 수 있습니다.</p>
    </div>

    <!-- 안내: 활성 알바가 없으면 새 알바 등록 모드로 동작 -->
    <div v-if="!activeJob" class="mb-4 p-4 bg-brand-50 border border-brand-200 rounded-lg text-sm text-brand-700">
      현재 선택된 알바가 없습니다. 아래 폼을 작성하면 새 알바가 등록되고 자동으로 선택됩니다.
    </div>

    <!-- 폼 -->
    <div class="p-4">
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

        <!-- 5인 이상 사업장 여부 -->
        <div class="mb-6">
          <label for="is_workplace_over_5" class="block text-sm font-semibold text-gray-900 mb-2">
            5인 이상 사업장인가요?
          </label>
          <select
            id="is_workplace_over_5"
            v-model="formData.is_workplace_over_5"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition">
            <option :value="false">아니오 (5인 미만)</option>
            <option :value="true">예 (5인 이상)</option>
          </select>
          <p class="mt-1 text-xs text-gray-500">
            사업장 규모에 따라 연차수당 등 근로조건이 달라질 수 있습니다.
          </p>
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
              step="1"
              class="w-full px-4 pr-12 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition"
              placeholder="2025년 최저시급은 10030원이에요">
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">원</span>
          </div>
        </div>


        <!-- 공제 방식 선택 -->
        <div class="mb-6">
          <label for="deduction_type" class="block text-sm font-semibold text-gray-900 mb-2">
            공제 방식 선택
          </label>
          <select
            id="deduction_type"
            v-model="formData.deduction_type"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-transparent transition">
            <option value="NONE">잘 모르겠어요 (기본)</option>
            <option value="FOUR_INSURANCE">4대보험 적용</option>
            <option value="FREELANCE">3.3% 공제 (프리랜서/삼쩜삼)</option>
          </select>
          <p class="mt-1 text-xs text-gray-500">
            실수령액 계산을 위해 필요한 정보입니다. 정확히 모르면 '잘 모르겠어요'를 선택하세요.
          </p>
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

        <!-- 기본 정보만 별도 저장 버튼 -->
        <div class="mb-8 flex justify-end">
          <button
            type="button"
            @click="saveBasicInfo"
            :disabled="isSubmitting"
            class="px-4 py-2 text-sm font-medium text-brand-700 bg-brand-50 border border-brand-200 rounded-lg hover:bg-brand-100 transition-colors flex items-center gap-2"
          >
            <span v-if="!isSubmitting">📝 기본 정보만 저장</span>
            <span v-else>저장 중...</span>
          </button>
        </div>

        <!-- 주간 스케줄 편집기 -->
        <div class="mb-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-2">주간 근무 스케줄</h2>
          <WeeklyScheduleEditor ref="weeklyScheduleEditorRef" :employeeId="activeJob?.id" />
        </div>

        <!-- 계약상 주 소정근로시간 -->
        <div class="mb-6">
          <div class="flex items-center justify-between mb-2">
            <label for="contract_weekly_hours" class="block text-sm font-semibold text-gray-900">
              계약상 주 소정근로시간(시간)
            </label>
            <button 
              type="button"
              @click="toggleManualInput"
              class="text-xs font-medium text-brand-600 hover:text-brand-700 bg-brand-50 px-2 py-1 rounded border border-brand-200 transition-colors"
            >
              {{ isManualInput ? '주간 스케줄로 자동 계산' : '직접 근로시간 입력' }}
            </button>
          </div>
          <div class="relative">
            <input
              id="contract_weekly_hours"
              v-model.number="formData.contract_weekly_hours"
              type="number"
              min="0"
              max="60"
              step="0.5"
              :readonly="!isManualInput"
              :class="[
                'w-full px-4 pr-12 py-2 border rounded-lg transition',
                isManualInput 
                  ? 'border-gray-300 focus:ring-2 focus:ring-brand-500 focus:border-transparent bg-white' 
                  : 'border-gray-200 bg-gray-50 cursor-not-allowed text-gray-600'
              ]"
              placeholder="예: 20, 40">
            <span class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500">시간</span>
          </div>
          <p class="mt-1 text-xs text-gray-500">
            {{ isManualInput 
              ? '직접 입력 모드입니다. 근로계약서에 적힌 주 소정근로시간을 입력하세요.' 
              : '주간 스케줄을 기준으로 자동 계산됩니다. 직접 입력하려면 위 버튼을 클릭하세요.'
            }}
          </p>
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
            <span v-if="!isSubmitting">{{ activeJob ? '전체 저장하기' : '등록하고 선택하기' }}</span>
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
  employment_type: '알바',
  is_workplace_over_5: false,
  start_date: '',
  hourly_rate: 0,
  contract_weekly_hours: null as number | null,
  deduction_type: 'NONE',
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

// 수동 입력 모드 상태
const isManualInput = ref(false)

// 수동 입력 모드 토글
function toggleManualInput() {
  isManualInput.value = !isManualInput.value
  
  // 자동 계산 모드로 전환 시 즉시 스케줄 기반으로 계산
  if (!isManualInput.value) {
    autoFillContractHours(true) // silent mode
  }
}

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
      formData.employment_type = '알바'
      formData.is_workplace_over_5 = data.is_workplace_over_5 || false
      formData.start_date = data.start_date || ''
      formData.hourly_rate = parseFloat(data.hourly_rate) || 0
      formData.contract_weekly_hours = data.contract_weekly_hours ?? null
      formData.deduction_type = data.deduction_type || 'NONE'
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
 * 기본 정보만 저장 (스케줄 제외)
 */
async function saveBasicInfo() {
  if (!activeJob.value) {
    alert('새 알바 등록 시에는 하단의 [등록하고 선택하기]를 이용해주세요.')
    return
  }
  
  isSubmitting.value = true
  submitError.value = null
  
  try {
    // 기본 정보만 포함된 페이로드 준비
    const payload: any = {
      workplace_name: formData.workplace_name,
      is_workplace_over_5: formData.is_workplace_over_5,
      hourly_rate: formData.hourly_rate,
      deduction_type: formData.deduction_type,
    }
    
    // Normalize dates
    const sd = formatDateForApi(formData.start_date)
    if (sd) {
      payload.start_date = sd
    }

    // PATCH 요청
    await apiClient.patch(`/labor/employees/${activeJob.value.id}/`, payload)
    
    // 스토어 및 데이터 갱신
    await fetchJobs()
    const month = getMonthString()
    await fetchJobSummary(activeJob.value.id, month)
    try {
      await fetchEvaluation(activeJob.value.id)
    } catch (e) {}
    
    window.dispatchEvent(new CustomEvent('job-updated'))
    window.dispatchEvent(new CustomEvent('labor-updated')) // 통계/업적 갱신용
    
    alert('기본 정보가 저장되었습니다.')
    
  } catch (err: any) {
    console.error('Failed to save basic info:', err)
    submitError.value = '기본 정보 저장 실패: ' + (err?.response?.data?.detail || '알 수 없는 오류')
  } finally {
    isSubmitting.value = false
  }
}

/**
 * 폼 제출: PATCH 요청으로 데이터 저장
 */
async function submitForm() {
  // 저장 확인
  if (!confirm('근로정보를 전체 저장하시겠습니까?')) {
    return
  }

  // 제출 직전 자동 계산 모드라면 스케줄 기반 시간 최신화
  if (!isManualInput.value) {
    autoFillContractHours(true)
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
      is_workplace_over_5: formData.is_workplace_over_5,
      hourly_rate: formData.hourly_rate,
      contract_weekly_hours: formData.contract_weekly_hours,
      deduction_type: formData.deduction_type,
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
    window.dispatchEvent(new CustomEvent('labor-updated')) // 통계 갱신용
    
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
 * 주간 스케줄 합계를 계산하여 계약상 시간에 자동 입력
 */
function autoFillContractHours(silent = false) {
  const scheduleSnapshot = weeklyScheduleEditorRef.value?.exportSchedules?.()
  if (!scheduleSnapshot) {
    if (!silent) alert('설정된 주간 스케줄이 없습니다.')
    return
  }

  const schedules = Object.values(scheduleSnapshot)
  if (schedules.length === 0) {
    if (!silent) alert('설정된 주간 스케줄이 없습니다.')
    return
  }

  let totalMinutes = 0
  schedules.forEach((s: any) => {
    if (s.enabled && s.start_time && s.end_time) {
      const [sh, sm] = s.start_time.split(':').map(Number)
      const [eh, em] = s.end_time.split(':').map(Number)
      
      // 1. 기본 근무 시간 계산 (종료시간 - 시작시간)
      let diffMinutes = (eh * 60 + em) - (sh * 60 + sm)
      
      // 2. 휴게 시간 제외
      if (s.break_minutes) {
        diffMinutes -= s.break_minutes
      }
      
      // 3. 익일 근무 시간 추가 (있는 경우)
      if (s.has_next_day_work && s.next_day_work_minutes) {
        diffMinutes += s.next_day_work_minutes
      }
      
      totalMinutes += Math.max(0, diffMinutes)
    }
  })

  formData.contract_weekly_hours = parseFloat((totalMinutes / 60).toFixed(1))
  const totalHours = totalMinutes / 60
  
  if (totalHours > 40 && !silent) {
    // 40시간 초과 시 경고 (법적 소정근로시간 한도는 40시간이지만 계약상 입력은 가능하게 유지)
    console.warn('법적 소정근로시간은 주 40시간입니다. 계약서 기준이면 괜찮습니다.')
  }
}

/**
 * 수정 취소
 */
function cancelEdit() {
  router.push('/dashboard?section=labor')
}

// 컴포넌트 마운트 시 폼 데이터 로드
onMounted(async () => {
  await loadFormData()
  
  // 폼 로드 후 스케줄 기반으로 자동 계산 (약간의 딜레이를 줘서 WeeklyScheduleEditor가 준비되도록 함)
  setTimeout(() => {
    if (!isManualInput.value) {
      autoFillContractHours(true) // silent mode
    }
  }, 500)
  
  // 주기적으로 스케줄 변경사항 확인하여 자동 계산 (자동 모드일 때만)
  const intervalId = setInterval(() => {
    if (!isManualInput.value && weeklyScheduleEditorRef.value) {
      autoFillContractHours(true) // silent mode
    }
  }, 2000) // 2초마다 확인
  
  // 컴포넌트 언마운트 시 인터벌 정리
  return () => clearInterval(intervalId)
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
