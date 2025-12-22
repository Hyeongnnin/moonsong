<template>
  <div class="max-w-4xl mx-auto">
    <!-- 헤더 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">근로진단</h1>
      <p class="text-sm text-gray-600">현재 근로 조건이 법적 기준을 충족하는지 확인하세요.</p>
    </div>

    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="bg-white rounded-lg border border-gray-200 p-12 text-center">
      <div class="text-6xl mb-4">📋</div>
      <h2 class="text-xl font-bold text-gray-900 mb-2">근로정보가 필요합니다</h2>
      <p class="text-gray-600 mb-6">근로진단을 받으려면 먼저 근로정보를 입력해주세요.</p>
      <button
        @click="router.push('/dashboard?section=profile-edit')"
        class="px-6 py-3 bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-lg transition-colors"
      >
        근로정보 입력하기
      </button>
    </div>

    <!-- 근로정보가 있을 때 -->
    <div v-else class="space-y-6">
      <!-- 1. 주휴수당 진단 카드 -->
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">{{ holidayPayDiagnosis.icon }}</span>
          <div>
            <h2 class="text-lg font-bold text-gray-900">주휴수당 요건</h2>
            <p class="text-sm text-gray-600">{{ holidayPayDiagnosis.summary }}</p>
          </div>
        </div>

        <div v-if="loadingHolidayPay" class="text-center py-8 text-gray-500">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600 mx-auto mb-2"></div>
          진단 중...
        </div>

        <div v-else-if="errorHolidayPay" class="bg-red-50 border border-red-200 rounded-lg p-4">
          <p class="text-sm text-red-700">데이터를 불러올 수 없습니다.</p>
        </div>

        <div v-else>
          <!-- 요건 배지 -->
          <div class="flex flex-wrap gap-2 mb-4">
            <div 
              v-for="criterion in holidayPayCriteria" 
              :key="criterion.key"
              :class="getCriterionBadgeClass(criterion.status)"
              class="px-3 py-2 rounded-lg text-sm font-medium"
            >
              <span class="mr-1">{{ getCriterionEmoji(criterion.status) }}</span>
              <span>{{ criterion.label }}</span>
              <span v-if="criterion.detail" class="ml-1 opacity-90">({{ criterion.detail }})</span>
            </div>
          </div>

          <!-- 상세 설명 -->
          <div class="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
            <p class="font-semibold text-gray-900">📌 주휴수당이란?</p>
            <p class="text-gray-700">주 15시간 이상 근무하고 개근한 근로자에게 지급되는 유급휴일 수당입니다.</p>
            <p class="text-gray-700">• 주간 근무시간: <span class="font-semibold">{{ holidayPayData.weekly_hours }}시간</span></p>
            <p class="text-gray-700">• 기준 시간: <span class="font-semibold">{{ holidayPayData.threshold }}시간</span></p>
            <p v-if="holidayPayData.eligible && holidayPayData.amount" class="text-green-700 font-semibold mt-2">
              💰 예상 주휴수당: {{ formatCurrency(holidayPayData.amount) }}
            </p>
            <p v-if="holidayPayData.week_start && holidayPayData.week_end" class="text-gray-500 text-xs mt-2">
              대상 기간: {{ formatDateRange(holidayPayData.week_start, holidayPayData.week_end) }}
            </p>
          </div>
        </div>
      </div>

      <!-- 2. 퇴직금 진단 카드 -->
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">{{ retirementDiagnosis.icon }}</span>
          <div>
            <h2 class="text-lg font-bold text-gray-900">퇴직금 요건</h2>
            <p class="text-sm text-gray-600">{{ retirementDiagnosis.summary }}</p>
          </div>
        </div>

        <div class="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
          <p class="font-semibold text-gray-900">📌 퇴직금이란?</p>
          <p class="text-gray-700">1년 이상 계속 근로한 근로자가 퇴직할 때 받는 법정 수당입니다.</p>
          <p class="text-gray-700">• 근속 기간: <span class="font-semibold">{{ retirementData.workDays }}일 (약 {{ retirementData.workYears }}년)</span></p>
          <p class="text-gray-700">• 요건: <span class="font-semibold">1년 이상 근무</span></p>
          <p v-if="retirementData.eligible" class="text-green-700 font-semibold mt-2">
            ✅ 퇴직금 수급 자격이 있습니다.
          </p>
          <p v-else class="text-gray-600 mt-2">
            ⏳ 1년 이상 근무 시 퇴직금을 받을 수 있습니다.
          </p>
        </div>
      </div>

      <!-- 3. 근로시간 진단 카드 -->
      <div class="bg-white rounded-lg border border-gray-200 p-6">
        <div class="flex items-center gap-3 mb-4">
          <span class="text-3xl">{{ workHoursDiagnosis.icon }}</span>
          <div>
            <h2 class="text-lg font-bold text-gray-900">주 52시간 준수</h2>
            <p class="text-sm text-gray-600">{{ workHoursDiagnosis.summary }}</p>
          </div>
        </div>

        <div class="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
          <p class="font-semibold text-gray-900">📌 주 52시간 제도란?</p>
          <p class="text-gray-700">1주일 최대 근로시간은 40시간(법정), 연장근로 12시간을 포함해 최대 52시간입니다.</p>
          <p class="text-gray-700">• 현재 주간 근무시간: <span class="font-semibold">{{ workHoursData.weeklyHours }}시간</span></p>
          <p class="text-gray-700">• 법정 한도: <span class="font-semibold">52시간</span></p>
          <p v-if="!workHoursData.exceeds" class="text-green-700 font-semibold mt-2">
            ✅ 법정 근로시간을 준수하고 있습니다.
          </p>
          <p v-else class="text-yellow-700 font-semibold mt-2">
            ⚠️ 주간 근로시간이 52시간을 초과할 우려가 있습니다.
          </p>
        </div>
      </div>

      <!-- 안내 사항 -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p class="text-sm text-blue-800">
          💡 <span class="font-semibold">알아두세요</span><br>
          이 진단 결과는 입력된 근로정보를 기반으로 자동 계산된 것입니다. 
          실제 법적 판단은 관할 노동청이나 전문가와 상담하시기 바랍니다.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useJob } from '../stores/jobStore';
import { apiClient } from '../api';

const router = useRouter();
const { activeJob } = useJob();

const loadingHolidayPay = ref(false);
const errorHolidayPay = ref(false);

const holidayPayData = ref({
  eligible: false,
  amount: 0,
  weekly_hours: 0,
  threshold: 15,
  reason: '',
  week_start: '',
  week_end: '',
  criteria: {
    is_worker: { status: 'unknown', label: '근로자 요건', detail: '' },
    weekly_hours: { status: 'unknown', label: '주 15시간 이상', detail: '' },
    attendance: { status: 'unknown', label: '개근', detail: '' }
  }
});

const retirementData = ref({
  eligible: false,
  workDays: 0,
  workYears: 0
});

const workHoursData = ref({
  weeklyHours: 0,
  exceeds: false
});

// 주휴수당 진단 결과
const holidayPayDiagnosis = computed(() => {
  if (holidayPayData.value.eligible) {
    return {
      icon: '✅',
      summary: '주휴수당 요건을 충족합니다'
    };
  }
  return {
    icon: '❌',
    summary: '주휴수당 요건을 충족하지 않습니다'
  };
});

// 주휴수당 요건 배지 배열
const holidayPayCriteria = computed(() => {
  const criteria = holidayPayData.value.criteria;
  return [
    { key: 'is_worker', ...criteria.is_worker },
    { key: 'weekly_hours', ...criteria.weekly_hours },
    { key: 'attendance', ...criteria.attendance }
  ];
});

// 퇴직금 진단 결과
const retirementDiagnosis = computed(() => {
  if (retirementData.value.eligible) {
    return {
      icon: '✅',
      summary: '퇴직금 요건을 충족합니다'
    };
  }
  return {
    icon: '⏳',
    summary: '1년 이상 근무 시 퇴직금 수급 가능'
  };
});

// 근로시간 진단 결과
const workHoursDiagnosis = computed(() => {
  if (!workHoursData.value.exceeds) {
    return {
      icon: '✅',
      summary: '법정 근로시간을 준수하고 있습니다'
    };
  }
  return {
    icon: '⚠️',
    summary: '주 52시간 초과 우려'
  };
});

const getCriterionBadgeClass = (status: string) => {
  if (status === 'pass') return 'bg-green-100 text-green-700 border border-green-300';
  if (status === 'fail') return 'bg-red-100 text-red-700 border border-red-300';
  return 'bg-yellow-100 text-yellow-700 border border-yellow-300';
};

const getCriterionEmoji = (status: string) => {
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

const fetchDiagnosisData = async () => {
  if (!activeJob.value) return;

  // 주휴수당 정보 조회
  loadingHolidayPay.value = true;
  errorHolidayPay.value = false;

  try {
    const response = await apiClient.get(`/labor/employees/${activeJob.value.id}/holiday-pay/`);
    const data = response.data;

    const eligible = data.amount > 0;
    const weeklyHours = data.actual_worked_hours || data.weekly_hours || 0;
    const threshold = data.policy_threshold || 15;
    const reason = data.reason || '';

    // criteria 생성
    const criteria = {
      is_worker: {
        status: 'pass' as const,
        label: '근로자 요건',
        detail: '충족'
      },
      weekly_hours: {
        status: weeklyHours >= threshold ? 'pass' as const : 'fail' as const,
        label: `주 ${threshold}시간 이상 근무`,
        detail: weeklyHours >= threshold ? '충족' : `미충족 (현재 ${weeklyHours.toFixed(1)}시간)`
      },
      attendance: {
        status: reason === 'absent' ? 'fail' as const : 
                reason === 'no_schedule' ? 'unknown' as const : 'pass' as const,
        label: '개근',
        detail: reason === 'absent' ? `결근 발생` :
                reason === 'no_schedule' ? '판단 불가' :
                eligible ? '충족' : '확인 필요'
      }
    };

    holidayPayData.value = {
      eligible,
      amount: data.amount || 0,
      weekly_hours: weeklyHours,
      threshold,
      reason,
      week_start: data.week_start || '',
      week_end: data.week_end || '',
      criteria
    };

    // 퇴직금 정보 계산
    const startDate = new Date(activeJob.value.start_date);
    const today = new Date();
    const workDays = Math.floor((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    const workYears = (workDays / 365).toFixed(1);

    retirementData.value = {
      eligible: workDays >= 365,
      workDays,
      workYears: parseFloat(workYears)
    };

    // 근로시간 정보
    workHoursData.value = {
      weeklyHours,
      exceeds: weeklyHours > 52
    };

  } catch (err) {
    console.error('근로진단 데이터 조회 실패:', err);
    errorHolidayPay.value = true;
  } finally {
    loadingHolidayPay.value = false;
  }
};

onMounted(() => {
  if (activeJob.value) {
    fetchDiagnosisData();
  }
});

watch(() => activeJob.value?.id, () => {
  if (activeJob.value) {
    fetchDiagnosisData();
  }
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
