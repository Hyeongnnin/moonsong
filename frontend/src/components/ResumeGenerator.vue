<template>
  <div class="space-y-4">
    <div>
      <p class="text-xs text-gray-500">입력한 정보로 이력서를 바로 만듭니다.</p>
      <h2 class="text-2xl font-semibold text-gray-900">이력서 자동 생성</h2>
    </div>

    <div class="p-4 border rounded bg-white space-y-4 shadow-sm">
      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="block text-sm font-medium mb-1">이름 *</label>
          <input v-model.trim="form.name" required type="text" class="w-full px-3 py-2 border rounded" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">직무/직책</label>
          <input v-model.trim="form.title" type="text" placeholder="예) 프론트엔드 개발자" class="w-full px-3 py-2 border rounded" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">연락처</label>
          <input v-model.trim="form.phone" type="text" placeholder="010-1234-5678" class="w-full px-3 py-2 border rounded" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">이메일</label>
          <input v-model.trim="form.email" type="email" placeholder="you@example.com" class="w-full px-3 py-2 border rounded" />
        </div>
        <div class="md:col-span-2">
          <label class="block text-sm font-medium mb-1">주소</label>
          <input v-model.trim="form.address" type="text" class="w-full px-3 py-2 border rounded" />
        </div>
      </div>

        <div>
          <label class="block text-sm font-medium mb-1">요약</label>
          <textarea v-model.trim="form.summary" rows="3" class="w-full px-3 py-2 border rounded" placeholder="핵심 역량과 한 줄 소개를 적어주세요."></textarea>
        </div>

        <div class="space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h4 class="text-sm font-semibold">학력 / 경력</h4>
            <button type="button" @click="addEntry" class="px-3 py-1 text-xs rounded border border-brand-200 text-brand-600">+ 항목 추가</button>
          </div>
          <div v-for="(entry, idx) in form.entries" :key="idx" class="p-3 border rounded space-y-2 bg-gray-50">
            <div class="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
              <span class="font-semibold">{{ entry.isExperience ? '경력' : '학력' }}</span>
              <label class="flex items-center gap-1">
                <input type="checkbox" v-model="entry.isExperience" />
                경력사항
              </label>
              <button type="button" @click="removeEntry(idx)" class="text-gray-500">삭제</button>
            </div>
            <div class="grid gap-2 md:grid-cols-2">
              <input
                v-model.trim="entry.organization"
                type="text"
                :placeholder="entry.isExperience ? '회사명' : '학교'"
                class="w-full px-3 py-2 border rounded"
              />
              <input
                v-model.trim="entry.title"
                type="text"
                :placeholder="entry.isExperience ? '직책' : '전공'"
                class="w-full px-3 py-2 border rounded"
              />
              <input
                v-model.trim="entry.period"
                type="text"
                placeholder="기간 (예: 2023.01-2024.12)"
                class="w-full px-3 py-2 border rounded md:col-span-2"
              />
            </div>
          </div>
        </div>

        <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-sm font-semibold">기술 / 언어 / 자격증</h4>
          <button type="button" @click="addTagged" class="text-sm text-brand-600">+ 추가</button>
        </div>
        <div v-for="(item, idx) in form.tagged" :key="idx" class="grid gap-2 md:grid-cols-[140px,1fr,auto] items-center p-3 border rounded bg-gray-50">
          <select v-model="item.category" class="px-3 py-2 border rounded bg-white">
            <option value="skill">기술</option>
            <option value="language">언어</option>
            <option value="cert">자격증</option>
          </select>
          <input v-model.trim="item.value" type="text" class="w-full px-3 py-2 border rounded" placeholder="예) React / 영어(업무 가능) / 정보처리기사" />
          <button type="button" @click="removeTagged(idx)" class="text-xs text-gray-500">삭제</button>
        </div>
      </div>

        <div class="p-3 border rounded bg-gray-50 space-y-2">
        <label class="flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" v-model="form.saveToDocuments" />
          생성된 파일을 나의 서류함에 저장
        </label>
        <div class="grid gap-2 md:grid-cols-2">
          <div>
            <label class="block text-xs text-gray-500">문서 제목</label>
            <input v-model.trim="form.documentTitle" type="text" class="w-full px-3 py-2 border rounded" placeholder="예) 이력서_홍길동" />
          </div>
          <div>
            <label class="block text-xs text-gray-500">상태</label>
            <select v-model="form.status" class="w-full px-3 py-2 border rounded bg-white">
              <option value="완료">완료</option>
              <option value="작성중">작성중</option>
              <option value="제출">제출</option>
            </select>
          </div>
        </div>
        <p class="text-xs text-gray-500">저장 시 나의 서류함에 docx로 기록됩니다.</p>
      </div>

      <div class="flex items-center justify-end gap-2">
        <button type="button" @click="resetForm" class="px-4 py-2 bg-gray-100 rounded">초기화</button>
        <button type="submit" :disabled="loading" class="px-4 py-2 bg-brand-600 text-white rounded">
          {{ loading ? '생성 중...' : '이력서 생성 및 다운로드' }}
        </button>
      </div>
      </form>

      <div v-if="toast" class="text-sm text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2">
        {{ toast }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { generateResumeDocx, type ResumePayload } from '../api'

const emit = defineEmits(['saved'])

const loading = ref(false)
const toast = ref('')

const createEntry = (isExperience = false) => ({
  isExperience,
  organization: '',
  title: '',
  period: '',
})
const emptyTagged = () => ({ category: 'skill', value: '' })

const form = reactive({
  name: '',
  title: '',
  phone: '',
  email: '',
  address: '',
  summary: '',
  entries: [createEntry(false)],
  tagged: [emptyTagged()],
  saveToDocuments: false,
  documentTitle: '이력서',
  status: '완료',
})

function splitList(text: string): string[] {
  if (!text) return []
  return text
    .split(/[,\n]/)
    .map((t) => t.trim())
    .filter(Boolean)
}

function mapExperiences() {
  return form.entries
    .filter((entry) => entry.isExperience)
    .map((entry) => ({
      company: entry.organization,
      role: entry.title,
      period: entry.period,
      description: undefined,
      achievements: [],
    }))
    .filter((e) => Object.values(e).some((v) => (Array.isArray(v) ? v.length : v)))
}

function mapTagged() {
  const skills: string[] = []
  const languages: string[] = []
  const certifications: string[] = []
  form.tagged.forEach((item) => {
    if (!item.value) return
    if (item.category === 'language') languages.push(item.value)
    else if (item.category === 'cert') certifications.push(item.value)
    else skills.push(item.value)
  })
  return { skills, languages, certifications }
}

function mapEducations() {
  return form.entries
    .filter((entry) => !entry.isExperience)
    .map((entry) => ({
      school: entry.organization,
      major: entry.title,
      period: entry.period,
      description: undefined,
    }))
    .filter((e) => Object.values(e).some((v) => v))
}

async function onSubmit() {
  if (!form.name) return
  loading.value = true
  toast.value = ''
  try {
    const payload: ResumePayload = {
      name: form.name,
      title: form.title || undefined,
      phone: form.phone || undefined,
      email: form.email || undefined,
      address: form.address || undefined,
      summary: form.summary || undefined,
      experiences: mapExperiences(),
      educations: mapEducations(),
      ...mapTagged(),
      save_to_documents: form.saveToDocuments,
      document_title: form.documentTitle || '이력서',
      status: form.status || '완료',
    }

    const result = await generateResumeDocx(payload)
    downloadBlob(result.blob, result.filename)
    if (result.saved) {
      emit('saved')
      toast.value = '생성된 이력서가 나의 서류함에 저장되었습니다.'
    } else {
      toast.value = '이력서 docx가 다운로드되었습니다.'
    }
  } catch (e: any) {
    console.error('이력서 생성 실패', e)
    toast.value = '생성에 실패했습니다. 로그인 상태와 입력을 확인하세요.'
  } finally {
    loading.value = false
    setTimeout(() => (toast.value = ''), 4000)
  }
}

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

function addEntry() { form.entries.push(createEntry(false)) }
function removeEntry(idx: number) { form.entries.splice(idx, 1) }
function addTagged() { form.tagged.push(emptyTagged()) }
function removeTagged(idx: number) { form.tagged.splice(idx, 1) }

function resetForm() {
  form.name = ''
  form.title = ''
  form.phone = ''
  form.email = ''
  form.address = ''
  form.summary = ''
  form.entries = [createEntry(false)]
  form.tagged = [emptyTagged()]
  form.saveToDocuments = false
  form.documentTitle = '이력서'
  form.status = '완료'
}
</script>
