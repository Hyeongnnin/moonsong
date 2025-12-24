<template>
  <div class="space-y-4">
    <!-- Header / Actions -->
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-xs text-gray-500">내가 올린 서류를 한 곳에서 관리하세요</p>
        <h2 class="text-2xl font-semibold text-gray-900">나의 서류함</h2>
      </div>
      <div class="flex flex-wrap gap-2">

        <button @click="showCreate = !showCreate" class="px-3 py-2 text-sm rounded bg-brand-600 text-white hover:bg-brand-700">
          {{ showCreate ? '업로드 닫기' : '새 서류 업로드' }}
        </button>
      </div>
    </div>

    <!-- Upload form -->
    <div v-if="showCreate" class="p-4 border border-dashed border-brand-200 rounded-lg bg-brand-50/50">
      <CreateDocumentForm @created="onCreated" @cancel="showCreate = false" />
    </div>

    <!-- Filters -->
    <div class="grid gap-3 md:grid-cols-4 bg-white border border-gray-200 rounded-lg p-4">
      <div class="md:col-span-3">
        <label class="text-xs text-gray-500">검색</label>
        <input v-model="search" type="text" placeholder="제목, 상태 검색" class="w-full mt-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
      </div>
      <div class="grid grid-cols-2 gap-2">
        <div>
          <label class="text-xs text-gray-500">상태</label>
          <select v-model="statusFilter" class="w-full mt-1 px-3 py-2 border rounded bg-white">
            <option value="all">전체</option>
            <option value="작성중">작성중</option>
            <option value="완료">완료</option>
            <option value="제출">제출</option>
          </select>
        </div>
        <div>
          <label class="text-xs text-gray-500">정렬</label>
          <select v-model="sortKey" class="w-full mt-1 px-3 py-2 border rounded bg-white">
            <option value="newest">최신순</option>
            <option value="oldest">오래된순</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="p-6 text-sm text-gray-500 bg-white border border-gray-200 rounded-lg">로딩 중...</div>

    <!-- Empty state -->
    <div v-else-if="filteredDocs.length === 0" class="p-10 border border-dashed rounded-lg text-center text-sm text-gray-500 bg-white">
      업로드한 서류가 없습니다. 새 서류를 업로드해보세요.
    </div>

    <!-- Documents grid -->
    <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="d in filteredDocs" :key="d.id" class="border border-gray-200 rounded-lg bg-white p-4 flex flex-col gap-3 shadow-sm">
        <div class="flex items-start justify-between gap-2">
          <div>
            <p class="text-xs text-gray-500">제목</p>
            <h3 class="text-lg font-semibold text-gray-900">{{ d.title || '제목 미입력' }}</h3>
          </div>
          <span class="px-2 py-1 text-xs rounded-full" :class="statusBadgeClass(d.status)">{{ d.status || '작성중' }}</span>
        </div>

        <div class="flex items-center justify-between text-xs text-gray-500">
          <span>{{ formatDate(d.created_at) }}</span>
          <span v-if="d.file_url" class="inline-flex items-center gap-1 text-green-700 font-semibold">첨부됨</span>
          <span v-else class="text-amber-700 font-medium">파일 없음</span>
        </div>

        <div class="flex flex-wrap gap-2 text-xs text-gray-600">
          <span class="px-2 py-1 bg-gray-100 rounded">ID {{ d.id }}</span>
          <span v-if="d.employee" class="px-2 py-1 bg-gray-100 rounded">직원: {{ d.employee }}</span>
          <span v-if="d.consultation" class="px-2 py-1 bg-gray-100 rounded">상담: {{ d.consultation }}</span>
        </div>

        <div class="flex flex-wrap gap-2 mt-auto">
          <button @click.prevent="openPreview(d)" class="px-3 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700">미리보기</button>
          <button v-if="d.file_url" @click.prevent="openDownload(d.file_url)" class="flex-1 px-3 py-2 text-sm border rounded hover:bg-gray-50">다운로드</button>
          <button @click="onDelete(d)" class="px-3 py-2 text-sm border border-red-200 text-red-700 rounded hover:bg-red-50">삭제</button>
        </div>
      </article>
    </div>
  </div>

  <!-- Edit modal: reuse create-like UI for editing -->
  <div v-if="showEdit" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
    <div class="bg-white p-5 rounded w-11/12 md:w-[560px] shadow-xl border border-gray-200 max-h-[90vh] overflow-y-auto">
      <h3 class="text-lg font-semibold mb-4">서류 수정</h3>
      <div class="space-y-4">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <label class="block text-sm font-medium mb-1">제목</label>
            <input v-model.trim="editForm.title" type="text" placeholder="예) 2025년 1월 급여명세서" class="w-full px-3 py-2 border rounded" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">상태</label>
            <select v-model="editForm.status" class="w-full px-3 py-2 border rounded bg-white">
              <option value="작성중">작성중</option>
              <option value="완료">완료</option>
              <option value="제출">제출</option>
            </select>
          </div>
        </div>



        <div>
          <label class="block text-sm font-medium mb-1">파일 교체 (선택, PDF)</label>
          <input type="file" @change="onEditFileChange" accept=".pdf,application/pdf" />
          <div v-if="editFileName" class="text-sm text-gray-600 mt-1">선택된 파일: {{ editFileName }}</div>
          <div class="text-xs text-gray-500 mt-1">미선택 시 기존 파일이 유지됩니다. 최대 10MB, PDF 권장.</div>
        </div>
      </div>

      <div class="flex justify-end gap-2 mt-6">
        <button @click="closeEdit" class="px-3 py-2 bg-gray-100 rounded">취소</button>
        <button @click="saveEdit" class="px-3 py-2 bg-brand-600 text-white rounded">저장</button>
      </div>
    </div>
  </div>

  <!-- 미리보기 모달 (격리된 Viewer) -->
  <Teleport to="body">
    <div 
      v-if="showPreviewModal" 
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4"
      @click.self="closePreviewModal"
    >
      <div class="bg-white rounded-lg shadow-xl w-full max-w-[95vw] max-h-[95vh] flex flex-col">
        <!-- 헤더 -->
        <div class="flex items-center justify-between p-4 border-b">
          <div>
            <h3 class="text-lg font-semibold">{{ previewDoc?.title || '서류 미리보기' }}</h3>
          </div>
          <button @click="closePreviewModal" class="text-gray-500 hover:text-gray-700">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <!-- 스크롤 가능한 뷰어 컨테이너 (100% 격리) -->
        <div class="flex-1 overflow-auto bg-gray-100">
          <div class="p-6">
            <!-- Loading Spinner -->
            <div v-if="previewLoading" class="min-h-[297mm] flex flex-col items-center justify-center bg-gray-50 border border-gray-200">
              <svg class="animate-spin h-10 w-10 text-brand-600 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-gray-500 font-medium">문서를 불러오는 중입니다...</p>
            </div>

            <!-- PDF 파일이 있는 경우 iframe으로 표시 -->
            <div v-else-if="previewPdfUrl" class="viewer-container">
              <iframe 
                :src="previewPdfUrl" 
                class="preview-iframe"
                frameborder="0"
              />
            </div>
            <!-- 파일이 없는 경우 정보만 표시 -->
            <div v-else class="preview-sheet">
              <div class="preview-content">
                <div class="text-center mb-6">
                  <h1 class="text-3xl font-bold">{{ previewDoc?.title || '제목 없음' }}</h1>
                </div>
                
                <div class="space-y-4 text-sm">
                  <div class="border border-gray-300 p-4 rounded bg-yellow-50">
                    <p class="font-medium mb-2">⚠️ 파일이 첨부되지 않았습니다</p>
                    <p class="text-gray-700">
                      이 서류에는 아직 파일이 업로드되지 않았습니다. 
                    </p>
                  </div>

                  <div class="border border-gray-300 p-4 rounded">
                    <p class="font-medium mb-2">서류 정보</p>
                    <ul class="list-disc list-inside space-y-1 text-gray-700">
                      <li>제목: {{ previewDoc?.title || '제목 없음' }}</li>
                      <li>상태: {{ previewDoc?.status || '작성중' }}</li>
                      <li>생성일: {{ formatDate(previewDoc?.created_at) }}</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 하단 버튼 -->
        <div class="p-4 border-t bg-gray-50 flex justify-end gap-2">
          <button 
            @click="closePreviewModal" 
            class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            닫기
          </button>
          <button 
            v-if="previewDoc?.file_url"
            @click="openDownload(previewDoc.file_url)" 
            class="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700"
          >
            다운로드
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Toast -->
  <div v-if="toast.message" :class="['fixed bottom-6 right-6 p-3 rounded shadow-lg text-white', toast.type === 'success' ? 'bg-green-600' : (toast.type === 'error' ? 'bg-red-600' : 'bg-gray-800')]">
    {{ toast.message }}
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, ref } from 'vue'
import { fetchGenerated, type GeneratedDocument, deleteGenerated, updateGenerated } from '../api'
import CreateDocumentForm from './CreateDocumentForm.vue'

const docs = ref<GeneratedDocument[]>([])
const loading = ref(true)
const showCreate = ref(false)
const showEdit = ref(false)
const editingDoc = ref<GeneratedDocument | null>(null)
const editForm = ref({ title: '', status: '작성중' })
const editFileRef = ref<File | null>(null)
const editFileName = ref('')
const toast = ref({ message: '', type: '' })

// 미리보기 관련 상태
const showPreviewModal = ref(false)
const previewDoc = ref<GeneratedDocument | null>(null)
const previewPdfUrl = ref<string>('')
const previewLoading = ref(false)

const search = ref('')
const statusFilter = ref<'all' | string>('all')
const sortKey = ref<'newest' | 'oldest'>('newest')

onMounted(async () => {
  await reload()
})

const filteredDocs = computed(() => {
  const term = search.value.trim().toLowerCase()
  const status = statusFilter.value

  let result = docs.value.filter((d) => {
    const matchesSearch = term
      ? (d.title || '').toLowerCase().includes(term)
        || (d.status || '').toLowerCase().includes(term)
      : true
    const matchesStatus = status === 'all' ? true : (d.status || '작성중') === status
    return matchesSearch && matchesStatus
  })

  result = result.sort((a, b) => {
    if (sortKey.value === 'oldest') {
      const aDate = a.created_at ? new Date(a.created_at).getTime() : 0
      const bDate = b.created_at ? new Date(b.created_at).getTime() : 0
      return aDate - bDate
    }
    // Default newest
    const aDate = a.created_at ? new Date(a.created_at).getTime() : 0
    const bDate = b.created_at ? new Date(b.created_at).getTime() : 0
    return bDate - aDate
  })

  return result
})

async function reload() {
  loading.value = true
  try {
    const generated = await fetchGenerated()
    docs.value = generated
  } catch (e) {
    console.error('문서 로드 실패', e)
    showToast('문서를 불러오지 못했습니다. 로그인 상태를 확인하세요.', 'error')
  } finally {
    loading.value = false
  }
}


function resolveFileUrl(url: string | undefined | null) {
  if (!url) return '#'
  if (url.startsWith('http')) return url
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
  const host = base.replace(/\/api\/?$/, '')
  return host + url
}

async function onDelete(d: GeneratedDocument) {
  if (!confirm('정말로 삭제하시겠습니까?')) return
  try {
    await deleteGenerated(d.id)
    showToast('삭제되었습니다.', 'success')
    await reload()
  } catch (e) {
    console.error('삭제 실패', e)
    showToast('삭제에 실패했습니다.', 'error')
  }
}

function onCreated(created: GeneratedDocument) {
  showCreate.value = false
  showToast('문서가 생성되었습니다.', 'success')
  docs.value = [created, ...docs.value]
}

function onEdit(d: GeneratedDocument) {
  editingDoc.value = d
  editForm.value.title = d.title || ''
  editForm.value.status = d.status || '작성중'
  editFileRef.value = null
  editFileName.value = ''
  showEdit.value = true
}

function closeEdit() {
  showEdit.value = false
  editingDoc.value = null
  editFileRef.value = null
  editFileName.value = ''
}

function onEditFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files || input.files.length === 0) {
    editFileRef.value = null
    editFileName.value = ''
    return
  }
  const file = input.files[0]
  if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
    alert('PDF 파일만 업로드 가능합니다.')
    input.value = ''
    return
  }
  editFileRef.value = file
  editFileName.value = file.name
}

async function saveEdit() {
  if (!editingDoc.value) return
  const fd = new FormData()
  fd.append('title', editForm.value.title)
  if (editForm.value.status) fd.append('status', editForm.value.status)
  if (editFileRef.value) fd.append('file', editFileRef.value)
  try {
    const updated = await updateGenerated(editingDoc.value.id, fd)
    showToast('문서가 수정되었습니다.', 'success')
    docs.value = docs.value.map((d) => (d.id === updated.id ? updated : d))
    closeEdit()
  } catch (e) {
    console.error('수정 실패', e)
    showToast('수정에 실패했습니다.', 'error')
  }
}

function openDownload(url: string | undefined | null) {
  if (!url) return
  const resolved = resolveFileUrl(url)
  window.open(resolved, '_blank')
}

function statusBadgeClass(status?: string) {
  const value = status || '작성중'
  if (value === '완료') return 'bg-green-100 text-green-700'
  if (value === '제출') return 'bg-blue-100 text-blue-700'
  return 'bg-amber-100 text-amber-700'
}

function formatDate(value?: string | null) {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleDateString('ko-KR') + ' ' + d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })
}

function showToast(message: string, type = 'info') {
  toast.value.message = message
  toast.value.type = type
  setTimeout(() => {
    toast.value.message = ''
    toast.value.type = ''
  }, 3000)
}

async function openPreview(d: GeneratedDocument) {
  previewDoc.value = d
  showPreviewModal.value = true
  previewPdfUrl.value = ''
  
  if (d.file_url) {
    try {
      previewLoading.value = true
      const url = resolveFileUrl(d.file_url)
      // fetch as blob to bypass X-Frame-Options SAMEORIGIN issues with localhost port mismatch
      const response = await axios.get(url, { responseType: 'blob' })
      const blob = new Blob([response.data], { type: 'application/pdf' })
      previewPdfUrl.value = URL.createObjectURL(blob)
    } catch (e) {
      console.error('Preview load failed', e)
      // Fallback
      previewPdfUrl.value = resolveFileUrl(d.file_url)
    } finally {
      previewLoading.value = false
    }
  }
}

function closePreviewModal() {
  if (previewPdfUrl.value && previewPdfUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewPdfUrl.value)
  }
  showPreviewModal.value = false
  previewDoc.value = null
  previewPdfUrl.value = ''
}

// 부모 컴포넌트에서 호출할 수 있도록 expose
defineExpose({
  reload
})
</script>

<style scoped>
/* 격리된 뷰어 컨테이너 */
.viewer-container {
  width: 100%;
  max-width: 100%;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow: visible;
}

/* PDF iframe */
.preview-iframe {
  width: 210mm;
  min-height: 297mm;
  background: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
}

/* A4 크기 미리보기 시트 */
.preview-sheet {
  width: 210mm;
  min-height: 297mm;
  background: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  margin: 0 auto;
}

.preview-content {
  padding: 20mm;
}

/* 반응형: 작은 화면에서는 축소 */
@media (max-width: 900px) {
  .preview-iframe,
  .preview-sheet {
    width: 100%;
    min-width: 280px;
  }
  
  .preview-content {
    padding: 16px;
  }
}

/* 브랜드 색상 */
.bg-brand-600 {
  background-color: #DE5D35;
}

.hover\:bg-brand-700:hover {
  background-color: #c54d28;
}
</style>
