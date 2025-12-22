<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-900">이번 주 주휴수당</h3>
      <span v-if="result.week_start && result.week_end" class="text-xs text-gray-500">
        {{ formatDateRange(result.week_start, result.week_end) }}
      </span>
    </div>

    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="text-center py-8">
      <div class="text-4xl mb-3">💰</div>
      <p class="text-sm text-gray-600 font-medium mb-2">아직 근로정보가 없어요</p>
      <p class="text-xs text-gray-500 mb-4">근로정보를 입력하면<br/>주휴수당이 자동으로 계산됩니다</p>
      <button
        @click="navigateToJobCreate"
        class="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        근로정보 입력하기
      </button>
    </div>

    <!-- 근로정보가 있을 때 -->
    <div v-else>
      <div v-if="loading" class="text-center text-gray-500 py-4 text-sm">
        로딩 중...
      </div>

      <div v-else-if="error" class="text-center text-red-500 py-4 text-sm">
        데이터를 불러오는데 실패했습니다.
      </div>

      <div v-else class="bg-brand-50 rounded-lg p-4 border border-brand-100">
        <div v-if="result.amount > 0">
          <p class="text-2xl font-bold text-brand-600 mb-1">
            +{{ formatCurrency(result.amount) }}
          </p>
          <p class="text-sm text-gray-600">
            주휴시간: {{ result.hours.toFixed(1) }}시간
          </p>
          <p class="text-xs text-gray-500 mt-2">
            실제 근무: {{ result.actual_worked_hours?.toFixed(1) || 0 }}시간
          </p>
        </div>
        
        <div v-else class="text-center py-2">
          <p class="text-gray-500 text-sm font-medium mb-1">
              <span v-if="result.reason === 'less_than_15h' || result.reason === 'less_than_threshold'">
                주 {{ result.policy_threshold || 15 }}시간 미만 근무
                <span class="text-xs block mt-1">(현재: {{ result.actual_worked_hours?.toFixed(1) || 0 }}시간)</span>
              </span>
              <span v-else-if="result.reason === 'absent'">결근 발생 <span v-if="result.absent_date" class="text-xs">({{ result.absent_date }})</span></span>
              <span v-else-if="result.reason === 'no_schedule'">스케줄 없음</span>
              <span v-else>발생 금액 없음</span>
          </p>
          <p class="text-xs text-gray-400">
              이번 주 주휴수당 대상이 아닙니다
          </p>
        </div>
      </div>
      
      <div class="mt-4 text-xs text-gray-400">
          * 주 {{ result.policy_threshold || 15 }}시간 이상 근무 시 발생합니다.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { apiClient } from '../api';
import type { Job } from '../stores/jobStore';

const props = defineProps<{
  activeJob: Job | null;
}>();

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const error = ref(false);
const result = ref({
  amount: 0,
  hours: 0,
  reason: '',
  weekly_hours: 0,
  actual_worked_hours: 0,
  policy_threshold: 0,
  week_start: '',
  week_end: '',
  absent_date: ''
});

const formatCurrency = (value: number) => {
  return value.toLocaleString('ko-KR') + '원';
};

const formatDateRange = (start: string, end: string) => {
  if (!start || !end) return '';
  
  const startDate = new Date(start);
  const endDate = new Date(end);
  
  const startMonth = startDate.getMonth() + 1;
  const startDay = startDate.getDate();
  const endMonth = endDate.getMonth() + 1;
  const endDay = endDate.getDate();
  
  if (startMonth === endMonth) {
    return `${startMonth}월 ${startDay}일~${endDay}일`;
  } else {
    return `${startMonth}월 ${startDay}일~${endMonth}월 ${endDay}일`;
  }
};

// 근로정보 입력 페이지로 이동
function navigateToJobCreate() {
  // 이미 동일 경로/섹션이면 이벤트로 강제 전환
  if (route.path === '/dashboard' && route.query.section === 'profile-edit') {
    window.dispatchEvent(new CustomEvent('go-section', { detail: 'profile-edit' }));
    return;
  }
  router.push('/dashboard?section=profile-edit').catch(() => {});
}

const fetchHolidayPay = async () => {
  if (!props.activeJob) {
      result.value = { 
        amount: 0, 
        hours: 0, 
        reason: 'no_job', 
        weekly_hours: 0,
        actual_worked_hours: 0,
        policy_threshold: 0,
        week_start: '',
        week_end: '',
        absent_date: ''
      };
      return;
  }

  console.log('=== Fetching Holiday Pay ===');
  console.log('Active Job ID:', props.activeJob.id);
  console.log('Active Job Name:', props.activeJob.workplace_name);
  console.log('URL:', `/labor/employees/${props.activeJob.id}/holiday-pay/`);

  loading.value = true;
  error.value = false;
  try {
    const response = await apiClient.get(`/labor/employees/${props.activeJob.id}/holiday-pay/`);
    console.log('=== Holiday Pay API Response ===');
    console.log('Full response:', response.data);
    console.log('Amount:', response.data.amount);
    console.log('Reason:', response.data.reason);
    console.log('Actual worked hours:', response.data.actual_worked_hours);
    console.log('================================');
    result.value = response.data;
  } catch (e) {
    console.error('Failed to fetch holiday pay:', e);
    error.value = true;
  } finally {
    loading.value = false;
  }
};

// Initial load
onMounted(() => {
  if (props.activeJob) {
    fetchHolidayPay();
  }
  // 전역 이벤트 리스너 등록 - 근로기록 변경 시 자동 갱신
  window.addEventListener('labor-updated', fetchHolidayPay);
});

onUnmounted(() => {
  // 이벤트 리스너 제거
  window.removeEventListener('labor-updated', fetchHolidayPay);
});

// Watch for job changes
watch(() => props.activeJob?.id, () => {
  fetchHolidayPay();
});

// Expose refresh method
defineExpose({
  refresh: fetchHolidayPay
});
</script>
