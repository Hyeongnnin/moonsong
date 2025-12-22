<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-gray-900">근로진단 요약</h3>
    </div>

    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="text-center py-6">
      <div class="text-3xl mb-2">📋</div>
      <p class="text-sm text-gray-600 mb-1">근로정보를 입력해주세요</p>
      <p class="text-xs text-gray-400">근로 상태를 진단할 수 있습니다</p>
    </div>

    <!-- 근로정보가 있을 때 -->
    <div v-else>
      <div v-if="loading" class="text-center text-gray-500 py-6 text-sm">
        <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600 mx-auto mb-2"></div>
        진단 중...
      </div>

      <div v-else-if="error" class="text-center py-4">
        <p class="text-xs text-red-500">진단 정보를 불러올 수 없습니다</p>
      </div>

      <div v-else class="space-y-3">
        <!-- 주휴수당 요건 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex items-center gap-2">
            <span class="text-lg">{{ diagnosis.holidayPay.icon }}</span>
            <span class="text-sm text-gray-700">주휴수당 요건</span>
          </div>
          <div class="flex items-center gap-1">
            <span :class="diagnosis.holidayPay.statusClass" class="text-sm font-medium">
              {{ diagnosis.holidayPay.statusText }}
            </span>
          </div>
        </div>

        <!-- 퇴직금 요건 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex items-center gap-2">
            <span class="text-lg">{{ diagnosis.retirement.icon }}</span>
            <span class="text-sm text-gray-700">퇴직금 요건</span>
          </div>
          <div class="flex items-center gap-1">
            <span :class="diagnosis.retirement.statusClass" class="text-sm font-medium">
              {{ diagnosis.retirement.statusText }}
            </span>
          </div>
        </div>

        <!-- 근로시간 준수 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex items-center gap-2">
            <span class="text-lg">{{ diagnosis.workHours.icon }}</span>
            <span class="text-sm text-gray-700">주 52시간 준수</span>
          </div>
          <div class="flex items-center gap-1">
            <span :class="diagnosis.workHours.statusClass" class="text-sm font-medium">
              {{ diagnosis.workHours.statusText }}
            </span>
          </div>
        </div>

        <!-- 필수 휴식시간 -->
        <div class="flex items-center justify-between py-2">
          <div class="flex items-center gap-2">
            <span class="text-lg">{{ diagnosis.breakTime.icon }}</span>
            <span class="text-sm text-gray-700">필수 휴식시간</span>
          </div>
          <div class="flex items-center gap-1">
            <span :class="diagnosis.breakTime.statusClass" class="text-sm font-medium">
              {{ diagnosis.breakTime.statusText }}
            </span>
          </div>
        </div>

        <!-- 자세히 보기 버튼 -->
        <button
          @click="goToDiagnosisDetail"
          class="w-full mt-4 py-2 px-4 bg-brand-50 hover:bg-brand-100 text-brand-700 text-sm font-medium rounded-lg border border-brand-200 transition-colors duration-200 flex items-center justify-center gap-2"
        >
          <span>자세히 알아보기</span>
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { apiClient } from '../api';
import type { Job } from '../stores/jobStore';

const props = defineProps<{
  activeJob: Job | null;
}>();

const router = useRouter();
const loading = ref(false);
const error = ref(false);

const diagnosisData = ref({
  holidayPayEligible: false,
  weeklyHours: 0,
  retirementEligible: false,
  workDays: 0,
  maxWeeklyHours: 0,
  exceedsLimit: false,
  // 휴식시간 관련
  dailyWorkHours: 0,
  providedBreakMinutes: 0,
  requiredBreakMinutes: 0,
  breakTimeStatus: 'unknown' as 'pass' | 'fail' | 'unknown'
});

// 진단 결과 computed
const diagnosis = computed(() => {
  return {
    holidayPay: {
      icon: diagnosisData.value.holidayPayEligible ? '✅' : '❌',
      statusText: diagnosisData.value.holidayPayEligible ? '충족' : '미충족',
      statusClass: diagnosisData.value.holidayPayEligible ? 'text-green-600' : 'text-red-600'
    },
    retirement: {
      icon: diagnosisData.value.retirementEligible ? '✅' : '❌',
      statusText: diagnosisData.value.retirementEligible ? '충족' : '미충족',
      statusClass: diagnosisData.value.retirementEligible ? 'text-green-600' : 'text-red-600'
    },
    workHours: {
      icon: !diagnosisData.value.exceedsLimit ? '✅' : '⚠️',
      statusText: !diagnosisData.value.exceedsLimit ? '준수' : '초과 우려',
      statusClass: !diagnosisData.value.exceedsLimit ? 'text-green-600' : 'text-yellow-600'
    },
    breakTime: {
      icon: diagnosisData.value.breakTimeStatus === 'pass' ? '✅' : 
            diagnosisData.value.breakTimeStatus === 'fail' ? '❌' : '🟡',
      statusText: diagnosisData.value.breakTimeStatus === 'pass' ? '충족' : 
                  diagnosisData.value.breakTimeStatus === 'fail' 
                    ? `미충족 (필요 ${diagnosisData.value.requiredBreakMinutes}분 / 제공 ${diagnosisData.value.providedBreakMinutes}분)`
                    : '판단 불가',
      statusClass: diagnosisData.value.breakTimeStatus === 'pass' ? 'text-green-600' : 
                   diagnosisData.value.breakTimeStatus === 'fail' ? 'text-red-600' : 'text-yellow-600'
    }
  };
});

const fetchDiagnosisData = async () => {
  if (!props.activeJob) return;

  loading.value = true;
  error.value = false;

  try {
    // 주휴수당 정보 조회
    const holidayPayRes = await apiClient.get(`/labor/employees/${props.activeJob.id}/holiday-pay/`);
    const holidayPayData = holidayPayRes.data;

    // 퇴직금 정보 조회 (임시로 근속 기간 기반 판단)
    const startDate = new Date(props.activeJob.start_date);
    const today = new Date();
    const workDays = Math.floor((today.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    const retirementEligible = workDays >= 365; // 1년 이상 근무

    // 주간 근무시간 확인
    const weeklyHours = holidayPayData.actual_worked_hours || holidayPayData.weekly_hours || 0;
    const exceedsLimit = weeklyHours > 52;

    // 휴식시간 판단 로직
    // 최근 근로 기록에서 평균 근로시간과 휴게시간 계산
    let dailyWorkHours = 0;
    let providedBreakMinutes = 0;
    let requiredBreakMinutes = 0;
    let breakTimeStatus: 'pass' | 'fail' | 'unknown' = 'unknown';

    try {
      // 최근 7일간의 근로 기록 조회
      const endDate = new Date().toISOString().split('T')[0];
      const startDateStr = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      
      const workRecordsRes = await apiClient.get(
        `/labor/employees/${props.activeJob.id}/work-records/?start=${startDateStr}&end=${endDate}`
      );
      const workRecords = workRecordsRes.data;

      if (workRecords && workRecords.length > 0) {
        // 최근 근무일의 데이터 사용 (첫 번째 레코드)
        const recentRecord = workRecords[0];
        
        if (recentRecord.start_time && recentRecord.end_time) {
          // 근로시간 계산 (시간 단위)
          const start = new Date(`2000-01-01T${recentRecord.start_time}`);
          const end = new Date(`2000-01-01T${recentRecord.end_time}`);
          dailyWorkHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);

          // 제공된 휴게시간 (분 단위)
          providedBreakMinutes = recentRecord.break_minutes || 0;

          // 법정 필요 휴게시간 계산
          if (dailyWorkHours < 4) {
            requiredBreakMinutes = 0; // 4시간 미만은 의무 없음
            breakTimeStatus = 'pass';
          } else if (dailyWorkHours >= 4 && dailyWorkHours < 8) {
            requiredBreakMinutes = 30; // 4~8시간은 30분 이상
            breakTimeStatus = providedBreakMinutes >= 30 ? 'pass' : 'fail';
          } else {
            requiredBreakMinutes = 60; // 8시간 이상은 60분 이상
            breakTimeStatus = providedBreakMinutes >= 60 ? 'pass' : 'fail';
          }
        }
      }
    } catch (breakErr) {
      console.warn('휴식시간 데이터 조회 실패:', breakErr);
      breakTimeStatus = 'unknown';
    }

    diagnosisData.value = {
      holidayPayEligible: holidayPayData.amount > 0,
      weeklyHours,
      retirementEligible,
      workDays,
      maxWeeklyHours: weeklyHours,
      exceedsLimit,
      dailyWorkHours,
      providedBreakMinutes,
      requiredBreakMinutes,
      breakTimeStatus
    };
  } catch (err) {
    console.error('근로진단 데이터 조회 실패:', err);
    error.value = true;
  } finally {
    loading.value = false;
  }
};

const goToDiagnosisDetail = () => {
  router.push('/dashboard?section=diagnosis');
};

const refresh = () => {
  fetchDiagnosisData();
};

// activeJob 변경 시 자동으로 데이터 갱신
watch(() => props.activeJob, (newJob) => {
  if (newJob) {
    fetchDiagnosisData();
  }
}, { immediate: true });

onMounted(() => {
  if (props.activeJob) {
    fetchDiagnosisData();
  }
});

// 외부에서 refresh 호출 가능하도록 expose
defineExpose({
  refresh
});
</script>

<style scoped>
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
