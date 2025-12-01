<template>
  <div class="min-h-screen bg-gray-50 pt-20">
    <!-- 네비게이션 탭 -->
    <div class="sticky top-20 bg-white border-b border-gray-200 z-40">
      <div class="flex overflow-x-auto scrollbar-hide">
        <button
          v-for="(tab, idx) in tabs"
          :key="idx"
          @click="currentTab = idx"
          :class="[
            'px-6 py-4 text-sm font-medium whitespace-nowrap transition-colors',
            currentTab === idx
              ? 'text-brand-600 border-b-2 border-brand-600'
              : 'text-gray-600 hover:text-gray-900',
          ]"
        >
          {{ tab }}
        </button>
      </div>
    </div>

    <!-- 스와이프 가능한 콘텐츠 영역 -->
    <div 
      class="overflow-hidden"
      @touchstart="handleTouchStart"
      @touchmove="handleTouchMove"
      @touchend="handleTouchEnd"
    >
      <div 
        class="flex transition-transform duration-300 ease-out"
        :style="{ transform: `translateX(-${currentTab * 100}%)` }"
      >
        <!-- 근로관리 탭 -->
        <div class="w-full flex-shrink-0 px-4 py-8">
          <div class="max-w-5xl mx-auto">
            <h2 class="text-2xl font-semibold text-gray-900 mb-6">근로 관리 · 근무시간</h2>
            <div class="space-y-6">
              <!-- 근로시간 캘린더 -->
              <div class="bg-white rounded-lg border border-gray-200 p-6">
                <div class="flex items-center justify-between mb-4">
                  <h3 class="text-lg font-semibold text-gray-900">2025년 11월</h3>
                  <div class="flex gap-2">
                    <button class="text-gray-600 hover:text-gray-900">◀</button>
                    <button class="text-gray-600 hover:text-gray-900">▶</button>
                  </div>
                </div>
                <div class="grid grid-cols-7 gap-2 mb-4">
                  <div v-for="day in ['일', '월', '화', '수', '목', '금', '토']" :key="day" class="text-center text-xs font-medium text-gray-500 py-2">
                    {{ day }}
                  </div>
                </div>
                <div class="grid grid-cols-7 gap-2">
                  <div v-for="day in 35" :key="day" class="aspect-square flex items-center justify-center text-sm rounded hover:bg-brand-50 cursor-pointer transition-colors" :class="[day <= 5 || day > 30 ? 'text-gray-300' : day === 25 ? 'bg-brand-600 text-white font-bold' : 'text-gray-900']">
                    {{ day <= 5 ? '' : day > 30 ? day - 30 : day - 5 }}
                  </div>
                </div>
              </div>

              <!-- 근무현황 -->
              <div class="bg-white rounded-lg border border-gray-200 p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">본일 근무현황</h3>
                <div class="space-y-3">
                  <div class="flex items-center justify-between p-3 bg-brand-50 rounded-lg">
                    <span class="text-sm font-medium text-gray-900">출근시간</span>
                    <span class="text-sm font-semibold text-brand-600">09:00 AM</span>
                  </div>
                  <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span class="text-sm font-medium text-gray-900">현재시간</span>
                    <span class="text-sm font-semibold text-gray-600">02:30 PM</span>
                  </div>
                  <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span class="text-sm font-medium text-gray-900">누적근로시간</span>
                    <span class="text-sm font-semibold text-gray-600">5시간 30분</span>
                  </div>
                </div>
              </div>

              <!-- 이번주 근로시간 -->
              <div class="bg-white rounded-lg border border-gray-200 p-6">
                <h3 class="text-lg font-semibold text-gray-900 mb-4">이번주 근로시간</h3>
                <div class="w-full bg-gray-200 rounded-full h-2">
                  <div class="bg-brand-600 h-2 rounded-full" style="width: 65%"></div>
                </div>
                <p class="text-sm text-gray-600 mt-2">35시간 / 40시간</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 편의기능 탭 -->
        <div class="w-full flex-shrink-0 px-4 py-8">
          <div class="max-w-5xl mx-auto">
            <h2 class="text-2xl font-semibold text-gray-900 mb-6">편의기능</h2>
            <div class="space-y-4">
              <button class="w-full bg-white border border-gray-200 rounded-lg p-4 text-left hover:shadow-md transition-shadow">
                <p class="text-sm font-semibold text-gray-900">근로계약서 관리</p>
                <p class="text-xs text-gray-500 mt-1">계약서 업로드 및 확인</p>
              </button>
              <button class="w-full bg-white border border-gray-200 rounded-lg p-4 text-left hover:shadow-md transition-shadow">
                <p class="text-sm font-semibold text-gray-900">급여 명세서</p>
                <p class="text-xs text-gray-500 mt-1">월별 급여 내역 조회</p>
              </button>
              <button class="w-full bg-white border border-gray-200 rounded-lg p-4 text-left hover:shadow-md transition-shadow">
                <p class="text-sm font-semibold text-gray-900">진단 결과</p>
                <p class="text-xs text-gray-500 mt-1">근로환경 진단 결과 보기</p>
              </button>
            </div>
          </div>
        </div>

        <!-- 상담기록 탭 -->
        <div class="w-full flex-shrink-0 px-4 py-8">
          <div class="max-w-5xl mx-auto">
            <h2 class="text-2xl font-semibold text-gray-900 mb-6">상담기록</h2>
            <div class="space-y-3">
              <div class="bg-white rounded-lg border border-gray-200 p-4">
                <div class="flex items-start justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">근로기준법 상담</p>
                    <p class="text-xs text-gray-500 mt-1">2025년 11월 20일 · 공인노무사 김철수</p>
                  </div>
                  <span class="inline-block px-2 py-1 text-xs font-medium bg-brand-100 text-brand-700 rounded">진행중</span>
                </div>
              </div>
              <div class="bg-white rounded-lg border border-gray-200 p-4 opacity-60">
                <div class="flex items-start justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-900">수당 청구 절차 상담</p>
                    <p class="text-xs text-gray-500 mt-1">2025년 11월 15일 · 공인노무사 이영희</p>
                  </div>
                  <span class="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">완료</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 고객센터 탭 -->
        <div class="w-full flex-shrink-0 px-4 py-8">
          <div class="max-w-5xl mx-auto">
            <h2 class="text-2xl font-semibold text-gray-900 mb-6">고객센터</h2>
            <div class="space-y-4">
              <div class="bg-white rounded-lg border border-gray-200 p-6">
                <p class="text-sm font-medium text-gray-900 mb-4">자주 묻는 질문</p>
                <div class="space-y-3">
                  <div class="border-t border-gray-200 pt-3">
                    <p class="text-sm text-gray-700">근로시간은 어떻게 기록하나요?</p>
                  </div>
                  <div class="border-t border-gray-200 pt-3">
                    <p class="text-sm text-gray-700">상담 신청은 어떻게 하나요?</p>
                  </div>
                </div>
              </div>
              <button class="w-full bg-brand-600 text-white py-3 rounded-lg font-medium hover:bg-brand-700 transition-colors">
                1:1 문의하기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const tabs = ["근로관리", "편의기능", "상담기록", "고객센터"];
const currentTab = ref(0);

let touchStartX = 0;
let touchEndX = 0;

function handleTouchStart(e: TouchEvent) {
  touchStartX = e.changedTouches[0].screenX;
}

function handleTouchMove(e: TouchEvent) {
  touchEndX = e.changedTouches[0].screenX;
}

function handleTouchEnd() {
  const diff = touchStartX - touchEndX;
  if (Math.abs(diff) > 50) {
    if (diff > 0 && currentTab.value < tabs.length - 1) {
      currentTab.value++;
    } else if (diff < 0 && currentTab.value > 0) {
      currentTab.value--;
    }
  }
}
</script>
