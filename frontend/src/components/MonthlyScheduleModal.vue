<template>
  <Teleport to="body">
    <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.self="close">
      <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <!-- 헤더 -->
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-900">{{ year }}년 {{ month }}월 근무 스케줄 변경</h2>
              <p class="text-sm text-gray-600 mt-1">이 달의 근무 스케줄만 변경됩니다. 다른 달의 스케줄에는 영향을 주지 않습니다.</p>
            </div>
            <button @click="close" class="text-gray-400 hover:text-gray-600 transition">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- 스케줄 편집 폼 -->
        <div class="px-6 py-4">
          <div v-if="hasOverride" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p class="text-sm text-blue-700">
              ✓ 이 달은 별도의 근무 스케줄이 설정되어 있습니다.
            </p>
          </div>
          
          <div v-else class="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
            <p class="text-sm text-gray-600">
              현재 기본 주간 스케줄을 사용 중입니다. 아래에서 이 달만의 스케줄을 설정할 수 있습니다.
            </p>
          </div>

          <div class="mb-4 text-sm text-gray-600 flex items-center bg-gray-50 border border-gray-200 rounded-lg p-3">
            각 요일의 휴게시간은 아래 근무시간 입력란에서 개별 설정할 수 있습니다.
          </div>

          <div class="space-y-3">
            <div v-for="d in weekdays" :key="d.value" class="border rounded-lg p-3 bg-white">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-16 text-sm font-medium">{{ d.label }}</div>
                
                <!-- 시작 시간 -->
                <TimeSelect
                  v-model="localSchedules[d.value].start_time" 
                  :options="timeOptions"
                  :disabled="!localSchedules[d.value].enabled"
                />
                
                <span class="text-xs text-gray-400">~</span>
                
                <!-- 종료 시간 -->
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
                  <span :class="localSchedules[d.value].enabled ? 'text-gray-900' : 'text-gray-400'">활성</span>
                </label>
              </div>
              
              <!-- 익일 근무 입력 섹션 -->
              <div v-if="localSchedules[d.value].enabled" class="ml-20 flex items-center gap-3">
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

        <!-- 액션 버튼 -->
        <div class="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 flex justify-end gap-3">
          <button 
            @click="close" 
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition">
            취소
          </button>
          <button 
            @click="saveSchedules" 
            :disabled="isSaving"
            class="px-4 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 transition disabled:opacity-50">
            {{ isSaving ? '저장 중...' : '저장하기' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { apiClient } from '../api'
import TimeSelect from './TimeSelect.vue'

const props = defineProps<{
  isOpen: boolean
  employeeId: number | null
  year: number
  month: number
}>()

const emit = defineEmits<{
  close: []
  saved: [data?: { stats?: any; dates?: any; cumulative_stats?: any }]
}>()

const weekdays = [
  { value: 0, label: '월' },
  { value: 1, label: '화' },
  { value: 2, label: '수' },
  { value: 3, label: '목' },
  { value: 4, label: '금' },
  { value: 5, label: '토' },
  { value: 6, label: '일' },
]

// 00:00 ~ 24:00까지 30분 단위 시간 옵션
const timeOptions = Array.from({ length: 49 }, (_, i) => {
  if (i === 48) return '24:00'
  const hour = Math.floor(i / 2)
  const minute = (i % 2) * 30
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
})

interface ScheduleData {
  enabled: boolean
  start_time: string
  end_time: string
  has_next_day_work: boolean
  next_day_work_minutes: number
  break_minutes: number
}

const localSchedules = reactive<Record<number, ScheduleData>>({
  0: { enabled: false, start_time: '09:00', end_time: '18:00', has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  1: { enabled: false, start_time: '09:00', end_time: '18:00', has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  2: { enabled: false, start_time: '09:00', end_time: '18:00', has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  3: { enabled: false, start_time: '09:00', end_time: '18:00', has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  4: { enabled: false, start_time: '09:00', end_time: '18:00', has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  5: { enabled: false, start_time: '09:00', end_time: '18:00', has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
  6: { enabled: false, start_time: '09:00', end_time: '18:00', has_next_day_work: false, next_day_work_minutes: 0, break_minutes: 0 },
})

const hasOverride = ref(false)
const isSaving = ref(false)
// weeklyRestDay는 사용자 요청으로 제거됨
// defaultBreaks는 제거됨 - 각 요일별로 break_minutes를 직접 입력받음

// 모달이 열릴 때 현재 스케줄 로드
watch(() => props.isOpen, async (newVal) => {
  if (newVal && props.employeeId) {
    await loadSchedules()
  }
})

async function loadSchedules() {
  if (!props.employeeId) return
  
  try {
    const response = await apiClient.get(
      `/labor/employees/${props.employeeId}/monthly-schedule-override/`,
      {
        params: {
          year: props.year,
          month: props.month
        }
      }
    )
    
    hasOverride.value = response.data.has_override
    const schedules = response.data.schedules || []
    
    console.log('[MonthlyScheduleModal] 로드된 스케줄:', { hasOverride: hasOverride.value, schedules })
    
    // 스케줄 데이터 채우기 - 주간 스케줄이 기본값으로 사용됨
    schedules.forEach((schedule: any) => {
      const weekday = schedule.weekday
      const nextDayMinutes = schedule.next_day_work_minutes || 0
      const breakMinutes = schedule.break_minutes || 0
      
      localSchedules[weekday] = {
        enabled: schedule.enabled ?? false,
        start_time: schedule.start_time || '09:00',  // 백엔드에서 주간 스케줄 기본값 제공
        end_time: schedule.end_time || '18:00',      // 백엔드에서 주간 스케줄 기본값 제공
        has_next_day_work: nextDayMinutes > 0,
        next_day_work_minutes: nextDayMinutes,
        break_minutes: breakMinutes
      }
      
      console.log(`[MonthlyScheduleModal] 요일 ${weekday} (${['월','화','수','목','금','토','일'][weekday]}):`, 
        `enabled=${schedule.enabled}, start=${schedule.start_time}, end=${schedule.end_time}, break=${breakMinutes}분`)
    })

    // 월별 메타 데이터 (weekly_rest_day 로드 로직 제거)
  } catch (error) {
    console.error('Failed to load monthly schedule:', error)
    alert('스케줄을 불러오는데 실패했습니다.')
  }
}

async function saveSchedules() {
  if (!props.employeeId) return
  
  if (!confirm(`${props.year}년 ${props.month}월 근무 스케줄을 저장하시겠습니까?\n\n스케줄에 맞춰 근로기록이 자동으로 생성됩니다.`)) {
    return
  }
  
  isSaving.value = true
  
  try {
    const schedulesArray = Object.entries(localSchedules).map(([weekday, data]) => {
      // 24:00 처리
      let endTime = data.end_time
      let isOvernight = false
      if (endTime === '24:00') {
        endTime = '00:00'
        isOvernight = true
      }
      
      // 익일 근무 시간 처리
      const nextDayMinutes = data.has_next_day_work ? (data.next_day_work_minutes || 0) : 0
      
      // 휴게시간 처리
      const breakMinutes = data.break_minutes || 0
      
      // 밸리데이션
      if (nextDayMinutes < 0 || nextDayMinutes > 360) {
        throw new Error(`익일 근무 시간은 0~360분 사이여야 합니다. (현재: ${nextDayMinutes}분)`)
      }
      
      if (breakMinutes < 0 || breakMinutes > 480) {
        throw new Error(`휴게시간은 0~480분 사이여야 합니다. (현재: ${breakMinutes}분)`)
      }
      
      return {
        weekday: parseInt(weekday),
        start_time: data.enabled ? data.start_time : null,
        end_time: data.enabled ? endTime : null,
        is_overnight: isOvernight,
        next_day_work_minutes: nextDayMinutes,
        break_minutes: breakMinutes,
        enabled: data.enabled
      }
    })
    
    const response = await apiClient.post(
      `/labor/employees/${props.employeeId}/monthly-schedule-override/`,
      {
        year: props.year,
        month: props.month,
        schedules: schedulesArray,
        weekly_rest_day: null // 주휴일 직접 선택 기능 제거
      }
    )
    
    const createdCount = response.data.created_records || 0
    const message = response.data.message || `${props.year}년 ${props.month}월 근무 스케줄이 저장되었습니다.`
    
    alert(message)
    
    // 통계 데이터가 포함되어 있으면 부모 컴포넌트에 전달
    emit('saved', {
      stats: response.data.stats,
      dates: response.data.dates,
      cumulative_stats: response.data.cumulative_stats
    })
    close()
  } catch (error: any) {
    console.error('Failed to save monthly schedule:', error)
    alert(error.message || '스케줄 저장에 실패했습니다.')
  } finally {
    isSaving.value = false
  }
}

function close() {
  emit('close')
}
</script>
