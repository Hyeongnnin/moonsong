<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 전체 페이지 컨테이너 -->
    <div class="w-full">
      <!-- 상단 헤더 유지 -->
      <DashboardHeader />

      <!-- 3-Column Grid: left gutter / center main / right sidebar -->
      <main class="dashboard-grid px-4 py-6">
        <!-- Left: 빈 여백 컬럼 (화면이 작으면 숨김) -->
        <div class="left-gutter hidden lg:block" aria-hidden="true"></div>

        <!-- Center: 메인 콘텐츠 (캘린더 등) -->
        <div class="main-column">
          <div class="mx-auto max-w-3xl">
            <!-- 캘린더와 통계 카드 (콘텐츠 기반 높이) -->
            <div class="grid lg:grid-cols-3 gap-6 mb-6">
              <!-- 왼쪽: 캘린더 (2/3 너비) -->
              <div class="lg:col-span-2">
                <WorkCalendar 
                  :activeJob="activeJob" 
                  @statsUpdated="handleStatsUpdated"
                  @monthChanged="handleMonthChanged" 
                />
              </div>

              <!-- 오른쪽: 선택된 달 통계 (1/3 너비) -->
              <div class="lg:col-span-1">
                <WorkSummaryCard 
                  ref="workSummaryCardRef" 
                  :activeJob="activeJob" 
                  :displayYear="selectedYear"
                  :displayMonth="selectedMonth"
                />
              </div>
            </div>

            <!-- 추가 섹션 아래 배치 유지 -->
            <div class="mt-6">
              <div class="grid md:grid-cols-2 gap-6">
                <!-- 편의기능 -->
                <div class="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4">편의기능</h3>
                  <div class="space-y-3">
                    <button class="w-full text-left p-4 bg-gray-50 rounded-lg hover:bg-brand-50 hover:border-brand-200 border border-gray-200 transition-colors">
                      <p class="text-sm font-semibold text-gray-900">근로계약서 관리</p>
                      <p class="text-xs text-gray-500 mt-1">계약서 업로드 및 확인</p>
                    </button>
                    <button class="w-full text-left p-4 bg-gray-50 rounded-lg hover:bg-brand-50 hover:border-brand-200 border border-gray-200 transition-colors">
                      <p class="text-sm font-semibold text-gray-900">급여 명세서</p>
                      <p class="text-xs text-gray-500 mt-1">월별 급여 내역 조회</p>
                    </button>
                    <button class="w-full text-left p-4 bg-gray-50 rounded-lg hover:bg-brand-50 hover:border-brand-200 border border-gray-200 transition-colors">
                      <p class="text-sm font-semibold text-gray-900">진단 결과</p>
                      <p class="text-xs text-gray-500 mt-1">근로환경 진단 결과 보기</p>
                    </button>
                  </div>
                </div>

                <!-- 고객센터 -->
                <div class="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 class="text-lg font-semibold text-gray-900 mb-4">고객센터</h3>
                  <div class="space-y-3 mb-4">
                    <div class="border-b border-gray-200 pb-3">
                      <p class="text-sm font-medium text-gray-900">근로시간은 어떻게 기록하나요?</p>
                      <p class="text-xs text-gray-500 mt-2">매일 출퇴근 시간을 기록하시면 자동으로 계산됩니다.</p>
                    </div>
                    <div class="border-b border-gray-200 pb-3">
                      <p class="text-sm font-medium text-gray-900">상담 신청은 어떻게 하나요?</p>
                      <p class="text-xs text-gray-500 mt-2">상담 신청 페이지에서 원하는 주제를 선택하면 됩니다.</p>
                    </div>
                  </div>
                  <button class="w-full bg-brand-600 text-white py-2 rounded-lg font-medium hover:bg-brand-700 transition-colors text-sm">
                    더 많은 FAQ 보기
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: 계정 및 통계 사이드바 -->
        <aside class="right-column hidden lg:block">
          <RightSidebar />
        </aside>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useJob } from '../stores/jobStore';
import DashboardHeader from './DashboardHeader.vue';
import LeftSidebar from './LeftSidebar.vue';
import RightSidebar from './RightSidebar.vue';
import WorkCalendar from './WorkCalendar.vue';
import WorkSummaryCard from './WorkSummaryCard.vue';

const { activeJob } = useJob();
const workSummaryCardRef = ref<InstanceType<typeof WorkSummaryCard> | null>(null);

// 캘린더에서 선택된 연/월을 추적
const selectedYear = ref<number | undefined>(undefined);
const selectedMonth = ref<number | undefined>(undefined);

// 캘린더에서 월이 변경될 때 호출
function handleMonthChanged(data: { year: number; month: number }) {
  console.log('[MainDashboard] Month changed to:', data.year, data.month);
  selectedYear.value = data.year;
  selectedMonth.value = data.month;
}

// 캘린더에서 통계 업데이트 이벤트를 받으면 WorkSummaryCard 갱신
// 이제 통계는 선택된 월(selectedYear/selectedMonth) 기준으로 표시됨
function handleStatsUpdated() {
  if (workSummaryCardRef.value) {
    workSummaryCardRef.value.updateStats();
  }
}
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1.4fr 0.8fr;
  column-gap: 24px;
  align-items: start;
}

.main-column {
  width: 100%;
}

.right-column {
  width: 100%;
}

/* 반응형 */
@media (max-width: 1024px) {
  .dashboard-grid {
    display: block;
  }
  .left-gutter, .right-column {
    display: none !important;
  }
  .main-column {
    padding: 0 16px;
  }
}
</style>
