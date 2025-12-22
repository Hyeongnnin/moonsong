<template>
  <div>
    <div class="max-w-4xl mx-auto">
      <!-- 현재 선택된 알바 정보 표시 (헤더) -->
      <div v-if="activeJob" class="mb-6 pb-4 border-b border-gray-200">
        <p class="text-sm text-gray-600 mb-1">현재 선택된 알바</p>
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold text-gray-900">{{ activeJob.workplace_name }}</h2>
            <p class="text-sm text-gray-600 mt-1">{{ activeJob.workplace_address }}</p>
          </div>
          <div class="text-right">
            <p class="text-sm text-gray-600">시급</p>
            <p class="text-lg font-bold text-brand-600">{{ formatWage(activeJob.hourly_rate) }}</p>
          </div>
        </div>
      </div>

      <div class="grid lg:grid-cols-3 gap-6 lg:grid-rows-[auto_1fr]">
        <div class="lg:col-span-2 lg:row-span-2 flex flex-col gap-6">
          <WorkCalendar 
            ref="workCalendarRef"
            :activeJob="activeJob" 
            @statsUpdated="handleStatsUpdate"
            @monthChanged="handleMonthChanged" 
          />
          <!-- 캘린더 아래 연차휴가 카드 - 우측 하단 카드와 bottom 정렬 -->
          <div class="flex-1 min-h-0">
            <LaborAnnualLeaveCard class="h-full" />
          </div>
        </div>

        <div class="lg:col-span-1 lg:row-span-1">
          <WorkSummaryCard 
            ref="summaryCardRef" 
            :activeJob="activeJob" 
            :displayYear="selectedYear"
            :displayMonth="selectedMonth"
          />
        </div>

        <div class="lg:col-span-1 lg:row-span-1 flex flex-col gap-6">
          <!-- 주휴수당 및 퇴직금 카드 (우측 사이드바에서 이동) -->
          <HolidayPayCard ref="holidayPayCardRef" :activeJob="activeJob" />
          <SeverancePayCard :activeJob="activeJob" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import WorkCalendar from './WorkCalendar.vue';
import LaborAnnualLeaveCard from './LaborAnnualLeaveCard.vue';
import WorkSummaryCard from './WorkSummaryCard.vue';
import HolidayPayCard from './HolidayPayCard.vue';
import SeverancePayCard from './SeverancePayCard.vue';
import { useJob, type Job } from '../stores/jobStore';

const { activeJob } = useJob();
const summaryCardRef = ref<InstanceType<typeof WorkSummaryCard> | null>(null);
const holidayPayCardRef = ref<InstanceType<typeof HolidayPayCard> | null>(null);
const workCalendarRef = ref<InstanceType<typeof WorkCalendar> | null>(null);

// 캘린더에서 선택된 연/월을 추적 (초기값: 현재 월)
const today = new Date();
const selectedYear = ref<number>(today.getFullYear());
const selectedMonth = ref<number>(today.getMonth() + 1);

// labor-updated 이벤트 핸들러
function handleLaborUpdate(event: Event) {
  const customEvent = event as CustomEvent;
  // 이벤트에 통계 데이터가 포함되어 있으면 사용, 없으면 카드 내부에서 다시 로드
  handleStatsUpdate(customEvent.detail?.stats);
  
  // 캘린더 새로고침
  if (workCalendarRef.value) {
    workCalendarRef.value.refreshCalendar();
  }
  
  // 주휴수당 갱신
  if (holidayPayCardRef.value) {
    holidayPayCardRef.value.refresh();
  }
}

onMounted(() => {
  window.addEventListener('labor-updated', handleLaborUpdate);
});

onUnmounted(() => {
  window.removeEventListener('labor-updated', handleLaborUpdate);
});

// 함수: 시급 포맷팅
function formatWage(wage: number | string): string {
  const n = Number(wage) || 0
  return n.toLocaleString('ko-KR', { maximumFractionDigits: 0, minimumFractionDigits: 0 }) + '원'
}

// 캘린더에서 월이 변경될 때 호출
function handleMonthChanged(data: { year: number; month: number }) {
  console.log('[DashboardContent] Month changed to:', data.year, data.month);
  selectedYear.value = data.year;
  selectedMonth.value = data.month;
}

// 통계 업데이트 핸들러
function handleStatsUpdate(stats?: any) {
  if (summaryCardRef.value) {
    summaryCardRef.value.updateStats(stats);
  }
}
</script>

<style scoped>
</style>
