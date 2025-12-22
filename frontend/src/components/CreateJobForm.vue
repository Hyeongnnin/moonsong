<template>
  <div class="p-4">
    <h3 class="text-lg font-semibold mb-4">새 알바 추가</h3>
    <form @submit.prevent="onSubmit" class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-1">사업장명</label>
        <input v-model="form.workplace_name" required class="w-full px-3 py-2 border rounded" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">5인 이상 사업장인가요?</label>
        <select v-model="form.is_workplace_over_5" class="w-full px-3 py-2 border rounded">
          <option :value="false">아니오 (5인 미만)</option>
          <option :value="true">예 (5인 이상)</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">시급</label>
        <input v-model.number="form.hourly_rate" type="number" class="w-full px-3 py-2 border rounded" />
      </div>

      <!-- 근로 시작일 -->
      <div>
        <label class="block text-sm font-medium mb-1">근로 시작일 <span class="text-red-500">*</span></label>
        <input v-model="form.start_date" type="date" required class="w-full px-3 py-2 border rounded" />
      </div>

      <!-- 근로 스케줄 안내 -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div class="flex items-start gap-2">
          <svg class="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          <div class="text-sm text-blue-800">
            <p class="font-medium mb-1">💡 근로 스케줄은 어디서 설정하나요?</p>
            <p class="text-blue-700">알바 등록 후 <span class="font-semibold">근로정보 수정 → 주간 근무 스케줄</span>에서 요일별 근무 시간을 설정할 수 있습니다.</p>
          </div>
        </div>
      </div>

      <div class="flex gap-2 justify-end">
        <button type="button" @click="$emit('cancel')" class="px-4 py-2 bg-gray-100 rounded">취소</button>
        <button type="submit" class="px-4 py-2 bg-brand-600 text-white rounded">저장</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { useJob } from '../stores/jobStore'
import { apiClient } from '../api'

const emit = defineEmits(['saved','cancel'])

const { createJob } = useJob()

const form = reactive({
  workplace_name: '',
  employment_type: '알바',
  is_workplace_over_5: false,
  hourly_rate: 0,
  start_date: ''
})

async function onSubmit() {
  if (!form.start_date) {
    alert('근로 시작일은 필수입니다.')
    return
  }

  try {
    const payload = {
      workplace_name: form.workplace_name,
      employment_type: form.employment_type,
      is_workplace_over_5: form.is_workplace_over_5,
      hourly_rate: form.hourly_rate,
      start_date: form.start_date,
      has_paid_weekly_holiday: true,
      is_severance_eligible: false,
      is_current: true
    }
    const created = await createJob(payload as any)
    emit('saved', created)
  } catch (e: any) {
    const serverErr = e?.response?.data ? e.response.data : e?.message || 'Unknown error'
    alert('알바 생성 실패: ' + JSON.stringify(serverErr))
  }
}
</script>

<style scoped>
</style>
