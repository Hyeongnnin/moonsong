<template>
  <div class="min-h-screen bg-gray-50">
    <TopNav />

    <div class="max-w-7xl mx-auto px-4 py-4">
      <div class="flex gap-6">
        <!-- Left Sidebar: static, always visible -->
        <aside class="w-64 hidden lg:block">
          <LeftSidebar />
        </aside>

        <!-- Main content column -->
        <div class="flex-1 min-h-[70vh] bg-transparent">
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

        <!-- Right sidebar placeholder (kept fixed) -->
        <aside class="w-72 hidden xl:block">
          <RightSidebar />
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineAsyncComponent, onMounted } from 'vue'
import TopNav from './TopNav.vue'
import LeftSidebar from './LeftSidebar.vue'
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

// 컴포넌트 마운트 시 Job 데이터 초기화
onMounted(async () => {
  try {
    await initializeJobs()
  } catch (err) {
    console.error('Failed to initialize jobs:', err)
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
</style>
