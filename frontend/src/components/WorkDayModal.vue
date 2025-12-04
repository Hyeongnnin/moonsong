<template>
  <div v-if="visible" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg w-full max-w-md p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">{{ dateLabel }} 근로기록</h3>
        <button @click="close" class="text-gray-500">✕</button>
      </div>

      <div class="space-y-4">
        <div>
          <label class="block text-sm text-gray-700 mb-1">출근 시간</label>
          <input type="time" v-model="timeIn" class="w-full px-3 py-2 border rounded" />
        </div>
        <div>
          <label class="block text-sm text-gray-700 mb-1">퇴근 시간</label>
          <input type="time" v-model="timeOut" class="w-full px-3 py-2 border rounded" />
        </div>
        <div>
          <label class="block text-sm text-gray-700 mb-1">휴게(분)</label>
          <input type="number" v-model.number="breakMinutes" min="0" class="w-full px-3 py-2 border rounded" />
        </div>
        <div v-if="error" class="text-sm text-red-600">{{ error }}</div>
      </div>

      <div class="mt-6 flex items-center justify-end gap-2">
        <button @click="onDelete" v-if="record && record.id" class="px-4 py-2 bg-red-500 text-white rounded">삭제</button>
        <button @click="close" class="px-4 py-2 bg-gray-100 rounded">취소</button>
        <button @click="onSave" class="px-4 py-2 bg-brand-600 text-white rounded">저장</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiClient } from '../api'

const props = defineProps({
  visible: { type: Boolean, required: true },
  employeeId: { type: Number, required: false, default: null },
  dateIso: { type: String, required: true },
  record: { type: Object as () => any, required: false, default: null }
})

const emit = defineEmits(['close', 'saved', 'deleted'])

const timeIn = ref<string | null>(null)
const timeOut = ref<string | null>(null)
const breakMinutes = ref<number>(0)
const error = ref<string | null>(null)

watch(() => props.record, (r) => {
  if (r) {
    // record.time_in/time_out may be ISO datetimes
    timeIn.value = r.time_in ? r.time_in.split('T')[1].slice(0,5) : null
    timeOut.value = r.time_out ? r.time_out.split('T')[1].slice(0,5) : null
    breakMinutes.value = r.break_minutes || 0
  } else {
    timeIn.value = null
    timeOut.value = null
    breakMinutes.value = 0
  }
}, { immediate: true })

const dateLabel = computed(() => {
  try {
    return new Date(props.dateIso).toLocaleDateString()
  } catch { return props.dateIso }
})

function close() {
  emit('close')
}

function validateTimes() {
  // 기본 검증: 둘 중 하나만 있으면 허용(반복적 부분 근무 가능)
  if (timeIn.value && !/^\d{2}:\d{2}$/.test(timeIn.value)) return '출근 시간이 형식에 맞지 않습니다.'
  if (timeOut.value && !/^\d{2}:\d{2}$/.test(timeOut.value)) return '퇴근 시간이 형식에 맞지 않습니다.'
  return null
}

async function onSave() {
  error.value = null
  const v = validateTimes()
  if (v) { error.value = v; return }

  if (!props.employeeId) { error.value = '직원이 선택되지 않았습니다.'; return }

  // build ISO datetime strings: YYYY-MM-DDTHH:MM:00
  const date = props.dateIso
  const payload: any = {
    employee: props.employeeId,
    work_date: date,
    break_minutes: breakMinutes.value || 0
  }
  if (timeIn.value) payload.time_in = `${date}T${timeIn.value}:00`
  else payload.time_in = null
  if (timeOut.value) payload.time_out = `${date}T${timeOut.value}:00`
  else payload.time_out = null

  try {
    if (props.record && props.record.id) {
      // update
      await apiClient.patch(`/labor/work-records/${props.record.id}/`, payload)
      emit('saved')
      close()
    } else {
      // create
      await apiClient.post('/labor/work-records/', payload)
      emit('saved')
      close()
    }
  } catch (e: any) {
    console.error('save failed', e)
    error.value = e?.response?.data?.detail || '저장 중 오류가 발생했습니다.'
  }
}

async function onDelete() {
  if (!(props.record && props.record.id)) return
  if (!props.employeeId) { error.value = '직원이 선택되지 않았습니다.'; return }
  try {
    await apiClient.delete(`/labor/work-records/${props.record.id}/`)
    emit('deleted')
    close()
  } catch (e: any) {
    console.error('delete failed', e)
    error.value = e?.response?.data?.detail || '삭제 중 오류가 발생했습니다.'
  }
}
</script>

<style scoped>
</style>