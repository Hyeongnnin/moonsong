/**
 * useLabor Composable
 * 
 * 근로 관련 API를 처리하는 Composable
 * - Job(알바) 목록 조회
 * - Job별 월 요약 정보
 * - Job별 기간별 근로 기록
 */

import { ref, computed } from 'vue'
import { apiClient } from '../api'

// ===== Types =====
export interface WorkRecord {
  id: number
  work_date: string
  time_in: string | null
  time_out: string | null
  break_minutes: number
  total_hours: number
  is_overtime: boolean
  is_night: boolean
  is_holiday: boolean
}

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
  work_records?: WorkRecord[]
}

export interface WeekStat {
  start_date: string
  end_date: string
  hours: number
  pay: number
}

export interface JobSummary {
  job_id: number
  job_name: string
  workplace_name: string
  hourly_wage: number
  month: string
  total_hours: number
  total_days: number
  estimated_salary: number
  week_stats: WeekStat[]
}

export interface LaborStats {
  totalHours: number
  totalDays: number
  estimatedSalary: number
  weekHours: number
  weekPay: number
  todayHours: number
}

export interface EvaluationResult {
  min_wage_ok: boolean
  min_wage_required: number
  weekly_holiday_pay: number
  annual_leave_days: number
  severance_estimate: number
  warnings: string[]
}

export interface AnnualLeaveResult {
  total: number
  used: number
  available: number
}

// ===== State =====
const jobs = ref<Job[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

// ===== Composable =====
export function useLabor(accessToken?: string) {
  /**
   * 사용자의 모든 Job(알바) 목록 조회
   */
  async function fetchJobs(): Promise<Job[]> {
    loading.value = true
    error.value = null

    try {
      const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
      const response = await apiClient.get<Job[]>('/labor/jobs/', { headers })
      jobs.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '알바 목록 조회 실패'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 특정 Job의 월별 요약 정보 조회
   * @param jobId - Job ID
   * @param month - 조회 월 (YYYY-MM 형식)
   */
  async function fetchJobSummary(jobId: number, month: string): Promise<JobSummary> {
    loading.value = true
    error.value = null

    try {
      const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
      const response = await apiClient.get<JobSummary>(`/labor/jobs/${jobId}/summary/`, {
        params: { month },
        headers,
      })
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '요약 정보 조회 실패'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 특정 Job의 노동법 평가 결과 조회
   * API 엔드포인트: GET /labor/jobs/<id>/evaluation/
   */
  async function fetchEvaluation(jobId: number): Promise<EvaluationResult> {
    loading.value = true
    error.value = null
    try {
      const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
      const response = await apiClient.get<EvaluationResult>(`/labor/jobs/${jobId}/evaluation/`, { headers })
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '평가 결과 조회 실패'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 연차휴가 요약 조회
   * API: GET /labor/jobs/<id>/annual-leave/
   */
  async function fetchAnnualLeave(jobId: number): Promise<AnnualLeaveResult> {
    loading.value = true
    error.value = null
    try {
      const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
      const response = await apiClient.get<AnnualLeaveResult>(`/labor/jobs/${jobId}/annual-leave/`, { headers })
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '연차 정보 조회 실패'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 특정 Job의 기간별 근로 기록 조회
   * @param jobId - Job ID
   * @param startDate - 시작 날짜 (YYYY-MM-DD)
   * @param endDate - 종료 날짜 (YYYY-MM-DD)
   */
  async function fetchWorkRecords(
    jobId: number,
    startDate: string,
    endDate: string
  ): Promise<WorkRecord[]> {
    loading.value = true
    error.value = null

    try {
      const headers = accessToken ? { Authorization: `Bearer ${accessToken}` } : {}
      const response = await apiClient.get<WorkRecord[]>(`/labor/jobs/${jobId}/work-records/`, {
        params: { start: startDate, end: endDate },
        headers,
      })
      return response.data
    } catch (err: any) {
      error.value = err.response?.data?.detail || '근로 기록 조회 실패'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 현재 월의 통계 계산
   * @param summary - Job 요약 정보
   * @param jobData - Job 데이터 (hourly_wage 등)
   */
  function calculateStats(summary: JobSummary, jobData: Job): LaborStats {
    // 이번 주 통계 (가장 최근 주)
    const weekStats = summary.week_stats[summary.week_stats.length - 1] || {
      hours: 0,
      pay: 0,
    }

    // 오늘 근로시간 (현재 월의 WorkRecord에서 가져올 수도 있음)
    const today = new Date().toISOString().split('T')[0]
    const todayRecord = summary.week_stats
      .flatMap((week) => [])
      .find((r) => r === today) || null

    return {
      totalHours: summary.total_hours,
      totalDays: summary.total_days,
      estimatedSalary: summary.estimated_salary,
      weekHours: weekStats.hours,
      weekPay: weekStats.pay,
      todayHours: todayRecord ? 8 : 0, // 임시값
    }
  }

  /**
   * 날짜 범위에 대한 월 형식 문자열 반환 (YYYY-MM)
   */
  function getMonthString(date?: Date): string {
    const d = date || new Date()
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    return `${year}-${month}`
  }

  /**
   * 날짜 범위에 대한 시작/종료 날짜 문자열 반환 (YYYY-MM-DD)
   */
  function getDateRange(startDate?: Date, endDate?: Date): { start: string; end: string } {
    const start = startDate || new Date(new Date().getFullYear(), new Date().getMonth(), 1)
    const end = endDate || new Date()

    const formatDate = (d: Date) => {
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return `${y}-${m}-${day}`
    }

    return {
      start: formatDate(start),
      end: formatDate(end),
    }
  }

  return {
    // State
    jobs: computed(() => jobs.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),

    // Methods
    fetchJobs,
    fetchJobSummary,
    fetchWorkRecords,
    fetchEvaluation,
    fetchAnnualLeave,
    calculateStats,
    getMonthString,
    getDateRange,
  }
}
