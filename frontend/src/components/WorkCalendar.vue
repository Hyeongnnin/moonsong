<template>
  <div class="bg-white rounded-lg border border-gray-200 p-6" :key="calendarVersion">
    <div class="flex items-center justify-between mb-6">
      <div>
        <h3 class="text-lg font-semibold text-gray-900">{{ currentYear }}년 {{ currentMonth }}월</h3>
        <p class="text-sm text-gray-500 mt-1">근로시간 기록</p>
      </div>
      <div class="flex gap-2">
        <!-- 월별 스케줄 변경 버튼 -->
        <button 
          v-if="activeJob"
          @click="openMonthlyScheduleModal"
          :disabled="isFutureMonth"
          :class="[
            'px-3 py-2 text-sm font-medium rounded-lg transition-colors',
            isFutureMonth
              ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
              : 'text-brand-600 bg-brand-50 hover:bg-brand-100'
          ]"
          :title="isFutureMonth ? '미래 월의 스케줄은 변경할 수 없습니다' : '이 달의 근무 스케줄을 변경합니다'"
        >
          📅 월별 스케줄 변경
        </button>
        <!-- 월별 근로기록 삭제 버튼 -->
        <button 
          v-if="activeJob"
          @click="deleteMonthlyRecords"
          :disabled="isFutureMonth || isDeleting"
          :class="[
            'px-3 py-2 text-sm font-medium rounded-lg transition-colors',
            isFutureMonth || isDeleting
              ? 'text-gray-400 bg-gray-100 cursor-not-allowed opacity-50'
              : 'text-red-600 bg-red-50 hover:bg-red-100'
          ]"
          :title="isFutureMonth ? '미래 월의 기록은 삭제할 수 없습니다' : '이 달의 모든 근로 기록을 삭제합니다'"
        >
          🗑️ 월별 기록 삭제
        </button>
        <button 
          @click="previousMonth"
          :disabled="!canGoPrevious"
          :class="[
            'p-2 rounded-lg transition-colors',
            canGoPrevious 
              ? 'text-gray-600 hover:bg-gray-100 cursor-pointer' 
              : 'text-gray-300 cursor-not-allowed opacity-50'
          ]"
          :title="!canGoPrevious ? '근로 시작일 이전 달은 볼 수 없습니다' : '이전 달'"
        >
          ◀
        </button>
        <button 
          @click="nextMonth"
          :disabled="!canGoNext"
          :class="[
            'p-2 rounded-lg transition-colors',
            canGoNext 
              ? 'text-gray-600 hover:bg-gray-100 cursor-pointer' 
              : 'text-gray-300 cursor-not-allowed opacity-50'
          ]"
          :title="!canGoNext ? '현재 월로부터 6개월 이후는 볼 수 없습니다' : '다음 달'"
        >
          ▶
        </button>
      </div>
    </div>

    <!-- 요일 헤더 -->
    <div class="grid grid-cols-7 gap-2 mb-3">
      <div 
        v-for="day in ['일', '월', '화', '수', '목', '금', '토']" 
        :key="day" 
        class="text-center text-xs font-semibold text-gray-600 py-2"
      >
        {{ day }}
      </div>
    </div>

    <!-- 달력 (콘텐츠 기반 높이) - calendarData 변경 시 전체 리렌더링 -->
    <div class="grid grid-cols-7 gap-2" :key="`calendar-grid-${currentYear}-${currentMonth}-${calendarVersion}`">
      <button
        v-for="dayObj in calendarDays"
        :key="`${currentYear}-${currentMonth}-${dayObj.dateIso || 'empty'}-${calendarVersion}`"
        @click="selectDate(dayObj.day)"
        :class="getCellClass(dayObj)"
        :disabled="!dayObj.day || isFutureMonth"
        :title="cellTitle(dayObj.dateIso, isDateScheduled(dayObj.dateIso))"
      >
        <div
          v-if="dayObj.day"
          class="absolute top-1 left-1 text-sm font-extrabold antialiased pointer-events-none"
          :class="[
            selectedDay === dayObj.day
              ? '!text-white !font-black'
              : (isScheduledWorkday(dayObj.dateIso) && isWorked(dayObj.dateIso))
              ? (isHoliday(dayObj.dateIso) ? '!text-red-600 !font-black' : '!text-gray-900 !font-black')
              : (!isScheduledWorkday(dayObj.dateIso) && isWorked(dayObj.dateIso))
              ? (isHoliday(dayObj.dateIso) ? '!text-red-600 !font-black' : '!text-white !font-black')
              : isScheduledWorkday(dayObj.dateIso)
              ? (isHoliday(dayObj.dateIso) ? '!text-red-600 !font-black' : '!text-gray-900 !font-black')
              : isHoliday(dayObj.dateIso)
              ? '!text-red-600 !font-bold'
              : '!text-gray-900 !font-semibold'
          ]"
          style="position: absolute; z-index: 30; text-shadow: 0 0 2px rgba(255, 255, 255, 0.5);"
        >
          {{ dayObj.day }}
        </div>

        <!-- ✅ W/M 뱃지 제거: 주간/월별 스케줄 구분은 내부 로직으로만 사용 -->

        <!-- 하단 라벨 영역: 숫자를 가리지 않도록 z-index를 더 올림 -->
        <div v-if="dayObj.day" class="absolute bottom-1 left-0 right-0 flex flex-col items-center pointer-events-none" style="z-index: 15;">
          <!-- 공휴일 표시 (최우선) -->
          <span
            v-if="isHoliday(dayObj.dateIso)"
            class="text-[10px] font-semibold text-red-500 leading-tight text-center px-1 truncate max-w-full"
          >
            {{ holidayNameForDate(dayObj.dateIso) }}
          </span>
          <!-- 주휴일 표시 -->
          <span
            v-else-if="isWeeklyRest(dayObj.dateIso)"
            class="text-[10px] font-semibold text-sky-600 leading-tight text-center px-1 truncate max-w-full"
          >
            주휴일
          </span>
          <!-- 출결 상태 표시 (소정근로일이거나, 값이 있으면 표시) -->
          <span
            v-else-if="(isScheduledWorkday(dayObj.dateIso) || getAttendanceStatus(dayObj.dateIso))"
            class="text-[10px] font-semibold text-orange-600 leading-tight text-center px-1 truncate max-w-full"
          >
            {{ getAttendanceStatusLabel(dayObj.dateIso) }}
          </span>
          <!-- 기념일 표시 -->
          <span
            v-else-if="isObservance(dayObj.dateIso)"
            class="text-[10px] font-medium text-gray-400 leading-tight text-center px-1 truncate max-w-full"
          >
            {{ observanceNameForDate(dayObj.dateIso) }}
          </span>
        </div>
      </button>
    </div>

    <WorkDayModal 
      v-if="modalVisible" 
      :visible="modalVisible"
      :employeeId="activeJob?.id"
      :dateIso="modalDateIso"
      :record="modalRecord"
      :holidayName="modalHolidayName || undefined"
      :weeklyRestName="modalWeeklyRestName || undefined"
      @close="onModalClose"
      @saved="onModalSaved" 
      @deleted="onModalDeleted" 
    />
    
    <MonthlyScheduleModal
      :isOpen="monthlyScheduleModalOpen"
      :employeeId="activeJob?.id || null"
      :year="currentYear"
      :month="currentMonth"
      @close="closeMonthlyScheduleModal"
      @saved="onMonthlyScheduleSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, toRefs } from 'vue';
import { apiClient } from '../api'
import type { Job } from '../stores/jobStore';
import WorkDayModal from './WorkDayModal.vue'
import MonthlyScheduleModal from './MonthlyScheduleModal.vue'

interface Props {
  activeJob?: Job | null;
}

interface HolidayApiItem {
  date?: string;
  name?: string;
  type?: string;
}

// Phase 3: calendar API 응답 타입 (주간/월별 스케줄 정보 추가)
interface CalendarDateItem {
  date: string;
  day: number;
  is_scheduled_workday?: boolean;  // Phase 3: 소정근로일 여부
  is_scheduled?: boolean;           // 하위 호환
  schedule_source?: 'monthly' | 'weekly' | null;  // Phase 3: 스케줄 소스
  scheduled_start_time?: string | null;  // Phase 3: 스케줄 기반 시작 시간
  scheduled_end_time?: string | null;    // Phase 3: 스케줄 기반 종료 시간
  scheduled_break_minutes?: number;      // Phase 3: 스케줄 기반 휴게 시간
  scheduled_is_overnight?: boolean;      // Phase 3: 익일 근무 여부
  scheduled_next_day_minutes?: number;   // Phase 3: 익일 근무 시간
  is_worked?: boolean;              // Phase 3: 실제 근무 여부
  attendance_status?: string | null; // Phase 3: 출결 상태
  record?: any;
}

const props = withDefaults(defineProps<Props>(), {
  activeJob: null,
});

const emit = defineEmits(['statsUpdated', 'monthChanged']);

const { activeJob } = toRefs(props)

const HOLIDAY_TYPE_LEGAL = 'LEGAL'
const HOLIDAY_TYPE_OBSERVANCE = 'OBSERVANCE'
const WEEKLY_REST_LABEL = '주휴일'

// 내부 강제 리마운트를 위한 버전 키
const calendarVersion = ref(0)

const currentDate = ref(new Date());
const selectedDay = ref<number | null>(null);
const modalVisible = ref(false)
const modalRecord = ref<any | null>(null)
const modalDateIso = ref<string>('')
const modalHolidayName = ref<string | null>(null)
const modalWeeklyRestName = ref<string | null>(null)

// 월별 스케줄 모달 상태
const monthlyScheduleModalOpen = ref(false)

// 삭제 상태
const isDeleting = ref(false)

const currentYear = computed(() => currentDate.value.getFullYear());
const currentMonth = computed(() => currentDate.value.getMonth() + 1);

// 근로 시작일 기준으로 이전 달로 이동 가능 여부 확인
const canGoPrevious = computed(() => {
  if (!activeJob?.value?.start_date) return true; // start_date가 없으면 제한 없음
  
  const startDate = new Date(activeJob.value.start_date);
  const startYear = startDate.getFullYear();
  const startMonth = startDate.getMonth() + 1; // 1-12
  
  // 현재 보고 있는 달이 시작일의 달보다 이후면 true
  if (currentYear.value > startYear) return true;
  if (currentYear.value === startYear && currentMonth.value > startMonth) return true;
  
  return false;
});

// 미래 월 이동 제한: 현재 월 + 6개월까지만 허용
const canGoNext = computed(() => {
  const today = new Date();
  const todayYear = today.getFullYear();
  const todayMonth = today.getMonth() + 1; // 1-12
  
  // 현재 월 + 6개월 계산
  const maxDate = new Date(todayYear, todayMonth - 1 + 6, 1); // month는 0-based
  const maxYear = maxDate.getFullYear();
  const maxMonth = maxDate.getMonth() + 1;
  
  // 현재 보고 있는 달이 최대 허용 월보다 이전이면 true
  if (currentYear.value < maxYear) return true;
  if (currentYear.value === maxYear && currentMonth.value < maxMonth) return true;
  
  return false;
});

// 미래 월 여부 확인 (현재 월보다 이후인지)
const isFutureMonth = computed(() => {
  const today = new Date();
  const todayYear = today.getFullYear();
  const todayMonth = today.getMonth() + 1; // 1-12
  
  if (currentYear.value > todayYear) return true;
  if (currentYear.value === todayYear && currentMonth.value > todayMonth) return true;
  
  return false;
});

// 🔥 calendarDays보다 먼저 선언되어야 함
const calendarData = ref<CalendarDateItem[]>([]);


const calendarDays = computed(() => {
  const year = currentYear.value;
  const monthDisplay = currentMonth.value; // 1-12 표시용
  const month = monthDisplay - 1; // 0-11 계산용
  const firstDayOfMonth = new Date(year, month, 1).getDay();
  const lastDateOfMonth = new Date(year, month + 1, 0).getDate();
  
  // 🔥 핵심: calendarData와 calendarVersion을 참조하여 Vue 의존성 추적
  const data = calendarData.value;
  const version = calendarVersion.value;
  
  const days: { day: number | null, dateIso?: string, cellClass?: string }[] = [];
  
  // 이전 달의 빈 공간 (0 대신 null 사용)
  for (let i = 0; i < firstDayOfMonth; i++) {
    days.push({ day: null });
  }
  
  // 현재 달의 날짜
  for (let i = 1; i <= lastDateOfMonth; i++) {
    // 로컬 날짜 문자열 생성 (UTC 변환 없이)
    const dateIso = `${year}-${String(month + 1).padStart(2, '0')}-${String(i).padStart(2, '0')}`;
    days.push({ day: i, dateIso });
  }
  
  console.log(`[calendarDays ${year}-${monthDisplay} v${version}] computed: ${days.length} days, dataLength=${data.length}`);
  console.log(`[calendarDays ${year}-${monthDisplay}] First 3:`, days.slice(0, 3));
  
  return days;
});

const holidayMap = ref<Record<string, string>>({});
const observanceMap = ref<Record<string, string>>({});

const parseLocalDate = (dateIso?: string): Date | null => {
  if (!dateIso) return null;
  const parts = dateIso.split('-');
  if (parts.length !== 3) return null;
  const [y, m, d] = parts.map((part) => Number(part));
  if ([y, m, d].some((num) => Number.isNaN(num))) return null;
  return new Date(y, m - 1, d);
};

const scheduledDayMap = computed(() => {
  // 🔥 명시적으로 currentYear, currentMonth를 의존성에 추가
  const year = currentYear.value;
  const month = currentMonth.value;
  const data = calendarData.value;
  const version = calendarVersion.value;
  
  const map: Record<string, { 
    is_scheduled_workday: boolean;
    is_worked: boolean;
    attendance_status: string | null;
    schedule_source?: 'monthly' | 'weekly' | null;
  }> = {};
  
  if (!data || !Array.isArray(data)) {
    console.warn(`[scheduledDayMap ${year}-${month}] calendarData is empty or not an array:`, data);
    return map;
  }
  
  console.log(`[scheduledDayMap ${year}-${month} v${version}] Building map from`, data.length, 'dates');
  
  for (const d of data) {
    if (d && d.date) {
      // Phase 3: 백엔드 API 응답 필드 사용 (schedule_source 추가)
      map[d.date] = { 
        is_scheduled_workday: !!d.is_scheduled_workday,
        is_worked: !!d.is_worked,
        attendance_status: d.attendance_status || null,
        schedule_source: d.schedule_source || null
      };
      
      // 처음 3개 날짜만 상세 로그
      if (Object.keys(map).length <= 3) {
        console.log(`[scheduledDayMap ${year}-${month}] ${d.date}:`, JSON.stringify({
          is_scheduled_workday: d.is_scheduled_workday,
          is_worked: d.is_worked,
          schedule_source: d.schedule_source,
          attendance_status: d.attendance_status,
          mapped_value: map[d.date]
        }, null, 2));
      }
    }
  }
  
  console.log(`[scheduledDayMap ${year}-${month}] Total dates in map:`, Object.keys(map).length);
  console.log(`[scheduledDayMap ${year}-${month}] 소정근로일 개수:`, Object.values(map).filter(v => v.is_scheduled_workday).length);
  
  return map;
});

// Phase 3: 스케줄 소스 확인 ("monthly" | "weekly" | null)
const getScheduleSource = (dateIso?: string): 'monthly' | 'weekly' | null => {
  if (!dateIso) return null;
  const dayData = calendarData.value.find(d => d.date === dateIso);
  const source = dayData?.schedule_source || null;
  
  // 디버깅: 처음 5개 날짜만 로그
  if (dayData && parseInt(dateIso.split('-')[2]) <= 5) {
    console.log(`[getScheduleSource] ${dateIso}:`, {
      found: !!dayData,
      schedule_source: dayData?.schedule_source,
      is_scheduled_workday: dayData?.is_scheduled_workday,
      result: source
    });
  }
  
  return source;
};

// Phase 3: 소정근로일 여부 확인
const isScheduledWorkday = (dateIso?: string): boolean => {
  if (!dateIso) {
    console.warn('[isScheduledWorkday] dateIso is empty');
    return false;
  }
  
  const mapEntry = scheduledDayMap.value[dateIso];
  const result = mapEntry?.is_scheduled_workday === true;
  
  // 디버깅: 처음 3개 날짜만 상세 로그
  const day = parseInt(dateIso.split('-')[2]);
  if (day <= 3) {
    console.log(`[isScheduledWorkday] ${dateIso}:`, JSON.stringify({
      has_entry: !!mapEntry,
      is_scheduled_workday: mapEntry?.is_scheduled_workday,
      is_worked: mapEntry?.is_worked,
      schedule_source: mapEntry?.schedule_source,
      result: result,
      map_size: Object.keys(scheduledDayMap.value).length
    }, null, 2));
  }
  
  return result;
};

// Phase 3: 실제 근무 여부 확인
const isWorked = (dateIso?: string): boolean => {
  if (!dateIso) return false;
  return scheduledDayMap.value[dateIso]?.is_worked === true;
};

// 날짜가 스케줄되어 있는지 확인하는 헬퍼 함수 (하위 호환성)
const isDateScheduled = (dateIso?: string): boolean => {
  if (!dateIso) return false;
  
  // Phase 3: 소정근로일 또는 실제 근무가 있으면 스케줄된 것으로 간주
  const scheduled = isScheduledWorkday(dateIso);
  const worked = isWorked(dateIso);
  
  return scheduled || worked;
};

const holidayNameForDate = (dateIso?: string): string | undefined => {
  if (!dateIso) return undefined;
  return holidayMap.value[dateIso];
};

const isHoliday = (dateIso?: string): boolean => {
  return Boolean(holidayNameForDate(dateIso));
};

const observanceNameForDate = (dateIso?: string): string | undefined => {
  if (!dateIso) return undefined;
  return observanceMap.value[dateIso];
};

const isObservance = (dateIso?: string): boolean => {
  return Boolean(observanceNameForDate(dateIso));
};

const isWeeklyRest = (dateIso?: string): boolean => {
  const parsed = parseLocalDate(dateIso);
  if (!parsed) return false;
  return parsed.getDay() === 0;
};

const weeklyRestNameForDate = (dateIso?: string): string | undefined => {
  return isWeeklyRest(dateIso) ? WEEKLY_REST_LABEL : undefined;
};

const calendarDataMap = computed(() => {
  const map = new Map();
  calendarData.value.forEach(item => {
    map.set(item.date, item);
  });
  return map;
});

// 날짜 셀의 배경색 클래스를 결정하는 함수
const getCellClass = (dayObj: { day: number | null, dateIso?: string }): string => {
  const baseClass = 'aspect-square flex flex-col items-center justify-center text-sm rounded-lg font-medium transition-all relative overflow-hidden';
  
  // Placeholder 셀 (날짜 없음)
  if (!dayObj.day) {
    return `${baseClass} bg-gray-50 cursor-default`;
  }
  
  const dateIso = dayObj.dateIso || '';
  const borderClass = 'border border-gray-200';
  
  // 🔍 디버깅: 처음 5개 날짜만 상세 로그
  if (dayObj.day <= 5) {
    console.log(`[getCellClass] Day ${dayObj.day} (${dateIso}):`, {
      isScheduled: isScheduledWorkday(dateIso),
      isWorked: isWorked(dateIso),
      mapEntry: scheduledDayMap.value[dateIso],
      calendarDataLength: calendarData.value.length,
      rawData: calendarData.value.find(d => d.date === dateIso)
    });
  }
  
  // 1. 미래 월이면 비활성화
  if (isFutureMonth.value) {
    return `${baseClass} ${borderClass} text-gray-400 bg-gray-100 cursor-not-allowed opacity-50`;
  }
  
  // 2. 선택된 날짜 (테두리나 밝기 변화로 표현 제안, 여기서는 기존 bg-brand-600 유지하되 우선순위 조정)
  // 사용자 요구: "선택 상태 때문에 주황색이 칠해지는 일이 없도록"
  // 해결: 배경색은 스케줄 우선, 선택 상태는 링/테두리로 표현하거나 선택 시에만 덮어쓰기
  
  const isScheduled = isScheduledWorkday(dateIso);
  const isWorkedDay = isWorked(dateIso);
  const isSelected = selectedDay.value === dayObj.day;
  const status = getAttendanceStatus(dateIso);

  // 색상 결정 규칙
  let bgColorClass = 'bg-white';
  let textColorClass = 'text-gray-900';
  let shadowClass = '';
  let ringClass = '';
  let borderOverride = ''; // 소정근로일 전용 테두리

  if (isScheduled) {
    // 소정근로일 (흰색 배경 + 주황색 테두리)
    if (status === 'ABSENT') {
      bgColorClass = 'bg-red-50 hover:bg-red-100'; // 결근: 연한 빨강
    } else if (status === 'ANNUAL_LEAVE') {
      bgColorClass = 'bg-orange-100 hover:bg-orange-200'; // 연차: 연한 주황
    } else {
      bgColorClass = 'bg-white hover:bg-orange-50';
    }
    textColorClass = 'text-gray-900';
    shadowClass = '';
    ringClass = ''; // ring 제거하여 box-shadow 테두리가 보이도록
    // box-shadow로 강력한 테두리 적용 (ring보다 우선)
    borderOverride = 'scheduled-workday-border'; // 커스텀 클래스 사용
  } else if (isWorkedDay) {
    // 비소정근로일 실제 근무 (초록색 배경)
    bgColorClass = 'bg-green-500 hover:bg-green-600';
    textColorClass = 'text-white';
    shadowClass = 'shadow-sm';
  } else if (status === 'ABSENT') {
    // 비소정근로일인데 결근 기록이 있는 경우 (특이 케이스)
    bgColorClass = 'bg-red-50';
    textColorClass = 'text-gray-400';
  } else if (isWeeklyRest(dateIso)) {
    // 주휴일
    bgColorClass = 'bg-sky-50 hover:bg-sky-100';
    textColorClass = 'text-sky-700';
    ringClass = 'ring-1 ring-sky-100';
  } else {
    // 일반 날짜
    bgColorClass = 'bg-white hover:bg-brand-50';
  }

  // 공휴일 스타일 (링 추가)
  if (isHoliday(dateIso)) {
    ringClass = 'ring-2 ring-red-200';
  }

  // 선택된 날짜 스타일 (최우선 색상 덮어쓰기 또는 링 추가)
  // 여기서는 선택된 날짜를 강조하기 위해 브랜드 색상으로 덮어씀
  if (isSelected) {
    bgColorClass = 'bg-brand-600';
    textColorClass = 'text-white';
    shadowClass = 'shadow-md';
    // 선택 시에도 소정근로일이면 주황색 테두리 유지
    if (isScheduled) {
      borderOverride = 'scheduled-workday-border';
    }
  }

  return `${baseClass} ${borderOverride || borderClass} ${bgColorClass} ${textColorClass} ${shadowClass} ${ringClass}`;
};

// 출결 상태 가져오기
const getAttendanceStatus = (dateIso?: string): string | null => {
  if (!dateIso) return null;
  return scheduledDayMap.value[dateIso]?.attendance_status || null;
};

// 출결 상태 한글 라벨
const getAttendanceStatusLabel = (dateIso?: string): string => {
  const status = getAttendanceStatus(dateIso);
  
  if (!status) {
    // 기록이 없지만 소정근로일인 경우 '근무' (예정) 표시
    if (isScheduledWorkday(dateIso)) {
        return '근무';
    }
    return '결근';
  }
  
  const statusLabels: Record<string, string> = {
    'REGULAR_WORK': '근무',
    'ANNUAL_LEAVE': '연차',
    'SICK_LEAVE': '병가',
    'ABSENT': '결근',
    'PERSONAL_LEAVE': '개인휴가',
    'UNPAID_LEAVE': '무급휴가'
  };
  
  return statusLabels[status] || '결근';
};

const cellTitle = (dateIso?: string, scheduled?: boolean): string => {
  if (!dateIso) return '';
  const parts: string[] = [];
  if (isFutureMonth.value) {
    // parts.push('미래 월에는 근로 기록을 입력할 수 없습니다'); // 삭제
    parts.push('미래 근무 예정');
  } else {
    parts.push(`${dateIso}: ${scheduled ? 'Workday' : 'Day off'}`);
  }
  const holidayName = holidayNameForDate(dateIso);
  if (holidayName) {
    parts.push(`공휴일: ${holidayName}`);
  }
  const weeklyRestName = weeklyRestNameForDate(dateIso);
  if (!holidayName && weeklyRestName) {
    parts.push(`주휴일: ${weeklyRestName}`);
  }
  const observanceName = observanceNameForDate(dateIso);
  if (!holidayName && !weeklyRestName && observanceName) {
    parts.push(`기념일: ${observanceName}`);
  }
  return parts.join(' | ');
};

let calendarAbortController: AbortController | null = null
let calendarRequestSeq = 0

async function loadCalendar() {
  const employeeId = activeJob?.value?.id;
  if (!employeeId) {
    calendarData.value = [];
    return;
  }

  try {
    // 이전 요청 취소 (race condition 방지)
    if (calendarAbortController) {
      try { calendarAbortController.abort() } catch (e) {}
    }
    calendarAbortController = new AbortController()
    const reqId = ++calendarRequestSeq
    const monthStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`;
    
    // Phase 3: calendar API 사용 (is_scheduled_workday, is_worked, attendance_status 포함)
    const res = await apiClient.get(`/labor/jobs/${employeeId}/calendar/`, {
      params: { month: monthStr },
      signal: calendarAbortController.signal,
    });
    
    // 응답 데이터 구조 확인 및 할당
    // 응답 도착 시점에 최신 요청인지 확인
    console.log('[WorkCalendar] Raw API response:', res.data);
    console.log('[WorkCalendar] Request ID match:', reqId === calendarRequestSeq, 'reqId:', reqId, 'seq:', calendarRequestSeq);
    
    if (reqId === calendarRequestSeq) {
      const responseData = res.data.dates || res.data;
      calendarData.value = Array.isArray(responseData) ? responseData : [];
      console.log('[WorkCalendar] Calendar data assigned:', calendarData.value.length, 'items');
      console.log('[WorkCalendar] First 3 items:', calendarData.value.slice(0, 3));
      
      // 🔥 핵심 수정: calendarData 변경 시 강제 리렌더링
      calendarVersion.value++;
      console.log('[WorkCalendar] calendarVersion incremented to:', calendarVersion.value);
    } else {
      console.warn('[WorkCalendar] Response discarded - stale request');
    }
    
    // 강제로 다음 틱에서 재렌더링 트리거
    await new Promise(resolve => setTimeout(resolve, 0));
  } catch (e) {
    // 취소된 요청은 조용히 무시
    if ((e as any)?.name === 'CanceledError' || (e as any)?.code === 'ERR_CANCELED') {
      return
    }
    console.error('[WorkCalendar] Failed to load calendar schedule', e);
    calendarData.value = [];
  }
}

async function loadHolidays() {
  const monthStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`;
  try {
    const res = await apiClient.get('/labor/holidays/', {
      params: { month: monthStr },
    });
    const legalMap: Record<string, string> = {};
    const observances: Record<string, string> = {};
    if (Array.isArray(res.data)) {
      for (const rawItem of res.data as HolidayApiItem[]) {
        const dateIso = rawItem?.date;
        const label = rawItem?.name;
        if (!dateIso || !label) continue;
        const typeValue = (rawItem?.type || HOLIDAY_TYPE_LEGAL).toUpperCase();
        if (typeValue === HOLIDAY_TYPE_OBSERVANCE) {
          observances[dateIso] = label;
        } else {
          legalMap[dateIso] = label;
        }
      }
    }
    holidayMap.value = legalMap;
    observanceMap.value = observances;
  } catch (e) {
    console.error('[WorkCalendar] Failed to load holidays', e);
    holidayMap.value = {};
    observanceMap.value = {};
  }
}

watch([() => activeJob?.value?.id, currentYear, currentMonth], () => {
  loadCalendar();
  loadHolidays();
  // 월이 변경될 때마다 통계 카드에 알림
  emit('monthChanged', { year: currentYear.value, month: currentMonth.value });
}, { immediate: true });

// 알바 변경 시 초기화: 시작 월로 리셋 + 상태 초기화 + 강제 리마운트
watch(() => activeJob?.value?.id, (newId, oldId) => {
  if (!newId || newId === oldId) return
  const sd = activeJob?.value?.start_date
  let base = new Date()
  if (sd) {
    const d = new Date(sd)
    base = new Date(d.getFullYear(), d.getMonth(), 1)
  }
  currentDate.value = base
  selectedDay.value = null
  modalVisible.value = false
  modalRecord.value = null
  modalDateIso.value = ''
  calendarData.value = []
  modalHolidayName.value = null
  modalWeeklyRestName.value = null
  holidayMap.value = {}
  observanceMap.value = {}
  // 강제 리마운트
  calendarVersion.value++
  // 진행 중 요청 취소
  if (calendarAbortController) {
    try { calendarAbortController.abort() } catch (e) {}
    calendarAbortController = null
  }
  // 새 달 데이터 로드
  loadCalendar()
  loadHolidays()
})

const previousMonth = () => {
  if (!canGoPrevious.value) return; // 근로 시작일 이전으로는 이동 불가
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() - 1);
  selectedDay.value = null;
};

const nextMonth = () => {
  if (!canGoNext.value) return; // 미래 월 제한
  currentDate.value = new Date(currentDate.value.getFullYear(), currentDate.value.getMonth() + 1);
  selectedDay.value = null;
};

function selectDate(day: number | null) {
  if (!day) return;
  const employeeId = activeJob?.value?.id;
  if (!employeeId) return;

  // 미래 월의 날짜는 클릭 불가
  if (isFutureMonth.value) {
    alert('미래 날짜에는 근로 기록을 입력할 수 없습니다.');
    return;
  }

  selectedDay.value = day;
  
  const dateIso = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  
  modalDateIso.value = dateIso;
  modalHolidayName.value = holidayNameForDate(dateIso) || null;
  modalWeeklyRestName.value = weeklyRestNameForDate(dateIso) || null;
  
  // 해당 날짜의 실제 근로기록 조회
  loadWorkRecordForDate(employeeId, dateIso);
  
  modalVisible.value = true;
}

async function loadWorkRecordForDate(employeeId: number, dateIso: string) {
  try {
    // date-schedule API를 사용하여 해당 날짜의 근로기록과 스케줄 정보 조회
    const res = await apiClient.get(`/labor/jobs/${employeeId}/date-schedule/`, {
      params: {
        date: dateIso
      }
    });
    
    // API 응답 전체 확인
    console.log('[WorkCalendar] Full API response:', JSON.stringify(res.data));
    console.log('[WorkCalendar] work_record:', res.data.work_record);
    console.log('[WorkCalendar] is_scheduled_workday:', res.data.is_scheduled_workday);
    
    // work_record가 있으면 사용, 없으면 스케줄 정보를 포함한 객체 생성
    if (res.data && res.data.work_record) {
      // Phase 3: 소정근로일 정보 추가
      modalRecord.value = {
        ...res.data.work_record,
        is_scheduled_workday: res.data.is_scheduled_workday
      };
      console.log('[WorkCalendar] Found work record:', modalRecord.value);
    } else if (res.data && res.data.has_schedule) {
      // 실제 근로기록은 없지만 스케줄이 있는 경우 스케줄 정보 전달
      modalRecord.value = {
        schedule_only: true,
        start_time: res.data.start_time,
        end_time: res.data.end_time,
        is_scheduled_workday: res.data.is_scheduled_workday  // Phase 3
      };
      console.log('[WorkCalendar] Found schedule for', dateIso, ':', modalRecord.value);
    } else {
      // Phase 3: 스케줄이 없어도 소정근로일 정보는 전달
      modalRecord.value = {
        is_scheduled_workday: res.data.is_scheduled_workday
      };
      console.log('[WorkCalendar] No work record or schedule, but scheduled workday info:', res.data.is_scheduled_workday);
    }
  } catch (e) {
    console.error('[WorkCalendar] Failed to load work record', e);
    modalRecord.value = null;
  }
}

function onModalClose() {
  modalVisible.value = false;
  selectedDay.value = null;
  modalRecord.value = null;
  modalHolidayName.value = null;
  modalWeeklyRestName.value = null;
}

// 월별 스케줄 모달 관련 함수
function openMonthlyScheduleModal() {
  monthlyScheduleModalOpen.value = true
}

function closeMonthlyScheduleModal() {
  monthlyScheduleModalOpen.value = false
}

async function onMonthlyScheduleSaved(data?: { stats?: any; dates?: any; cumulative_stats?: any }) {
  closeMonthlyScheduleModal()
  
  // 서버에서 받은 데이터가 있으면 직접 업데이트
  if (data?.dates) {
    // 캘린더 날짜 데이터 업데이트
    calendarData.value = Array.isArray(data.dates) ? data.dates : []
    // 🔥 핵심 수정: 강제 리렌더링
    calendarVersion.value++
    
    // 업적 통계 업데이트 이벤트 발송
    emit('statsUpdated')
    window.dispatchEvent(new Event('labor-updated'))
  } else {
    // 데이터가 없으면 전체 다시 로드
    await loadCalendar()
    emit('statsUpdated')
  }
}

async function deleteMonthlyRecords() {
  const employeeId = activeJob?.value?.id;
  if (!employeeId) return;
  
  const yearMonth = `${currentYear.value}년 ${currentMonth.value}월`;
  
  // 확인 다이얼로그
  const confirmed = confirm(
    `${yearMonth}의 모든 근로 기록을 삭제하시겠습니까?\n\n` +
    `삭제된 기록은 복구할 수 없으며, 통계 및 주휴수당, 알바 업적 등 모든 연동된 데이터가 함께 업데이트됩니다.`
  );
  
  if (!confirmed) return;
  
  isDeleting.value = true;
  
  try {
    const monthStr = `${currentYear.value}-${String(currentMonth.value).padStart(2, '0')}`;
    const res = await apiClient.delete(`/labor/jobs/${employeeId}/monthly-work-records/`, {
      params: {
        month: monthStr,
      },
    });
    
    // 성공 메시지
    alert(res.data.message || `${yearMonth}의 데이터가 삭제되었습니다.`);
    
    // 캘린더 데이터 업데이트
    if (res.data.dates) {
      calendarData.value = res.data.dates;
    }
    
    // 통계 업데이트 알림 (누적 통계 포함)
    emit('statsUpdated', {
      monthlyStats: res.data.stats,
      cumulativeStats: res.data.cumulative_stats
    });
    
    // 캘린더 다시 로드
    await loadCalendar();
    
    // 전역 이벤트 발생 (다른 컴포넌트들도 업데이트)
    window.dispatchEvent(new CustomEvent('labor-updated'));
    
  } catch (error: any) {
    console.error('[WorkCalendar] Failed to delete monthly records', error);
    alert('근로 기록 삭제 중 오류가 발생했습니다.');
  } finally {
    isDeleting.value = false;
  }
}

const skipNextGlobalUpdate = ref(false)

async function onModalSaved(responseData?: any) {
  modalVisible.value = false;
  modalRecord.value = null;
  selectedDay.value = null; // 선택된 날짜 초기화
  modalHolidayName.value = null;
  modalWeeklyRestName.value = null;
  
  // 응답 데이터에 최신 통계가 있으면 사용, 없으면 다시 로드
  if (responseData && responseData.dates && responseData.stats) {
    calendarData.value = responseData.dates;
    // 🔥 핵심 수정: 강제 리렌더링
    calendarVersion.value++;
    // 캘린더 데이터만 업데이트하고, 통계는 WorkSummaryCard에서 현재 월 기준으로 다시 로드
    emit('statsUpdated');
    
    // 🔥 Race Condition 방지: 방금 데이터를 업데이트했으므로, 
    // 곧바로 이어질 labor-updated 이벤트에 의한 재로딩은 건너뜀
    skipNextGlobalUpdate.value = true;
    console.log('[WorkCalendar] Updated from save response, skipping next global reload');
  } else {
    await loadCalendar();
    emit('statsUpdated');
  }
}

async function onModalDeleted(responseData?: any) {
  console.log('[WorkCalendar] onModalDeleted called with:', responseData);
  modalVisible.value = false;
  modalRecord.value = null;
  selectedDay.value = null; // 선택된 날짜 초기화 - 중요!
  modalHolidayName.value = null;
  modalWeeklyRestName.value = null;
  
  // 응답 데이터에 최신 통계가 있으면 사용, 없으면 다시 로드
  if (responseData && responseData.dates && responseData.stats) {
    console.log('[WorkCalendar] Using response data from delete');
    calendarData.value = responseData.dates;
    // 🔥 핵심 수정: 강제 리렌더링
    calendarVersion.value++;
    // 캘린더 데이터만 업데이트하고, 통계는 WorkSummaryCard에서 현재 월 기준으로 다시 로드
    emit('statsUpdated');
    
    // 🔥 Race Condition 방지
    skipNextGlobalUpdate.value = true;
  } else {
    console.log('[WorkCalendar] No response data, reloading calendar');
    await loadCalendar();
    emit('statsUpdated');
  }
}

// 전역 이벤트 리스너 - 스케줄 저장 시 캘린더 자동 갱신
function handleLaborUpdate() {
  if (skipNextGlobalUpdate.value) {
    console.log('[WorkCalendar] Skipping redundant reload (handled by local update)');
    skipNextGlobalUpdate.value = false;
    return;
  }
  
  console.log('[WorkCalendar] Labor updated event received, reloading calendar');
  loadCalendar();
}

onMounted(() => {
  window.addEventListener('labor-updated', handleLaborUpdate);
});

onUnmounted(() => {
  window.removeEventListener('labor-updated', handleLaborUpdate);
});

// 외부에서 캘린더를 새로고침할 수 있도록 노출
defineExpose({
  refreshCalendar: loadCalendar
});
</script>

<style scoped>
.scheduled-day {
  background-color: #f97316 !important;
  color: white !important;
  font-weight: bold !important;
}

/* 소정근로일 테두리: box-shadow로 구현 (ring/border보다 우선순위 높음) */
.scheduled-workday-border {
  box-shadow: inset 0 0 0 2px #f97316 !important;
  border: none !important;
  /* ring 스타일 강제 제거 */
}

/* ring 클래스가 있어도 scheduled-workday-border가 우선 */
.scheduled-workday-border.ring-1,
.scheduled-workday-border.ring-2 {
  box-shadow: inset 0 0 0 2px #f97316 !important;
}
</style>
