<template>
  <div class="p-4 border rounded bg-white">
    <h3 class="text-lg font-semibold mb-3">문서 생성</h3>
    <form @submit.prevent="onSubmit" class="space-y-4">
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="block text-sm font-medium mb-1">제목</label>
          <input v-model.trim="form.title" required type="text" placeholder="예) 2025년 1월 급여명세서" class="w-full px-3 py-2 border rounded" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">상태</label>
          <select v-model="form.status" class="w-full px-3 py-2 border rounded bg-white">
            <option value="작성중">작성중</option>
            <option value="완료">완료</option>
            <option value="제출">제출</option>
          </select>
        </div>
      </div>



      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="block text-sm font-medium mb-1">파일 (선택: .pdf)</label>
          <input type="file" @change="onFileChange" accept=".pdf,application/pdf" />
          <div v-if="fileName" class="text-sm text-gray-600 mt-1">선택된 파일: {{ fileName }}</div>
        </div>
      </div>

      <div class="flex justify-end gap-2">
        <button type="button" @click="$emit('cancel')" class="px-4 py-2 bg-gray-100 rounded">취소</button>
        <button type="submit" class="px-4 py-2 bg-brand-600 text-white rounded">생성</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { createGenerated } from '../api'

const emit = defineEmits(['created','cancel'])

const form = ref({ title: '', status: '작성중' })
const formValues = ref<Record<string, any>>({})
const fileRef = ref<File | null>(null)
const fileName = ref('')

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files || input.files.length === 0) {
    fileRef.value = null
    fileName.value = ''
    return
  }
  const file = input.files[0]

  // validation: allow only PDF and max size
  const allowedExt = ['.pdf']
  const allowedMimes = [
    'application/pdf',
  ]
  const name = (file.name || '').toLowerCase()
  const okExt = allowedExt.some((ext) => name.endsWith(ext))
  const okMime = allowedMimes.includes(file.type)

  const maxSize = 10 * 1024 * 1024 // 10MB
  if (!(okExt || okMime)) {
    alert('허용되지 않는 파일 형식입니다. PDF만 업로드 가능합니다.')
    input.value = ''
    fileRef.value = null
    fileName.value = ''
    return
  }
  if (file.size > maxSize) {
    alert('파일 크기는 10MB 이하이어야 합니다.')
    input.value = ''
    fileRef.value = null
    fileName.value = ''
    return
  }

  fileRef.value = file
  fileName.value = file.name
}

async function onSubmit() {
  const fd = new FormData()
  fd.append('title', form.value.title)
  if (form.value.status) {
    fd.append('status', form.value.status)
  }
  if (fileRef.value) fd.append('file', fileRef.value)

  try {
    const created = await createGenerated(fd)
    emit('created', created)
  } catch (e: any) {
    console.error('문서 생성 실패', e?.response?.data || e)
    alert('문서 생성 실패: ' + JSON.stringify(e?.response?.data || e?.message || e))
  }
}
</script>

<style scoped>
</style>
