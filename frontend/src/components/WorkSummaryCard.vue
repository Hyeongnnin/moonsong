<template>
  <div class="space-y-4">
    <!-- 근무현황 -->
    <div class="bg-white rounded-lg border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">오늘 근무현황</h3>
      <div class="space-y-3">
        <div class="flex items-center justify-between p-4 bg-brand-50 rounded-lg border border-brand-100">
          <div>
            <p class="text-sm font-medium text-gray-700">출근시간</p>
            <p class="text-xs text-gray-500 mt-1">오늘의 시작 시간</p>
          </div>
          <p class="text-xl font-bold text-brand-600">{{ checkInTime }}</p>
        </div>

        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <p class="text-sm font-medium text-gray-700">현재시간</p>
            <p class="text-xs text-gray-500 mt-1">지금 시각</p>
          </div>
          <p class="text-xl font-bold text-gray-600">{{ currentTime }}</p>
        </div>

        <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <p class="text-sm font-medium text-gray-700">누적근로시간</p>
            <p class="text-xs text-gray-500 mt-1">오늘 일한 시간</p>
          </div>
          <p class="text-xl font-bold text-gray-600">{{ workedHours }}</p>
        </div>
      </div>
    </div>

    <!-- 이번주 근로시간 -->
    <div class="bg-white rounded-lg border border-gray-200 p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-lg font-semibold text-gray-900">이번주 근로시간</h3>
          <p class="text-xs text-gray-500 mt-1">월요일 ~ 일요일</p>
        </div>
        <p class="text-sm font-semibold text-gray-900">{{ weeklyHours }} / 40시간</p>
      </div>
      
      <div class="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div 
          class="bg-gradient-to-r from-brand-500 to-brand-600 h-3 rounded-full transition-all duration-300"
          :style="{ width: weeklyProgressPercent + '%' }"
        ></div>
      </div>

      <div class="mt-4 grid grid-cols-7 gap-2">
        <div 
          v-for="(day, idx) in weekDays"
          :key="idx"
          class="text-center"
        >
          <p class="text-xs font-medium text-gray-600 mb-1">{{ day.label }}</p>
          <p class="text-sm font-semibold text-gray-900">{{ day.hours }}h</p>
          <p class="text-xs text-gray-500">{{ day.percentage }}%</p>
        </div>
      </div>
    </div>

    <!-- 상담 신청 버튼 -->
    <div class="bg-gradient-to-r from-brand-600 to-brand-700 rounded-lg p-6 text-white">
      <h3 class="text-lg font-semibold mb-2">근무 관련 상담이 필요하신가요?</h3>
      <p class="text-sm text-brand-100 mb-4">공인 노무사와 1:1 상담을 통해 근로환경을 진단받으세요.</p>
      <button class="w-full bg-white text-brand-600 py-2 rounded-lg font-semibold hover:bg-brand-50 transition-colors">
        상담 신청하기
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import type { Job } from '../stores/jobStore';

interface Props {
  activeJob?: Job | null;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
});

const checkInTime = ref('09:00 AM');
const currentTime = ref('02:30 PM');
const workedHours = ref('5시간 30분');
const weeklyHours = ref(35);

const weekDays = ref([
  { label: '월', hours: 8, percentage: 100 },
  { label: '화', hours: 8, percentage: 100 },
  { label: '수', hours: 8, percentage: 100 },
  { label: '목', hours: 8, percentage: 100 },
  { label: '금', hours: 3, percentage: 37 },
  { label: '토', hours: 0, percentage: 0 },
  { label: '일', hours: 0, percentage: 0 },
]);

const weeklyProgressPercent = computed(() => {
  return (weeklyHours.value / 40) * 100;
});

// 현재 시간 업데이트
const updateCurrentTime = () => {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const period = now.getHours() >= 12 ? 'PM' : 'AM';
  const displayHours = now.getHours() % 12 || 12;
  
  currentTime.value = `${String(displayHours).padStart(2, '0')}:${minutes} ${period}`;
};

let intervalId: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  updateCurrentTime();
  intervalId = setInterval(updateCurrentTime, 60000); // 1분마다 업데이트
});

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId);
});
</script>

<style scoped>
</style>
