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

          <!-- 주휴일 및 기본 휴게 설정 -->
          <div class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm text-gray-700 mb-1">주휴일 요일</label>
              <select v-model="weeklyRestDay" class="w-full px-3 py-2 border rounded">
                <option :value="null">선택 없음</option>
                <option v-for="d in weekdays" :key="d.value" :value="d.value">{{ d.label }}</option>
              </select>
            </div>
            <div class="text-sm text-gray-600">
              각 요일의 기본 휴게시간(분)을 입력하면, 해당 달의 생성되는 근로기록에 참고값으로 저장됩니다.
            </div>
          </div>

          <div class="space-y-3">
            <div v-for="d in weekdays" :key="d.value" class="flex items-center gap-3">
              <div class="w-16 text-sm font-medium">{{ d.label }}</div>
              <input type="number" min="0" v-model.number="defaultBreaks[d.value]" class="w-24 px-2 py-1 border rounded" placeholder="휴게(분)" />
            </div>
          </div>

          <div class="space-y-3">
            <div v-for="d in weekdays" :key="d.value" class="flex items-center gap-3">
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
              
              <label class="ml-2 inline-flex items-center gap-2 text-sm cursor-pointer select-none">
                <input type="checkbox" v-model="localSchedules[d.value].enabled" class="rounded border-gray-300 text-brand-600 focus:ring-brand-500" /> 
                <span :class="localSchedules[d.value].enabled ? 'text-gray-900' : 'text-gray-400'">활성</span>
              </label>
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

// 00:00 ~ 23:30까지 30분 단위 시간 옵션
const timeOptions = Array.from({ length: 48 }, (_, i) => {
  const hour = Math.floor(i / 2)
  const minute = (i % 2) * 30
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
})

interface ScheduleData {
  enabled: boolean
  start_time: string
  end_time: string
}

const localSchedules = reactive<Record<number, ScheduleData>>({
  0: { enabled: false, start_time: '09:00', end_time: '18:00' },
  1: { enabled: false, start_time: '09:00', end_time: '18:00' },
  2: { enabled: false, start_time: '09:00', end_time: '18:00' },
  3: { enabled: false, start_time: '09:00', end_time: '18:00' },
  4: { enabled: false, start_time: '09:00', end_time: '18:00' },
  5: { enabled: false, start_time: '09:00', end_time: '18:00' },
  6: { enabled: false, start_time: '09:00', end_time: '18:00' },
})

const hasOverride = ref(false)
const isSaving = ref(false)
const weeklyRestDay = ref<number | null>(null)
const defaultBreaks = reactive<Record<number, number>>({
  0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0
})

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
    
    // 스케줄 데이터 채우기
    schedules.forEach((schedule: any) => {
      const weekday = schedule.weekday
      localSchedules[weekday] = {
        enabled: schedule.enabled ?? false,
        start_time: schedule.start_time || '09:00',
        end_time: schedule.end_time || '18:00'
      }
    })

    // 월별 메타 데이터 (존재하는 경우 첫 항목에서 로드)
    const metaSource = schedules.find((s: any) => s.default_break_minutes_by_weekday || s.weekly_rest_day)
    if (metaSource) {
      const breaksMap = metaSource.default_break_minutes_by_weekday || {}
      weekdays.forEach(w => {
        defaultBreaks[w.value] = breaksMap[w.value] ?? 0
      })
      weeklyRestDay.value = typeof metaSource.weekly_rest_day === 'number' ? metaSource.weekly_rest_day : null
    } else {
      // 기본값 리셋
      weekdays.forEach(w => { defaultBreaks[w.value] = 0 })
      weeklyRestDay.value = null
    }
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
    const schedulesArray = Object.entries(localSchedules).map(([weekday, data]) => ({
      weekday: parseInt(weekday),
      start_time: data.enabled ? data.start_time : null,
      end_time: data.enabled ? data.end_time : null,
      enabled: data.enabled
    }))
    
    const response = await apiClient.post(
      `/labor/employees/${props.employeeId}/monthly-schedule-override/`,
      {
        year: props.year,
        month: props.month,
        schedules: schedulesArray,
        default_break_minutes_by_weekday: { ...defaultBreaks },
        weekly_rest_day: weeklyRestDay.value
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
  } catch (error) {
    console.error('Failed to save monthly schedule:', error)
    alert('스케줄 저장에 실패했습니다.')
  } finally {
    isSaving.value = false
  }
}

function close() {
  emit('close')
}
</script>
