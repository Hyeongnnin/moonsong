<template>
  <div class="min-h-screen bg-gray-50">
    <TopNav />

    <!-- Full width section with centered two-column group -->
    <div class="w-full px-0 py-4">
      <!-- Centered container that groups main + right sidebar; constrains overall width and centers it -->
      <!-- max-w를 1200 → 1320으로 늘려 메인 컨텐츠를 약 10% 넓게 -->
      <div class="mx-auto w-full max-w-[1320px] px-4">
        <!-- Grid: main (left) + sidebar (right). main : sidebar = 2fr : 1fr -->
        <!-- gap을 48 → 40으로 살짝 줄여 가운데 영역이 좀 더 넓어 보이게 -->
        <div class="grid items-start" style="grid-template-columns: 2fr 360px; gap: 40px;">

          <!-- Main column (탭 및 슬라이더) -->
          <div class="min-h-[70vh]">
            <!-- Section Tabs (근로관리 / AI상담 / 근로정보 수정 / 근로서류) -->
            <div class="flex gap-2 mb-4 border-b border-gray-200 pb-2 overflow-x-auto">
              <button
                v-for="(section, index) in sections"
                :key="section.id"
                @click="activeSection = index"
                class="px-4 py-2 text-sm font-medium whitespace-nowrap rounded-t-lg transition-all duration-200"
                :class="activeSection === index
                  ? 'text-brand-600 bg-brand-50 border-b-2 border-brand-600 -mb-[2px]'
                  : 'text-gray-600 hover:text-brand-600 hover:bg-brand-50'">
                {{ section.label }}
              </button>
            </div>

            <!-- Content Slider with slide animation -->
            <div class="relative h-[calc(100vh-200px)] overflow-hidden bg-transparent">
              <!-- Arrow buttons -->
              <button
                class="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white/90 shadow flex items-center justify-center hover:bg-white hover:shadow-md transition-all duration-200 text-gray-700 font-bold text-lg"
                :class="{ 'opacity-40 pointer-events-none': activeSection === 0 }"
                @click="prevSection"
              >
                ‹
              </button>

              <button
                class="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white/90 shadow flex items-center justify-center hover:bg-white hover:shadow-md transition-all duration-200 text-gray-700 font-bold text-lg"
                :class="{ 'opacity-40 pointer-events-none': activeSection === sections.length - 1 }"
                @click="nextSection"
              >
                ›
              </button>

              <!-- Sliding content track -->
              <div
                class="h-full flex transition-transform duration-300 ease-out"
                :style="{ transform: `translateX(-${activeSection * 100}%)` }">

                <!-- Section 0: 근로관리 (LaborDashboard) -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto">
                  <ErrorBoundary>
                    <LaborDashboard />
                  </ErrorBoundary>
                </section>

                <!-- Section 1: AI상담 -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto">
                  <AiConsultSection />
                </section>

                <!-- Section 2: 근로정보 수정 -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto">
                  <LaborEditSection />
                </section>

                <!-- Section 3: 근로서류 -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto">
                  <DocumentsSection />
                </section>
              </div>
            </div>
          </div>

          <!-- Right sidebar column: 이제 중앙 그룹 내부에 포함되어 있어 화면에 더 안쪽으로 배치됩니다 -->
          <aside class="hidden lg:block">
            <RightSidebar />
          </aside>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import TopNav from './TopNav.vue'
import RightSidebar from './RightSidebar.vue'
import { useJob } from '../stores/jobStore'
import ErrorBoundary from './ErrorBoundary.vue'

// Import section components
const LaborDashboard = defineAsyncComponent(() => import('./DashboardContent.vue'))
const AiConsultSection = defineAsyncComponent(() => import('../pages/AiConsult.vue'))
const LaborEditSection = defineAsyncComponent(() => import('../pages/LaborEdit.vue'))
const DocumentsSection = defineAsyncComponent(() => import('../pages/Documents.vue'))

// Section definitions
const sections = [
  { id: 'labor', label: '근로관리' },
  { id: 'ai-consult', label: 'AI상담' },
  { id: 'profile-edit', label: '근로정보 수정' },
  { id: 'documents', label: '근로서류' },
]

// Active section state (0-3)
const activeSection = ref(0)

const { initialize: initializeJobs } = useJob()
const route = useRoute()

// 컴포넌트 마운트 시 Job 데이터 초기화 및 URL 쿼리 파라미터 확인
onMounted(async () => {
  try {
    await initializeJobs()
    
    // URL에 section 쿼리 파라미터가 있으면 해당 섹션으로 이동
    const sectionParam = route.query.section as string
    if (sectionParam) {
      const sectionIndex = sections.findIndex(s => s.id === sectionParam)
      if (sectionIndex !== -1) {
        activeSection.value = sectionIndex
      }
    }
  } catch (err) {
    console.error('Failed to initialize jobs:', err)
  }
})

// URL 쿼리 파라미터 변경 감지 (실시간 섹션 전환)
watch(() => route.query.section, (newSection) => {
  if (newSection) {
    const sectionIndex = sections.findIndex(s => s.id === newSection)
    if (sectionIndex !== -1) {
      activeSection.value = sectionIndex
    }
  }
})

// Navigation functions
function prevSection() {
  if (activeSection.value > 0) {
    activeSection.value--
  }
}

function nextSection() {
  if (activeSection.value < sections.length - 1) {
    activeSection.value++
  }
}
</script>

<style scoped>
/* Smooth scroll for content sections */
section {
  scroll-behavior: smooth;
}

/* Responsive: 작은 화면에서는 한 열로 쌓음 */
@media (max-width: 1024px) {
  .mx-auto.w-full.max-w-\[1200px\].px-4 { padding-left: 16px; padding-right: 16px; }
  /* Grid 내부에서 aside 숨김 및 main full width */
  .mx-auto > .grid { display: block; }
  .mx-auto > .grid > aside { display: none !important; }
}
</style>
