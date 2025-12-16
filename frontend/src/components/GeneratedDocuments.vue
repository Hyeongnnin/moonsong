<template>
  <div class="space-y-4">
    <!-- Header / Actions -->
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-xs text-gray-500">내가 올린 서류를 한 곳에서 관리하세요</p>
        <h2 class="text-2xl font-semibold text-gray-900">나의 서류함</h2>
      </div>
      <div class="flex flex-wrap gap-2">
        <button @click="reload" class="px-3 py-2 text-sm rounded border border-gray-200 hover:bg-gray-50 flex items-center gap-2">
          <span>새로고침</span>
        </button>
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
      <div class="md:col-span-2">
        <label class="text-xs text-gray-500">검색</label>
        <input v-model="search" type="text" placeholder="제목, 템플릿명, 상태 검색" class="w-full mt-1 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-brand-200" />
      </div>
      <div>
        <label class="text-xs text-gray-500">문서 유형</label>
        <select v-model="typeFilter" class="w-full mt-1 px-3 py-2 border rounded bg-white">
          <option value="all">전체</option>
          <option v-for="t in docTypes" :key="t" :value="t">{{ t }}</option>
        </select>
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
            <option value="name">템플릿명</option>
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
            <p class="text-xs text-gray-500 mt-1">템플릿: {{ getTemplateName(d) }} · {{ getDocType(d) }}</p>
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
          <button v-if="d.file_url" @click.prevent="openDownload(d.file_url)" class="flex-1 px-3 py-2 text-sm border rounded hover:bg-gray-50">다운로드</button>
          <button @click="onEdit(d)" class="px-3 py-2 text-sm border rounded hover:bg-gray-50">수정</button>
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

        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <label class="block text-sm font-medium mb-1">템플릿 (선택)</label>
            <select v-model="editForm.template" class="w-full px-3 py-2 border rounded bg-white">
              <option value="">변경 없음 / 해제</option>
              <option v-for="t in templates" :key="t.id" :value="String(t.id)">{{ t.name }} ({{ t.doc_type }})</option>
            </select>
          </div>
          <div class="text-xs text-gray-500 self-end">
            템플릿을 해제하면 사용자 지정 문서로 남습니다. 필요 시 다시 선택하세요.
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

  <!-- Toast -->
  <div v-if="toast.message" :class="['fixed bottom-6 right-6 p-3 rounded shadow-lg text-white', toast.type === 'success' ? 'bg-green-600' : (toast.type === 'error' ? 'bg-red-600' : 'bg-gray-800')]">
    {{ toast.message }}
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { fetchGenerated, fetchTemplates, type GeneratedDocument, deleteGenerated, updateGenerated } from '../api'
import CreateDocumentForm from './CreateDocumentForm.vue'

const docs = ref<GeneratedDocument[]>([])
const templates = ref<any[]>([])
const loading = ref(true)
const showCreate = ref(false)
const showEdit = ref(false)
const editingDoc = ref<GeneratedDocument | null>(null)
const editForm = ref({ title: '', status: '작성중', template: '' })
const editFileRef = ref<File | null>(null)
const editFileName = ref('')
const toast = ref({ message: '', type: '' })

const search = ref('')
const statusFilter = ref<'all' | string>('all')
const typeFilter = ref<'all' | string>('all')
const sortKey = ref<'newest' | 'oldest' | 'name'>('newest')

onMounted(async () => {
  await reload()
})

const docTypes = computed(() => {
  const types = new Set<string>()
  // ✅ B 프로젝트 병합: 템플릿 기반 + doc_type 필드 모두 포함
  templates.value.forEach((t: any) => {
    if (t.doc_type) types.add(t.doc_type)
  })
  docs.value.forEach((d) => {
    if (d.doc_type) types.add(d.doc_type)
  })
  return Array.from(types)
})

const filteredDocs = computed(() => {
  const term = search.value.trim().toLowerCase()
  const type = typeFilter.value
  const status = statusFilter.value

  const enriched = docs.value.map((d) => {
    const tpl = resolveTemplate(d)
    // ✅ B 프로젝트 병합: doc_type 필드도 고려
    const docType = d.doc_type || tpl?.doc_type || ''
    return { ...d, _templateName: tpl?.name || '템플릿 없음', _docType: docType }
  })

  let result = enriched.filter((d) => {
    const matchesSearch = term
      ? (d.title || '').toLowerCase().includes(term)
        || d._templateName.toLowerCase().includes(term)
        || d._docType.toLowerCase().includes(term)
        || (d.status || '').toLowerCase().includes(term)
      : true
    const matchesType = type === 'all' ? true : d._docType === type
    const matchesStatus = status === 'all' ? true : (d.status || '작성중') === status
    return matchesSearch && matchesType && matchesStatus
  })

  result = result.sort((a, b) => {
    if (sortKey.value === 'name') {
      return a._templateName.localeCompare(b._templateName)
    }
    const aDate = a.created_at ? new Date(a.created_at).getTime() : 0
    const bDate = b.created_at ? new Date(b.created_at).getTime() : 0
    return sortKey.value === 'newest' ? bDate - aDate : aDate - bDate
  })

  return result
})

async function reload() {
  loading.value = true
  try {
    const [generated, tpl] = await Promise.all([fetchGenerated(), fetchTemplates()])
    docs.value = generated
    templates.value = tpl
  } catch (e) {
    console.error('문서 로드 실패', e)
    showToast('문서를 불러오지 못했습니다. 로그인 상태를 확인하세요.', 'error')
  } finally {
    loading.value = false
  }
}

function resolveTemplate(d: GeneratedDocument) {
  if (!d.template) return null
  if (typeof d.template === 'number') {
    return templates.value.find((x: any) => x.id === d.template) || null
  }
  return d.template as any
}

function getTemplateName(d: GeneratedDocument) {
  const tpl = resolveTemplate(d)
  return tpl?.name || '템플릿 없음'
}

function getDocType(d: GeneratedDocument) {
  // ✅ B 프로젝트 병합: doc_type 필드 우선, 없으면 템플릿에서 가져오기
  if (d.doc_type) return d.doc_type
  const tpl = resolveTemplate(d)
  return tpl?.doc_type || '유형 미지정'
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
  editForm.value.template = d.template ? String((d.template as any).id ?? d.template) : ''
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
  if (editForm.value.template !== '') fd.append('template', editForm.value.template)
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
</script>

<style scoped>
</style>
