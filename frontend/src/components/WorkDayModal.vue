<template>
  <div v-if="visible" class="fixed inset-0 flex items-center justify-center z-50" style="background-color: rgba(0, 0, 0, 0.5);">
    <div class="bg-white rounded-lg w-full max-w-md p-6 shadow-xl">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">{{ dateLabel }} 근로기록</h3>
        <button @click="close" class="text-gray-500 hover:text-gray-700">✕</button>
      </div>

      <div class="space-y-4">
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
  record: { type: Object as () => any, required: false, default: null }
})

const emit = defineEmits(['close', 'saved', 'deleted'])

const timeIn = ref<string | null>(null)
const timeOut = ref<string | null>(null)
const breakMinutes = ref<number>(0)
const error = ref<string | null>(null)
const hasSchedule = ref(false)
const hasWorkRecord = computed(() => {
  const result = !!(props.record && props.record.id && !props.record.schedule_only);
  return result;
})

// 00:00 ~ 23:30까지 30분 단위 시간 옵션 생성
const timeOptions = computed(() => {
  const options = []
  for (let h = 0; h < 24; h++) {
    const hh = String(h).padStart(2, '0')
    options.push(`${hh}:00`)
    options.push(`${hh}:30`)
  }
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
watch(() => props.record, (r) => {
  console.log('[WorkDayModal] Props record changed:', r);
  
  if (r && r.schedule_only) {
    // 스케줄만 있는 경우 (실제 근로기록 없음)
    timeIn.value = roundToNearest30(r.start_time || null);
    timeOut.value = roundToNearest30(r.end_time || null);
    breakMinutes.value = 60;
    hasSchedule.value = true;
  } else if (r && r.id) {
    // 실제 근로기록이 있는 경우
    // DB에는 초 단위까지 있을 수 있으므로 slice 후 반올림 적용
    const rawIn = r.time_in ? r.time_in.split('T')[1].slice(0, 5) : null;
    const rawOut = r.time_out ? r.time_out.split('T')[1].slice(0, 5) : null;
    
    timeIn.value = roundToNearest30(rawIn);
    timeOut.value = roundToNearest30(rawOut);
    breakMinutes.value = r.break_minutes || 0;
    hasSchedule.value = false;
  } else {
    // 근로기록도 스케줄도 없음
    timeIn.value = null;
    timeOut.value = null;
    breakMinutes.value = 0;
    hasSchedule.value = false;
  }
}, { immediate: true })

const dateLabel = computed(() => {
  try {
    return new Date(props.dateIso).toLocaleDateString()
  } catch { return props.dateIso }
})

function close() {
  emit('close')
}

function validateTimes() {
  if (timeIn.value && !/^\d{2}:\d{2}$/.test(timeIn.value)) return '출근 시간이 형식에 맞지 않습니다.'
  if (timeOut.value && !/^\d{2}:\d{2}$/.test(timeOut.value)) return '퇴근 시간이 형식에 맞지 않습니다.'
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
    break_minutes: breakMinutes.value || 0
  }
  if (timeIn.value) payload.time_in = `${date}T${timeIn.value}:00`
  else payload.time_in = null
  if (timeOut.value) payload.time_out = `${date}T${timeOut.value}:00`
  else payload.time_out = null

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
  if (!confirm('정말 이 날짜의 근로를 취소하시겠습니까?\n실제 근로기록이 삭제되거나 빈 기록으로 대체됩니다.')) {
    return
  }
  
  error.value = null
  
  try {
    if (hasWorkRecord.value) {
      // 실제 기록이 있으면 삭제
      console.log('[WorkDayModal] Deleting work record:', props.record.id);
      const response = await apiClient.delete(`/labor/work-records/${props.record.id}/`)
      emit('deleted', response.data)
    } else if (hasSchedule.value) {
      // 스케줄만 있으면 빈 기록 생성하여 덮어쓰기
      console.log('[WorkDayModal] Creating empty record to cancel schedule');
      const payload: any = {
        employee: props.employeeId,
        work_date: props.dateIso,
        time_in: null,
        time_out: null,
        break_minutes: 0
      }
      const response = await apiClient.post('/labor/work-records/', payload)
      emit('saved', response.data) // Treat as saved since we created a record
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
