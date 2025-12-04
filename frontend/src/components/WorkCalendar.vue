<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ currentYear }}년 {{ currentMonth }}월</h3>
        <p class="text-sm text-gray-500 mt-1">근로시간 기록</p>
      </div>
      <div class="flex gap-2">
        <button 
          @click="previousMonth"
          class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          ◀
        </button>
        <button 
          @click="nextMonth"
          class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          ▶
        </button>
      </div>
    </div>

    <!-- 요일 헤더 -->
    <div class="grid grid-cols-7 gap-2 mb-4">
      <div 
        v-for="day in ['일', '월', '화', '수', '목', '금', '토']" 
        :key="day" 
        class="text-center text-xs font-semibold text-gray-600 py-2"
      >
        {{ day }}
      </div>
    </div>

    <!-- 달력 -->
    <div class="grid grid-cols-7 gap-2">
      <button
        v-for="dayObj in calendarDays"
        :key="dayObj.day + '-' + Math.random()"
        @click="selectDate(dayObj.day)"
        :class="[
          'aspect-square flex items-center justify-center text-sm rounded-lg font-medium transition-all',
          dayObj.day === 0 
            ? 'text-gray-300 cursor-default' 
            : dayObj.day === selectedDay
            ? 'bg-brand-600 text-white shadow-md'
            : (scheduledDayMap[dayObj.day])
              ? 'text-white bg-red-500'
              : 'text-gray-700 hover:bg-brand-50 cursor-pointer'
        ]"
      >
        {{ dayObj.day === 0 ? '' : dayObj.day }}
      </button>
    </div>

    <!-- 선택된 날짜의 근로시간 -->
    <div v-if="selectedDay" class="mt-6 pt-6 border-t border-gray-200">
      <p class="text-sm font-medium text-gray-900 mb-3">
        {{ currentYear }}년 {{ currentMonth }}월 {{ selectedDay }}일 근로시간
      </p>
      <div class="bg-brand-50 rounded-lg p-4 border border-brand-100">
        <p class="text-2xl font-bold text-brand-600">8시간</p>
        <p class="text-xs text-gray-600 mt-1">09:00 AM - 06:00 PM (휴게 1시간)</p>
      </div>
    </div>

    <WorkDayModal v-if="modalVisible" :visible="modalVisible" :employeeId="activeJob?.id" :dateIso="modalDateIso" :record="modalRecord" @close="modalVisible=false" @saved="onModalSaved" @deleted="onModalDeleted" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, toRefs } from 'vue';
import { apiClient } from '../api'
import type { Job } from '../stores/jobStore';
import WorkDayModal from './WorkDayModal.vue'

interface Props {
  activeJob?: Job | null;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
});

// expose activeJob to template safely
const { activeJob } = toRefs(props)

const currentDate = ref(new Date());
const selectedDay = ref<number | null>(null);
const modalVisible = ref(false)
const modalRecord = ref<any | null>(null)
const modalDateIso = ref<string>('')

const currentYear = computed(() => currentDate.value.getFullYear());
const currentMonth = computed(() => currentDate.value.getMonth() + 1);

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear();
  const month = currentDate.value.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const lastDate = new Date(year, month + 1, 0).getDate();
  
  const days: { day: number, dateIso?: string, is_scheduled?: boolean, record?: any }[] = [];
  
  // 이전 달의 빈 공간
  for (let i = 0; i < firstDay; i++) {
    days.push({ day: 0 });
  }
  
  // 현재 달의 날짜
  for (let i = 1; i <= lastDate; i++) {
    days.push({ day: i });
  }
  
  return days;
});

const monthKey = computed(() => `${currentYear.value}-${String(currentMonth.value).padStart(2,'0')}`)
const calendarData = ref<{ dates: Array<{date: string, day: number, is_scheduled: boolean, record: any}> } | null>(null)

const scheduledDayMap = computed(() => {
  const map: Record<number, {date:string, record:any} | null> = {}
  if (!calendarData.value) return map
  for (const d of calendarData.value.dates) {
    map[d.day] = { date: d.date, record: d.record }
  }
  return map
})

async function loadCalendar() {
  // resolve job id robustly (props.activeJob might be a value or a ref-like)
  const job = activeJob?.value ?? (props.activeJob as any)
  const jobId = job?.id
  if (!jobId) return
  try {
    const res = await apiClient.get(`/labor/jobs/${jobId}/calendar/`, { params: { month: monthKey.value } })
    calendarData.value = res.data
  } catch (e) {
    console.error('Failed to load calendar', e)
  }
}

onMounted(() => {
  // only load if job present
  const job = activeJob?.value ?? (props.activeJob as any)
  if (job && job.id) loadCalendar()
})

watch(monthKey, () => loadCalendar())

const previousMonth = () => {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1);
  selectedDay.value = null;
};

const nextMonth = () => {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1);
  selectedDay.value = null;
};

function selectDate(day: number) {
  // do nothing for empty cells
  if (day === 0) return
  const job = activeJob?.value ?? (props.activeJob as any)
  if (!job || !job.id) return

  selectedDay.value = day
  if (!calendarData.value) return
  const d = calendarData.value.dates.find((x: any) => x.day === day)
  modalDateIso.value = d?.date || `${currentYear.value}-${String(currentMonth.value).padStart(2,'0')}-${String(day).padStart(2,'0')}`
  modalRecord.value = d?.record || null
  modalVisible.value = true
}

function onModalSaved() {
  modalVisible.value = false
  modalRecord.value = null
  // reload calendar data
  loadCalendar()
}

function onModalDeleted() {
  modalVisible.value = false
  modalRecord.value = null
  loadCalendar()
}

// expose nothing
</script>

<style scoped>
</style>
