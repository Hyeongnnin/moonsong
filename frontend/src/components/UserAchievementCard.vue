<template>
  <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-200 p-5">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-base font-semibold text-gray-900">
        {{ userName }}님의 알바 업적
      </h3>
      <span class="text-2xl">🏆</span>
    </div>

    <!-- 근로정보가 없을 때 -->
    <div v-if="!activeJob" class="text-center py-8">
      <div class="text-4xl mb-3">📋</div>
      <p class="text-sm text-gray-600 font-medium mb-2">아직 근로정보가 없어요</p>
      <p class="text-xs text-gray-500 mb-4">근로정보를 입력하면<br/>자동으로 누적 통계가 계산됩니다</p>
      <button
        @click="navigateToJobCreate"
        class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        근로정보 입력하기
      </button>
    </div>

    <!-- 근로정보가 있을 때 (빈 상태 안내/데이터 표시) -->
    <div v-else>
      <!-- 빈 상태: 누적 데이터 전무 -->
      <div v-if="!hasAnyRecords" class="text-center py-8">
        <div class="text-4xl mb-3">🧮</div>
        <p class="text-sm text-gray-600 font-medium mb-2">아직 집계된 근로 기록이 없어요</p>
        <p class="text-xs text-gray-500 mb-4">근로정보를 설정하면 누적 업적이 표시됩니다</p>
        <button
          @click="navigateToJobCreate"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          근로정보 수정하러 가기
        </button>
      </div>

      <!-- 데이터가 있을 때 -->
      <div v-else class="space-y-3">
        <!-- 총 근로시간 -->
        <div class="bg-white bg-opacity-60 rounded-lg p-3 border border-blue-100">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-xl">⏱️</span>
              <div>
                <p class="text-xs text-gray-600 font-medium">총 근로시간</p>
                <p class="text-xs text-gray-500 mt-0.5">누적</p>
              </div>
            </div>
            <p class="text-lg font-bold text-blue-600">
              {{ totalHours.toFixed(1) }}<span class="text-sm font-normal text-gray-600">시간</span>
            </p>
          </div>
        </div>

        <!-- 총 누적 급여 (업적 합계) -->
        <div class="bg-indigo-600 rounded-lg p-4 text-white shadow-md">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="text-xl">🏆</span>
              <p class="text-xs font-bold uppercase tracking-wider opacity-90">업적 합계</p>
            </div>

          </div>
          <h4 class="text-2xl font-black mb-2">
            {{ formatCurrency(achievementTotal) }}
          </h4>

        </div>

        <!-- 근무 일수 -->
        <div class="bg-white bg-opacity-60 rounded-lg p-3 border border-blue-100">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-xl">📅</span>
              <div>
                <p class="text-xs text-gray-600 font-medium">총 근무 일수</p>
                <p class="text-xs text-gray-500 mt-0.5">누적</p>
              </div>
            </div>
            <p class="text-lg font-bold text-purple-600">
              {{ totalWorkDays }}<span class="text-sm font-normal text-gray-600">일</span>
            </p>
          </div>
        </div>
      </div>

      <!-- 업적 레벨 뱃지 -->
      <div class="mt-4 pt-4 border-t border-blue-200">
        <div class="flex items-center justify-center gap-2 mb-2">
          <span class="text-lg">{{ achievementBadge.icon }}</span>
          <span class="text-sm font-semibold" :class="achievementBadge.color">
            {{ achievementBadge.level }}
          </span>
        </div>
        
        <!-- 다음 등급까지 남은 시간 -->
        <div v-if="nextLevelInfo.hasNext" class="mt-3">
          <div class="flex items-center justify-between text-xs text-gray-600 mb-1">
            <span>{{ nextLevelInfo.nextLevel }}</span>
            <span class="font-semibold text-blue-600">{{ nextLevelInfo.remaining }}시간 남음</span>
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
            <div 
              class="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full transition-all duration-500"
              :style="{ width: nextLevelInfo.progress + '%' }"
            ></div>
          </div>
        </div>
        <div v-else class="mt-2 text-center">
          <p class="text-xs text-yellow-600 font-semibold">🎉 최고 등급 달성!</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import type { Job } from '../stores/jobStore';
import { apiClient } from '../api';
import { useUser } from '../stores/userStore';

interface Props {
  activeJob?: Job | null;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
});

const router = useRouter();
const route = useRoute();
const { user } = useUser();

const totalHours = ref(0);
const totalEarnings = ref(0);
const totalWorkDays = ref(0);
const totalConfirmedHolidayPay = ref(0);
const totalConfirmedNightPay = ref(0);
const achievementTotal = ref(0);
const hasAnyRecords = computed(() => totalHours.value > 0 || totalEarnings.value > 0 || totalWorkDays.value > 0);

const userName = computed(() => user.nickname || user.username || '사용자');

// 금액 포맷팅
const formatCurrency = (value: number) => {
  return value.toLocaleString('ko-KR') + '원';
};

// 업적 레벨 계산
const achievementBadge = computed(() => {
  const hours = totalHours.value;
  
  if (hours >= 500) {
    return { level: '전설의 알바생', icon: '👑', color: 'text-yellow-600' };
  } else if (hours >= 300) {
    return { level: '베테랑 알바생', icon: '⭐', color: 'text-purple-600' };
  } else if (hours >= 150) {
    return { level: '숙련 알바생', icon: '💪', color: 'text-blue-600' };
  } else if (hours >= 50) {
    return { level: '중급 알바생', icon: '🌱', color: 'text-green-600' };
  } else {
    return { level: '초보 알바생', icon: '🐣', color: 'text-gray-600' };
  }
});

// 다음 등급까지 남은 정보 계산
const nextLevelInfo = computed(() => {
  const hours = totalHours.value;
  
  const levels = [
    { threshold: 0, name: '초보 알바생' },
    { threshold: 50, name: '중급 알바생' },
    { threshold: 150, name: '숙련 알바생' },
    { threshold: 300, name: '베테랑 알바생' },
    { threshold: 500, name: '전설의 알바생' }
  ];
  
  // 현재 레벨 찾기
  let currentLevelIndex = 0;
  for (let i = levels.length - 1; i >= 0; i--) {
    if (hours >= levels[i].threshold) {
      currentLevelIndex = i;
      break;
    }
  }
  
  // 다음 레벨이 있는지 확인
  if (currentLevelIndex >= levels.length - 1) {
    return { hasNext: false, nextLevel: '', remaining: 0, progress: 100 };
  }
  
  const currentLevel = levels[currentLevelIndex];
  const nextLevel = levels[currentLevelIndex + 1];
  const remaining = nextLevel.threshold - hours;
  const progress = ((hours - currentLevel.threshold) / (nextLevel.threshold - currentLevel.threshold)) * 100;
  
  return {
    hasNext: true,
    nextLevel: `다음 등급: ${nextLevel.name}`,
    remaining: remaining.toFixed(1),
    progress: Math.min(100, Math.max(0, progress))
  };
});


// 근로정보 입력 페이지로 이동
function navigateToJobCreate() {
  // MainLayout의 "근로정보 수정" 탭으로 이동
  if (route.path === '/dashboard' && route.query.section === 'profile-edit') {
    window.dispatchEvent(new CustomEvent('go-section', { detail: 'profile-edit' }));
    return;
  }
  router.push('/dashboard?section=profile-edit').catch(() => {});
}

// 누적 데이터 로드
async function loadAchievementData() {
  const employeeId = props.activeJob?.id;
  if (!employeeId) {
    totalHours.value = 0;
    totalEarnings.value = 0;
    totalWorkDays.value = 0;
    return;
  }

  try {
    // 누적 통계 API 호출 (전체 기간)
    console.log(`[UserAchievementCard] 📡 API 호출: /labor/jobs/${employeeId}/cumulative-stats/`);
    const res = await apiClient.get(`/labor/jobs/${employeeId}/cumulative-stats/`);
    
    console.log('[UserAchievementCard] ✅ API 응답:', res.data);
    if (res.data?.records_debug) {
      console.log('[UserAchievementCard] 🧾 집계에 포함된 레코드 상세 (records_debug):');
      for (const r of res.data.records_debug) {
        console.log(`  #${r.id} ${r.date} in=${r.time_in} out=${r.time_out} break=${r.break_minutes} ▶ minutes=${r.daily_work_minutes}`);
      }
      console.log('[UserAchievementCard] 🧮 record_ids:', res.data.record_ids);
    }
    console.log('[UserAchievementCard] 📊 total_hours:', res.data.total_hours, typeof res.data.total_hours);
    console.log('[UserAchievementCard] 💰 total_earnings:', res.data.total_earnings, typeof res.data.total_earnings);
    console.log('[UserAchievementCard] 📅 total_work_days:', res.data.total_work_days, typeof res.data.total_work_days);
    
    totalHours.value = res.data.total_hours || 0;
    // total_earnings는 순수 근로(기본+야간+휴일 등)의 합계임.
    // 사용자가 UI에서 '근로급여'를 기본급 개념으로 보고 싶어한다면 분리가 필요하지만,
    // 현재는 total_earnings를 그대로 '근로급여'로 쓰고 있음.
    // 만약 '야간수당'을 별도로 + 표시하려면, total_earnings에서 야간수당을 빼거나
    // 아니면 그냥 total_earnings가 포함하고 있음을 인지해야 함.
    // 요청사항: "야간 수당 금액을 ... 밑에 띄워줄래? + 이렇게"
    // 이는 보통 "기본급 + 야간수당 + 주휴수당 = 총액" 구조를 원한다는 의미일 수 있음.
    // 그러나 API는 currently 'total_earnings'(전체 근로수당)만 줌.
    // --> 백엔드 api 응답에 'total_night_pay' 등이 있다면 좋겠지만, 없다면 계산해야 함.
    // 다행히 get_cumulative_stats_data에 보면 night_bonus 등이 계산되고는 있음.
    // 일단 API 응답에 extra_work_earnings 등으로 분리되어 있을 수 있음.
    // (이전 코드에서 regular_work_earnings, extra_work_earnings 등은 봤음)
    
    // 임시: total_earnings에는 야간수당이 포함되어 있음.
    // 별도 표기를 위해 API가 'total_night_pay'를 내려주도록 백엔드를 수정하거나
    // 여기서는 0으로 두고 백엔드 수정을 요청해야 함.
    // 하지만 이미 ViewSet을 수정할 수 있으므로, 
    // 여기서는 일단 있는 데이터 혹은 추후 추가될 필드를 매핑.
    
    totalEarnings.value = res.data.total_earnings || 0;
    totalWorkDays.value = res.data.total_work_days || 0;
    totalConfirmedHolidayPay.value = res.data.total_confirmed_holiday_pay || 0;
    totalConfirmedNightPay.value = res.data.total_night_pay || 0; // 백엔드에서 내려줘야 함
    achievementTotal.value = res.data.achievement_total || 0;
    
    console.log('[UserAchievementCard] ✅ 값 할당 완료:', {
      totalHours: totalHours.value,
      totalEarnings: totalEarnings.value,
      totalWorkDays: totalWorkDays.value,
      totalConfirmedHolidayPay: totalConfirmedHolidayPay.value,
      totalConfirmedNightPay: totalConfirmedNightPay.value,
      achievementTotal: achievementTotal.value
    });
  } catch (e) {
    console.error('[UserAchievementCard] Failed to load achievement data', e);
    
    // API가 없는 경우 폴백: 월별 통계로 추정
    try {
      const now = new Date();
      const startDate = new Date(props.activeJob?.start_date || now);
      let cumulativeHours = 0;
      let cumulativeEarnings = 0;
      let cumulativeDays = 0;
      
      // 시작 월부터 현재 월까지 반복
      const currentYear = now.getFullYear();
      const currentMonth = now.getMonth() + 1;
      const startYear = startDate.getFullYear();
      const startMonth = startDate.getMonth() + 1;
      
      for (let year = startYear; year <= currentYear; year++) {
        const monthStart = (year === startYear) ? startMonth : 1;
        const monthEnd = (year === currentYear) ? currentMonth : 12;
        
        for (let month = monthStart; month <= monthEnd; month++) {
          const monthStr = `${year}-${String(month).padStart(2, '0')}`;
          const monthRes = await apiClient.get(`/labor/jobs/${employeeId}/monthly-summary/`, {
            params: { month: monthStr }
          });
          
          cumulativeHours += monthRes.data.actual_total_hours || 0;
          cumulativeEarnings += monthRes.data.actual_estimated_salary || 0;
          cumulativeDays += monthRes.data.actual_work_days || 0;
        }
      }
      
      totalHours.value = cumulativeHours;
      totalEarnings.value = cumulativeEarnings;
      totalWorkDays.value = cumulativeDays;
      
      console.log('[UserAchievementCard] Fallback calculation completed');
    } catch (fallbackError) {
      console.error('[UserAchievementCard] Fallback calculation failed', fallbackError);
    }
  }
}

// activeJob 변경 시 데이터 다시 로드
watch(() => props.activeJob?.id, () => {
  if (props.activeJob) {
    loadAchievementData();
  }
}, { immediate: true });

// 외부에서 호출 가능하도록 expose
defineExpose({ refresh: loadAchievementData });

onMounted(() => {
  // 전역 이벤트 리스너 추가 (근로기록 변경 시 자동 갱신)
  window.addEventListener('labor-updated', loadAchievementData);
});
</script>

<style scoped>
/* 추가 스타일 필요시 */
</style>
