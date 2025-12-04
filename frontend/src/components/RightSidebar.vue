<template>
  <aside class="hidden xl:block bg-white border-l border-gray-200 h-screen sticky top-0 overflow-y-auto w-80">
    <div class="p-6">
      <!-- 프로필 섹션 -->
      <div class="mb-8 pb-8 border-b border-gray-200">
        <div class="flex items-center gap-4 mb-4">
          <div class="w-12 h-12 rounded-full overflow-hidden bg-gray-100">
            <img v-if="userAvatar" :src="userAvatar" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center text-white font-bold text-lg bg-gradient-to-br from-brand-400 to-brand-600">{{ userInitial }}</div>
          </div>
          <div>
            <p class="font-semibold text-gray-900">{{ userName }}</p>
            <p class="text-xs text-gray-500">{{ userRole }}</p>
          </div>
        </div>
        <button 
          @click="navigateToEditProfile"
          class="w-full text-sm text-brand-600 hover:text-brand-700 font-medium py-2 px-4 rounded-lg border border-brand-200 hover:bg-brand-50 transition-colors duration-200">
          프로필 수정
        </button>

        <!-- 알바 선택 버튼 -->
        <button 
          @click="openJobSelector"
          class="w-full mt-3 text-sm text-brand-600 hover:text-brand-700 font-medium py-2 px-4 rounded-lg border border-brand-200 hover:bg-brand-50 transition-colors duration-200 flex items-center justify-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          다른 알바 보기
        </button>

        <!-- 현재 선택된 알바 정보 -->
        <div v-if="activeJob" class="mt-4 p-3 bg-brand-50 rounded-lg border border-brand-100">
          <p class="text-xs text-brand-700 font-medium mb-1">현재 선택된 알바</p>
          <p class="text-sm font-semibold text-gray-900">{{ activeJob.workplace_name }}</p>
          <p class="text-xs text-gray-600 mt-1">{{ activeJob.workplace_address }}</p>
        </div>
      </div>

      <!-- 주요 통계 (API 기반) -->
      <div class="mb-8">
        <h3 class="text-sm font-semibold text-gray-900 mb-4">이번 달 통계</h3>
        
        <div v-if="statLoading" class="text-center text-gray-600 text-sm py-4">
          로딩 중...
        </div>

        <div v-else-if="jobSummary" class="space-y-3">
          <div class="bg-brand-50 rounded-lg p-4 border border-brand-100">
            <p class="text-xs text-gray-600 mb-1">총 근로시간</p>
            <p class="text-2xl font-bold text-brand-600">{{ jobSummary.total_hours }}시간</p>
            <p class="text-xs text-gray-500 mt-1">근무일: {{ jobSummary.total_days }}일</p>
          </div>

          <div class="bg-green-50 rounded-lg p-4 border border-green-100">
            <p class="text-xs text-gray-600 mb-1">총 급여 예상액</p>
            <p class="text-2xl font-bold text-green-600">{{ formatSalary(jobSummary.estimated_salary) }}</p>
            <p class="text-xs text-gray-500 mt-1">시급 {{ formatWage(activeJob?.hourly_rate || 0) }} 기준</p>
          </div>

          <div class="bg-purple-50 rounded-lg p-4 border border-purple-100">
            <p class="text-xs text-gray-600 mb-1">이번 주 근로시간</p>
            <p class="text-2xl font-bold text-purple-600">{{ currentWeekHours }}시간</p>
            <p class="text-xs text-gray-500 mt-1">예상 급여: {{ formatSalary(currentWeekPay) }}</p>
          </div>
        </div>

        <div v-else class="text-center text-gray-600 text-sm py-4">
          통계 데이터를 불러올 수 없습니다.
        </div>
      </div>

      <!-- 근로조건 평가 카드 -->
      <EvaluationCard />

      <!-- 최근 상담 -->
      <div class="mb-8 pb-8 border-b border-gray-200 mt-10">
        <h3 class="text-sm font-semibold text-gray-900 mb-4">최근 상담</h3>
        <div class="space-y-3">
          <div class="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow cursor-pointer">
            <div class="flex items-start justify-between mb-2">
              <p class="text-sm font-medium text-gray-900">주휴수당 계산 방법</p>
              <span class="text-xs px-2 py-1 rounded-full bg-brand-100 text-brand-700">해결</span>
            </div>
            <p class="text-xs text-gray-500">2025.11.20</p>
          </div>

          <div class="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow cursor-pointer">
            <div class="flex items-start justify-between mb-2">
              <p class="text-sm font-medium text-gray-900">야근 수당 청구</p>
              <span class="text-xs px-2 py-1 rounded-full bg-yellow-100 text-yellow-700">진행중</span>
            </div>
            <p class="text-xs text-gray-500">2025.11.18</p>
          </div>
        </div>
      </div>

      <!-- 빠른 링크 -->
      <div>
        <h3 class="text-sm font-semibold text-gray-900 mb-4">도움말</h3>
        <div class="space-y-2">
          <button class="w-full text-left text-sm text-gray-600 hover:text-gray-900 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors duration-200">
            🎓 이용 가이드
          </button>
          <button class="w-full text-left text-sm text-gray-600 hover:text-gray-900 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors duration-200">
            ❓ 자주 묻는 질문
          </button>
          <button class="w-full text-left text-sm text-gray-600 hover:text-gray-900 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors duration-200">
            💬 1:1 문의
          </button>
          <button class="w-full text-left text-sm text-gray-600 hover:text-gray-900 py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors duration-200">
            ⚙️ 설정
          </button>
        </div>
      </div>

      <!-- JobSelector 모달 컴포넌트 -->
      <JobSelector ref="jobSelectorRef" />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useJob, type Job } from '../stores/jobStore'
import { useLabor, type JobSummary } from '../composables/useLabor'
import JobSelector from './JobSelector.vue'
import EvaluationCard from './EvaluationCard.vue'
import { useUser } from '../stores/userStore'

const router = useRouter()
const { activeJob } = useJob()
const { fetchJobSummary, getMonthString } = useLabor()

const { user, fetchMe } = useUser()

const jobSelectorRef = ref<InstanceType<typeof JobSelector> | null>(null)
const jobSummary = ref<JobSummary | null>(null)
const statLoading = ref(false)

const userName = computed(() => user.first_name || user.username || '사용자')
const userRole = computed(() => user.role || '알바생')
const userInitial = computed(() => (user.first_name || user.username || '사용자').charAt(0))
const userAvatar = computed(() => user.avatar)

onMounted(async () => {
  try { await fetchMe() } catch(e) { /* ignore */ }
  loadJobSummary()
})

/**
 * Job 변경 시 해당 Job의 월 요약 정보 조회
 */
async function loadJobSummary() {
  if (!activeJob.value) return

  statLoading.value = true
  try {
    const month = getMonthString()
    const summary = await fetchJobSummary(activeJob.value.id, month)
    jobSummary.value = summary
  } catch (err) {
    console.error('Failed to fetch job summary:', err)
    jobSummary.value = null
  } finally {
    statLoading.value = false
  }
}

/**
 * 현재 주(week_stats의 마지막)의 시간과 급여
 */
const currentWeekHours = computed(() => {
  if (!jobSummary.value || jobSummary.value.week_stats.length === 0) {
    return 0
  }
  const lastWeek = jobSummary.value.week_stats[jobSummary.value.week_stats.length - 1]
  return lastWeek.hours.toFixed(1)
})

const currentWeekPay = computed(() => {
  if (!jobSummary.value || jobSummary.value.week_stats.length === 0) {
    return 0
  }
  const lastWeek = jobSummary.value.week_stats[jobSummary.value.week_stats.length - 1]
  return lastWeek.pay
})

// activeJob이 변경되면 통계 다시 로드
watch(
  () => activeJob.value?.id,
  () => {
    loadJobSummary()
  },
)

// 컴포넌트 마운트 시 초기 데이터 로드
onMounted(() => {
  loadJobSummary()
})

// 함수: 금액 포맷팅
function formatSalary(salary: number): string {
  return salary.toLocaleString('ko-KR') + '원'
}

function formatWage(wage: number): string {
  return wage.toLocaleString('ko-KR') + '원'
}

// 함수: 프로필 수정 페이지 이동
function navigateToEditProfile() {
  router.push('/edit-profile')
}

// 함수: 알바 선택 모달 열기
function openJobSelector() {
  jobSelectorRef.value?.openModal()
}

defineExpose({
  navigateToEditProfile,
  openJobSelector,
})
</script>

<style scoped>
</style>
