<template>
  <div class="mt-8" v-if="activeJob">
    <h3 class="text-sm font-semibold text-gray-900 mb-4 flex items-center gap-2">
      <svg class="w-5 h-5 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
      근로조건 평가 결과
    </h3>
    <div v-if="loading" class="text-center text-xs text-gray-500 py-3">평가 로딩 중...</div>
    <div v-else-if="error" class="p-3 bg-red-50 border border-red-100 rounded-lg text-xs text-red-700">{{ error }}</div>
    <div v-else-if="evaluation" class="space-y-3">
      <div class="grid grid-cols-2 gap-3">
        <div class="p-4 rounded-lg border" :class="evaluation.min_wage_ok ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'">
          <p class="text-[10px] tracking-wide text-gray-600 mb-1">최저임금</p>
          <p class="text-lg font-bold" :class="evaluation.min_wage_ok ? 'text-green-700' : 'text-red-700'">{{ evaluation.min_wage_ok ? '충족' : '미달' }}</p>
          <p class="text-[10px] text-gray-500 mt-1">기준 {{ evaluation.min_wage_required.toLocaleString('ko-KR') }}원</p>
        </div>
        <div class="p-4 rounded-lg border bg-blue-50 border-blue-200">
          <p class="text-[10px] tracking-wide text-gray-600 mb-1">주휴수당(예상)</p>
          <p class="text-lg font-bold text-blue-700">{{ formatWon(evaluation.weekly_holiday_pay) }}</p>
        </div>
        <div class="p-4 rounded-lg border bg-purple-50 border-purple-200">
          <p class="text-[10px] tracking-wide text-gray-600 mb-1">연차 발생일수</p>
          <p class="text-lg font-bold text-purple-700">{{ evaluation.annual_leave_days }}</p>
        </div>
        <div class="p-4 rounded-lg border bg-amber-50 border-amber-200">
          <p class="text-[10px] tracking-wide text-gray-600 mb-1">퇴직금(예상)</p>
          <p class="text-lg font-bold text-amber-700">{{ formatWon(evaluation.severance_estimate) }}</p>
        </div>
      </div>
      <div v-if="evaluation.warnings.length" class="p-3 rounded-lg bg-red-50 border border-red-200">
        <p class="text-xs font-semibold text-red-700 mb-2">주의 필요 사항</p>
        <ul class="space-y-1">
          <li v-for="w in evaluation.warnings" :key="w" class="flex items-start gap-1 text-[11px] text-red-700">
            <svg class="w-3.5 h-3.5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M4.93 4.93l14.14 14.14M12 22a10 10 0 100-20 10 10 0 000 20z"/></svg>
            <span>{{ w }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useJob } from '../stores/jobStore'
import { useLabor, type EvaluationResult } from '../composables/useLabor'

const { activeJob } = useJob()
const { fetchEvaluation } = useLabor()

const evaluation = ref<EvaluationResult | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

async function loadEvaluation() {
  if (!activeJob.value) return
  loading.value = true
  error.value = null
  try {
    evaluation.value = await fetchEvaluation(activeJob.value.id)
  } catch (err: any) {
    error.value = err.response?.data?.detail || '평가 결과를 불러올 수 없습니다.'
    evaluation.value = null
  } finally {
    loading.value = false
  }
}

watch(() => activeJob.value?.id, () => {
  loadEvaluation()
})

function handleJobUpdated() {
  loadEvaluation()
}

onMounted(() => {
  loadEvaluation()
  window.addEventListener('job-updated', handleJobUpdated)
})

onBeforeUnmount(() => {
  window.removeEventListener('job-updated', handleJobUpdated)
})

function formatWon(v: number) {
  return v.toLocaleString('ko-KR') + '원'
}
</script>

<style scoped></style>