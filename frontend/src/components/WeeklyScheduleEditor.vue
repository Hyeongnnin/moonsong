<template>
  <div class="space-y-4">
    <p class="text-sm text-gray-600">저장 시 캘린더 전체 근로시간이 변경돼요! 월별 및 일별 근로정보 변경은 캘린더에서 해주세요.</p>
    <div class="grid grid-cols-1 gap-3">
      <div v-for="d in weekdays" :key="d.value" class="flex items-center gap-3">
        <div class="w-20 text-sm font-medium">{{ d.label }}</div>
        
        <!-- 시작 시간 Select -->
        <TimeSelect
          v-model="localSchedules[d.value].start_time" 
          :options="timeOptions"
          :disabled="!localSchedules[d.value].enabled"
        />
        
        <span class="text-xs text-gray-400">~</span>
        
        <!-- 종료 시간 Select -->
        <TimeSelect
          v-model="localSchedules[d.value].end_time" 
          :options="timeOptions"
          :disabled="!localSchedules[d.value].enabled"
        />
        
        <label class="ml-2 inline-flex items-center gap-2 text-sm cursor-pointer select-none">
          <input type="checkbox" v-model="localSchedules[d.value].enabled" class="rounded border-gray-300 text-brand-600 focus:ring-brand-500" /> 
          <span :class="localSchedules[d.value].enabled ? 'text-gray-900' : 'text-gray-400'">일하는 날</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch, onMounted, computed } from 'vue'
import { apiClient } from '../api'
import TimeSelect from './TimeSelect.vue'

const props = defineProps({ employeeId: { type: Number, required: false } })

const weekdays = [
  { value: 0, label: '월' },
  { value: 1, label: '화' },
  { value: 2, label: '수' },
  { value: 3, label: '목' },
  { value: 4, label: '금' },
  { value: 5, label: '토' },
  { value: 6, label: '일' },
]

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

const localSchedules = reactive<Record<number, { start_time: string | null, end_time: string | null, enabled: boolean }>>({
  0: { start_time: null, end_time: null, enabled: false },
  1: { start_time: null, end_time: null, enabled: false },
  2: { start_time: null, end_time: null, enabled: false },
  3: { start_time: null, end_time: null, enabled: false },
  4: { start_time: null, end_time: null, enabled: false },
  5: { start_time: null, end_time: null, enabled: false },
  6: { start_time: null, end_time: null, enabled: false },
})

/**
 * 30분 단위 반올림 함수
 * 예: 09:12 -> 09:00, 09:40 -> 09:30, 09:50 -> 10:00
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
  
  // 24시 넘어가면 00시로 (필요 시 수정, 보통 스케줄은 당일 기준)
  if (h >= 24) h = 0
  
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

async function loadSchedules() {
  try {
    if (!props.employeeId) return
    const res = await apiClient.get(`/labor/jobs/${props.employeeId}/schedules/`)
    
    // reset to defaults first
    resetSchedules()
    
    for (const s of res.data) {
      const idx = parseInt(s.weekday)
      if (Number.isNaN(idx)) continue
      
      // DB에서 가져온 시간을 30분 단위로 반올림하여 매핑
      const roundedStart = roundToNearest30(s.start_time)
      const roundedEnd = roundToNearest30(s.end_time)
      
      localSchedules[idx] = { 
        start_time: roundedStart, 
        end_time: roundedEnd, 
        enabled: !!s.enabled 
      }
    }
  } catch (e) {
    console.error('Failed to load schedules', e)
  }
}

type ScheduleState = Record<number, { start_time: string | null, end_time: string | null, enabled: boolean }>

function cloneSchedules(source?: ScheduleState | null): ScheduleState {
  const target: ScheduleState = {
    0: { start_time: null, end_time: null, enabled: false },
    1: { start_time: null, end_time: null, enabled: false },
    2: { start_time: null, end_time: null, enabled: false },
    3: { start_time: null, end_time: null, enabled: false },
    4: { start_time: null, end_time: null, enabled: false },
    5: { start_time: null, end_time: null, enabled: false },
    6: { start_time: null, end_time: null, enabled: false },
  }
  const src = source || localSchedules
  weekdays.forEach(w => {
    const data = src[w.value]
    target[w.value] = {
      start_time: data?.start_time ?? null,
      end_time: data?.end_time ?? null,
      enabled: !!data?.enabled,
    }
  })
  return target
}

async function saveSchedules(options?: { schedules?: ScheduleState, employeeId?: number }) {
  const targetEmployeeId = options?.employeeId ?? props.employeeId
  if (!targetEmployeeId) {
    alert('먼저 알바 정보를 저장한 다음 스케줄을 저장하세요.')
    return
  }

  const scheduleSource = options?.schedules || localSchedules
  
  try {
    const requests = weekdays.map(w => {
      const schedule = scheduleSource[w.value];
      const payload = {
        weekday: w.value,
        start_time: schedule.enabled ? schedule.start_time : null,
        end_time: schedule.enabled ? schedule.end_time : null,
        enabled: schedule.enabled,
      };
      return apiClient.post(`/labor/jobs/${targetEmployeeId}/schedules/`, payload);
    });
    
    const responses = await Promise.all(requests);
    
    // 마지막 응답에서 최신 통계 추출 (모든 응답이 동일한 통계를 포함)
    const lastResponse = responses[responses.length - 1];
    if (lastResponse?.data?.stats) {
      // 통계 정보를 이벤트와 함께 전달
      window.dispatchEvent(new CustomEvent('labor-updated', {
        detail: {
          stats: lastResponse.data.stats,
          dates: lastResponse.data.dates,
          cumulative_stats: lastResponse.data.cumulative_stats
        }
      }));
    } else {
      // 이전 방식 호환성 유지
      window.dispatchEvent(new CustomEvent('labor-updated'));
    }
  } catch (e) {
    console.error('Failed to save schedules', e);
    throw e; // 상위로 에러 전파
  }
}

function resetSchedules() {
  for (const k of Object.keys(localSchedules)) {
    localSchedules[parseInt(k)].start_time = null
    localSchedules[parseInt(k)].end_time = null
    localSchedules[parseInt(k)].enabled = false
  }
}

// Load schedules when component mounts and when employeeId changes
onMounted(() => {
  if (props.employeeId) {
    loadSchedules();
  }
});

watch(() => props.employeeId, (newId, oldId) => {
  if (newId && newId !== oldId) {
    loadSchedules();
  } else if (!newId) {
    resetSchedules();
  }
});

defineExpose({
  saveSchedules,
  loadSchedules,
  exportSchedules: () => cloneSchedules(localSchedules),
});
</script>

<style scoped>
</style>
