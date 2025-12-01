<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ currentYear }}년 {{ currentMonth }}월</h3>
        <p class="text-sm text-gray-500 mt-1">근로시간 기록</p>
      </div>
      <div class="flex gap-2">
        <button 
          @click="previousMonth"
          class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          ◀
        </button>
        <button 
          @click="nextMonth"
          class="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          ▶
        </button>
      </div>
    </div>

    <!-- 요일 헤더 -->
    <div class="grid grid-cols-7 gap-2 mb-4">
      <div 
        v-for="day in ['일', '월', '화', '수', '목', '금', '토']" 
        :key="day" 
        class="text-center text-xs font-semibold text-gray-600 py-2"
      >
        {{ day }}
      </div>
    </div>

    <!-- 달력 -->
    <div class="grid grid-cols-7 gap-2">
      <button
        v-for="day in calendarDays"
        :key="day"
        @click="selectDate(day)"
        :class="[
          'aspect-square flex items-center justify-center text-sm rounded-lg font-medium transition-all',
          day === 0 
            ? 'text-gray-300 cursor-default' 
            : day === selectedDay
            ? 'bg-brand-600 text-white shadow-md'
            : 'text-gray-700 hover:bg-brand-50 cursor-pointer'
        ]"
      >
        {{ day === 0 ? '' : day }}
      </button>
    </div>

    <!-- 선택된 날짜의 근로시간 -->
    <div v-if="selectedDay" class="mt-6 pt-6 border-t border-gray-200">
      <p class="text-sm font-medium text-gray-900 mb-3">
        {{ currentYear }}년 {{ currentMonth }}월 {{ selectedDay }}일 근로시간
      </p>
      <div class="bg-brand-50 rounded-lg p-4 border border-brand-100">
        <p class="text-2xl font-bold text-brand-600">8시간</p>
        <p class="text-xs text-gray-600 mt-1">09:00 AM - 06:00 PM (휴게 1시간)</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Job } from '../stores/jobStore';

interface Props {
  activeJob?: Job | null;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
});

const currentDate = ref(new Date());
const selectedDay = ref<number | null>(null);

const currentYear = computed(() => currentDate.value.getFullYear());
const currentMonth = computed(() => currentDate.value.getMonth() + 1);

const calendarDays = computed(() => {
  const year = currentDate.value.getFullYear();
  const month = currentDate.value.getMonth();
  const firstDay = new Date(year, month, 1).getDay();
  const lastDate = new Date(year, month + 1, 0).getDate();
  
  const days: number[] = [];
  
  // 이전 달의 빈 공간
  for (let i = 0; i < firstDay; i++) {
    days.push(0);
  }
  
  // 현재 달의 날짜
  for (let i = 1; i <= lastDate; i++) {
    days.push(i);
  }
  
  return days;
});

const previousMonth = () => {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1);
  selectedDay.value = null;
};

const nextMonth = () => {
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1);
  selectedDay.value = null;
};

const selectDate = (day: number) => {
  if (day !== 0) {
    selectedDay.value = day;
  }
};
</script>

<style scoped>
</style>
