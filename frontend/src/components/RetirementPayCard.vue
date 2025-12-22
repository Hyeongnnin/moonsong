<template>
  <div class="bg-white rounded-lg p-5 shadow-sm border border-gray-200">
    <h3 class="text-lg font-semibold text-gray-900 mb-3">퇴직금 예상액</h3>
    
    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="text-center py-8">
      <div class="text-4xl mb-3">🎁</div>
      <p class="text-sm text-gray-600 font-medium mb-2">아직 근로정보가 없어요</p>
      <p class="text-xs text-gray-500 mb-4">근로정보를 입력하면<br/>퇴직금이 자동으로 계산됩니다</p>
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
      <div v-if="loading" class="text-center py-4">
        <div class="text-gray-500">계산 중...</div>
      </div>
      
      <div v-else-if="error" class="text-center py-4">
        <div class="text-red-600 text-sm">{{ error }}</div>
      </div>
      
      <div v-else-if="data">
        <!-- 퇴직금 금액 -->
        <div class="mb-3">
          <div 
            :class="[
              'text-3xl font-bold',
              data.eligible ? 'text-brand-600' : 'text-gray-400'
            ]"
          >
            {{ data.eligible ? '+' : '' }}{{ formatCurrency(data.retirement_pay) }}원
          </div>
        </div>

        <!-- 상세 정보 -->
        <div class="space-y-1.5 text-sm">
          <div class="flex justify-between text-gray-600">
            <span>평균임금 (일급)</span>
            <span class="font-medium">{{ formatCurrency(data.average_wage) }}원</span>
          </div>
          <div class="flex justify-between text-gray-600">
            <span>재직기간</span>
            <span class="font-medium">{{ data.service_months }}개월 ({{ data.service_days }}일)</span>
          </div>
        </div>

        <!-- 자격 여부 메시지 -->
        <div v-if="!data.eligible" class="mt-3 pt-3 border-t border-gray-100">
          <p class="text-xs text-red-500 leading-tight">
            ⚠️ {{ data.calculation_details }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiClient } from '../api'

interface RetirementPayData {
  retirement_pay: number
  average_wage: number
  regular_wage: number
  service_days: number
  service_months: number
  eligible: boolean
  calculation_details: string
}

const props = defineProps<{
  activeJob: {
    id: number
    workplace_name: string
    hourly_rate: number
  } | null
}>()

const router = useRouter()
const route = useRoute()
const data = ref<RetirementPayData | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const showDetails = ref(false)

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('ko-KR').format(value)
}

// 근로정보 입력 페이지로 이동
function navigateToJobCreate() {
  // 이미 동일 경로/섹션이면 전역 이벤트로 강제 전환
  if (route.path === '/dashboard' && route.query.section === 'profile-edit') {
    window.dispatchEvent(new CustomEvent('go-section', { detail: 'profile-edit' }))
    return
  }
  router.push('/dashboard?section=profile-edit').catch(() => {})
}

const fetchRetirementPay = async () => {
  if (!props.activeJob?.id) {
    error.value = '직장 정보가 없습니다.'
    return
  }

  loading.value = true
  error.value = null

  console.log('=== Fetching Retirement Pay ===')
  console.log('Active Job ID:', props.activeJob.id)
  console.log('Active Job Name:', props.activeJob.workplace_name)

  try {
    const response = await apiClient.get(`/labor/employees/${props.activeJob.id}/retirement-pay/`)
    data.value = response.data
    
    console.log('Retirement Pay Response:', response.data)
  } catch (err: any) {
    console.error('Failed to fetch retirement pay:', err)
    error.value = err?.response?.data?.detail || '퇴직금 계산 중 오류가 발생했습니다.'
  } finally {
    loading.value = false
  }
}

// 컴포넌트 마운트 시 데이터 로드
onMounted(() => {
  fetchRetirementPay()
})

// activeJob 변경 감지
watch(() => props.activeJob?.id, (newId) => {
  if (newId) {
    fetchRetirementPay()
  }
})

// 전역 이벤트 리스너 (근로기록 변경 시 자동 갱신)
onMounted(() => {
  const handleLaborUpdate = () => {
    console.log('[RetirementPayCard] Labor data updated, refreshing...')
    fetchRetirementPay()
  }
  
  window.addEventListener('labor-updated', handleLaborUpdate)
  
  // cleanup
  return () => {
    window.removeEventListener('labor-updated', handleLaborUpdate)
  }
})
</script>

<style scoped>
/* 추가 스타일이 필요하면 여기에 작성 */
</style>
