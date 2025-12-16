<template>
  <!-- 선택된 달 통계 카드 - 콘텐츠 기반 높이 -->
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">{{ statsTitle }}</h3>
    <div class="space-y-3">
      <div class="flex items-center justify-between p-4 bg-brand-50 rounded-lg border border-brand-100">
        <div>
          <p class="text-sm font-medium text-gray-700">총 근로시간</p>
          <p class="text-xs text-gray-500 mt-1">{{ monthLabel }} 누적</p>
        </div>
        <p class="text-xl font-bold text-brand-600">{{ monthlyTotalHours.toFixed(1) }}시간</p>
      </div>

      <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div>
          <p class="text-sm font-medium text-gray-700">급여 예상액</p>
          <p class="text-xs text-gray-500 mt-1">{{ monthLabel }} 예상</p>
        </div>
        <p class="text-xl font-bold text-gray-600">{{ formatCurrency(monthlyEstimatedSalary) }}</p>
      </div>

      <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div>
          <p class="text-sm font-medium text-gray-700">총 근로일수</p>
          <p class="text-xs text-gray-500 mt-1">{{ monthLabel }} 누적</p>
        </div>
        <p class="text-xl font-bold text-gray-600">{{ totalWorkDays }}일</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import type { Job } from '../stores/jobStore';
import { apiClient } from '../api';

interface Props {
  activeJob?: Job | null;
  displayYear?: number;
  displayMonth?: number;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
  displayYear: undefined,
  displayMonth: undefined,
});

const monthlyTotalHours = ref(0);
const monthlyEstimatedSalary = ref(0);
const totalWorkDays = ref(0);

// 통계 카드 제목 (동적)
const statsTitle = computed(() => {
  if (props.displayYear && props.displayMonth) {
    return `${props.displayYear}년 ${props.displayMonth}월 통계`;
  }
  return '이번 달 통계';
});

// 월 레이블 (동적)
const monthLabel = computed(() => {
  if (props.displayYear && props.displayMonth) {
    return `${props.displayYear}년 ${props.displayMonth}월`;
  }
  return '이번 달';
});

// 금액 포맷팅
const formatCurrency = (value: number) => {
  return value.toLocaleString('ko-KR') + '원';
};

// 통계 데이터 로드
// displayYear/displayMonth가 제공되면 해당 월 기준, 없으면 현재 월 기준
async function loadJobSummary() {
  const employeeId = props.activeJob?.id;
  if (!employeeId) {
    return;
  }

  try {
    let monthStr: string;
    
    // displayYear/displayMonth가 제공되면 해당 월, 없으면 현재 월
    if (props.displayYear && props.displayMonth) {
      monthStr = `${props.displayYear}-${String(props.displayMonth).padStart(2, '0')}`;
      console.log('[WorkSummaryCard] Loading summary for selected month:', monthStr);
    } else {
      const today = new Date();
      monthStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
      console.log('[WorkSummaryCard] Loading summary for current month:', monthStr);
    }
    
    const res = await apiClient.get(`/labor/jobs/${employeeId}/monthly-summary/`, {
      params: { month: monthStr }
    });

    monthlyTotalHours.value = res.data.scheduled_total_hours || 0;
    monthlyEstimatedSalary.value = res.data.scheduled_estimated_salary || 0;
    totalWorkDays.value = res.data.scheduled_work_days || 0;
  } catch (e) {
    console.error('[WorkSummaryCard] Failed to load job summary', e);
  }
}

// 외부에서 통계 업데이트 트리거
function updateStats(stats?: any) {
  console.log('[WorkSummaryCard] updateStats called, reloading month data');
  loadJobSummary();
}

// activeJob, displayYear, displayMonth 중 하나라도 변경되면 로드
watch([() => props.activeJob?.id, () => props.displayYear, () => props.displayMonth], () => {
  if (props.activeJob) {
    loadJobSummary();
  }
}, { immediate: true });

// 외부에서 호출 가능하도록 expose
defineExpose({ updateStats });
</script>

<style scoped>
</style>
