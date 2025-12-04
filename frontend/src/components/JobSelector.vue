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
          <div class="flex items-center gap-2">
            <button
              v-if="viewMode === 'list'"
              @click.stop="showCreate"
              class="px-3 py-1 text-sm bg-brand-600 text-white rounded-lg hover:opacity-95 transition">
              알바 추가하기
            </button>
            <button
              @click="closeModal"
              class="p-1 text-gray-500 hover:text-gray-700 hover:bg-white/50 rounded-lg transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Job List or Create Form -->
        <div class="max-h-96 overflow-y-auto">
          <div v-if="viewMode === 'create'">
            <CreateJobForm @saved="onCreated" @cancel="showList" />
          </div>
          <div v-else>
            <div v-if="loading" class="p-8 text-center">
              <p class="text-gray-600">로딩 중...</p>
            </div>
            
            <div v-else-if="jobs.length === 0" class="p-8 text-center">
              <p class="text-gray-600">등록된 알바가 없습니다.</p>
            </div>
            
            <div v-else class="p-4 space-y-2">
              <div
                v-for="job in jobs"
                :key="job.id"
                class="w-full rounded-lg border border-gray-200 transition-all duration-200"
                :class="isJobSelected(job.id) ? 'bg-brand-50 border-brand-300 shadow-md' : 'bg-white hover:bg-gray-50 hover:border-gray-300'">

                <!-- Use a full-height flex row and center items vertically -->
                <div class="flex items-center justify-between">
                  <!-- Left: job info (clickable area) -->
                  <div class="flex-1 min-w-0 p-4 cursor-pointer" @click="selectJob(job)">
                    <div class="flex items-center gap-2 mb-1">
                      <p class="text-sm font-semibold text-gray-900 truncate">
                        {{ job.workplace_name }}
                      </p>
                      <span v-if="isJobSelected(job.id)" class="flex-shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-brand-600">
                        <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                        </svg>
                      </span>
                      <span v-else-if="!job.is_current" class="flex-shrink-0 text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                        비활성
                      </span>
                    </div>

                    <p class="text-xs text-gray-600 truncate mb-2">
                      {{ job.workplace_address }}
                    </p>

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

                  <!-- Right: delete button vertically centered -->
                  <div class="flex items-center pr-4">
                    <button
                      @click.stop="handleDelete(job)"
                      class="text-sm text-white bg-[#DE5D35] px-3 py-1 rounded hover:opacity-90 transition-colors mr-2">
                      삭제
                    </button>
                  </div>

                </div>
              </div>
            </div>
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
import { apiClient } from '../api'
import CreateJobForm from './CreateJobForm.vue'

const { jobs: storeJobs, activeJobId, setActiveJob, loading, fetchJobs, deleteJob } = useJob()

const isOpen = ref(false)
const viewMode = ref<'list' | 'create'>('list')

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

// 모드 전환: 목록 보기
function showList() {
  viewMode.value = 'list'
}

// 모드 전환: 생성 폼 보기
function showCreate() {
  viewMode.value = 'create'
}

// 새 알바 생성 후 처리
async function onCreated(created: Job) {
  // Ensure store has latest
  try {
    await fetchJobs()
  } catch (e) {}
  setActiveJob(created.id)
  viewMode.value = 'list'
}

async function handleDelete(job: Job) {
  if (!confirm('정말 삭제하시겠습니까?')) return

  const endpoint = `/labor/employees/${job.id}/`
  const fullUrl = (apiClient.defaults.baseURL || '') + endpoint
  // Read current access token for debugging purposes
  let token = null
  try { token = localStorage.getItem('access') } catch(e) { token = null }

  console.log('Job delete request', { url: fullUrl, method: 'DELETE', jobId: job.id, tokenPreview: token ? (token.split('.')?.[0] ? 'JWT(...)' : 'token') : null })

  try {
    const res = await apiClient.delete(endpoint)
    console.log('Delete response', res.status, res.data)

    // Update client-side store immediately
    deleteJob(job.id)

    // If deleted job was active, pick another or clear
    if (activeJobId.value === job.id) {
      const remaining = jobs.value.filter((j: Job) => j.id !== job.id)
      if (remaining.length > 0) {
        setActiveJob(remaining[0].id)
      } else {
        try { localStorage.removeItem('activeJobId') } catch {}
        // setActiveJob expects a number; pass null via any to clear
        setActiveJob(null as any)
      }
    }

    // Optional: close modal if no jobs left
    // if (jobs.value.length === 0) closeModal()
  } catch (err: any) {
    console.error('Failed to delete job', err)
    // Show detailed server error if available
    const serverErr = err?.response?.data ? err.response.data : err?.message || 'Unknown error'
    alert('삭제에 실패했습니다: ' + JSON.stringify(serverErr))
  }
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
