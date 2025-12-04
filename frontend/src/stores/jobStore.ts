import { ref, computed } from 'vue'
import { apiClient } from '../api'

export interface Job {
  id: number
  workplace_name: string
  workplace_address: string
  industry: string
  employment_type: string
  start_date: string
  end_date: string | null
  hourly_rate: number
  weekly_hours: number
  daily_hours: number
  has_paid_weekly_holiday: boolean
  is_severance_eligible: boolean
  is_current: boolean
}

// 전역 상태 (싱글톤)
const jobs = ref<Job[]>([])
const activeJobId = ref<number | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Composable: useJob
export function useJob(accessToken?: string) {
  // 계산: 현재 선택된 알바 객체
  const activeJob = computed(() => {
    if (!activeJobId.value) return null
    return jobs.value.find((job) => job.id === activeJobId.value) || null
  })

  // 계산: 활성 상태의 알바들만
  const activeJobs = computed(() => {
    return jobs.value.filter((job) => job.is_current)
  })

  /**
   * API에서 Job 목록 조회
   */
  async function fetchJobs() {
    loading.value = true
    error.value = null

    try {
      const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
      const response = await apiClient.get<Job[]>('/labor/jobs/', { headers })
      jobs.value = response.data

      // activeJobId 복원 (로컬스토리지 또는 첫 번째 활성 job)
      const savedJobId = localStorage.getItem('activeJobId')
      if (savedJobId) {
        const jobId = parseInt(savedJobId, 10)
        if (jobs.value.some((j) => j.id === jobId)) {
          activeJobId.value = jobId
        } else {
          // 저장된 job이 없으면 첫 번째 job으로 설정
          activeJobId.value = jobs.value[0]?.id || null
        }
      } else {
        // 처음이면 첫 번째 job으로 설정
        activeJobId.value = jobs.value[0]?.id || null
      }

      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Job 목록 조회 실패'
      console.error('Error fetching jobs:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 선택된 알바 변경
   */
  function setActiveJob(jobId: number) {
    const job = jobs.value.find((j) => j.id === jobId)
    if (job) {
      activeJobId.value = jobId
      // 로컬스토리지에 저장 (선택 정보 유지)
      localStorage.setItem('activeJobId', jobId.toString())
    }
  }

  /**
   * 액션: 알바 추가 (향후 사용)
   */
  function addJob(job: Job) {
    jobs.value.push(job)
  }

  /**
   * 액션: 알바 수정 (향후 사용)
   */
  function updateJob(jobId: number, updatedJob: Partial<Job>) {
    const index = jobs.value.findIndex((j) => j.id === jobId)
    if (index !== -1) {
      jobs.value[index] = { ...jobs.value[index], ...updatedJob }
    }
  }

  /**
   * 액션: 알바 삭제 (향후 사용)
   */
  function deleteJob(jobId: number) {
    jobs.value = jobs.value.filter((j) => j.id !== jobId)
    // 삭제된 알바가 활성 상태였다면 첫 번째 알바로 변경
    if (activeJobId.value === jobId && jobs.value.length > 0) {
      activeJobId.value = jobs.value[0].id
    }
  }

  /**
   * 액션: 알바 생성 (서버에 POST)
   */
  async function createJob(payload: Partial<Job>) {
    try {
      const response = await apiClient.post('/labor/employees/', payload)
      const created: Job = response.data
      // Add to front of list
      jobs.value.unshift(created)
      // Set as active
      activeJobId.value = created.id
      try { localStorage.setItem('activeJobId', String(created.id)) } catch (e) {}
      return created
    } catch (err: any) {
      console.error('Failed to create job:', err)
      throw err
    }
  }

  /**
   * 초기화 (앱 시작 시 호출)
   */
  async function initialize() {
    await fetchJobs()
  }

  return {
    // 상태
    jobs: computed(() => jobs.value),
    activeJobId: computed(() => activeJobId.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),

    // 계산
    activeJob,
    activeJobs,

    // 액션
    fetchJobs,
    setActiveJob,
    addJob,
    updateJob,
    deleteJob,
    initialize,
    createJob,
  }
}
