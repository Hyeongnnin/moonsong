<template>
  <!-- Modal Overlay -->
  <Teleport to="body">
    <div 
      v-if="isOpen"
      class="fixed inset-0 bg-black/40 z-40 backdrop-blur-sm transition-opacity duration-200"
      @click="closeModal">
    </div>
  </Teleport>

  <!-- Modal Content -->
  <Teleport to="body">
    <div 
      v-if="isOpen"
      class="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 w-full max-w-md animate-in fade-in zoom-in duration-200">
      
      <div class="bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden">
        
        <!-- Header -->
        <div class="bg-gradient-to-r from-brand-50 to-brand-100/50 border-b border-brand-200 px-6 py-4 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-gray-900">내 알바 목록</h2>
          <button
            @click="closeModal"
            class="p-1 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-lg transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Job List -->
        <div class="max-h-96 overflow-y-auto">
          <div v-if="loading" class="p-8 text-center">
            <p class="text-gray-600">로딩 중...</p>
          </div>
          
          <div v-else-if="jobs.length === 0" class="p-8 text-center">
            <p class="text-gray-600">등록된 알바가 없습니다.</p>
          </div>
          
          <div v-else class="p-4 space-y-2">
            <button
              v-for="job in jobs"
              :key="job.id"
              @click="selectJob(job)"
              class="w-full text-left p-4 rounded-lg border border-gray-200 transition-all duration-200"
              :class="isJobSelected(job.id)
                ? 'bg-brand-50 border-brand-300 shadow-md'
                : 'bg-white hover:bg-gray-50 hover:border-gray-300'">
              
              <div class="flex items-start justify-between gap-3">
                <div class="flex-1 min-w-0">
                  <!-- 알바 이름 -->
                  <div class="flex items-center gap-2 mb-1">
                    <p class="text-sm font-semibold text-gray-900 truncate">
                      {{ job.workplace_name }}
                    </p>
                    <!-- 현재 선택 표시 -->
                    <span v-if="isJobSelected(job.id)" class="flex-shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-brand-600">
                      <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                      </svg>
                    </span>
                    <!-- 비활성 표시 -->
                    <span v-else-if="!job.is_current" class="flex-shrink-0 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                      비활성
                    </span>
                  </div>

                  <!-- 직장 정보 -->
                  <p class="text-xs text-gray-600 truncate mb-2">
                    {{ job.workplace_address }}
                  </p>

                  <!-- 시급 및 주당 시간 -->
                  <div class="flex items-center gap-3 text-xs text-gray-500">
                    <span class="inline-flex items-center gap-1">
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      시급 {{ formatWage(job.hourly_rate) }}
                    </span>
                    <span class="inline-flex items-center gap-1">
                      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 2m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {{ job.weekly_hours }}시간/주
                    </span>
                  </div>
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-gray-200 bg-gray-50 px-6 py-3 flex items-center justify-end gap-2">
          <button
            @click="closeModal"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
            닫기
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useJob, type Job } from '../stores/jobStore'

const { jobs: storeJobs, activeJobId, setActiveJob, loading } = useJob()

const isOpen = ref(false)

// Store의 jobs를 computed로 감싸기
const jobs = computed(() => storeJobs.value)

// 함수: 모달 열기
function openModal() {
  isOpen.value = true
}

// 함수: 모달 닫기
function closeModal() {
  isOpen.value = false
}

// 함수: 모달 토글
function toggleModal() {
  isOpen.value = !isOpen.value
}

// 함수: 알바 선택
function selectJob(job: Job) {
  setActiveJob(job.id)
  closeModal()
}

// 함수: 알바 선택 여부 확인
function isJobSelected(jobId: number): boolean {
  return activeJobId.value === jobId
}

// 함수: 시급 포맷팅
function formatWage(wage: number): string {
  return wage.toLocaleString('ko-KR') + '원'
}

// 외부에서 접근 가능하도록 expose
defineExpose({
  openModal,
  closeModal,
  toggleModal,
})
</script>

<style scoped>
/* Teleport 애니메이션 */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes zoomIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.animate-in {
  animation: fadeIn 0.2s ease-out;
}

.fade-in {
  animation: fadeIn 0.2s ease-out;
}

.zoom-in {
  animation: zoomIn 0.2s ease-out;
}
</style>
