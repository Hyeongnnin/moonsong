<template>
  <div class="space-y-4">
    <p class="text-sm text-gray-600">주간 근무 스케줄을 입력하세요. 각 요일에 대해 출근/퇴근 시간을 설정합니다.</p>
    <div class="grid grid-cols-1 gap-3">
      <div v-for="d in weekdays" :key="d.value" class="flex items-center gap-3">
        <div class="w-20 text-sm font-medium">{{ d.label }}</div>
        <input type="time" v-model="localSchedules[d.value].start_time" class="px-2 py-1 border rounded" />
        <span class="text-xs text-gray-400">~</span>
        <input type="time" v-model="localSchedules[d.value].end_time" class="px-2 py-1 border rounded" />
        <label class="ml-2 inline-flex items-center gap-2 text-sm">
          <input type="checkbox" v-model="localSchedules[d.value].enabled" /> 활성
        </label>
      </div>
    </div>
    <div class="flex gap-2">
      <button @click="saveSchedules" class="px-4 py-2 bg-brand-600 text-white rounded">저장</button>
      <button @click="resetSchedules" class="px-4 py-2 bg-gray-100 rounded">초기화</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, toRefs, watch, ref } from 'vue'
import { apiClient } from '../api'

const props = defineProps({ employeeId: { type: Number, required: true } })

const weekdays = [
  { value: 0, label: '월' },
  { value: 1, label: '화' },
  { value: 2, label: '수' },
  { value: 3, label: '목' },
  { value: 4, label: '금' },
  { value: 5, label: '토' },
  { value: 6, label: '일' },
]

const localSchedules = reactive<Record<number, { start_time: string | null, end_time: string | null, enabled: boolean }>>({
  0: { start_time: null, end_time: null, enabled: false },
  1: { start_time: null, end_time: null, enabled: false },
  2: { start_time: null, end_time: null, enabled: false },
  3: { start_time: null, end_time: null, enabled: false },
  4: { start_time: null, end_time: null, enabled: false },
  5: { start_time: null, end_time: null, enabled: false },
  6: { start_time: null, end_time: null, enabled: false },
})

async function loadSchedules() {
  try {
    const res = await apiClient.get(`/labor/jobs/${props.employeeId}/schedules/`)
    for (const s of res.data) {
      localSchedules[s.weekday] = { start_time: s.start_time, end_time: s.end_time, enabled: s.enabled }
    }
  } catch (e) {
    console.error('Failed to load schedules', e)
  }
}

async function saveSchedules() {
  try {
    for (const w of weekdays) {
      const payload = {
        weekday: w.value,
        start_time: localSchedules[w.value].start_time,
        end_time: localSchedules[w.value].end_time,
        enabled: localSchedules[w.value].enabled ? '1' : '0',
      }
      await apiClient.post(`/labor/jobs/${props.employeeId}/schedules/`, payload)
    }
    alert('저장되었습니다.')
  } catch (e) {
    console.error('Failed to save schedules', e)
    alert('저장 실패')
  }
}

function resetSchedules() {
  for (const k of Object.keys(localSchedules)) {
    localSchedules[parseInt(k)].start_time = null
    localSchedules[parseInt(k)].end_time = null
    localSchedules[parseInt(k)].enabled = false
  }
}

loadSchedules()
</script>

<style scoped>
</style>
