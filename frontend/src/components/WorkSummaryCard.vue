<template>
  <!-- 선택된 달 통계 카드 - 콘텐츠 기반 높이 -->
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">{{ statsTitle }}</h3>

    <!-- 빈 상태: 새 알바 생성 직후 안내 CTA -->
    <div v-if="showSetupCTA" class="text-center py-8">
      <div class="text-4xl mb-3">🛠️</div>
      <p class="text-sm text-gray-600 font-medium mb-2">아직 통계가 없어요</p>
      <p class="text-xs text-gray-500 mb-4">근로정보를 설정하면 이 달의 통계가 표시됩니다</p>
      <button
        @click="goToEdit"
        class="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        근로정보 수정하러 가기
      </button>
    </div>

    <!-- 통계 표시 -->
    <div v-else class="space-y-3">
      <div class="flex items-center justify-between p-4 bg-brand-50 rounded-lg border border-brand-100">
        <div>
          <p class="text-sm font-medium text-gray-700">총 근로시간</p>
          <p class="text-xs text-gray-500 mt-1">{{ monthLabel }} 누적</p>
        </div>
        <p class="text-xl font-bold text-brand-600">{{ monthlyTotalHours.toFixed(1) }}시간</p>
      </div>

      <button
        type="button"
        class="flex items-center justify-between w-full p-4 bg-gray-50 rounded-lg border border-transparent transition shadow-none focus-visible:outline-none"
        :class="monthlyPayroll ? 'hover:bg-white hover:border-brand-200 focus-visible:ring-2 focus-visible:ring-brand-200 cursor-pointer' : 'cursor-not-allowed opacity-60'"
        :title="monthlyPayroll ? '급여 계산 근거 보기' : '급여 정보가 없습니다'"
        :disabled="!monthlyPayroll"
        @click="openBreakdownModal"
      >
        <div class="text-left">
          <p class="text-sm font-medium text-gray-700">급여 예상액</p>
          <p class="text-xs text-gray-500 mt-1">{{ monthLabel }} 예상</p>
        </div>
        <p class="text-xl font-bold text-gray-600">{{ formatCurrency(monthlyEstimatedSalary) }}</p>
      </button>

      <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
        <div>
          <p class="text-sm font-medium text-gray-700">총 근로일수</p>
          <p class="text-xs text-gray-500 mt-1">{{ monthLabel }} 누적</p>
        </div>
        <p class="text-xl font-bold text-gray-600">{{ totalWorkDays }}일</p>
      </div>
    </div>
  </div>
  <PayrollBreakdownModal
    :visible="breakdownModalVisible"
    :payroll="monthlyPayroll"
    @close="closeBreakdownModal"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import type { Job } from '../stores/jobStore';
import { apiClient } from '../api';
import PayrollBreakdownModal from './PayrollBreakdownModal.vue';

interface Props {
  activeJob?: Job | null;
  displayYear?: number;
  displayMonth?: number;
}

interface PayrollBreakdown {
  base_hours: number;
  overtime_hours: number;
  night_hours: number;
  holiday_hours: number;
  weekly_holiday_hours: number;
  base_pay: number;
  overtime_pay: number;
  night_pay: number;
  holiday_pay: number;
  weekly_holiday_pay: number;
}

interface MonthlyPayrollResponse {
  month: string;
  total_hours: number;
  total_work_days: number;
  estimated_salary: number;
  hourly_wage?: number;
  holiday_hours?: number;
  holiday_pay?: number;
  breakdown?: PayrollBreakdown;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
  displayYear: undefined,
  displayMonth: undefined,
});

const monthlyTotalHours = ref(0);
const monthlyEstimatedSalary = ref(0);
const totalWorkDays = ref(0);
const monthlyPayroll = ref<MonthlyPayrollResponse | null>(null);
const breakdownModalVisible = ref(false);
const hasAnyData = computed(() => (monthlyTotalHours.value > 0 || monthlyEstimatedSalary.value > 0 || totalWorkDays.value > 0));
const isFutureMonth = computed(() => {
  if (!props.displayYear || !props.displayMonth) return false;
  const today = new Date();
  const ty = today.getFullYear();
  const tm = today.getMonth() + 1;
  return props.displayYear > ty || (props.displayYear === ty && props.displayMonth > tm);
});
// 미래 달은 0값이라도 CTA를 보여주지 않고, 숫자 카드(0 표시)를 그대로 노출한다.
const showSetupCTA = computed(() => !!props.activeJob && !hasAnyData.value && !isFutureMonth.value);
const router = useRouter();
const route = useRoute();
function goToEdit() {
  if (route.path === '/dashboard' && route.query.section === 'profile-edit') {
    window.dispatchEvent(new CustomEvent('go-section', { detail: 'profile-edit' }));
    return;
  }
  router.push('/dashboard?section=profile-edit').catch(() => {});
}

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
const formatCurrency = (value: number | undefined | null = 0) => {
  const safeValue = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  return safeValue.toLocaleString('ko-KR') + '원';
};

// 통계 데이터 로드
// displayYear/displayMonth가 제공되면 해당 월 기준, 없으면 현재 월 기준
async function loadJobSummary() {
  const employeeId = props.activeJob?.id;
  if (!employeeId) {
    monthlyTotalHours.value = 0;
    monthlyEstimatedSalary.value = 0;
    totalWorkDays.value = 0;
    monthlyPayroll.value = null;
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
    
    const res = await apiClient.get(`/labor/jobs/${employeeId}/monthly-payroll/`, {
      params: { month: monthStr }
    });

    const payload = res.data as MonthlyPayrollResponse;
    monthlyPayroll.value = payload || null;

    monthlyTotalHours.value = Number(payload?.total_hours) || 0;
    monthlyEstimatedSalary.value = Number(payload?.estimated_salary) || 0;
    totalWorkDays.value = Number(payload?.total_work_days) || 0;
  } catch (e) {
    console.error('[WorkSummaryCard] Failed to load job summary', e);
    monthlyTotalHours.value = 0;
    monthlyEstimatedSalary.value = 0;
    totalWorkDays.value = 0;
    monthlyPayroll.value = null;
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

// 근로기록 저장/삭제/월스케줄 저장 시 새로고침 이벤트 수신
function onLaborUpdated() {
  updateStats();
}

function openBreakdownModal() {
  if (monthlyPayroll.value) {
    breakdownModalVisible.value = true;
  }
}

function closeBreakdownModal() {
  breakdownModalVisible.value = false;
}

onMounted(() => {
  window.addEventListener('labor-updated', onLaborUpdated);
});

onUnmounted(() => {
  window.removeEventListener('labor-updated', onLaborUpdated);
});

// 외부에서 호출 가능하도록 expose
defineExpose({ updateStats });
</script>

<style scoped>
</style>
