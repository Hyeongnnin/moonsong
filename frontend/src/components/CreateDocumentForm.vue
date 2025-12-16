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
          <label class="block text-sm font-medium mb-1">템플릿 (선택)</label>
          <select v-model="form.template" class="w-full px-3 py-2 border rounded bg-white">
            <option value="">템플릿 없이 업로드</option>
            <option v-for="t in templates" :key="t.id" :value="t.id">{{ t.name }} ({{ t.doc_type }})</option>
          </select>
        </div>
        <!-- ✅ B 프로젝트 병합: doc_type 필드 추가 -->
        <div>
          <label class="block text-sm font-medium mb-1">서류 유형 (선택)</label>
          <input v-model.trim="form.doc_type" type="text" placeholder="예) 근로계약서, 급여명세서" class="w-full px-3 py-2 border rounded" />
        </div>
      </div>
      
      <div class="text-xs text-gray-500">템플릿 없이도 파일을 업로드할 수 있습니다. 서류 유형을 직접 입력하세요. 최대 10MB, PDF 권장.</div>

      <div v-if="selectedTemplate" class="mb-1">
        <div class="text-sm text-gray-600">템플릿 유형: <strong>{{ selectedTemplate.doc_type || '-' }}</strong></div>
        <div v-if="selectedTemplate.required_fields_json" class="mt-3 space-y-3">
          <div v-for="(meta, key) in selectedTemplate.required_fields_json" :key="key">
            <label class="block text-sm font-medium mb-1">{{ meta.label || key }} <span v-if="meta.required" class="text-red-500">*</span></label>
            <template v-if="meta.type === 'string'">
              <input v-model="formValues[key]" type="text" :placeholder="meta.placeholder || ''" class="w-full px-3 py-2 border rounded" />
            </template>
            <template v-else-if="meta.type === 'date'">
              <input v-model="formValues[key]" type="date" class="w-full px-3 py-2 border rounded" />
            </template>
            <template v-else-if="meta.type === 'number'">
              <input v-model.number="formValues[key]" type="number" class="w-full px-3 py-2 border rounded" />
            </template>
            <template v-else-if="meta.type === 'boolean'">
              <input v-model="formValues[key]" type="checkbox" />
            </template>
            <template v-else>
              <input v-model="formValues[key]" type="text" class="w-full px-3 py-2 border rounded" />
            </template>
          </div>
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
import { fetchTemplates, createGenerated } from '../api'

const emit = defineEmits(['created','cancel'])

const templates = ref<any[]>([])
const form = ref({ title: '', template: '', doc_type: '', status: '작성중' })  // ✅ B 프로젝트 병합: doc_type 추가
const selectedTemplate = ref<any | null>(null)
const formValues = ref<Record<string, any>>({})
const fileRef = ref<File | null>(null)
const fileName = ref('')

onMounted(async () => {
  try {
    templates.value = await fetchTemplates()
  } catch (e) {
    console.error('템플릿 로드 실패', e)
  }
})

function initFormForTemplate() {
  const id = String(form.value.template)
  selectedTemplate.value = templates.value.find((t: any) => String(t.id) === id) || null
  formValues.value = {}
  if (selectedTemplate.value && selectedTemplate.value.required_fields_json) {
    const schema = selectedTemplate.value.required_fields_json
    for (const key in schema) {
      const meta = schema[key]
      if (meta.type === 'boolean') formValues.value[key] = !!meta.default
      else formValues.value[key] = meta.default ?? ''
    }
  }
}

watch(() => form.value.template, () => initFormForTemplate())

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
  // ✅ B 프로젝트 병합: doc_type 추가
  if (form.value.doc_type) {
    fd.append('doc_type', form.value.doc_type)
  }
  if (form.value.template) {
    fd.append('template', String(form.value.template))
    if (selectedTemplate.value) {
      fd.append('filled_data_json', JSON.stringify(formValues.value))
    }
  }
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
