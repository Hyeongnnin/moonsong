<template>
  <div class="space-y-4">
    <!-- 헤더 -->
    <div>
      <p class="text-xs text-gray-500">입력한 정보로 한국 표준 이력서를 생성합니다.</p>
      <h2 class="text-xl font-semibold text-gray-900">이력서 자동 생성</h2>
    </div>

    <!-- 입력 폼 (A 카드 스타일) -->
    <div class="p-4 border rounded bg-white shadow-sm space-y-4">
      <!-- 사진 업로드 -->
      <div class="flex items-start gap-4">
        <div class="w-24 h-30 border-2 border-dashed border-gray-300 rounded overflow-hidden bg-gray-50 flex items-center justify-center">
          <img v-if="photoUrl" :src="photoUrl" class="w-full h-full object-cover" alt="증명사진" />
          <span v-else class="text-xs text-gray-400">4x5 사진</span>
        </div>
        <div class="flex-1">
          <label class="block text-sm font-medium mb-1">증명사진 업로드</label>
          <input 
            type="file" 
            accept="image/*" 
            @change="onPhotoChange" 
            class="text-sm"
          />
          <p class="text-xs text-gray-500 mt-1">4x5 비율 권장</p>
        </div>
      </div>

      <!-- 기본 정보 -->
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="block text-sm font-medium mb-1">성명 *</label>
          <input v-model.trim="form.name" required type="text" 
                 class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">생년월일</label>
          <input v-model.trim="form.birthDate" type="text" 
                 placeholder="YYYY.MM.DD" 
                 class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">연락처</label>
          <input v-model.trim="form.phone" type="text" 
                 placeholder="010-0000-0000" 
                 class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">이메일</label>
          <input v-model.trim="form.email" type="email" 
                 class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
        </div>
      </div>

      <!-- 주소 -->
      <div>
        <label class="block text-sm font-medium mb-1">주소</label>
        <input v-model.trim="form.address" type="text" 
               class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
      </div>

      <!-- 학력 및 경력사항 -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <label class="text-sm font-medium">학력 및 경력사항</label>
          <button type="button" @click="addCareer" 
                  class="text-sm text-brand-600 hover:text-brand-700 font-medium">
            + 추가
          </button>
        </div>
        <div v-for="(career, idx) in form.careers" :key="idx" 
             class="p-3 border rounded bg-gray-50 space-y-2">
          <div class="grid gap-2 md:grid-cols-[120px,1fr,1fr,auto] items-center">
            <input v-model.trim="career.date" type="text" 
                   placeholder="년월일" 
                   class="px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-200" />
            <input v-model.trim="career.content" type="text" 
                   placeholder="학력 및 경력사항" 
                   class="px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-200" />
            <input v-model.trim="career.note" type="text" 
                   placeholder="발령청(비고)" 
                   class="px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-200" />
            <button type="button" @click="removeCareer(idx)" 
                    class="text-xs text-gray-500 hover:text-red-600">
              삭제
            </button>
          </div>
        </div>
      </div>

      <!-- 작성일 및 서명 -->
      <div class="grid gap-3 md:grid-cols-2">
        <div>
          <label class="block text-sm font-medium mb-1">작성일</label>
          <input v-model.trim="form.writtenDate" type="text" 
                 placeholder="YYYY.MM.DD" 
                 class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1">서명</label>
          <input v-model.trim="form.signature" type="text" 
                 placeholder="성명 입력" 
                 class="w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
        </div>
      </div>

      <!-- 저장 옵션 -->
      <div class="p-3 border rounded bg-gray-50 space-y-2">
        <label class="flex items-center gap-2 text-sm font-medium">
          <input type="checkbox" v-model="saveToDocuments" class="h-4 w-4 text-brand-600" />
          생성 시 나의 서류함에 저장
        </label>
        <div v-if="saveToDocuments" class="grid gap-2 md:grid-cols-2">
          <div>
            <label class="block text-xs text-gray-600 mb-1">문서 제목</label>
            <input v-model.trim="documentTitle" type="text" 
                   placeholder="예) 이력서_홍길동" 
                   class="w-full px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-200" />
          </div>
          <div>
            <label class="block text-xs text-gray-600 mb-1">상태</label>
            <select v-model="status" 
                    class="w-full px-3 py-2 border rounded bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-200">
              <option value="완료">완료</option>
              <option value="작성중">작성중</option>
              <option value="제출">제출</option>
            </select>
          </div>
        </div>
      </div>

      <!-- 액션 버튼 (A 스타일) -->
      <div class="flex flex-wrap gap-2 justify-end">
        <button type="button" @click="resetForm" 
                class="px-4 py-2 text-sm border rounded hover:bg-gray-50 transition-colors">
          초기화
        </button>
        <button type="button" @click="handlePreview" 
                :disabled="!canGenerate"
                class="px-4 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          미리보기
        </button>
        <button type="button" @click="handleGenerateDocx" 
                :disabled="loading || !canGenerate"
                class="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {{ loading ? 'DOCX 생성 중...' : 'DOCX 생성' }}
        </button>
        <button type="button" @click="handleGeneratePdf" 
                :disabled="loading || !canGenerate"
                class="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {{ loading ? 'PDF 생성 중...' : 'PDF 생성' }}
        </button>
      </div>
    </div>

    <!-- 실시간 미리보기 -->
    <div class="mt-8 space-y-4">
      <div class="flex items-center justify-between border-b pb-2">
        <h3 class="text-lg font-semibold text-gray-900">서류 미리보기</h3>
        <p class="text-xs text-gray-500">입력한 내용이 실시간으로 이력서 양식에 반영됩니다.</p>
      </div>
      <!-- 고정 높이(520px) 및 내부 스크롤 처리 -->
      <div class="h-[520px] bg-gray-50 border rounded-lg overflow-auto custom-scrollbar flex justify-center p-4">
        <ResumePreview :form="form" :photoUrl="photoUrl" />
      </div>
    </div>

    <!-- 토스트 -->
    <Transition name="toast">
      <div v-if="toast" 
           class="fixed bottom-6 right-6 p-4 rounded-lg shadow-lg text-white bg-green-600 z-40">
        {{ toast }}
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { generateResumeDocx, type ResumePayload } from '../api'
import ResumePreview from './ResumePreview.vue'

const emit = defineEmits(['preview', 'generated'])

interface CareerRow {
  date: string
  content: string
  note: string
}

const form = reactive({
  name: '',
  birthDate: '',
  address: '',
  phone: '',
  email: '',
  writtenDate: new Date().toISOString().slice(0, 10).replace(/-/g, '.'),
  signature: '',
  careers: [{ date: '', content: '', note: '' }] as CareerRow[]
})

const photoUrl = ref('')
const photoFile = ref<File | null>(null)
const saveToDocuments = ref(false)
const documentTitle = ref('이력서')
const status = ref('완료')
const loading = ref(false)
const toast = ref('')

const canGenerate = computed(() => form.name.trim() !== '')

function onPhotoChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    photoFile.value = file
    photoUrl.value = URL.createObjectURL(file)
  }
}

function addCareer() {
  form.careers.push({ date: '', content: '', note: '' })
}

function removeCareer(idx: number) {
  if (form.careers.length > 1) {
    form.careers.splice(idx, 1)
  }
}

function resetForm() {
  Object.assign(form, {
    name: '',
    birthDate: '',
    address: '',
    phone: '',
    email: '',
    writtenDate: new Date().toISOString().slice(0, 10).replace(/-/g, '.'),
    signature: '',
    careers: [{ date: '', content: '', note: '' }]
  })
  photoUrl.value = ''
  photoFile.value = null
  saveToDocuments.value = false
  documentTitle.value = '이력서'
  status.value = '완료'
}

function buildPayload(): ResumePayload {
  // careers 데이터를 서버의 experiences 규격으로 변환
  const experiences = form.careers.map(c => ({
    company: c.content, // '내용'을 회사명/기관명으로 매핑
    role: c.note,      // '비고'를 역할/직무로 매핑
    period: c.date,    // '날짜'를 기간으로 매핑
    description: '',
    achievements: []
  }))

  return {
    name: form.name,
    title: '',
    phone: form.phone,
    email: form.email,
    address: form.address,
    summary: '',
    experiences: experiences, // 매핑된 데이터 전달
    educations: [],
    skills: [],
    certifications: [],
    languages: [],
    save_to_documents: saveToDocuments.value,
    document_title: documentTitle.value || `이력서_${form.name}`,
    status: status.value
  }
}

function handlePreview() {
  if (!canGenerate.value) return
  
  emit('preview', {
    form: { ...form },
    photoUrl: photoUrl.value
  })
}

async function handleGenerateDocx() {
  if (!canGenerate.value || loading.value) return
  
  try {
    loading.value = true
    const payload = buildPayload()
    const result = await generateResumeDocx(payload)
    
    // 다운로드
    const url = URL.createObjectURL(result.blob)
    const a = document.createElement('a')
    a.href = url
    a.download = result.filename
    a.click()
    URL.revokeObjectURL(url)
    
    showToast('DOCX 파일이 생성되었습니다.')
    
    if (result.saved) {
      emit('generated')
    }
  } catch (error) {
    console.error('DOCX 생성 실패:', error)
    showToast('DOCX 생성에 실패했습니다.')
  } finally {
    loading.value = false
  }
}

function handleGeneratePdf() {
  if (!canGenerate.value || loading.value) return
  
  emit('preview', {
    form: { ...form },
    photoUrl: photoUrl.value,
    downloadPdf: true
  })
}

function showToast(message: string) {
  toast.value = message
  setTimeout(() => { toast.value = '' }, 3000)
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
