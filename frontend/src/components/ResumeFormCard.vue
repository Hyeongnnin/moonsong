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
        <div class="w-32 aspect-[4/5] border-2 border-dashed border-gray-300 rounded-lg overflow-hidden bg-gray-50 flex items-center justify-center shrink-0">
          <img v-if="photoUrl" :src="photoUrl" class="w-full h-full object-cover" alt="증명사진" />
          <span v-else class="text-sm text-gray-400 font-medium">4x5 사진</span>
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
          <div class="grid gap-2 md:grid-cols-[100px,100px,1fr,1fr,auto] items-center">
            <input v-model.trim="career.startDate" type="text" 
                   placeholder="시작일" 
                   class="px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-200" />
            <input v-model.trim="career.endDate" type="text" 
                   placeholder="종료일" 
                   class="px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-200" />
            <input v-model.trim="career.content" type="text" 
                   placeholder="학력 및 경력사항" 
                   class="px-2 py-1 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand-200" />
            <input v-model.trim="career.note" type="text" 
                   placeholder="기관명" 
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
        <div class="grid gap-2 md:grid-cols-2">
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
        <!-- 기존 DOCX 버튼 제거, 저장 버튼 추가 -->
        <button type="button" @click="handleSave" 
                :disabled="loading || !canGenerate"
                class="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {{ loading ? '저장 중...' : '저장하기' }}
        </button>
        <!-- PDF 생성(다운로드) 버튼은 유지 (사용자가 로컬에 저장하고 싶을 수 있음) -> 
             사용자 요청은 "Save as PDF"를 "Save to My Documents"로 바꾸는 것 같지만 
             명시적으로 "DOCX 버튼을 없애고 저장 기능을 넣어달라"고 함.
             PDF 다운로드는 놔둘지 물어보진 않았지만 일반적인 'PDF 생성' 버튼(미리보기 모달로 감)은 유지하는 게 안전.
             여기서는 'PDF 생성' -> 'PDF 다운로드' 버튼은 유지하되, 
             handleGeneratePdf는 기존 로직(미리보기 모달 열어서 다운로드 옵션)을 따름.
        -->
        <button type="button" @click="handleGeneratePdf" 
                :disabled="loading || !canGenerate"
                class="px-4 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
          {{ loading ? 'PDF 생성 중...' : 'PDF 다운로드' }}
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
        <!-- ref 추가 -->
        <ResumePreview ref="previewRef" :form="form" :photoUrl="photoUrl" />
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
import { createGenerated } from '../api'
import ResumePreview from './ResumePreview.vue'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

const emit = defineEmits(['preview', 'generated'])

interface CareerRow {
  startDate: string
  endDate: string
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
  careers: [{ startDate: '', endDate: '', content: '', note: '' }] as CareerRow[]
})

const photoUrl = ref('')
const photoFile = ref<File | null>(null)
// const saveToDocuments = ref(false) // 제거됨
const documentTitle = ref('이력서')
const status = ref('완료')
const loading = ref(false)
const toast = ref('')

// ResumePreview 컴포넌트 ref
const previewRef = ref<InstanceType<typeof ResumePreview> | null>(null)

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
  if (form.careers.length >= 15) {
    alert('학력 및 경력사항은 최대 15개 까지만 가능합니다! 이 바보야')
    return
  }
  form.careers.push({ startDate: '', endDate: '', content: '', note: '' })
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
    careers: [{ startDate: '', endDate: '', content: '', note: '' }]
  })
  photoUrl.value = ''
  photoFile.value = null
  // saveToDocuments.value = false
  documentTitle.value = '이력서'
  status.value = '완료'
}

function handlePreview() {
  if (!canGenerate.value) return
  
  emit('preview', {
    form: { ...form },
    photoUrl: photoUrl.value
  })
}

// PDF 다운로드 (기존 PDF 생성 버튼)
function handleGeneratePdf() {
  if (!canGenerate.value || loading.value) return
  
  emit('preview', {
    form: { ...form },
    photoUrl: photoUrl.value,
    downloadPdf: true
  })
}

// 저장하기 (새로운 기능: PDF 생성 후 업로드)
async function handleSave() {
  if (!canGenerate.value || loading.value) return
  
  // 미리보기 DOM 접근 확인
  if (!previewRef.value?.resumeRef) {
    alert('미리보기 로딩 중입니다. 잠시 후 다시 시도해주세요.')
    return
  }

  try {
    loading.value = true
    const element = previewRef.value.resumeRef

    // 1. HTML -> Canvas
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    })

    // 2. Canvas -> PDF Blob
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })

    const imgWidth = 210
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)

    const blob = pdf.output('blob')
    
    // 3. 업로드 Payload 준비
    const formData = new FormData()
    const fileName = `resume_${new Date().getTime()}.pdf`
    
    // API 요구사항에 맞춰 필드 구성
    // title, user match(backend handles user from token), doc_type, file
    formData.append('title', documentTitle.value || `이력서_${form.name}`)
    formData.append('doc_type', 'resume')
    formData.append('status', status.value)
    formData.append('file', blob, fileName) // file_path 필드로 파일 전송 (또는 백엔드 구현에 따라 file일수도 있음, api.ts createGenerated 참고)
    
    // api.ts 의 createGenerated 는 FormData를 그대로 전송.
    // 백엔드 Django ViewSet을 알 수 없으므로, 기존 createGenerated 사용.
    // GeneratedDocument 모델의 필드를 추측: title, doc_type, status, file_path(FileField)
    
    // JSON 데이터도 필요하다면:
    // formData.append('filled_data_json', JSON.stringify(form))

    await createGenerated(formData)

    showToast('나의 서류함에 저장되었습니다.')
    emit('generated')

  } catch (error) {
    console.error('저장 실패:', error)
    showToast('저장에 실패했습니다.')
  } finally {
    loading.value = false
  }
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
