<template>
  <div v-if="visible" class="fixed inset-0 flex items-center justify-center z-50" style="background-color: rgba(0, 0, 0, 0.5);">
    <div class="bg-white rounded-lg w-full max-w-md p-6 shadow-xl">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">{{ dateLabel }} 근로기록</h3>
        <button @click="close" class="text-gray-500 hover:text-gray-700">✕</button>
      </div>

      <div class="space-y-4">
        <!-- 소정근로일 안내 메시지 (Phase 3) -->
        <div
          v-if="isScheduledWorkday"
          class="flex items-center gap-2 text-sm font-semibold text-orange-700 bg-orange-50 border border-orange-200 rounded px-3 py-2"
        >
          <span>📋 소정근로일</span>

        </div>
        <div
          v-else-if="!isScheduledWorkday && hasAnyTime"
          class="flex items-center gap-2 text-sm font-semibold text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2"
        >
          <span>➕ 추가 근무</span>
          <span class="text-xs text-green-600">예정일 외 근무입니다</span>
        </div>
        
        <div
          v-if="holidayName"
          class="flex items-center gap-2 text-sm font-semibold text-red-600 bg-red-50 border border-red-100 rounded px-3 py-2"
        >
          <span>🎌 법정공휴일 근무</span>
          <span class="truncate">{{ holidayName }}</span>
        </div>
        <div
          v-else-if="weeklyRestName"
          class="flex items-center gap-2 text-sm font-semibold text-sky-700 bg-sky-50 border border-sky-100 rounded px-3 py-2"
        >
          <span>🛌 주휴일 근무</span>
          <span class="truncate">{{ weeklyRestName }}</span>
        </div>
        <div>
          <label class="block text-sm text-gray-700 mb-1">출근 시간</label>
          <TimeSelect 
            v-model="timeIn" 
            :options="timeOptions"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-700 mb-1">퇴근 시간</label>
          <TimeSelect 
            v-model="timeOut" 
            :options="timeOptions"
            class="w-full"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-700 mb-1">휴게(분)</label>
          <input type="number" v-model.number="breakMinutes" min="0" class="w-full px-3 py-2 border rounded" />
        </div>
        
        <!-- 익일 근무 시간 입력 -->
        <div class="border-t border-gray-200 pt-4 mt-2">
          <div class="flex items-center gap-2 mb-2">
            <input 
              id="hasNextDayWork" 
              type="checkbox" 
              v-model="hasNextDayWork" 
              class="rounded border-gray-300"
            />
            <label for="hasNextDayWork" class="text-sm font-medium text-gray-700">
              익일 근무 있음 (24:00~06:00)
            </label>
          </div>
          <div v-if="hasNextDayWork" class="ml-6">
            <label class="block text-sm text-gray-600 mb-1">익일 근무 시간 (분)</label>
            <input 
              type="number" 
              v-model.number="nextDayWorkMinutes" 
              min="0" 
              max="360" 
              step="30"
              class="w-full px-3 py-2 border rounded text-sm"
              placeholder="0~360분 (최대 6시간)"
            />
            <p class="text-xs text-gray-500 mt-1">
              💡 당일 24:00부터 다음날 06:00 사이의 추가 근로시간을 입력하세요.
            </p>
            <p class="text-xs text-brand-600 font-medium mt-1">
              ✨ 22:00~06:00 사이의 모든 근무(익일 포함)는 50% 가산수당이 자동 적용됩니다.
            </p>
          </div>
        </div>
        
        <!-- Phase 3: 출결 상태 선택 (5가지) -->
        <div>
          <label class="block text-sm text-gray-700 mb-1 font-medium">출결 상태</label>
          <select v-model="attendanceStatus" class="w-full px-3 py-2 border rounded">
            <option value="REGULAR_WORK">✅ 소정근로 (정상 출근)</option>
            <option value="EXTRA_WORK">➕ 추가근무 (대타/초과근무)</option>
            <option value="ANNUAL_LEAVE">🌴 연차 사용</option>
            <option value="ABSENT">❌ 결근</option>
            <option value="SICK_LEAVE">🤒 병가</option>
          </select>
          <p class="text-xs text-gray-500 mt-1">
            💡 주휴수당 자격: <strong>소정근로</strong>와 <strong>연차</strong>만 출근으로 인정됩니다.
          </p>
        </div>
        
        <div v-if="error" class="text-sm text-red-600">{{ error }}</div>
      </div>

      <div class="mt-6 flex items-center justify-between gap-2">
        <button 
          @click="onCancelWorkDay" 
          v-if="hasWorkRecord || hasSchedule"
          class="px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
          title="이 날짜의 근로기록을 삭제합니다"
        >
          근로날짜 취소
        </button>
        <div class="flex gap-2 ml-auto">
          <button @click="close" class="px-4 py-2 bg-gray-100 rounded hover:bg-gray-200">취소</button>
          <button @click="onSave" class="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700">저장</button>
        </div>
      </div>
  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiClient } from '../api'
import TimeSelect from './TimeSelect.vue'

const props = defineProps({
  visible: { type: Boolean, required: true },
  employeeId: { type: Number, required: false, default: null },
  dateIso: { type: String, required: true },
  record: { type: Object as () => any, required: false, default: null },
  holidayName: { type: String, required: false, default: null },
  weeklyRestName: { type: String, required: false, default: null }
})

const emit = defineEmits(['close', 'saved', 'deleted'])

const timeIn = ref<string | null>(null)
const timeOut = ref<string | null>(null)
const breakMinutes = ref<number>(0)
const hasNextDayWork = ref<boolean>(false)
const nextDayWorkMinutes = ref<number>(0)
const attendanceStatus = ref<string>('REGULAR_WORK')  // Phase 3: 5가지 출결 상태
const error = ref<string | null>(null)
const hasSchedule = ref(false)
const isScheduledWorkday = ref(false)  // Phase 3: 소정근로일 여부
const hasWorkRecord = computed(() => {
  const result = !!(props.record && props.record.id && !props.record.schedule_only);
  return result;
})

const hasAnyTime = computed(() => {
  return !!(timeIn.value || timeOut.value)
})

// 00:00 ~ 24:00까지 30분 단위 시간 옵션 생성
const timeOptions = computed(() => {
  const options = []
  for (let h = 0; h < 24; h++) {
    const hh = String(h).padStart(2, '0')
    options.push(`${hh}:00`)
    options.push(`${hh}:30`)
  }
  options.push('24:00')  // 24:00 추가
  return options
})

/**
 * 30분 단위 반올림 함수
 */
function roundToNearest30(timeStr: string | null): string | null {
  if (!timeStr) return null
  
  // HH:MM:SS format handling
  const parts = timeStr.split(':')
  if (parts.length < 2) return null
  
  let h = parseInt(parts[0], 10)
  let m = parseInt(parts[1], 10)
  
  if (m < 15) {
    m = 0
  } else if (m < 45) {
    m = 30
  } else {
    m = 0
    h += 1
  }
  
  if (h >= 24) h = 0
  
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

// props.record 변경 감지 - 실제 근로기록 또는 스케줄 정보 로드
// [Fix] 스케줄 정보 복원을 위해 항상 상세 데이터를 가져오거나, 최소한 백그라운드 스케줄 정보를 확보해야 합니다.
const scheduledTimeIn = ref<string | null>(null)
const scheduledTimeOut = ref<string | null>(null)
const scheduledBreakMinutes = ref<number>(0)
const scheduledNextDay = ref<number>(0)

watch(() => props.record, async (r) => {
  console.log('[WorkDayModal] Props record changed:', r);
  
  // 1. 초기값 설정 (UI 표시용)
  if (r && r.schedule_only) {
    // 스케줄만 있는 경우
    timeIn.value = roundToNearest30(r.start_time || null);
    timeOut.value = roundToNearest30(r.end_time || null);
    breakMinutes.value = r.break_minutes || 60;
    hasSchedule.value = true;
    
    hasNextDayWork.value = (r.next_day_work_minutes || 0) > 0;
    nextDayWorkMinutes.value = r.next_day_work_minutes || 0;
    
    isScheduledWorkday.value = r.is_scheduled_workday || false;
    attendanceStatus.value = 'REGULAR_WORK';
    
    // 백업해두기
    scheduledTimeIn.value = timeIn.value
    scheduledTimeOut.value = timeOut.value
    scheduledBreakMinutes.value = breakMinutes.value
    scheduledNextDay.value = nextDayWorkMinutes.value
    
  } else if (r && r.id) {
    // 실제 근로기록이 있는 경우 (ABSENT 등 포함)
    const rawIn = r.time_in ? r.time_in.split('T')[1].slice(0, 5) : null;
    const rawOut = r.time_out ? r.time_out.split('T')[1].slice(0, 5) : null;
    
    timeIn.value = roundToNearest30(rawIn);
    timeOut.value = roundToNearest30(rawOut);
    breakMinutes.value = r.break_minutes || 0;
    
    hasNextDayWork.value = !!r.next_day_work_minutes && r.next_day_work_minutes > 0;
    nextDayWorkMinutes.value = r.next_day_work_minutes || 0;
    
    attendanceStatus.value = r.attendance_status || 'REGULAR_WORK';
    isScheduledWorkday.value = r.is_scheduled_workday || false;
    hasSchedule.value = false;
    
    // [Fix] 실제 기록이 있더라도, "원래 스케줄"이 무엇이었는지 알기 위해 API 호출 필요
    // (특히 ABSENT -> REGULAR_WORK 복구 시 자동 입력을 위해)
    await fetchBackingSchedule()
    
  } else {
    // 근로기록도 스케줄도 없음 (Init from API)
    await fetchBackingSchedule()
    
    // API 호출 결과(scheduledTimeIn 등)를 현재 값으로 적용
    if (scheduledTimeIn.value) {
        timeIn.value = scheduledTimeIn.value
        timeOut.value = scheduledTimeOut.value
        breakMinutes.value = scheduledBreakMinutes.value
        nextDayWorkMinutes.value = scheduledNextDay.value
        hasNextDayWork.value = scheduledNextDay.value > 0
        hasSchedule.value = true
        attendanceStatus.value = 'REGULAR_WORK'
    } else {
        // 완전 빈 상태
        timeIn.value = null
        timeOut.value = null
        breakMinutes.value = 0
        hasNextDayWork.value = false
        attendanceStatus.value = 'EXTRA_WORK' // 스케줄 없으면 기본 추가근무
    }
  }
}, { immediate: true })

// Helper: 원래 스케줄 정보만 가져오기
async function fetchBackingSchedule() {
    if (!props.employeeId || !props.dateIso) return
    
    try {
        const response = await apiClient.get(
          `/labor/employees/${props.employeeId}/date-schedule/`,
          { params: { date: props.dateIso } }
        );
        const info = response.data
        
        isScheduledWorkday.value = info.is_scheduled_workday || false
        
        if (info.has_schedule && info.start_time) {
            scheduledTimeIn.value = info.start_time
            scheduledTimeOut.value = info.end_time
            scheduledBreakMinutes.value = info.break_minutes || 0
            scheduledNextDay.value = info.next_day_work_minutes || 0
            hasSchedule.value = true
        } else {
            // 스케줄 없음
            scheduledTimeIn.value = null
            scheduledTimeOut.value = null
            scheduledBreakMinutes.value = 0
            scheduledNextDay.value = 0
            hasSchedule.value = false
        }
        
    } catch (e) {
        console.error('Failed to fetch schedule info', e)
    }
}

// Watcher: 출결 상태를 '소정근로'로 변경 시, 시간이 비어있으면 스케줄 시간 자동 입력
watch(attendanceStatus, (newVal) => {
    if (newVal === 'REGULAR_WORK') {
        // 시간이 모두 비어있고, 백업된 스케줄이 있다면 복원
        if (!timeIn.value && !timeOut.value && scheduledTimeIn.value) {
            timeIn.value = scheduledTimeIn.value
            timeOut.value = scheduledTimeOut.value
            breakMinutes.value = scheduledBreakMinutes.value
            nextDayWorkMinutes.value = scheduledNextDay.value
            hasNextDayWork.value = scheduledNextDay.value > 0
        }
    }
})

const dateLabel = computed(() => {
  try {
    return new Date(props.dateIso).toLocaleDateString()
  } catch { return props.dateIso }
})

function close() {
  emit('close')
}

function validateTimes() {
  if (timeIn.value && !/^(\d{2}:\d{2}|24:00)$/.test(timeIn.value)) return '출근 시간이 형식에 맞지 않습니다.'
  if (timeOut.value && !/^(\d{2}:\d{2}|24:00)$/.test(timeOut.value)) return '퇴근 시간이 형식에 맞지 않습니다.'
  
  // 익일 근무 시간 검증
  if (hasNextDayWork.value) {
    const minutes = nextDayWorkMinutes.value || 0
    if (minutes < 0 || minutes > 360) {
      return '익일 근무 시간은 0~360분 사이여야 합니다.'
    }
  }
  
  return null
}

async function onSave() {
  error.value = null
  const v = validateTimes()
  if (v) { error.value = v; return }

  if (!props.employeeId) { 
    error.value = '직원이 선택되지 않았습니다.'; 
    console.error('[WorkDayModal] No employeeId provided');
    return 
  }

  const date = props.dateIso
  const payload: any = {
    employee: props.employeeId,
    work_date: date,
    break_minutes: breakMinutes.value || 0,
    next_day_work_minutes: hasNextDayWork.value ? (nextDayWorkMinutes.value || 0) : 0,
    attendance_status: attendanceStatus.value  // Phase 3: 새로운 필드
  }
  
  // 시간 변환
  if (timeIn.value) {
    if (timeIn.value === '24:00') {
      const nextDate = new Date(date)
      nextDate.setDate(nextDate.getDate() + 1)
      payload.time_in = `${nextDate.toISOString().split('T')[0]}T00:00:00`
    } else {
      payload.time_in = `${date}T${timeIn.value}:00`
    }
  } else {
    payload.time_in = null
  }
  
  if (timeOut.value) {
    let tOutDate = date
    let isOver = false
    
    // [Fix] 퇴근 시간이 24:00이거나, 출근 시간보다 앞선 경우(예: 22:00 출근 - 02:00 퇴근) 익일로 처리
    if (timeOut.value === '24:00') {
      const nextDate = new Date(date)
      nextDate.setDate(nextDate.getDate() + 1)
      tOutDate = nextDate.toISOString().split('T')[0]
      payload.time_out = `${tOutDate}T00:00:00`
      isOver = true
    } else {
      // 출근 시간이 있고, 퇴근 시간이 출근 시간보다 작으면 익일로 간주
      if (timeIn.value && timeIn.value !== '24:00' && timeOut.value < timeIn.value) {
        const nextDate = new Date(date)
        nextDate.setDate(nextDate.getDate() + 1)
        tOutDate = nextDate.toISOString().split('T')[0]
        isOver = true
      }
      payload.time_out = `${tOutDate}T${timeOut.value}:00`
    }
    payload.is_overnight = isOver
  } else {
    payload.time_out = null
    payload.is_overnight = false
  }

  console.log('[WorkDayModal] Saving with payload:', payload);

  try {
    let response
    if (props.record && props.record.id && !props.record.schedule_only) {
      console.log('[WorkDayModal] Updating existing record:', props.record.id);
      response = await apiClient.patch(`/labor/work-records/${props.record.id}/`, payload)
    } else {
      console.log('[WorkDayModal] Creating new record');
      response = await apiClient.post('/labor/work-records/', payload)
    }
    
    emit('saved', response.data)
    window.dispatchEvent(new CustomEvent('labor-updated')) // Auto-refresh sidebar
    close()
  } catch (e: any) {
    console.error('save failed', e)
    
    if (e?.response?.data) {
      const errorData = e.response.data
      if (typeof errorData === 'object') {
        const errorMessages = Object.entries(errorData)
          .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
          .join('\n')
        error.value = errorMessages || '저장 중 오류가 발생했습니다.'
      } else {
        error.value = String(errorData) || '저장 중 오류가 발생했습니다.'
      }
    } else {
      error.value = e?.message || '저장 중 오류가 발생했습니다.'
    }
  }
}

async function onCancelWorkDay() {
  if (!confirm('정말 이 날짜의 근로를 취소하시겠습니까?\n소정근로일인 경우 결근으로 처리되며, 그 외의 경우 기록이 삭제됩니다.')) {
    return
  }
  
  error.value = null
  
  try {
    if (isScheduledWorkday.value) {
      // 소정근로일인 경우: 삭제하지 않고 ABSENT 상태로 저장 (그래야 예정 통계에 합산되지 않음)
      console.log('[WorkDayModal] Canceling scheduled workday - marking as ABSENT');
      const payload: any = {
        employee: props.employeeId,
        work_date: props.dateIso,
        time_in: null,
        time_out: null,
        break_minutes: 0,
        attendance_status: 'ABSENT'
      }
      
      let response
      if (hasWorkRecord.value) {
        response = await apiClient.patch(`/labor/work-records/${props.record.id}/`, payload)
      } else {
        response = await apiClient.post('/labor/work-records/', payload)
      }
      emit('saved', response.data)
    } else {
      // 소정근로일이 아닌 경우: 실제 기록이 있으면 완전 삭제
      if (hasWorkRecord.value) {
        console.log('[WorkDayModal] Deleting extra work record:', props.record.id);
        const response = await apiClient.delete(`/labor/work-records/${props.record.id}/`)
        emit('deleted', response.data)
      } else {
        // 스케줄도 없고 기록도 없는 경우 (이론상 버튼 비활성화)
        close()
        return
      }
    }
    
    window.dispatchEvent(new CustomEvent('labor-updated')) // Auto-refresh sidebar
    close()
  } catch (e: any) {
    console.error('[WorkDayModal] Cancel failed:', e)
    error.value = e?.response?.data?.detail || '취소 중 오류가 발생했습니다.'
  }
}
</script>

<style scoped>
</style>
