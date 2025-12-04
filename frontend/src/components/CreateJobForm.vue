<template>
  <div class="p-4">
    <h3 class="text-lg font-semibold mb-4">새 알바 추가</h3>
    <form @submit.prevent="onSubmit" class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-1">사업장명</label>
        <input v-model="form.workplace_name" required class="w-full px-3 py-2 border rounded" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">사업장 주소</label>
        <input v-model="form.workplace_address" class="w-full px-3 py-2 border rounded" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">업종</label>
        <input v-model="form.industry" class="w-full px-3 py-2 border rounded" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">고용형태</label>
        <select v-model="form.employment_type" class="w-full px-3 py-2 border rounded">
          <option value="">-- 선택 --</option>
          <option value="알바">알바</option>
          <option value="정규직">정규직</option>
          <option value="계약직">계약직</option>
        </select>
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">시급</label>
        <input v-model.number="form.hourly_rate" type="number" class="w-full px-3 py-2 border rounded" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">주당 근로시간</label>
        <input v-model.number="form.weekly_hours" type="number" class="w-full px-3 py-2 border rounded" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">1일 근로시간</label>
        <input v-model.number="form.daily_hours" type="number" class="w-full px-3 py-2 border rounded" />
      </div>

      <!-- 근로 시작일 / 종료일 추가 -->
      <div>
        <label class="block text-sm font-medium mb-1">근로 시작일 <span class="text-red-500">*</span></label>
        <input v-model="form.start_date" type="date" required class="w-full px-3 py-2 border rounded" />
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">근로 종료일</label>
        <input v-model="form.end_date" type="date" class="w-full px-3 py-2 border rounded" />
        <p class="text-xs text-gray-500 mt-1">현재 재직 중이면 비워두세요.</p>
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
  workplace_address: '',
  industry: '',
  employment_type: '',
  hourly_rate: 0,
  weekly_hours: 0,
  daily_hours: 0,
  start_date: '',
  end_date: ''
})

async function onSubmit() {
  if (!form.start_date) {
    alert('근로 시작일은 필수입니다.')
    return
  }

  try {
    const payload = {
      workplace_name: form.workplace_name,
      workplace_address: form.workplace_address,
      industry: form.industry,
      employment_type: form.employment_type,
      hourly_rate: form.hourly_rate,
      weekly_hours: form.weekly_hours,
      daily_hours: form.daily_hours,
      // start_date must not be null
      start_date: form.start_date,
      end_date: form.end_date || null,
      has_paid_weekly_holiday: true,
      is_severance_eligible: false,
      is_current: form.end_date ? true : true,
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
