<template>
  <div class="max-w-4xl mx-auto">
    <!-- 헤더 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">근로진단</h1>
      <p class="text-sm text-gray-600">현재 근로 조건이 법적 기준을 충족하는지 확인하세요.</p>
    </div>

    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="p-12 text-center">
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
    <div v-else class="space-y-8">
      <!-- 1. 주휴수당 진단 카드 -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="p-6">
          <!-- (1) 한 줄 요약 -->
          <div class="flex items-center gap-3 mb-4">
            <span class="text-3xl">{{ holidayPayDiagnosis.icon }}</span>
            <h2 class="text-xl font-bold text-gray-900">{{ holidayPayDiagnosis.title }}</h2>
          </div>

          <!-- (2) 바로 이해되는 이유 설명 -->
          <p class="text-gray-700 mb-6 bg-brand-50 p-4 rounded-lg border border-brand-100">
            {{ holidayPayDiagnosis.description }}
          </p>

          <!-- (3) 조건 시각화 -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
            <div 
              v-for="criterion in holidayPayCriteria" 
              :key="criterion.key"
              :class="getCriterionBadgeClass(criterion.status)"
              class="flex items-center gap-2 p-3 rounded-lg border font-medium"
            >
              <span>{{ getCriterionEmoji(criterion.status) }}</span>
              <span>{{ criterion.label }}</span>
            </div>
          </div>

          <!-- (4) 내 데이터 연결 -->
          <div class="bg-gray-50 rounded-lg p-5 mb-6">
            <h3 class="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
              📊 내 데이터 확인
            </h3>
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <p class="text-xs text-gray-500 mb-1">이번 주 근무</p>
                <p class="text-sm font-semibold text-gray-900">{{ holidayPayData.weekly_hours }}시간</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1">기준 시간</p>
                <p class="text-sm font-semibold text-gray-900">{{ holidayPayData.threshold }}시간</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1">대상 기간</p>
                <p class="text-sm font-semibold text-gray-900">{{ formatDateRange(holidayPayData.week_start, holidayPayData.week_end) }}</p>
              </div>
              <div v-if="holidayPayData.eligible">
                <p class="text-xs text-gray-500 mb-1">예상 주휴수당</p>
                <p class="text-sm font-bold text-brand-600">{{ formatCurrency(holidayPayData.amount) }}</p>
              </div>
            </div>
          </div>

          <!-- (5) 쉬운 개념 설명 -->
          <div class="border-t border-gray-100 pt-6">
            <h3 class="text-sm font-bold text-gray-900 mb-2">💡 주휴수당이란?</h3>
            <p class="text-sm text-gray-600 leading-relaxed">
              일주일 동안 정해진 근무일(소정근로일)에 모두 출근하고, 주 15시간 이상 근무한 분들에게 주어지는 <strong>유급 휴일 수당</strong>이에요. 
              쉽게 말해, 일주일간 고생한 당신에게 나라에서 정한 '유급 휴식'에 대한 보상이라고 생각하면 돼요!
            </p>
          </div>
        </div>
      </div>

      <!-- 2. 퇴직금 진단 카드 -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="p-6">
          <div class="flex items-center gap-3 mb-4">
            <span class="text-3xl">{{ retirementDiagnosis.icon }}</span>
            <h2 class="text-xl font-bold text-gray-900">{{ retirementDiagnosis.title }}</h2>
          </div>

          <p class="text-gray-700 mb-6 bg-brand-50 p-4 rounded-lg border border-brand-100">
            {{ retirementDiagnosis.description }}
          </p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
            <div :class="getCriterionBadgeClass(retirementData.eligible ? 'pass' : 'fail')" class="flex items-center gap-2 p-3 rounded-lg border font-medium">
              <span>{{ getCriterionEmoji(retirementData.eligible ? 'pass' : 'fail') }}</span>
              <span>1년 이상 근무</span>
            </div>
            <div :class="getCriterionBadgeClass(holidayPayData.weekly_hours >= 15 ? 'pass' : 'fail')" class="flex items-center gap-2 p-3 rounded-lg border font-medium">
              <span>{{ getCriterionEmoji(holidayPayData.weekly_hours >= 15 ? 'pass' : 'fail') }}</span>
              <span>주 15시간 이상</span>
            </div>
          </div>

          <div class="bg-gray-50 rounded-lg p-5 mb-6">
            <h3 class="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
              📊 내 데이터 확인
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-gray-500 mb-1">현재 근속 기간</p>
                <p class="text-sm font-semibold text-gray-900">{{ retirementData.workDays }}일 (약 {{ retirementData.workYears }}년)</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1">근로 시작일</p>
                <p class="text-sm font-semibold text-gray-900">{{ activeJob.start_date }}</p>
              </div>
            </div>
          </div>

          <div class="border-t border-gray-100 pt-6">
            <h3 class="text-sm font-bold text-gray-900 mb-2">💡 퇴직금이란?</h3>
            <p class="text-sm text-gray-600 leading-relaxed">
              한 직장에서 1년 이상, 매주 평균 15시간 이상 근무한 근로자가 일을 그만둘 때 받는 돈이에요. 
              오랫동안 성실히 근무한 것에 대한 보상금 성격입니다.
            </p>
          </div>
        </div>
      </div>

      <!-- 3. 연차휴가 진단 카드 -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="p-6">
          <div class="flex items-center gap-3 mb-4">
            <span class="text-3xl">{{ annualLeaveDiagnosis.icon }}</span>
            <h2 class="text-xl font-bold text-gray-900">{{ annualLeaveDiagnosis.title }}</h2>
          </div>

          <p class="text-gray-700 mb-6 bg-brand-50 p-4 rounded-lg border border-brand-100">
            {{ annualLeaveDiagnosis.description }}
          </p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
            <div :class="getCriterionBadgeClass(activeJob.is_workplace_over_5 ? 'pass' : 'fail')" class="flex items-center gap-2 p-3 rounded-lg border font-medium">
              <span>{{ getCriterionEmoji(activeJob.is_workplace_over_5 ? 'pass' : 'fail') }}</span>
              <span>5인 이상 사업장</span>
            </div>
            <div :class="getCriterionBadgeClass(holidayPayData.weekly_hours >= 15 ? 'pass' : 'fail')" class="flex items-center gap-2 p-3 rounded-lg border font-medium">
              <span>{{ getCriterionEmoji(holidayPayData.weekly_hours >= 15 ? 'pass' : 'fail') }}</span>
              <span>주 15시간 이상</span>
            </div>
          </div>

          <div class="bg-gray-50 rounded-lg p-5 mb-6">
            <h3 class="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
              📊 내 데이터 확인
            </h3>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <p class="text-xs text-gray-500 mb-1">발생 연차</p>
                <p class="text-sm font-semibold text-gray-900">{{ annualLeaveData.total }}일</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1">사용한 연차</p>
                <p class="text-sm font-semibold text-gray-900">{{ annualLeaveData.used }}일</p>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1">남은 연차</p>
                <p class="text-sm font-bold text-brand-600">{{ annualLeaveData.available }}일</p>
              </div>
            </div>
          </div>

          <div class="border-t border-gray-100 pt-6">
            <h3 class="text-sm font-bold text-gray-900 mb-2">💡 연차휴가는 언제 생기나요?</h3>
            <p class="text-sm text-gray-600 leading-relaxed">
              입사한 지 1년 미만일 때는 한 달 개근할 때마다 1일씩 생기고, 1년이 되면 총 15일의 연차휴가가 생겨요. 
              단, 5인 이상 사업장에서 주 15시간 이상 일하는 경우에만 법적으로 보장됩니다.
            </p>
          </div>
        </div>
      </div>

      <!-- 4. 추가 수당 진단 카드 -->
      <div class="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        <div class="p-6">
          <div class="flex items-center gap-3 mb-4">
            <span class="text-3xl">{{ extraPayDiagnosis.icon }}</span>
            <h2 class="text-xl font-bold text-gray-900">{{ extraPayDiagnosis.title }}</h2>
          </div>

          <p class="text-gray-700 mb-6 bg-brand-50 p-4 rounded-lg border border-brand-100">
            {{ extraPayDiagnosis.description }}
          </p>

          <div class="bg-gray-50 rounded-lg p-5 mb-6">
            <h3 class="text-sm font-bold text-gray-900 mb-3 flex items-center gap-2">
              📊 내 사업장 정보
            </h3>
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600">사업장 규모</span>
              <span class="text-sm font-bold" :class="activeJob.is_workplace_over_5 ? 'text-brand-600' : 'text-gray-600'">
                {{ activeJob.is_workplace_over_5 ? '5인 이상 사업장' : '5인 미만 사업장' }}
              </span>
            </div>
          </div>

          <div class="border-t border-gray-100 pt-6">
            <h3 class="text-sm font-bold text-gray-900 mb-2">💡 야간·휴일 수당이란?</h3>
            <p class="text-sm text-gray-600 leading-relaxed">
              밤 10시부터 다음날 아침 6시 사이에 일하거나(야간), 쉬는 날(휴일)에 일할 때 받는 추가 금전적 보상이에요. 
              보통 원래 시급의 50%를 더 받게 되는데, 이 규정은 5인 이상 사업장에만 적용됩니다.
            </p>
          </div>
        </div>
      </div>

      <!-- 5. 사업장 규모 비교 섹션 -->
      <div class="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-8 text-white shadow-lg">
        <div class="flex items-center gap-3 mb-6">
          <span class="text-2xl">🏢</span>
          <h2 class="text-xl font-bold">5인 이상 vs 5인 미만, 뭐가 다른가요?</h2>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white/10 rounded-xl p-5 border border-white/10" :class="{'ring-2 ring-brand-400': activeJob.is_workplace_over_5}">
            <div class="flex justify-between items-start mb-4">
              <h3 class="font-bold text-lg">5인 이상 사업장</h3>
              <span v-if="activeJob.is_workplace_over_5" class="bg-brand-500 text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider">나의 사업장</span>
            </div>
            <ul class="space-y-3 text-sm text-gray-300">
              <li class="flex items-center gap-2"><span class="text-brand-400">✔</span> 야간·휴일·연장수당 (50% 가산)</li>
              <li class="flex items-center gap-2"><span class="text-brand-400">✔</span> 연차유급휴가 발생</li>
              <li class="flex items-center gap-2"><span class="text-brand-400">✔</span> 정당한 이유 없는 해고 금지</li>
            </ul>
          </div>

          <div class="bg-white/10 rounded-xl p-5 border border-white/10" :class="{'ring-2 ring-brand-400': !activeJob.is_workplace_over_5}">
            <div class="flex justify-between items-start mb-4">
              <h3 class="font-bold text-lg">5인 미만 사업장</h3>
              <span v-if="!activeJob.is_workplace_over_5" class="bg-brand-500 text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider">나의 사업장</span>
            </div>
            <ul class="space-y-3 text-sm text-gray-300">
              <li class="flex items-center gap-2"><span class="text-gray-500">❌</span> 가산수당 의무 없음 (시급대로)</li>
              <li class="flex items-center gap-2"><span class="text-gray-500">❌</span> 연차휴가 의무 없음</li>
              <li class="flex items-center gap-2"><span class="text-gray-500">❌</span> 해고 제한 규정 미적용</li>
            </ul>
          </div>
        </div>
        
        <p class="mt-6 text-xs text-gray-400 text-center">
          주휴수당과 퇴직금은 사업장 규모에 상관없이 15시간 이상 근무 시 모두 받을 수 있어요!
        </p>
      </div>

      <!-- 하단 공통 안내 문구 -->
      <div class="bg-blue-50 border border-blue-100 rounded-xl p-6 text-center">
        <p class="text-sm text-blue-800 leading-relaxed">
          이 근로진단은 입력한 근로기록을 바탕으로 근로기준을 쉽게 이해할 수 있도록 정리한 결과입니다.<br>
          실제 법적 판단이나 분쟁이 필요한 경우에는 <strong>고용노동부</strong> 또는 <strong>전문가 상담</strong>을 권장합니다.
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

const annualLeaveData = ref({
  total: 0,
  used: 0,
  available: 0
});

const holidayPayDiagnosis = computed(() => {
  if (holidayPayData.value.eligible) {
    return {
      icon: '✅',
      title: '주휴수당을 받을 수 있어요!',
      description: '이번 주 근무시간과 출석 요건을 모두 채우셨네요. 다음 급여 때 주휴수당이 포함되는지 꼭 확인해보세요.'
    };
  }
  return {
    icon: '❌',
    title: '주휴수당을 아직 받을 수 없어요',
    description: holidayPayData.value.reason === 'less_than_threshold' 
      ? `주간 근무시간이 ${holidayPayData.value.threshold}시간 미만이라 주휴수당 지급 조건을 충족하지 못했어요.`
      : holidayPayData.value.reason === 'not_perfect_attendance'
      ? '약속된 근무일에 결근이 있어 이번 주 주휴수당 지급 대기 중입니다.'
      : '근무 기록이 부족하거나 조건이 맞지 않아 아직 받을 수 없어요.'
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
      title: '퇴직금을 받을 수 있어요!',
      description: '1년 이상 성실히 근무하셨군요! 퇴직 시 근무 기간에 비례한 퇴직금을 청구할 수 있는 자격이 생겼습니다.'
    };
  }
  return {
    icon: '⏳',
    title: '퇴직금까지 조금 더 힘내봐요',
    description: `현재 근속 기간이 1년 미만입니다. 앞으로 ${Math.max(0, 365 - retirementData.value.workDays)}일 더 근무하면 퇴직금을 받을 수 있어요.`
  };
});

// 연차휴가 진단 결과
const annualLeaveDiagnosis = computed(() => {
  if (annualLeaveData.value.available > 0) {
    return {
      icon: '✅',
      title: '사용 가능한 연차가 있어요',
      description: `지금까지 총 ${annualLeaveData.value.total}일의 연차가 쌓였고, 그중 ${annualLeaveData.value.available}일을 더 쉴 수 있어요.`
    };
  }
  return {
    icon: '❌',
    title: '아직 사용할 수 있는 연차가 없어요',
    description: activeJob.value?.is_workplace_over_5 
      ? '연차 발생 조건(1개월 개근 등)을 기다리고 있거나 이미 연차를 모두 사용하셨네요.'
      : '5인 미만 사업장은 법적으로 연차유급휴가 의무가 적용되지 않는 곳이에요.'
  };
});

// 추가 수당 진단 결과
const extraPayDiagnosis = computed(() => {
  if (activeJob.value?.is_workplace_over_5) {
    return {
      icon: '✅',
      title: '추가 수당이 적용되는 곳이에요',
      description: '5인 이상 사업장이므로 야간(22시~06시)이나 휴일근무 시 50%의 가산 수당을 받을 권리가 있습니다.'
    };
  }
  return {
    icon: '🟡',
    title: '추가 수당이 의무는 아니에요',
    description: '5인 미만 사업장은 법적으로 야간·휴일 가산 수당 지급 의무가 없는 곳입니다. 시급대로 급여가 계산돼요.'
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

    // 퇴직금 정보 조회
    const retirementRes = await apiClient.get(`/labor/employees/${activeJob.value.id}/retirement-pay/`);
    const rData = retirementRes.data;

    retirementData.value = {
      eligible: rData.eligible,
      workDays: rData.service_days,
      workYears: parseFloat((rData.service_days / 365).toFixed(1))
    };

    // 연차휴가 정보 조회
    const annualLeaveRes = await apiClient.get(`/labor/employees/${activeJob.value.id}/annual-leave/`);
    const aData = annualLeaveRes.data;
    annualLeaveData.value = {
      total: aData.total,
      used: aData.used,
      available: aData.available
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
