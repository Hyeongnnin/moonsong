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
            <div class="resume-preview-isolated" ref="resumeRef">
              <!-- A4 용지 크기로 격리된 미리보기 -->
              <div class="resume-page">
                <!-- 헤더: 사진 + 제목 -->
                <div class="resume-header">
                  <div class="photo-box">
                    <img v-if="data.photoUrl" :src="data.photoUrl" alt="증명사진" />
                    <span v-else class="photo-placeholder">사진</span>
                  </div>
                  <div class="title-box">
                    <h1>이 력 서</h1>
                  </div>
                </div>

                <!-- 기본 정보 테이블 -->
                <table class="info-table">
                  <tbody>
                    <tr>
                      <th>성명</th>
                      <td>{{ data.form.name || '\u00A0' }}</td>
                      <th>생년월일</th>
                      <td>{{ data.form.birthDate || '\u00A0' }}</td>
                    </tr>
                    <tr>
                      <th>주소</th>
                      <td colspan="3">{{ data.form.address || '\u00A0' }}</td>
                    </tr>
                    <tr>
                      <th>연락처</th>
                      <td>{{ data.form.phone || '\u00A0' }}</td>
                      <th>이메일</th>
                      <td>{{ data.form.email || '\u00A0' }}</td>
                    </tr>
                  </tbody>
                </table>

                <!-- 학력/경력 테이블 -->
                <table class="career-table">
                  <thead>
                    <tr>
                      <th class="col-date">년 월 일</th>
                      <th class="col-content">학력 및 경력사항</th>
                      <th class="col-note">발령청(비고)</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(career, idx) in displayCareers" :key="idx">
                      <td class="text-center">{{ career.date || '\u00A0' }}</td>
                      <td>{{ career.content || '\u00A0' }}</td>
                      <td>{{ career.note || '\u00A0' }}</td>
                    </tr>
                  </tbody>
                </table>

                <!-- 서명 섹션 -->
                <div class="signature-section">
                  <p class="signature-statement">위 기재 사항은 사실과 틀림없음을 확인합니다.</p>
                  <div class="signature-box">
                    <div class="signature-line">작성일: {{ data.form.writtenDate || '\u00A0' }}</div>
                    <div class="signature-line">
                      <span>작성자: {{ data.form.name || '\u00A0' }}</span>
                      <span class="signature-underline">{{ data.form.signature || '\u00A0' }}</span>
                      <span>(서명)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

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
const resumeRef = ref<HTMLElement | null>(null)

// 최소 10줄 표시
const displayCareers = computed(() => {
  const careers = props.data.form.careers || []
  const minRows = 10
  const filled = [...careers]
  while (filled.length < minRows) {
    filled.push({ date: '', content: '', note: '' })
  }
  return filled
})

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
  if (!resumeRef.value) {
    // 아직 렌더링 전이면 잠시 대기
    await new Promise(resolve => setTimeout(resolve, 100))
  }
  
  try {
    pdfGenerating.value = true
    
    const element = resumeRef.value
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
   격리된 이력서 미리보기 (A4 고정)
   ======================================== */
.resume-preview-isolated {
  width: 210mm;
  min-height: 297mm;
  background: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
  margin: 0 auto;
}

.resume-page {
  padding: 14mm;
  font-family: 'Pretendard', -apple-system, sans-serif;
  font-size: 11px;
  line-height: 1.5;
  color: #000;
}

/* ========================================
   이력서 헤더 (사진 + 제목)
   ======================================== */
.resume-header {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
}

.photo-box {
  width: 32mm;
  height: 40mm;
  border: 1px solid #000;
  flex-shrink: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
}

.photo-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-placeholder {
  font-size: 10px;
  color: #9ca3af;
}

.title-box {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-box h1 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 8px;
  margin: 0;
}

/* ========================================
   테이블 스타일 (스코프드)
   ======================================== */
.info-table,
.career-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
  font-size: 11px;
  table-layout: fixed;
}

.info-table th,
.info-table td,
.career-table th,
.career-table td {
  border: 1px solid #000;
  padding: 8px 10px;
  text-align: left;
  vertical-align: middle;
}

.info-table th,
.career-table th {
  background: #f9fafb;
  font-weight: 600;
  text-align: center;
}

.info-table th {
  width: 20%;
}

.career-table .col-date {
  width: 18%;
}

.career-table .col-content {
  width: 52%;
}

.career-table .col-note {
  width: 30%;
}

.career-table tbody td {
  vertical-align: top;
  min-height: 30px;
}

/* ========================================
   서명 섹션
   ======================================== */
.signature-section {
  margin-top: 40px;
  font-size: 11px;
}

.signature-statement {
  text-align: center;
  margin-bottom: 20px;
  font-weight: 500;
}

.signature-box {
  text-align: right;
  padding-right: 20px;
}

.signature-line {
  margin-bottom: 10px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.signature-underline {
  display: inline-block;
  min-width: 70px;
  border-bottom: 1px solid #000;
  text-align: center;
  padding: 0 8px;
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
  
  .resume-preview-isolated {
    width: 100%;
    min-height: auto;
    transform: scale(0.85);
    transform-origin: top center;
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
  
  .resume-preview-isolated {
    box-shadow: none;
    page-break-after: always;
  }
}
</style>
