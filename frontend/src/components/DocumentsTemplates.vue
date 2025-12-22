<template>
  <div class="p-4">
    <h2 class="text-xl font-semibold mb-4">문서 템플릿</h2>
    <div v-if="loading" class="text-sm text-gray-500">로딩 중...</div>
    <div v-else>
      <ul class="space-y-3">
        <li v-for="t in templates" :key="t.id" class="p-3 border rounded bg-white shadow-sm">
          <div class="flex justify-between items-start gap-3">
            <div class="flex-1">
              <div class="font-medium">{{ t.name }}</div>
              <div class="text-xs text-gray-500">{{ t.doc_type }}</div>
              <div class="text-sm mt-2 text-gray-600">{{ t.description }}</div>
            </div>
            <button 
              @click="openPreview(t)" 
              class="px-3 py-2 text-sm bg-brand-600 text-white rounded hover:bg-brand-700 whitespace-nowrap"
            >
              미리보기
            </button>
          </div>
        </li>
      </ul>
      <div v-if="templates.length === 0" class="text-sm text-gray-500 mt-3">사용 가능한 템플릿이 없습니다.</div>
    </div>

    <!-- 미리보기 모달 (격리된 Viewer) -->
    <Teleport to="body">
      <div 
        v-if="showPreview" 
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999] p-4"
        @click.self="closePreview"
      >
        <div class="bg-white rounded-lg shadow-xl w-full max-w-[95vw] max-h-[95vh] flex flex-col">
          <!-- 헤더 -->
          <div class="flex items-center justify-between p-4 border-b">
            <div>
              <h3 class="text-lg font-semibold">{{ previewTemplate?.name }}</h3>
              <p class="text-xs text-gray-500">{{ previewTemplate?.doc_type }}</p>
            </div>
            <button @click="closePreview" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <!-- 스크롤 가능한 뷰어 컨테이너 (100% 격리) -->
          <div class="flex-1 overflow-auto p-6 bg-gray-100">
            <div class="viewer-container">
              <!-- A4 크기 미리보기 영역 -->
              <div class="preview-sheet">
                <div class="preview-content">
                  <div class="text-center mb-6">
                    <h1 class="text-3xl font-bold">{{ previewTemplate?.name }}</h1>
                    <p class="text-sm text-gray-600 mt-2">{{ previewTemplate?.description }}</p>
                  </div>
                  
                  <div class="space-y-4 text-sm">
                    <div class="border border-gray-300 p-4 rounded">
                      <p class="font-medium mb-2">템플릿 정보</p>
                      <ul class="list-disc list-inside space-y-1 text-gray-700">
                        <li>문서 유형: {{ previewTemplate?.doc_type }}</li>
                        <li>템플릿 ID: {{ previewTemplate?.id }}</li>
                        <li>설명: {{ previewTemplate?.description }}</li>
                      </ul>
                    </div>

                    <div class="border border-gray-300 p-4 rounded bg-blue-50">
                      <p class="font-medium mb-2">사용 방법</p>
                      <ol class="list-decimal list-inside space-y-1 text-gray-700">
                        <li>이 템플릿을 선택하여 서류를 작성하세요</li>
                        <li>필요한 정보를 입력하고 저장합니다</li>
                        <li>나의 서류함에서 언제든지 다운로드할 수 있습니다</li>
                      </ol>
                    </div>

                    <div class="border border-gray-300 p-4 rounded">
                      <p class="font-medium mb-2">템플릿 미리보기</p>
                      <div class="bg-white p-6 rounded border-2 border-dashed border-gray-300 min-h-[200px]">
                        <p class="text-center text-gray-500 italic">
                          실제 서류 작성 시 이 영역에 내용이 표시됩니다.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 하단 버튼 -->
          <div class="p-4 border-t bg-gray-50 flex justify-end gap-2">
            <button 
              @click="closePreview" 
              class="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
            >
              닫기
            </button>
            <button 
              class="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700"
              @click="useTemplate"
            >
              이 템플릿 사용하기
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchTemplates, type DocumentTemplate } from '../api'

const templates = ref<DocumentTemplate[]>([])
const loading = ref(true)
const showPreview = ref(false)
const previewTemplate = ref<DocumentTemplate | null>(null)

onMounted(async () => {
  try {
    loading.value = true
    templates.value = await fetchTemplates()
  } catch (e: any) {
    console.error('템플릿 가져오기 실패', e?.response?.data || e)
    alert('템플릿을 로드하지 못했습니다.')
  } finally {
    loading.value = false
  }
})

function openPreview(template: DocumentTemplate) {
  previewTemplate.value = template
  showPreview.value = true
}

function closePreview() {
  showPreview.value = false
  previewTemplate.value = null
}

function useTemplate() {
  if (!previewTemplate.value) return
  // 템플릿 사용 로직 (추후 구현 가능)
  alert(`"${previewTemplate.value.name}" 템플릿을 사용합니다.`)
  closePreview()
}
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
