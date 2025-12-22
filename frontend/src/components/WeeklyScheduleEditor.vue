<template>
  <div class="space-y-4">
    <p class="text-sm text-gray-600">저장 시 캘린더 전체 근로시간이 변경돼요! 월별 및 일별 근로정보 변경은 캘린더에서 해주세요.</p>
    <div class="grid grid-cols-1 gap-3">
      <div v-for="d in weekdays" :key="d.value" class="border rounded-lg p-3 bg-gray-50">
        <div class="flex items-center gap-3 mb-2">
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
          
          <!-- 휴게시간 입력 -->
          <div class="flex items-center gap-1">
            <span class="text-xs text-gray-500">휴게</span>
            <input
              type="number"
              v-model.number="localSchedules[d.value].break_minutes"
              min="0"
              max="480"
              :disabled="!localSchedules[d.value].enabled"
              class="w-16 px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-brand-500 disabled:bg-gray-100 disabled:text-gray-400"
              placeholder="0"
            />
            <span class="text-xs text-gray-500">분</span>
          </div>
          
          <label class="ml-2 inline-flex items-center gap-2 text-sm cursor-pointer select-none">
            <input type="checkbox" v-model="localSchedules[d.value].enabled" class="rounded border-gray-300 text-brand-600 focus:ring-brand-500" /> 
            <span :class="localSchedules[d.value].enabled ? 'text-gray-900' : 'text-gray-400'">일하는 날</span>
          </label>
        </div>
        
        <!-- 익일 근무 입력 섹션 -->
        <div v-if="localSchedules[d.value].enabled" class="ml-24 flex items-center gap-3">
          <label class="inline-flex items-center gap-2 text-sm cursor-pointer select-none">
            <input 
              type="checkbox" 
              v-model="localSchedules[d.value].has_next_day_work"
              class="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
            />
            <span class="text-gray-700">익일 근무 있음 (24:00~06:00)</span>
          </label>
          
          <div v-if="localSchedules[d.value].has_next_day_work" class="flex items-center gap-2">
            <input
              type="number"
              v-model.number="localSchedules[d.value].next_day_work_minutes"
              min="0"
              max="360"
              class="w-20 px-2 py-1 text-sm border rounded focus:ring-2 focus:ring-brand-500"
              placeholder="0"
            />
            <span class="text-xs text-gray-600">분 (0~360)</span>
          </div>
        </div>
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

const localSchedules = reactive<Record<number, { 
  start_time: string | null, 
  end_time: string | null, 
  enabled: boolean,
  has_next_day_work: boolean,
  next_day_work_minutes: number,
  break_minutes: number
}>>({
  0: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  1: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  2: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  3: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  4: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  5: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  6: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
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
      
      // 익일 근무 데이터 로드
      const nextDayMinutes = s.next_day_work_minutes || 0
      const breakMinutes = s.break_minutes || 0
      
      localSchedules[idx] = { 
        start_time: roundedStart, 
        end_time: roundedEnd, 
        enabled: !!s.enabled,
        has_next_day_work: nextDayMinutes > 0,
        next_day_work_minutes: nextDayMinutes,
        break_minutes: breakMinutes
      }
    }
  } catch (e) {
    console.error('Failed to load schedules', e)
  }
}

type ScheduleState = Record<number, { 
  start_time: string | null, 
  end_time: string | null, 
  enabled: boolean,
  has_next_day_work: boolean,
  next_day_work_minutes: number,
  break_minutes: number
}>

function cloneSchedules(source?: ScheduleState | null): ScheduleState {
  const target: ScheduleState = {
    0: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
    1: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
    2: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
    3: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
    4: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
    5: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
    6: { start_time: null, end_time: null, enabled: false, has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  }
  const src = source || localSchedules
  weekdays.forEach(w => {
    const data = src[w.value]
    target[w.value] = {
      start_time: data?.start_time ?? null,
      end_time: data?.end_time ?? null,
      enabled: !!data?.enabled,
      has_next_day_work: !!data?.has_next_day_work,
      next_day_work_minutes: data?.next_day_work_minutes ?? 0,
      break_minutes: data?.break_minutes ?? 0,
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
      
      // 24:00 처리: 다음날 00:00으로 변환
      let startTime = schedule.start_time;
      let endTime = schedule.end_time;
      let isOvernight = false;
      
      if (endTime === '24:00') {
        endTime = '00:00';
        isOvernight = true;
      }
      
      // 익일 근무 시간 처리
      const nextDayMinutes = schedule.has_next_day_work ? (schedule.next_day_work_minutes || 0) : 0;
      
      // 휴게시간 처리
      const breakMinutes = schedule.break_minutes || 0;
      
      // 밸리데이션: 0~360 범위 체크
      if (nextDayMinutes < 0 || nextDayMinutes > 360) {
        throw new Error(`익일 근무 시간은 0~360분 사이여야 합니다. (현재: ${nextDayMinutes}분)`);
      }
      
      // 밸리데이션: 휴게시간 범위 체크
      if (breakMinutes < 0 || breakMinutes > 480) {
        throw new Error(`휴게시간은 0~480분 사이여야 합니다. (현재: ${breakMinutes}분)`);
      }
      
      const payload = {
        weekday: w.value,
        start_time: schedule.enabled ? startTime : null,
        end_time: schedule.enabled ? endTime : null,
        is_overnight: isOvernight,
        next_day_work_minutes: nextDayMinutes,
        break_minutes: breakMinutes,
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
    const idx = parseInt(k)
    localSchedules[idx].start_time = null
    localSchedules[idx].end_time = null
    localSchedules[idx].enabled = false
    localSchedules[idx].has_next_day_work = false
    localSchedules[idx].next_day_work_minutes = 0
    localSchedules[idx].break_minutes = 0
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
