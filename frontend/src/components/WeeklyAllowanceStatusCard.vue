<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-900">주휴수당 판단 결과</h3>
      <button 
        @click="refresh"
        class="text-gray-400 hover:text-gray-600 transition-colors"
        title="새로고침"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>

    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="text-center py-6">
      <div class="text-3xl mb-2">📋</div>
      <p class="text-sm text-gray-600 mb-1">근로정보를 입력해주세요</p>
      <p class="text-xs text-gray-400">주휴수당 발생 여부를 확인할 수 있습니다</p>
    </div>

    <!-- 근로정보가 있을 때 -->
    <div v-else>
      <div v-if="loading" class="text-center text-gray-500 py-6 text-sm">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto mb-2"></div>
        판단 중...
      </div>

      <div v-else-if="error" class="text-center py-6">
        <div class="text-3xl mb-2">⚠️</div>
        <p class="text-sm text-red-500">데이터를 불러오는데 실패했습니다</p>
      </div>

      <div v-else>
        <!-- 결과 문구 -->
        <div class="mb-4 text-center">
          <p v-if="result.eligible" class="text-lg font-bold text-green-600">
            주휴수당 대상이에요 🎉
          </p>
          <p v-else class="text-lg font-bold text-red-600">
            주휴수당 대상이 아니에요 😢
          </p>
        </div>

        <!-- 요건 배지 (가로 배치) -->
        <div class="flex flex-wrap gap-2 mb-4">
          <div 
            v-for="criterion in orderedCriteria" 
            :key="criterion.key"
            :class="getBadgeClass(criterion.status)"
            class="px-3 py-2 rounded-full text-xs font-medium whitespace-nowrap"
          >
            <span class="mr-1">{{ getStatusEmoji(criterion.status) }}</span>
            <span>{{ criterion.label }}</span>
            <span v-if="criterion.detail" class="ml-1 opacity-90">({{ criterion.detail }})</span>
          </div>
        </div>

        <!-- 추가 정보 -->
        <div class="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-500">
          <p v-if="result.week_start && result.week_end">
            대상 기간: {{ formatDateRange(result.week_start, result.week_end) }}
          </p>
          <p v-if="result.eligible && result.amount" class="mt-1 text-green-700 font-semibold">
            예상 금액: {{ formatCurrency(result.amount) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { apiClient } from '../api';
import type { Job } from '../stores/jobStore';

const props = defineProps<{
  activeJob: Job | null;
}>();

const loading = ref(false);
const error = ref(false);
const result = ref({
  eligible: false,
  amount: 0,
  weekly_hours: 0,
  threshold: 15,
  reason: '',
  week_start: '',
  week_end: '',
  absent_date: '',
  criteria: {
    is_worker: { status: 'unknown', label: '근로자 요건', detail: '판단 불가' },
    weekly_hours: { status: 'unknown', label: '주 15시간 이상 근무', detail: '판단 불가' },
    attendance: { status: 'unknown', label: '개근', detail: '판단 불가' }
  }
});

// 요건을 순서대로 정렬된 배열로 변환
const orderedCriteria = computed(() => {
  const criteriaObj = result.value.criteria || {};
  return [
    { key: 'is_worker', ...criteriaObj.is_worker },
    { key: 'weekly_hours', ...criteriaObj.weekly_hours },
    { key: 'attendance', ...criteriaObj.attendance }
  ];
});

// status에 따른 배지 클래스 반환
const getBadgeClass = (status: string) => {
  if (status === 'pass') {
    return 'bg-green-100 text-green-700 border border-green-300';
  } else if (status === 'fail') {
    return 'bg-red-100 text-red-700 border border-red-300';
  } else {
    return 'bg-yellow-100 text-yellow-700 border border-yellow-300';
  }
};

// status에 따른 이모지 반환
const getStatusEmoji = (status: string) => {
  if (status === 'pass') return '🟢';
  if (status === 'fail') return '🔴';
  return '🟡';
};

const formatCurrency = (value: number) => {
  return value.toLocaleString('ko-KR') + '원';
};

const formatDateRange = (start: string, end: string) => {
  if (!start || !end) return '';
  const startDate = new Date(start);
  const endDate = new Date(end);
  return `${startDate.getMonth() + 1}/${startDate.getDate()} - ${endDate.getMonth() + 1}/${endDate.getDate()}`;
};

const fetchWeeklyAllowanceStatus = async () => {
  if (!props.activeJob) return;

  loading.value = true;
  error.value = false;

  try {
    console.log('=== Fetching Weekly Allowance Status ===');
    console.log('Active Job ID:', props.activeJob.id);
    console.log('URL:', `/labor/employees/${props.activeJob.id}/holiday-pay/`);
    
    const response = await apiClient.get(`/labor/employees/${props.activeJob.id}/holiday-pay/`);
    const data = response.data;
    
    console.log('=== API Response ===');
    console.log('Full response:', data);

    // API 응답을 기반으로 판단 결과 설정 및 criteria 생성
    const eligible = data.amount > 0;
    const weeklyHours = data.actual_worked_hours || data.weekly_hours || 0;
    const threshold = data.policy_threshold || 15;
    const reason = data.reason || '';

    // criteria 객체 생성
    const criteria = {
      is_worker: {
        status: 'pass' as const,
        label: '근로자 요건',
        detail: '충족'
      },
      weekly_hours: {
        status: weeklyHours >= threshold ? 'pass' as const : 'fail' as const,
        label: `주 ${threshold}시간 이상 근무`,
        detail: weeklyHours >= threshold 
          ? '충족' 
          : `미충족 (현재 ${weeklyHours.toFixed(1)}시간)`
      },
      attendance: {
        status: reason === 'absent' ? 'fail' as const : 
                reason === 'no_schedule' ? 'unknown' as const : 'pass' as const,
        label: '개근',
        detail: reason === 'absent' ? `결근 발생${data.absent_date ? ` (${data.absent_date})` : ''}` :
                reason === 'no_schedule' ? '여부 판단 불가' :
                eligible ? '충족' : '확인 필요'
      }
    };

    result.value = {
      eligible,
      amount: data.amount || 0,
      weekly_hours: weeklyHours,
      threshold,
      reason,
      week_start: data.week_start || '',
      week_end: data.week_end || '',
      absent_date: data.absent_date || '',
      criteria
    };
    
    console.log('=== Processed Result ===');
    console.log('Eligible:', eligible);
    console.log('Criteria:', criteria);
    console.log('========================');
  } catch (err: any) {
    console.error('=== Weekly Allowance Status Error ===');
    console.error('Error:', err);
    console.error('Response:', err?.response?.data);
    console.error('Status:', err?.response?.status);
    console.error('=====================================');
    error.value = true;
  } finally {
    loading.value = false;
  }
};

const refresh = () => {
  fetchWeeklyAllowanceStatus();
};

// activeJob 변경 시 자동으로 데이터 갱신
watch(() => props.activeJob, (newJob) => {
  if (newJob) {
    fetchWeeklyAllowanceStatus();
  }
}, { immediate: true });

onMounted(() => {
  if (props.activeJob) {
    fetchWeeklyAllowanceStatus();
  }
});

// 외부에서 refresh 호출 가능하도록 expose
defineExpose({
  refresh
});
</script>

<style scoped>
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
