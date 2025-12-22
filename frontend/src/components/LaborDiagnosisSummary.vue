<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-900">근로진단 요약</h3>
    </div>

    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="text-center py-6">
      <div class="text-3xl mb-2">📋</div>
      <p class="text-sm text-gray-600 mb-1">근로정보를 입력해주세요</p>
      <p class="text-xs text-gray-400">근로 상태를 진단할 수 있습니다</p>
    </div>

    <!-- 근로정보가 있을 때 -->
    <div v-else>
      <div v-if="loading" class="text-center text-gray-500 py-6 text-sm">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600 mx-auto mb-2"></div>
        진단 중...
      </div>

      <div v-else-if="error" class="text-center py-4">
        <p class="text-xs text-red-500">진단 정보를 불러올 수 없습니다</p>
      </div>

      <div v-else class="space-y-4">
        <!-- 주휴수당 요건 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex flex-col">
            <span class="text-xs text-brand-600 font-medium mb-0.5">주휴수당</span>
            <span class="text-sm text-gray-900 font-semibold">받을 수 있나요?</span>
          </div>
          <div class="flex items-center gap-2">
            <span :class="diagnosis.holidayPay.statusClass" class="text-sm font-bold">
              {{ diagnosis.holidayPay.statusText }}
            </span>
            <span class="text-lg">{{ diagnosis.holidayPay.icon }}</span>
          </div>
        </div>

        <div class="border-t border-gray-100"></div>

        <!-- 퇴직금 요건 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex flex-col">
            <span class="text-xs text-brand-600 font-medium mb-0.5">퇴직금</span>
            <span class="text-sm text-gray-900 font-semibold">받을 수 있나요?</span>
          </div>
          <div class="flex items-center gap-2">
            <span :class="diagnosis.retirement.statusClass" class="text-sm font-bold">
              {{ diagnosis.retirement.statusText }}
            </span>
            <span class="text-lg">{{ diagnosis.retirement.icon }}</span>
          </div>
        </div>

        <div class="border-t border-gray-100"></div>

        <!-- 연차휴가 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex flex-col">
            <span class="text-xs text-brand-600 font-medium mb-0.5">연차휴가</span>
            <span class="text-sm text-gray-900 font-semibold">생기나요?</span>
          </div>
          <div class="flex items-center gap-2">
            <span :class="diagnosis.annualLeave.statusClass" class="text-sm font-bold">
              {{ diagnosis.annualLeave.statusText }}
            </span>
            <span class="text-lg">{{ diagnosis.annualLeave.icon }}</span>
          </div>
        </div>

        <div class="border-t border-gray-100"></div>

        <!-- 추가 수당 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex flex-col">
            <span class="text-xs text-brand-600 font-medium mb-0.5">추가 수당</span>
            <span class="text-sm text-gray-900 font-semibold">적용되나요?</span>
          </div>
          <div class="flex items-center gap-2">
            <span :class="diagnosis.extraPay.statusClass" class="text-sm font-bold">
              {{ diagnosis.extraPay.statusText }}
            </span>
            <span class="text-lg">{{ diagnosis.extraPay.icon }}</span>
          </div>
        </div>

        <!-- 자세히 보기 버튼 -->
        <button
          @click="goToDiagnosisDetail"
          class="w-full mt-4 py-2 px-4 bg-brand-50 hover:bg-brand-100 text-brand-700 text-sm font-medium rounded-lg border border-brand-200 transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <span>자세히 알아보기</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { apiClient } from '../api';
import type { Job } from '../stores/jobStore';

const props = defineProps<{
  activeJob: Job | null;
}>();

const router = useRouter();
const loading = ref(false);
const error = ref(false);

const diagnosisData = ref({
  holidayPayEligible: false,
  retirementEligible: false,
  annualLeaveEligible: false,
  extraPayApplicable: false,
  loading: false
});

// 진단 결과 computed
const diagnosis = computed(() => {
  return {
    holidayPay: {
      icon: diagnosisData.value.holidayPayEligible ? '✅' : '❌',
      statusText: diagnosisData.value.holidayPayEligible ? '받을 수 있어요' : '아직 못 받아요',
      statusClass: diagnosisData.value.holidayPayEligible ? 'text-green-600' : 'text-red-600'
    },
    retirement: {
      icon: diagnosisData.value.retirementEligible ? '✅' : '❌',
      statusText: diagnosisData.value.retirementEligible ? '받을 수 있어요' : '아직 아니에요',
      statusClass: diagnosisData.value.retirementEligible ? 'text-green-600' : 'text-red-600'
    },
    annualLeave: {
      icon: diagnosisData.value.annualLeaveEligible ? '✅' : '❌',
      statusText: diagnosisData.value.annualLeaveEligible ? '생겨요' : '아직 아니에요',
      statusClass: diagnosisData.value.annualLeaveEligible ? 'text-green-600' : 'text-red-600'
    },
    extraPay: {
      icon: diagnosisData.value.extraPayApplicable ? '✅' : '🟡',
      statusText: diagnosisData.value.extraPayApplicable ? '적용돼요' : '적용되지 않아요',
      statusClass: diagnosisData.value.extraPayApplicable ? 'text-green-600' : 'text-yellow-600'
    }
  };
});

const fetchDiagnosisData = async () => {
  if (!props.activeJob) return;

  loading.value = true;
  error.value = false;

  try {
    // 1. 주휴수당 정보 조회
    const holidayPayRes = await apiClient.get(`/labor/employees/${props.activeJob.id}/holiday-pay/`);
    const holidayPayData = holidayPayRes.data;

    // 2. 퇴직금 정보 조회
    const retirementRes = await apiClient.get(`/labor/employees/${props.activeJob.id}/retirement-pay/`);
    const retirementData = retirementRes.data;

    // 3. 연차휴가 정보 조회
    const annualLeaveRes = await apiClient.get(`/labor/employees/${props.activeJob.id}/annual-leave/`);
    const annualLeaveData = annualLeaveRes.data;

    // 4. 추가 수당 정보 (야간/휴일/연장)
    // 5인 이상 사업장이면 기본적으로 가산수당 적용 대상
    const extraPayApplicable = props.activeJob.is_workplace_over_5;

    diagnosisData.value = {
      holidayPayEligible: (holidayPayData.amount || 0) > 0,
      retirementEligible: retirementData.eligible || false,
      annualLeaveEligible: annualLeaveData.available > 0,
      extraPayApplicable,
      loading: false
    };
  } catch (err) {
    console.error('근로진단 데이터 조회 실패:', err);
    error.value = true;
  } finally {
    loading.value = false;
  }
};

const goToDiagnosisDetail = () => {
  router.push('/dashboard?section=diagnosis');
};

const refresh = () => {
  fetchDiagnosisData();
};

// activeJob 변경 시 자동으로 데이터 갱신
watch(() => props.activeJob, (newJob) => {
  if (newJob) {
    fetchDiagnosisData();
  }
}, { immediate: true });

onMounted(() => {
  if (props.activeJob) {
    fetchDiagnosisData();
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
