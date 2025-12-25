<template>
  <div class="h-screen bg-gray-50 flex flex-col overflow-hidden">
    <TopNav />

    <!-- Entire content area -->
    <main class="flex-1 min-h-0 w-full flex flex-col overflow-hidden">
      <!-- Centered container -->
      <div class="flex-1 min-h-0 w-full max-w-[1600px] mx-auto px-4 py-4">
        <!-- Grid: left sidebar + main + right sidebar -->
        <div class="grid h-full items-stretch" style="grid-template-columns: 180px 1fr 360px; gap: 20px;">

          <!-- Left Sidebar - Section Navigation -->
          <aside class="flex flex-col gap-2 h-full overflow-y-auto pr-1 custom-scrollbar">
            <button
              v-for="(section, index) in sections"
              :key="section.id"
              @click="activeSection = index"
              class="px-4 py-3 text-sm font-medium text-left rounded-lg transition-all duration-200 whitespace-nowrap"
              :class="activeSection === index
                ? 'bg-brand-600 text-white shadow-md'
                : 'text-gray-700 hover:bg-brand-50 hover:text-brand-600'">
              {{ section.label }}
            </button>
          </aside>

          <!-- Main column -->
          <div class="flex flex-col h-full min-h-0 overflow-hidden">
            <!-- Welcome Message -->
            <div class="mb-4 px-4 py-3 bg-gradient-to-r from-brand-50 to-blue-50 rounded-lg border border-brand-100">
              <h2 class="text-lg font-semibold text-gray-800">
                <span class="text-brand-600">{{ userName }}</span>님 환영합니다!
              </h2>
            </div>

            <!-- Content Container (The Unified White Card) -->
            <div class="relative flex-1 min-h-0 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
              <!-- Arrow buttons -->
              <button
                class="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white/95 shadow-xl flex items-center justify-center hover:bg-white hover:scale-110 transition-all duration-200 text-gray-700 font-bold text-lg border border-gray-100"
                :class="{ 'opacity-30 pointer-events-none': activeSection === 0 }"
                @click="prevSection"
                aria-label="Previous Section"
              >
                ‹
              </button>

              <button
                class="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white/95 shadow-xl flex items-center justify-center hover:bg-white hover:scale-110 transition-all duration-200 text-gray-700 font-bold text-lg border border-gray-100"
                :class="{ 'opacity-30 pointer-events-none': activeSection === sections.length - 1 }"
                @click="nextSection"
                aria-label="Next Section"
              >
                ›
              </button>

              <!-- Sliding content track -->
              <div
                class="h-full flex transition-transform duration-500 cubic-bezier(0.4, 0, 0.2, 1)"
                :style="{ transform: `translateX(-${activeSection * 100}%)` }">

                <!-- Section 0: 근로관리 (LaborDashboard) -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto p-8 custom-scrollbar">
                  <ErrorBoundary>
                    <LaborDashboard />
                  </ErrorBoundary>
                </section>

                <!-- Section 1: 근로진단 -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto p-8 custom-scrollbar">
                  <LaborDiagnosisSection />
                </section>

                <!-- Section 2: AI상담 -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto p-8 custom-scrollbar">
                  <AiConsultSection />
                </section>

                <!-- Section 3: 근로정보 수정 -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto p-8 custom-scrollbar">
                  <LaborEditSection />
                </section>

                <!-- Section 4: 근로서류 -->
                <section class="flex-shrink-0 w-full h-full overflow-y-auto p-8 custom-scrollbar">
                  <DocumentsSection />
                </section>
              </div>
            </div>
          </div>

          <!-- Right sidebar column -->
          <aside class="hidden lg:block h-full overflow-y-auto pr-1 custom-scrollbar">
            <RightSidebar />
          </aside>

        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent, onMounted, watch, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import TopNav from './TopNav.vue'
import RightSidebar from './RightSidebar.vue'
import { useJob } from '../stores/jobStore'
import { useUser } from '../stores/userStore'
import ErrorBoundary from './ErrorBoundary.vue'

// Import section components
const LaborDashboard = defineAsyncComponent(() => import('./DashboardContent.vue'))
const AiConsultSection = defineAsyncComponent(() => import('../pages/AiConsult.vue'))
const LaborEditSection = defineAsyncComponent(() => import('../pages/LaborEdit.vue'))
const DocumentsSection = defineAsyncComponent(() => import('../pages/Documents.vue'))
const LaborDiagnosisSection = defineAsyncComponent(() => import('../pages/LaborDiagnosis.vue'))

// Section definitions
const sections = [
  { id: 'labor', label: '내 알바 관리' },
  { id: 'diagnosis', label: '알바 근로진단' },
  { id: 'ai-consult', label: 'AI 알바상담' },
  { id: 'profile-edit', label: '알바 근로정보 수정' },
  { id: 'documents', label: '알바서류' },
]

// Active section state (0-4)
const activeSection = ref(0)

const { initialize: initializeJobs } = useJob()
const { user } = useUser()
const route = useRoute()

// Computed property for user name
const userName = computed(() => user.nickname || user.username || '사용자')


// 컴포넌트 마운트 시 Job 데이터 초기화 및 URL 쿼리 파라미터 확인
function handleGoSection(ev: CustomEvent<string>) {
  const id = ev.detail
  const sectionIndex = sections.findIndex(s => s.id === id)
  if (sectionIndex !== -1) {
    activeSection.value = sectionIndex
  }
}

onMounted(async () => {
  // Lock body scroll for the dashboard layout
  document.documentElement.style.height = '100%'
  document.body.style.height = '100%'
  document.body.style.overflow = 'hidden'

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
  // 전역 섹션 전환 이벤트 리스너 등록 (같은 URL 내에서 강제 전환용)
  window.addEventListener('go-section', handleGoSection as EventListener)
})

// URL 쿼리 파라미터 변경 감지 (실시간 섹션 전환)
watch(() => route.query.section, (newSection) => {
  const sectionParam = newSection as string | undefined; // Ensure type is string | undefined
  if (sectionParam) {
    const sectionIndex = sections.findIndex(s => s.id === sectionParam);
    if (sectionIndex !== -1) {
      activeSection.value = sectionIndex;
    }
  } else {
    // If section query param is removed, reset to default or first section
    activeSection.value = 0; 
  }
}, { immediate: true }); // immediate: true to run the watcher immediately on component mount

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

onUnmounted(() => {
  // Restore body scroll when leaving dashboard
  document.documentElement.style.height = ''
  document.body.style.height = ''
  document.body.style.overflow = ''

  window.removeEventListener('go-section', handleGoSection as EventListener)
})
</script>

<style scoped>
/* Smooth scroll for content sections */
section {
  scroll-behavior: smooth;
}

/* content track height */
.flex-shrink-0 {
  flex-shrink: 0;
}

/* Responsive: 작은 화면에서는 한 열로 쌓음 */
@media (max-width: 1024px) {
  .mx-auto.w-full.max-w-\[1320px\].px-4 { padding-left: 16px; padding-right: 16px; }
  /* Grid 내부에서 sidebars 숨김 및 main full width */
  .mx-auto > .grid { 
    display: block; 
  }
  .mx-auto > .grid > aside { 
    display: none !important; 
  }
}
</style>
