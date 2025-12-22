<template>
  <div class="h-full">
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-5 h-full flex flex-col">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-lg font-semibold text-gray-900">연차휴가</h3>
        <span 
          v-if="!result?.is_eligible"
          class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full" 
          :style="{backgroundColor:'#FFE7DF', color:'#DE5D35'}"
        >
          Notav
        </span>
      </div>

      <div v-if="loading" class="text-sm text-gray-500 py-4 flex-1 flex items-center justify-center">연차 정보를 불러오는 중…</div>
      <div v-else-if="error" class="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{{ error }}</div>
      <div v-else-if="!result?.is_eligible" class="flex-1">
        <div class="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700">
          {{ result?.reason || '연차 발생 대상이 아닙니다.' }}
        </div>
      </div>
      <div v-else-if="result" class="flex-1 flex flex-col justify-between">
        <div>
          <div class="mb-3">
            <p class="text-sm text-gray-600 mb-1">잔여 연차</p>
            <p class="text-3xl font-bold" :style="{color:'#DE5D35'}">{{ result.remaining_days }}일</p>
          </div>
          
          <div class="space-y-1.5 text-sm">
            <div class="flex justify-between text-gray-600">
              <span>발생 연차</span>
              <span class="font-medium">{{ result.earned_days }}일</span>
            </div>
            <div class="flex justify-between text-gray-600">
              <span>사용 연차</span>
              <span class="font-medium">{{ result.used_days }}일</span>
            </div>
          </div>
        </div>

        <div class="mt-3 pt-3 border-t border-gray-100">
          <p class="text-xs text-gray-500 leading-tight">* {{ currentYear }}년 누적 기준 (입사 1년 미만은 개근 시 월 1일)</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useJob } from '../stores/jobStore'
import { useLabor, type AnnualLeaveResult } from '../composables/useLabor'

const { activeJob } = useJob()
const { fetchAnnualLeave } = useLabor()

const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<AnnualLeaveResult | null>(null)

const currentYear = computed(() => new Date().getFullYear())

async function load() {
  if (!activeJob.value) return
  loading.value = true
  error.value = null
  try {
    result.value = await fetchAnnualLeave(activeJob.value.id)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '연차 정보를 불러올 수 없습니다.'
    result.value = null
  } finally {
    loading.value = false
  }
}

watch(() => activeJob.value?.id, () => load())
onMounted(() => {
  load()
  window.addEventListener('job-updated', load)
  // labor-updated 이벤트도 처리 (연차 사용 등록 시 갱신)
  window.addEventListener('labor-updated', load)
})
</script>

<style scoped>
</style>
