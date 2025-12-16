<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ currentYear }}년 {{ currentMonth }}월</h3>
        <p class="text-sm text-gray-500 mt-1">근로시간 기록</p>
      </div>
      <div class="flex gap-2">
        <!-- 월별 스케줄 변경 버튼 -->
        <button 
          v-if="activeJob"
          @click="openMonthlyScheduleModal"
          :disabled="isFutureMonth"
          :class="[
            'px-3 py-2 text-sm font-medium rounded-lg transition-colors',
            isFutureMonth
              ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
              : 'text-brand-600 bg-brand-50 hover:bg-brand-100'
          ]"
          :title="isFutureMonth ? '미래 월의 스케줄은 변경할 수 없습니다' : '이 달의 근무 스케줄을 변경합니다'"
        >
          📅 월별 스케줄 변경
        </button>
        <button 
          @click="previousMonth"
          :disabled="!canGoPrevious"
          :class="[
            'p-2 rounded-lg transition-colors',
            canGoPrevious 
              ? 'text-gray-600 hover:bg-gray-100 cursor-pointer' 
              : 'text-gray-300 cursor-not-allowed opacity-50'
          ]"
          :title="!canGoPrevious ? '근로 시작일 이전 달은 볼 수 없습니다' : '이전 달'"
        >
          ◀
        </button>
        <button 
          @click="nextMonth"
          :disabled="!canGoNext"
          :class="[
            'p-2 rounded-lg transition-colors',
            canGoNext 
              ? 'text-gray-600 hover:bg-gray-100 cursor-pointer' 
              : 'text-gray-300 cursor-not-allowed opacity-50'
          ]"
          :title="!canGoNext ? '현재 월로부터 6개월 이후는 볼 수 없습니다' : '다음 달'"
        >
          ▶
        </button>
      </div>
    </div>

    <!-- 요일 헤더 -->
    <div class="grid grid-cols-7 gap-2 mb-3">
      <div 
        v-for="day in ['일', '월', '화', '수', '목', '금', '토']" 
        :key="day" 
        class="text-center text-xs font-semibold text-gray-600 py-2"
      >
        {{ day }}
      </div>
    </div>

    <!-- 달력 (콘텐츠 기반 높이) -->
    <div class="grid grid-cols-7 gap-2">
      <button
        v-for="dayObj in calendarDays"
        :key="dayObj.dateIso || Math.random()"
        @click="selectDate(dayObj.day)"
        :style="dayObj.day !== 0 && selectedDay !== dayObj.day && isDateScheduled(dayObj.dateIso) ? 'background-color: #f97316 !important; color: white !important;' : ''"
        :class="[
          'aspect-square flex items-center justify-center text-sm rounded-lg font-medium transition-all',
          {
            'text-transparent cursor-default': dayObj.day === 0,
            'bg-brand-600 text-white shadow-md': dayObj.day !== 0 && selectedDay === dayObj.day,
            'scheduled-day': dayObj.day !== 0 && selectedDay !== dayObj.day && isDateScheduled(dayObj.dateIso),
            'text-gray-900 hover:bg-brand-50 bg-white border border-gray-200': dayObj.day !== 0 && selectedDay !== dayObj.day && !isDateScheduled(dayObj.dateIso) && !isFutureMonth,
            'text-gray-400 bg-gray-100 cursor-not-allowed border border-gray-300': dayObj.day !== 0 && isFutureMonth
          }
        ]"
        :disabled="dayObj.day === 0 || isFutureMonth"
        :title="dayObj.dateIso ? (isFutureMonth ? '미래 월에는 근로 기록을 입력할 수 없습니다' : `${dayObj.dateIso}: ${isDateScheduled(dayObj.dateIso) ? 'Scheduled' : 'Not scheduled'}`) : ''"
      >
        {{ dayObj.day || '' }}
      </button>
    </div>

    <WorkDayModal 
      v-if="modalVisible" 
      :visible="modalVisible" 
      :employeeId="activeJob?.id" 
      :dateIso="modalDateIso" 
      :record="modalRecord" 
      @close="onModalClose" 
      @saved="onModalSaved" 
      @deleted="onModalDeleted" 
    />
    
    <MonthlyScheduleModal
      :isOpen="monthlyScheduleModalOpen"
      :employeeId="activeJob?.id || null"
      :year="currentYear"
      :month="currentMonth"
      @close="closeMonthlyScheduleModal"
      @saved="onMonthlyScheduleSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, toRefs } from 'vue';
import { apiClient } from '../api'
import type { Job } from '../stores/jobStore';
import WorkDayModal from './WorkDayModal.vue'
import MonthlyScheduleModal from './MonthlyScheduleModal.vue'

interface Props {
  activeJob?: Job | null;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
});

const emit = defineEmits(['statsUpdated', 'monthChanged']);

const { activeJob } = toRefs(props)

const currentDate = ref(new Date());
const selectedDay = ref<number | null>(null);
const modalVisible = ref(false)
const modalRecord = ref<any | null>(null)
const modalDateIso = ref<string>('')

// 월별 스케줄 모달 상태
const monthlyScheduleModalOpen = ref(false)

const currentYear = computed(() => currentDate.value.getFullYear());
const currentMonth = computed(() => currentDate.value.getMonth() + 1);

// 근로 시작일 기준으로 이전 달로 이동 가능 여부 확인
const canGoPrevious = computed(() => {
  if (!activeJob?.value?.start_date) return true; // start_date가 없으면 제한 없음
  
  const startDate = new Date(activeJob.value.start_date);
  const startYear = startDate.getFullYear();
  const startMonth = startDate.getMonth() + 1; // 1-12
  
  // 현재 보고 있는 달이 시작일의 달보다 이후면 true
  if (currentYear.value > startYear) return true;
  if (currentYear.value === startYear && currentMonth.value > startMonth) return true;
  
  return false;
});

// 미래 월 이동 제한: 현재 월 + 6개월까지만 허용
const canGoNext = computed(() => {
  const today = new Date();
  const todayYear = today.getFullYear();
  const todayMonth = today.getMonth() + 1; // 1-12
  
  // 현재 월 + 6개월 계산
  const maxDate = new Date(todayYear, todayMonth - 1 + 6, 1); // month는 0-based
  const maxYear = maxDate.getFullYear();
  const maxMonth = maxDate.getMonth() + 1;
  
  // 현재 보고 있는 달이 최대 허용 월보다 이전이면 true
  if (currentYear.value < maxYear) return true;
  if (currentYear.value === maxYear && currentMonth.value < maxMonth) return true;
  
  return false;
});

// 미래 월 여부 확인 (현재 월보다 이후인지)
const isFutureMonth = computed(() => {
  const today = new Date();
  const todayYear = today.getFullYear();
  const todayMonth = today.getMonth() + 1; // 1-12
  
  if (currentYear.value > todayYear) return true;
  if (currentYear.value === todayYear && currentMonth.value > todayMonth) return true;
  
  return false;
});

const calendarDays = computed(() => {
  const year = currentYear.value;
  const month = currentMonth.value - 1; // getMonth() is 0-indexed
  const firstDayOfMonth = new Date(year, month, 1).getDay();
  const lastDateOfMonth = new Date(year, month + 1, 0).getDate();
  
  const days: { day: number, dateIso?: string }[] = [];
  
  // 이전 달의 빈 공간
  for (let i = 0; i < firstDayOfMonth; i++) {
    days.push({ day: 0 });
  }
  
  // 현재 달의 날짜
  for (let i = 1; i <= lastDateOfMonth; i++) {
    // 로컬 날짜 문자열 생성 (UTC 변환 없이)
    const dateIso = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
    days.push({ day: i, dateIso });
  }
  
  return days;
});

const calendarData = ref<Array<{date: string, is_scheduled: boolean}>>([]);

const scheduledDayMap = computed(() => {
  const map: Record<string, { is_scheduled: boolean }> = {};
  if (!calendarData.value || !Array.isArray(calendarData.value)) {
    return map;
  }
  
  for (const d of calendarData.value) {
    if (d && d.date) {
      map[d.date] = { is_scheduled: !!d.is_scheduled };
    }
  }
  
  return map;
});

// 날짜가 스케줄되어 있는지 확인하는 헬퍼 함수
const isDateScheduled = (dateIso?: string): boolean => {
  if (!dateIso) return false;
  
  // 실제 데이터만 확인 (폴백 로직 제거)
  const mapEntry = scheduledDayMap.value[dateIso];
  const result = mapEntry?.is_scheduled === true;
  
  return result;
};

async function loadCalendar() {
  const employeeId = activeJob?.value?.id;
  if (!employeeId) {
    calendarData.value = [];
    return;
  }

  try {
    const monthStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`;
    const res = await apiClient.get(`/labor/jobs/${employeeId}/monthly-schedule/`, {
      params: {
        month: monthStr,
      },
    });
    
    // 응답 데이터 구조 확인 및 할당
    const responseData = res.data.dates || res.data;
    calendarData.value = Array.isArray(responseData) ? responseData : [];
    
    // 강제로 다음 틱에서 재렌더링 트리거
    await new Promise(resolve => setTimeout(resolve, 0));
  } catch (e) {
    console.error('[WorkCalendar] Failed to load calendar schedule', e);
    calendarData.value = [];
  }
}

watch([() => activeJob?.value?.id, currentYear, currentMonth], () => {
  loadCalendar();
  // 월이 변경될 때마다 통계 카드에 알림
  emit('monthChanged', { year: currentYear.value, month: currentMonth.value });
}, { immediate: true });

const previousMonth = () => {
  if (!canGoPrevious.value) return; // 근로 시작일 이전으로는 이동 불가
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1);
  selectedDay.value = null;
};

const nextMonth = () => {
  if (!canGoNext.value) return; // 미래 월 제한
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1);
  selectedDay.value = null;
};

function selectDate(day: number) {
  if (day === 0) return;
  const employeeId = activeJob?.value?.id;
  if (!employeeId) return;

  // 미래 월의 날짜는 클릭 불가
  if (isFutureMonth.value) {
    alert('미래 날짜에는 근로 기록을 입력할 수 없습니다.');
    return;
  }

  selectedDay.value = day;
  
  const dateIso = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  
  modalDateIso.value = dateIso;
  
  // 해당 날짜의 실제 근로기록 조회
  loadWorkRecordForDate(employeeId, dateIso);
  
  modalVisible.value = true;
}

async function loadWorkRecordForDate(employeeId: number, dateIso: string) {
  try {
    // date-schedule API를 사용하여 해당 날짜의 근로기록과 스케줄 정보 조회
    const res = await apiClient.get(`/labor/jobs/${employeeId}/date-schedule/`, {
      params: {
        date: dateIso
      }
    });
    
    // API 응답 전체 확인
    console.log('[WorkCalendar] Full API response:', JSON.stringify(res.data));
    console.log('[WorkCalendar] work_record:', res.data.work_record);
    console.log('[WorkCalendar] work_record type:', typeof res.data.work_record);
    console.log('[WorkCalendar] has_schedule:', res.data.has_schedule);
    
    // work_record가 있으면 사용, 없으면 스케줄 정보를 포함한 객체 생성
    if (res.data && res.data.work_record) {
      modalRecord.value = res.data.work_record;
      console.log('[WorkCalendar] Found work record:', modalRecord.value);
    } else if (res.data && res.data.has_schedule) {
      // 실제 근로기록은 없지만 스케줄이 있는 경우 스케줄 정보 전달
      modalRecord.value = {
        schedule_only: true,
        start_time: res.data.start_time,
        end_time: res.data.end_time
      };
      console.log('[WorkCalendar] Found schedule for', dateIso, ':', modalRecord.value);
    } else {
      modalRecord.value = null;
      console.log('[WorkCalendar] No work record or schedule found for', dateIso);
    }
  } catch (e) {
    console.error('[WorkCalendar] Failed to load work record', e);
    modalRecord.value = null;
  }
}

function onModalClose() {
  modalVisible.value = false;
  selectedDay.value = null;
  modalRecord.value = null;
}

// 월별 스케줄 모달 관련 함수
function openMonthlyScheduleModal() {
  monthlyScheduleModalOpen.value = true
}

function closeMonthlyScheduleModal() {
  monthlyScheduleModalOpen.value = false
}

async function onMonthlyScheduleSaved() {
  closeMonthlyScheduleModal()
  // 캘린더 다시 로드하여 변경된 스케줄 반영
  await loadCalendar()
  emit('statsUpdated')
}

async function onModalSaved(responseData?: any) {
  modalVisible.value = false;
  modalRecord.value = null;
  selectedDay.value = null; // 선택된 날짜 초기화
  
  // 응답 데이터에 최신 통계가 있으면 사용, 없으면 다시 로드
  if (responseData && responseData.dates && responseData.stats) {
    calendarData.value = responseData.dates;
    // 캘린더 데이터만 업데이트하고, 통계는 WorkSummaryCard에서 현재 월 기준으로 다시 로드
    emit('statsUpdated');
  } else {
    await loadCalendar();
    emit('statsUpdated');
  }
}

async function onModalDeleted(responseData?: any) {
  console.log('[WorkCalendar] onModalDeleted called with:', responseData);
  modalVisible.value = false;
  modalRecord.value = null;
  selectedDay.value = null; // 선택된 날짜 초기화 - 중요!
  
  // 응답 데이터에 최신 통계가 있으면 사용, 없으면 다시 로드
  if (responseData && responseData.dates && responseData.stats) {
    console.log('[WorkCalendar] Using response data from delete');
    console.log('[WorkCalendar] New dates:', responseData.dates);
    console.log('[WorkCalendar] New stats:', responseData.stats);
    calendarData.value = responseData.dates;
    // 캘린더 데이터만 업데이트하고, 통계는 WorkSummaryCard에서 현재 월 기준으로 다시 로드
    emit('statsUpdated');
  } else {
    console.log('[WorkCalendar] No response data, reloading calendar');
    await loadCalendar();
    emit('statsUpdated');
  }
}

// 전역 이벤트 리스너 - 스케줄 저장 시 캘린더 자동 갱신
function handleLaborUpdate() {
  console.log('[WorkCalendar] Labor updated event received, reloading calendar');
  loadCalendar();
}

onMounted(() => {
  window.addEventListener('labor-updated', handleLaborUpdate);
});

onUnmounted(() => {
  window.removeEventListener('labor-updated', handleLaborUpdate);
});
</script>

<style scoped>
.scheduled-day {
  background-color: #f97316 !important;
  color: white !important;
  font-weight: bold !important;
}
</style>
