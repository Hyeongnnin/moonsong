<template>
  <!-- 선택된 달 통계 카드 - 콘텐츠 기반 높이 -->
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-gray-900">{{ statsTitle }}</h3>
    </div>

    <!-- 빈 상태: 미래 달이거나 데이터 없을 때 -->
    <div v-if="showSetupCTA" class="text-center py-10">
      <div class="text-4xl mb-3">{{ isFutureMonth ? '🗓️' : '🛠️' }}</div>
      <p class="text-sm text-gray-600 font-medium mb-2">
        {{ isFutureMonth ? '아직 근로 전이에요' : '아직 통계가 없어요' }}
      </p>
      <p class="text-xs text-gray-500 mb-6">
        {{ isFutureMonth ? '해당 월의 근로가 시작되면\n실시간 통계가 집계됩니다' : '근로정보를 설정하면 이 달의 통계가 표시됩니다' }}
      </p>
      <button
        v-if="!isFutureMonth"
        @click="goToEdit"
        class="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        근로정보 수정하러 가기
      </button>
    </div>

    <!-- 통계 표시 -->
    <div v-else class="space-y-3">
      <div 
        class="flex items-center justify-between p-4 rounded-lg border transition-colors"
        :class="isFutureMonth ? 'bg-gray-50 border-gray-100' : 'bg-brand-50 border-brand-100'"
      >
        <div>
          <p class="text-sm font-medium text-gray-700">일한 시간</p>
        </div>
        <div class="text-right">
          <p class="text-xl font-bold" :class="isFutureMonth ? 'text-gray-400' : 'text-brand-600'">{{ monthlyTotalHours.toFixed(1) }}시간</p>
        </div>
      </div>

      <div class="flex items-center justify-between p-4 bg-orange-50 bg-opacity-40 rounded-lg border border-orange-100">
        <div>
          <p class="text-sm font-medium text-orange-900">주휴수당</p>
          <p class="text-[10px] font-bold text-orange-400 mt-1 uppercase tracking-tighter">주 15시간 이상 & 개근</p>
        </div>
        <div class="text-right">
          <p class="text-lg font-bold text-orange-700">{{ weeklyHolidayHours.toFixed(1) }}시간</p>
          <p class="text-xs font-semibold text-orange-500">+ {{ formatCurrency(weeklyHolidayPay) }}</p>
        </div>
      </div>

      <div v-if="nightHours > 0 || (monthlyPayroll?.night_bonus && monthlyPayroll.night_bonus > 0)" class="flex items-center justify-between p-4 bg-indigo-50 bg-opacity-40 rounded-lg border border-indigo-100">
        <div>
          <p class="text-sm font-medium text-indigo-900">야간 근로시간</p>
          <p class="text-[10px] font-bold text-indigo-400 mt-1 uppercase tracking-tighter">22:00 ~ 06:00 가산</p>
        </div>
        <div class="text-right">
          <p class="text-lg font-bold text-indigo-700">{{ nightHours.toFixed(1) }}시간</p>
          <p class="text-xs font-semibold text-indigo-500">+ {{ formatCurrency(nightBonus) }}</p>
        </div>
      </div>

      <button
        type="button"
        class="flex items-center justify-between w-full p-4 bg-gray-50 rounded-lg border border-transparent transition shadow-none focus-visible:outline-none ring-0 focus:ring-0 outline-none"
        :class="monthlyPayroll ? 'hover:bg-white hover:border-brand-200 focus-visible:ring-2 focus-visible:ring-brand-200 cursor-pointer pointer-events-auto' : 'cursor-not-allowed opacity-60 pointer-events-none'"
        :title="monthlyPayroll ? '급여 계산 근거 보기' : '급여 정보가 없습니다'"
        @click="openBreakdownModal"
      >
        <div class="text-left">
          <p class="text-sm font-medium text-gray-700">급여 예상액</p>
          <p class="text-[10px] font-bold text-gray-400 mt-1 uppercase tracking-tighter">
            {{ netPayLabel }}
          </p>
        </div>
        <div class="text-right">
          <p class="text-xl font-bold text-gray-600">{{ formatCurrency(monthlyEstimatedSalary) }}</p>
          <p v-if="isDeducted" class="text-[10px] text-gray-400 line-through">{{ formatCurrency(monthlyGrossPay) }}</p>
        </div>
      </button>



      <!-- 미래 달 안내 문구 -->
      <div v-if="isFutureMonth" class="mt-4 p-3 bg-blue-50 bg-opacity-50 rounded-lg border border-blue-100">
         <p class="text-[11px] text-blue-700 leading-relaxed font-medium">
           ℹ️ 미래의 날짜는 '오늘' 이후 실제 기록이 추가되면 위 수치가 업데이트됩니다.
         </p>
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

interface PayrollBreakdownItem {
  date: string;
  source: string; // actual | scheduled | none
  hours: number;
  is_holiday: boolean;
  holiday_type: string | null;
  day_pay: number;
  holiday_bonus: number;
  night_hours: number;
  night_bonus: number;
  is_future: boolean;
}

interface PayrollSummaryResponse {
  month: string;
  hourly_wage: number;
  workplace_size: string;
  contract_weekly_hours: number | null;
  total_hours: number;
  actual_hours: number;
  scheduled_hours: number;
  base_pay: number;
  holiday_hours: number;
  holiday_bonus: number;
  night_hours: number;
  night_bonus: number;
  estimated_monthly_pay: number;
  net_pay: number;
  summary: {
    base_pay: number;
    night_extra: number;
    holiday_extra: number;
    total: number;
    deduction?: {
      type: string;
      total_deduction: number;
      net_pay: number;
      details: Array<{ label: string; amount: number }>;
    };
  };
  rows: PayrollBreakdownItem[];
  notes: string[];
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
  displayYear: undefined,
  displayMonth: undefined,
});

const monthlyTotalHours = ref(0);
const actualHours = ref(0);
const scheduledHours = ref(0);
const monthlyEstimatedSalary = computed(() => {
  return monthlyPayroll.value?.net_pay ?? monthlyPayroll.value?.estimated_monthly_pay ?? 0;
});
const monthlyGrossPay = computed(() => monthlyPayroll.value?.estimated_monthly_pay ?? 0);

const isDeducted = computed(() => {
  const type = monthlyPayroll.value?.summary?.deduction?.type;
  return type === 'FOUR_INSURANCE' || type === 'FREELANCE';
});

const netPayLabel = computed(() => {
  const type = monthlyPayroll.value?.summary?.deduction?.type;
  if (type === 'FOUR_INSURANCE') return '4대보험 적용 예상 실수령액';
  if (type === 'FREELANCE') return '3.3% 공제 적용 예상 실수령액';
  return '상세보기 (세전)';
});
const nightHours = ref(0);
const nightBonus = ref(0);
const weeklyHolidayHours = ref(0);
const weeklyHolidayPay = ref(0);
const monthlyPayroll = ref<PayrollSummaryResponse | null>(null);
const breakdownModalVisible = ref(false);

const hasAnyData = computed(() => (monthlyTotalHours.value > 0 || monthlyEstimatedSalary.value > 0 || scheduledHours.value > 0));
const isFutureMonth = computed(() => {
  if (!props.displayYear || !props.displayMonth) return false;
  const today = new Date();
  const ty = today.getFullYear();
  const tm = today.getMonth() + 1;
  // 현재 달보다 미래인지 (년도가 크거나, 년도가 같고 월이 크거나)
  return props.displayYear > ty || (props.displayYear === ty && props.displayMonth > tm);
});

// 미래 달이라도 스케줄이 있을 수 있으므로 hasAnyData가 true일 수 있음.
const showSetupCTA = computed(() => !!props.activeJob && !hasAnyData.value);
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
async function loadJobSummary() {
  const employeeId = props.activeJob?.id;
  if (!employeeId) {
    clearStats();
    return;
  }

  try {
    let monthStr: string;
    if (props.displayYear && props.displayMonth) {
      monthStr = `${props.displayYear}-${String(props.displayMonth).padStart(2, '0')}`;
    } else {
      const today = new Date();
      monthStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
    }
    
    console.log('[WorkSummaryCard] Loading summary for month:', monthStr);
    
    // 두 API 동시 호출
    const [payrollRes, holidayRes] = await Promise.all([
      apiClient.get(`/labor/jobs/${employeeId}/payroll-summary/`, { params: { month: monthStr } }),
      apiClient.get(`/labor/employees/${employeeId}/monthly-holiday-pay/`, { params: { month: monthStr } }).catch(() => ({ data: { confirmed_total: 0 } }))
    ]);

    const payload = payrollRes.data as PayrollSummaryResponse;
    monthlyPayroll.value = payload;

    // Use summary-nested fields if available (v2), otherwise fallback to top-level (v1)
    monthlyTotalHours.value = payload?.summary?.total_hours ?? payload?.total_hours ?? 0;
    actualHours.value = payload?.actual_hours || 0;
    scheduledHours.value = payload?.summary?.scheduled_hours ?? payload?.scheduled_hours ?? 0;
    
    nightHours.value = payload?.night_hours || 0;
    nightBonus.value = payload?.summary?.night_extra ?? payload?.night_bonus ?? 0;

    // 주휴수당 처리
    const holidayData = holidayRes.data;
    weeklyHolidayPay.value = holidayData.confirmed_total || 0;
    // 시급으로 시간 역산 (데이터가 없으면 0)
    const wage = payload.hourly_wage || props.activeJob?.hourly_wage || 0;
    if (weeklyHolidayPay.value > 0 && wage > 0) {
      weeklyHolidayHours.value = weeklyHolidayPay.value / wage;
    } else {
      weeklyHolidayHours.value = 0;
    }

  } catch (e) {
    console.error('[WorkSummaryCard] Failed to load job summary', e);
    clearStats();
  }
}

function clearStats() {
    monthlyTotalHours.value = 0;
    actualHours.value = 0;
    scheduledHours.value = 0;

    nightHours.value = 0;
    nightBonus.value = 0;
    weeklyHolidayHours.value = 0;
    weeklyHolidayPay.value = 0;
    monthlyPayroll.value = null;
}

// 외부에서 통계 업데이트 트리거
function updateStats(stats?: any) {
  loadJobSummary();
}

// activeJob, displayYear, displayMonth 중 하나라도 변경되면 로드
watch([() => props.activeJob?.id, () => props.displayYear, () => props.displayMonth], () => {
  if (props.activeJob) {
    loadJobSummary();
  } else {
    clearStats();
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
