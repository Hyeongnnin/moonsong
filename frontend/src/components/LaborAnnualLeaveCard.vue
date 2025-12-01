<template>
  <div class="mt-6">
    <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">연차휴가</h3>
        <span class="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full" :style="{backgroundColor:'#FFE7DF', color:'#DE5D35'}">Notav</span>
      </div>

      <div v-if="loading" class="text-sm text-gray-500 py-4">연차 정보를 불러오는 중…</div>
      <div v-else-if="error" class="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{{ error }}</div>
      <div v-else-if="result" class="grid sm:grid-cols-3 gap-4 items-end">
        <div class="sm:col-span-3">
          <p class="text-sm text-gray-600 mb-1">사용 가능 연차</p>
          <p class="text-3xl sm:text-4xl font-extrabold" :style="{color:'#DE5D35'}">{{ result.available }}일</p>
        </div>
        <div class="p-4 rounded-lg bg-gray-50 border border-gray-200">
          <p class="text-xs text-gray-500">올해 발생 연차</p>
          <p class="text-xl font-bold text-gray-900 mt-1">{{ result.total }}일</p>
        </div>
        <div class="p-4 rounded-lg bg-gray-50 border border-gray-200">
          <p class="text-xs text-gray-500">사용한 연차</p>
          <p class="text-xl font-bold text-gray-900 mt-1">{{ result.used }}일</p>
        </div>
        <div class="p-4 rounded-lg bg-gray-50 border border-gray-200">
          <p class="text-xs text-gray-500">남은 연차</p>
          <p class="text-xl font-bold text-gray-900 mt-1">{{ Math.max(0, result.total - result.used) }}일</p>
        </div>
      </div>

      <p class="text-xs text-gray-500 mt-4">근로기준법 기준으로 계산된 예상 연차입니다. 실제와 차이가 있을 수 있습니다.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useJob } from '../stores/jobStore'
import { useLabor, type AnnualLeaveResult } from '../composables/useLabor'

const { activeJob } = useJob()
const { fetchAnnualLeave } = useLabor()

const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<AnnualLeaveResult | null>(null)

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
})
</script>

<style scoped>
</style>
