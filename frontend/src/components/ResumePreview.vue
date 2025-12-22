<template>
  <div class="resume-preview-isolated" ref="resumeRef">
    <!-- A4 용지 크기로 격리된 미리보기 -->
    <div class="resume-page">
      <!-- 헤더: 사진 + 제목 -->
      <div class="resume-header">
        <div class="photo-box">
          <img v-if="photoUrl" :src="photoUrl" alt="증명사진" />
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
            <td>{{ form.name || '\u00A0' }}</td>
            <th>생년월일</th>
            <td>{{ form.birthDate || '\u00A0' }}</td>
          </tr>
          <tr>
            <th>주소</th>
            <td colspan="3">{{ form.address || '\u00A0' }}</td>
          </tr>
          <tr>
            <th>연락처</th>
            <td>{{ form.phone || '\u00A0' }}</td>
            <th>이메일</th>
            <td>{{ form.email || '\u00A0' }}</td>
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
          <div class="signature-line">작성일: {{ form.writtenDate || '\u00A0' }}</div>
          <div class="signature-line">
            <span>작성자: {{ form.name || '\u00A0' }}</span>
            <span class="signature-underline">{{ form.signature || '\u00A0' }}</span>
            <span>(서명)</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface CareerRow {
  date: string
  content: string
  note: string
}

interface Props {
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
}

const props = defineProps<Props>()
const resumeRef = ref<HTMLElement | null>(null)

// 최소 10줄 표시
const displayCareers = computed(() => {
  const careers = props.form.careers || []
  const minRows = 10
  const filled = [...careers]
  while (filled.length < minRows) {
    filled.push({ date: '', content: '', note: '' })
  }
  return filled
})

defineExpose({
  resumeRef
})
</script>

<style scoped>
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
   테이블 스타일
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

/* 반응형 (화면에 맞춰 축소) */
@media (max-width: 900px) {
  .resume-preview-isolated {
    width: 100%;
    min-height: auto;
    transform: scale(0.9);
    transform-origin: top center;
  }
}
</style>
