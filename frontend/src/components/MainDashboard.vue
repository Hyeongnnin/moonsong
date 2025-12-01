<template>
  <div class="flex h-screen bg-gray-50">
    <!-- 좌측 사이드바 -->
    <LeftSidebar />

    <!-- 메인 콘텐츠 -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- 상단 헤더 -->
      <DashboardHeader />

      <!-- 스크롤 가능한 콘텐츠 -->
      <div class="flex-1 overflow-y-auto">
        <div class="flex">
          <!-- 중앙 콘텐츠 -->
          <div class="flex-1 p-6">
            <div class="max-w-4xl mx-auto">
              <div class="grid lg:grid-cols-3 gap-6">
                <!-- 왼쪽: 캘린더 (2/3 너비) -->
                <div class="lg:col-span-2">
                  <WorkCalendar />
                </div>

                <!-- 오른쪽: 요약 정보 (1/3 너비) -->
                <div class="lg:col-span-1">
                  <WorkSummaryCard />
                </div>
              </div>

              <!-- 추가 섹션 -->
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

          <!-- 우측 사이드바 -->
          <RightSidebar />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import DashboardHeader from './DashboardHeader.vue';
import LeftSidebar from './LeftSidebar.vue';
import RightSidebar from './RightSidebar.vue';
import WorkCalendar from './WorkCalendar.vue';
import WorkSummaryCard from './WorkSummaryCard.vue';
</script>

<style scoped>
</style>
