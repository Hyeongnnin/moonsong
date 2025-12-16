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
      <!-- 알바 업적 요약 카드 (NEW) - 항상 표시 -->
      <div class="mb-6">
        <UserAchievementCard ref="achievementCardRef" :activeJob="activeJob" />
      </div>

      <!-- 주휴수당 카드 - 항상 표시 -->
      <div class="mb-6">
        <HolidayPayCard ref="holidayPayCardRef" :activeJob="activeJob" />
      </div>

      <!-- 퇴직금 카드 - 항상 표시 -->
      <div class="mb-8">
        <RetirementPayCard :activeJob="activeJob" />
      </div>

      <!-- 근로조건 평가 카드 -->
      <EvaluationCard />

      <!-- JobSelector 모달 컴포넌트 -->
      <JobSelector ref="jobSelectorRef" />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useJob } from '../stores/jobStore'
import { useLabor, type MonthlySummary } from '../composables/useLabor'
import JobSelector from './JobSelector.vue'
import EvaluationCard from './EvaluationCard.vue'
import HolidayPayCard from './HolidayPayCard.vue'
import RetirementPayCard from './RetirementPayCard.vue'
import UserAchievementCard from './UserAchievementCard.vue'
import { useUser } from '../stores/userStore'

const router = useRouter()
const { activeJob } = useJob()
const { fetchMonthlySummary } = useLabor()

const { user, fetchMe } = useUser()

const jobSelectorRef = ref<InstanceType<typeof JobSelector> | null>(null)
const holidayPayCardRef = ref<InstanceType<typeof HolidayPayCard> | null>(null)
const achievementCardRef = ref<InstanceType<typeof UserAchievementCard> | null>(null)
// jobSummary is no longer needed for the main stats, but keeping it if needed for other parts (though we removed the UI)
// Actually we can remove loadJobSummary for the stats part if we fully replace it.
// user requested "Sidebar has only Holiday Pay Card".
// So we can remove jobSummary logic if it's not used elsewhere.
// But let's keep it safe or remove it if unused.
// "최종적으로 사이드바는 '주휴수당 카드' 하나만 보이도록 구성해주세요" -> Yes.
// So we don't need jobSummary for the old cards anymore.

const userName = computed(() => user.nickname || user.username || '사용자')
const userRole = computed(() => user.role || '알바생')
const userInitial = computed(() => (user.nickname || user.username || '사용자').charAt(0))
const userAvatar = computed(() => user.avatar)

onMounted(async () => {
  try { await fetchMe() } catch(e) { /* ignore */ }
  // loadJobSummary() -> Not needed if we remove the old cards
  window.addEventListener('labor-updated', handleLaborUpdate)
})

onUnmounted(() => {
  window.removeEventListener('labor-updated', handleLaborUpdate)
})

function handleLaborUpdate() {
  if (holidayPayCardRef.value) {
    holidayPayCardRef.value.refresh()
  }
  if (achievementCardRef.value) {
    achievementCardRef.value.refresh()
  }
}

// activeJob이 변경되면 HolidayPayCard는 내부 watch로 자동 업데이트됨.
// 하지만 명시적으로 refresh를 호출해줄 수도 있음.

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
