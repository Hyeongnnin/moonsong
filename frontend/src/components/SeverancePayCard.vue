<template>
  <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow">
    <div class="flex items-center justify-between mb-5">
      <h3 class="text-base font-bold text-gray-900">퇴직금 예상액</h3>
      <button 
        :disabled="!result.eligible"
        @click="showModal = true"
        class="text-xs font-medium flex items-center gap-1 transition-colors"
        :class="result.eligible ? 'text-brand-600 hover:text-brand-700' : 'text-gray-300 cursor-not-allowed'"
      >
        상세보기
        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- 로딩/에러 상태 -->
    <div v-if="loading" class="text-center py-6 text-gray-500 text-sm">로딩 중...</div>
    <div v-else-if="!activeJob" class="text-center py-6 text-gray-400 text-xs italic">근로정보를 입력하면 퇴직금이 계산됩니다.</div>
    
    <div v-else>
      <!-- 퇴직금 메인 금액 -->
      <div class="mb-5">
        <p class="text-3xl font-black text-gray-900 leading-tight">
          {{ formatCurrency(result.severance_pay) }}
        </p>
      </div>

      <!-- 정보 리스트 -->
      <div class="space-y-3">
        <div class="flex justify-between items-baseline">
          <span class="text-xs text-gray-500 font-medium">평균임금 (일급)</span>
          <span class="text-sm font-semibold text-gray-800">{{ formatCurrency(result.avg_daily_wage) }}</span>
        </div>
        <div class="flex justify-between items-baseline">
          <span class="text-xs text-gray-500 font-medium">재직기간</span>
          <span class="text-sm font-semibold text-gray-800">
            {{ result.service_months }}개월 ({{ result.service_days }}일)
          </span>
        </div>
      </div>

      <div class="mt-5 pt-4 border-t border-gray-100">
        <!-- 부적격 사유 안내 -->
        <div v-if="!result.eligible" class="flex gap-2 p-3 bg-red-50 rounded-lg border border-red-100">
          <span class="text-lg leading-none">⚠️</span>
          <p class="text-[11px] text-red-600 font-semibold leading-relaxed">
            <span v-if="result.reason === 'service_period_under_1y'">
              재직기간 1년 미만(퇴직금 지급 대상 아님)
            </span>
            <span v-else-if="result.reason === 'hours_under_15'">
              주 15시간 미만(퇴직금 대상 아님)
            </span>
            <span v-else>퇴직금 지급 요건을 충족하지 않습니다.</span>
          </p>
        </div>
        
        <!-- 산정 방식 안내 -->
        <div v-else class="flex items-center justify-between text-[10px] text-gray-400 font-medium">
          <span>산정 방식</span>
          <span class="px-1.5 py-0.5 bg-gray-50 rounded border border-gray-100">
            {{ result.method === 'ROLLING_90D_ACTUAL' ? '최근 90일 실적 기반' : '계약 정보 기반 추정' }}
          </span>
        </div>
      </div>
    </div>

    <!-- 상세 모달 -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-40 backdrop-blur-sm">
      <div class="bg-white rounded-2xl w-full max-w-sm shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <div class="p-6">
          <div class="flex justify-between items-center mb-6">
            <h4 class="text-lg font-bold text-gray-900">퇴직금 산정 내역</h4>
            <button @click="showModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="space-y-6">
            <!-- 계산식 설명 -->
            <div class="p-4 bg-gray-50 rounded-xl border border-gray-100">
              <p class="text-[10px] text-gray-500 font-bold mb-2 uppercase tracking-wider">Calculation Formula</p>
              <p class="text-sm font-semibold text-gray-800 leading-relaxed">
                일평균임금 × 30일 × (재직일수 / 365)
              </p>
            </div>

            <!-- 세부 데이터 -->
            <div class="space-y-4 px-1">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">산정 방식</span>
                <span class="text-xs font-bold text-brand-600">
                   {{ result.method === 'ROLLING_90D_ACTUAL' ? '최근 90일 실근로 기준' : '계약 정보 기준 추정' }}
                </span>
              </div>
              <div v-if="result.method === 'ROLLING_90D_ACTUAL'" class="flex justify-between">
                <span class="text-xs text-gray-500">90일 총 임금</span>
                <span class="text-xs font-bold text-gray-900">{{ formatCurrency(result.total_wage_last_90d || 0) }}</span>
              </div>
              <div v-else class="flex justify-between">
                <span class="text-xs text-gray-500">계약 시급/시간</span>
                <span class="text-xs font-bold text-gray-900">{{ formatCurrency(result.hourly_rate || 0) }} / {{ result.contract_weekly_hours }}h</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">평균임금 (일급)</span>
                <span class="text-xs font-bold text-gray-900">{{ formatCurrency(result.avg_daily_wage) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">총 재직일수</span>
                <span class="text-xs font-bold text-gray-900">{{ result.service_days }}일</span>
              </div>
            </div>

            <div class="pt-4 border-t border-gray-100">
              <div class="flex justify-between items-center bg-brand-50 p-4 rounded-xl border border-brand-100">
                <span class="text-sm font-bold text-brand-700">퇴직금 예상액</span>
                <span class="text-xl font-black text-brand-600">{{ formatCurrency(result.severance_pay) }}</span>
              </div>
            </div>
            
            <p class="text-[10px] text-gray-400 leading-normal">
              * 위 금액은 단순 예상액이며 실제 퇴직 시점의 임금 변동 및 상세 근로 조건에 따라 달라질 수 있습니다.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useLabor, type SeveranceData } from '../composables/useLabor';
import type { Job } from '../stores/jobStore';

const props = defineProps<{
  activeJob: Job | null;
}>();

const { fetchSeverance } = useLabor();
const loading = ref(false);
const error = ref(false);
const showModal = ref(false);

const result = ref<SeveranceData>({
  eligible: false,
  severance_pay: 0,
  avg_daily_wage: 0,
  service_days: 0,
  service_months: 0,
  method: 'NONE',
  reason: '',
  total_wage_last_90d: 0,
  contract_weekly_hours: 0,
  hourly_rate: 0
});

const formatCurrency = (value: number) => {
  return value.toLocaleString('ko-KR') + '원';
};

const loadSeveranceData = async () => {
  if (!props.activeJob) return;
  
  loading.value = true;
  error.value = false;
  try {
    const data = await fetchSeverance(props.activeJob.id);
    result.value = data;
  } catch (e) {
    console.error('Failed to load severance data:', e);
    error.value = true;
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  if (props.activeJob) {
    loadSeveranceData();
  }
  window.addEventListener('labor-updated', loadSeveranceData);
});

onUnmounted(() => {
  window.removeEventListener('labor-updated', loadSeveranceData);
});

watch(() => props.activeJob?.id, () => {
  loadSeveranceData();
});
</script>

<style scoped>
@keyframes zoom-in {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
.animate-in {
  animation: zoom-in 0.2s ease-out;
}
</style>
