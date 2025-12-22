<template>
  <!-- 전체 화면 오버레이 - Teleport로 body에 직접 마운트 -->
  <Teleport to="body">
    <div class="modal-overlay" @click.self="handleClose">
      <!-- 모달 컨테이너 (완전 격리) -->
      <div class="modal-container">
        <!-- 헤더 -->
        <div class="modal-header">
          <h3 class="text-lg font-semibold">이력서 미리보기</h3>
          <div class="flex gap-2">
            <button @click="handleDownloadPdf" 
                    :disabled="pdfGenerating"
                    class="btn-primary">
              {{ pdfGenerating ? 'PDF 생성 중...' : 'PDF 다운로드' }}
            </button>
            <button @click="handleClose" 
                    class="btn-secondary">
              닫기
            </button>
          </div>
        </div>

        <!-- 미리보기 영역 -->
        <div class="modal-body">
          <!-- 로딩 -->
          <div v-if="loading" class="loading-state">
            <div class="spinner"></div>
            <div class="text-gray-500 mt-2">미리보기 생성 중...</div>
          </div>
          
          <!-- PDF iframe (PDF 생성 후 표시) -->
          <iframe v-else-if="pdfUrl" 
                  :src="pdfUrl" 
                  class="pdf-iframe"
                  title="이력서 미리보기">
          </iframe>
          
          <!-- HTML 미리보기 (폴백) -->
          <div v-else class="html-preview-container">
            <ResumePreview 
              ref="resumeComponent" 
              :form="data.form" 
              :photoUrl="data.photoUrl" 
            />
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import ResumePreview from './ResumePreview.vue'

interface CareerRow {
  date: string
  content: string
  note: string
}

interface Props {
  data: {
    form: {
      name: string
      birthDate: string
      address: string
      phone: string
      email: string
      writtenDate: string
      signature: string
      careers: CareerRow[]
    }
    photoUrl?: string
    downloadPdf?: boolean
  }
}

const props = defineProps<Props>()
const emit = defineEmits(['close'])

const loading = ref(false)
const pdfGenerating = ref(false)
const pdfUrl = ref('')
const resumeComponent = ref<InstanceType<typeof ResumePreview> | null>(null)

onMounted(async () => {
  // 자동 PDF 생성 요청이 있으면
  if (props.data.downloadPdf) {
    await handleDownloadPdf()
  }
})

onUnmounted(() => {
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
  }
})

async function handleDownloadPdf() {
  if (!resumeComponent.value?.resumeRef) {
    // 아직 렌더링 전이면 잠시 대기
    await new Promise(resolve => setTimeout(resolve, 200))
  }
  
  try {
    pdfGenerating.value = true
    
    const element = resumeComponent.value?.resumeRef
    if (!element) {
      throw new Error('미리보기 요소를 찾을 수 없습니다.')
    }
    
    // HTML을 Canvas로 변환
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff'
    })
    
    // Canvas를 PDF로 변환
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })
    
    const imgWidth = 210 // A4 width in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    
    pdf.addImage(imgData, 'PNG', 0, 0, imgWidth, imgHeight)
    
    // 다운로드
    const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    const filename = `이력서_${props.data.form.name || 'resume'}_${timestamp}.pdf`
    pdf.save(filename)
    
    // Blob URL 생성 (미리보기용, 선택사항)
    const blob = pdf.output('blob')
    if (pdfUrl.value) {
      URL.revokeObjectURL(pdfUrl.value)
    }
    pdfUrl.value = URL.createObjectURL(blob)
    
  } catch (error) {
    console.error('PDF 생성 실패:', error)
    alert('PDF 생성에 실패했습니다. 다시 시도해주세요.')
  } finally {
    pdfGenerating.value = false
  }
}

function handleClose() {
  emit('close')
}
</script>

<style scoped>
/* ========================================
   모달 오버레이 - body에 마운트
   ======================================== */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(2px);
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* ========================================
   모달 컨테이너 - 완전 격리
   ======================================== */
.modal-container {
  width: 90vw;
  max-width: 900px;
  height: 90vh;
  background: white;
  border-radius: 12px;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px); 
  }
  to { 
    opacity: 1;
    transform: translateY(0); 
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
  background: #fafafa;
}

.modal-body {
  flex: 1;
  overflow: auto;
  background: #f3f4f6;
  position: relative;
}

/* ========================================
   버튼 스타일
   ======================================== */
.btn-primary {
  padding: 8px 16px;
  font-size: 14px;
  background: #DE5D35;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #C64F2C;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 8px 16px;
  font-size: 14px;
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-secondary:hover {
  background: #f9fafb;
}

/* ========================================
   로딩 상태
   ======================================== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e5e7eb;
  border-top-color: #DE5D35;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ========================================
   PDF iframe - 완전 격리
   ======================================== */
.pdf-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

/* ========================================
   HTML 미리보기 컨테이너
   ======================================== */
.html-preview-container {
  width: 100%;
  min-height: 100%;
  padding: 24px;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

/* ========================================
   반응형 (모바일)
   ======================================== */
@media (max-width: 768px) {
  .modal-container {
    width: 100vw;
    height: 100vh;
    max-width: none;
    border-radius: 0;
  }
  
  .modal-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .modal-header > div {
    width: 100%;
    display: flex;
    gap: 8px;
  }
  
  .modal-header button {
    flex: 1;
  }
  
  .html-preview-container {
    padding: 12px;
  }
}

/* ========================================
   인쇄용 스타일
   ======================================== */
@media print {
  .modal-overlay {
    background: none;
  }
  
  .modal-header {
    display: none;
  }
  
  .modal-body {
    overflow: visible;
  }
}
</style>

