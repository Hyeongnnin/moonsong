<template>
  <div v-if="visible" class="fixed inset-0 z-[60] flex items-center justify-center px-4 py-6">
    <div class="absolute inset-0 bg-black/40 backdrop-blur-sm" @click="close"></div>
    <div
      class="relative z-10 w-full max-w-3xl bg-white rounded-2xl shadow-2xl p-6 pb-12 overflow-y-auto max-h-[85vh]"
      @click.stop
    >
      <!-- Header -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <p class="text-xs font-semibold text-brand-600 uppercase tracking-wider">{{ payrollMonthLabel }}</p>
          <h3 class="text-2xl font-bold text-gray-900 mt-1">급여 예상액 명세서</h3>
        </div>
        <button
          type="button"
          class="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition"
          @click="close"
        >
          ✕
        </button>
      </div>

      <div v-if="payroll" class="space-y-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="p-4 rounded-xl bg-brand-50 border border-brand-100 flex flex-col justify-between">
            <p class="text-[10px] font-bold text-brand-600 uppercase">최종 예상 급여 (실수령)</p>
            <p class="text-xl font-black text-brand-900 mt-1">{{ formatCurrency(payroll.net_pay || payroll.summary.total) }}</p>
          </div>
          <div class="p-4 rounded-xl bg-gray-50 border border-gray-200 flex flex-col justify-between">
            <p class="text-[10px] font-bold text-gray-500 uppercase">기본급</p>
            <p class="text-lg font-bold text-gray-800 mt-1">{{ formatCurrency(payroll.summary.base_pay) }}</p>
          </div>
          <!-- 주휴수당 카드 추가 -->
          <div class="p-4 rounded-xl bg-orange-50 border border-orange-100 flex flex-col justify-between">
            <p class="text-[10px] font-bold text-orange-600 uppercase">주휴수당 (예상)</p>
            <p class="text-lg font-bold text-orange-800 mt-1">{{ formatCurrency(payroll.summary.weekly_holiday_pay) }}</p>
          </div>
          <div class="p-4 rounded-xl bg-indigo-50 border border-indigo-100 flex flex-col justify-between">
            <p class="text-[10px] font-bold text-indigo-600 uppercase">야간 수당</p>
            <p class="text-lg font-bold text-indigo-800 mt-1">{{ formatCurrency(payroll.summary.night_extra) }}</p>
          </div>
          <div class="p-4 rounded-xl bg-red-50 border border-red-100 flex flex-col justify-between">
            <p class="text-[10px] font-bold text-red-600 uppercase">휴일 수당</p>
            <p class="text-lg font-bold text-red-800 mt-1">{{ formatCurrency(payroll.summary.holiday_extra) }}</p>
          </div>
        </div>



        <!-- 공제 내역 섹션 (신규) -->
        <section v-if="payroll.summary.deduction && payroll.summary.deduction.type !== 'NONE'">
          <div class="flex items-center justify-between mb-4">
             <h4 class="text-lg font-bold text-gray-900">공제 내역 (예상)</h4>
             <span class="text-xs font-bold px-2 py-1 bg-gray-100 text-gray-600 rounded">
               {{ payroll.summary.deduction.type === 'FOUR_INSURANCE' ? '4대보험 적용' : '3.3% 프리랜서 적용' }}
             </span>
          </div>
          <div class="bg-gray-50 rounded-xl p-6 border border-gray-200">
             <div v-for="(item, idx) in payroll.summary.deduction.details" :key="idx" class="flex justify-between items-center mb-2 text-sm text-gray-600">
                <span>{{ item.label }}</span>
                <span>- {{ formatCurrency(item.amount) }}</span>
             </div>
             <div class="border-t border-gray-200 my-4 border-dashed"></div>
             <div class="flex justify-between items-center mb-2">
                <span class="font-bold text-gray-700">총 공제액</span>
                <span class="font-bold text-gray-700">- {{ formatCurrency(payroll.summary.deduction.total_deduction) }}</span>
             </div>
             <div class="bg-white rounded-lg p-4 mt-4 border border-brand-100 flex justify-between items-center shadow-sm">
                <div>
                   <span class="block text-xs font-bold text-brand-600 mb-1">세전 {{ formatCurrency(payroll.summary.total) }} - 공제 {{ formatCurrency(payroll.summary.deduction.total_deduction) }}</span>
                   <span class="text-lg font-black text-brand-900">실수령 예상액</span>
                </div>
                <span class="text-2xl font-black text-brand-600">{{ formatCurrency(payroll.summary.deduction.net_pay) }}</span>
             </div>
          </div>
        </section>

        <!-- 공제 미선택 안내 -->
        <section v-else class="p-4 bg-orange-50 border border-orange-100 rounded-lg flex items-start gap-3">
           <div class="text-xl">⚠️</div>
           <div>
              <p class="font-bold text-orange-900 text-sm mb-1">공제 방식이 선택되지 않았습니다</p>
              <p class="text-xs text-orange-700 leading-relaxed">
                 현재 표시된 급여는 세전 기준입니다. <br/>
                 실제 수령액을 확인하려면 근로정보 수정에서 공제 방식을 선택해주세요.
              </p>
           </div>
        </section>

        <!-- 2. Detailed Breakdown Table -->
        <section>
          <div class="flex items-center justify-between mb-4">
            <h4 class="text-lg font-bold text-gray-900">날짜별 상세 내역</h4>
            <span class="text-xs text-gray-500 font-medium">전체 {{ payroll.rows.length }}일 내역</span>
          </div>
          <div class="overflow-x-auto rounded-xl border border-gray-200">
            <table class="w-full text-sm text-left">
              <thead class="bg-gray-50 text-gray-500 font-bold uppercase text-[10px] tracking-widest border-b border-gray-200">
                <tr>
                  <th class="px-4 py-3">날짜</th>
                  <th class="px-4 py-3">분류</th>
                   <th class="px-3 py-3 text-center">인정(h)</th>
                   <th class="px-3 py-3 text-center">야간(h)</th>
                   <th class="px-3 py-3 text-right">기본급</th>
                   <th class="px-3 py-3 text-right">추가수당</th>
                 </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                <tr v-for="day in displayedBreakdown" :key="day.date" class="hover:bg-gray-50 transition-colors">
                  <td class="px-4 py-3 font-medium text-gray-900">{{ day.date }}</td>
                  <td class="px-4 py-3">
                    <span :class="sourceClass(day.source)" class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase">
                      {{ sourceLabel(day.source) }}
                    </span>
                  </td>
                   <td class="px-3 py-3 text-center font-semibold text-gray-700">{{ day.hours.toFixed(1) }}</td>
                   <td class="px-3 py-3 text-center text-gray-600">
                     <span v-if="day.night_hours > 0" class="font-bold text-indigo-600">{{ day.night_hours.toFixed(1) }}</span>
                     <span v-else class="text-gray-300">-</span>
                   </td>
                   <td class="px-3 py-3 text-right font-medium text-gray-600">{{ formatCurrency(day.day_pay) }}</td>
                   <td class="px-4 py-3 text-right">
                     <span v-if="day.holiday_bonus + day.night_bonus > 0" class="text-xs font-bold text-brand-600">
                       +{{ formatCurrency(day.holiday_bonus + day.night_bonus) }}
                     </span>
                     <span v-else class="text-gray-300 text-xs">-</span>
                   </td>
                 </tr>
              </tbody>
            </table>
          </div>
          <button 
            v-if="payroll.rows.length > 10" 
            @click="showAll = !showAll"
            class="w-full mt-3 py-2 text-xs font-bold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100 rounded-lg transition-colors border border-brand-200 border-dashed"
          >
            {{ showAll ? '간략히 보기' : `내역 더 보기 (${payroll.rows.length - 10}일)` }}
          </button>
        </section>

        <!-- 3. Policy Notes -->
        <section class="p-4 rounded-xl bg-gray-50 border border-gray-200">
           <h4 class="text-xs font-bold text-gray-800 mb-3 flex items-center gap-2">
             <span class="w-1 h-3 bg-brand-500 rounded-full"></span>
             계산 정책 안내
           </h4>
           <ul class="space-y-2 text-[11px] leading-relaxed text-gray-600 font-medium">
             <li v-for="(note, idx) in payroll.notes" :key="idx" class="flex gap-2">
               <span class="text-brand-500">·</span>
               <p>{{ note }}</p>
             </li>
           </ul>
        </section>
      </div>

      <div v-else class="text-center text-gray-400 py-20 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-100">
        <p class="text-sm font-bold">급여 데이터를 불러올 수 없습니다.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface PayrollBreakdownItem {
  date: string;
  source: string; // actual | scheduled | none
  hours: number;
  is_holiday: boolean;
  holiday_type: string | null;
  day_pay: number;
  holiday_bonus: number;
  night_hours: number;
  night_bonus: number;
  is_future: boolean;
}

interface PayrollSummaryResponse {
  month: string;
  hourly_wage: number;
  workplace_size: string;
  contract_weekly_hours: number | null;
  total_hours: number;
  actual_hours: number;
  scheduled_hours: number;
  base_pay: number;
  holiday_hours: number;
  holiday_bonus: number;
  night_hours: number;
  night_bonus: number;

  estimated_monthly_pay: number;
  net_pay: number;
  summary: {
    base_pay: number;
    night_extra: number;
    holiday_extra: number;
    weekly_holiday_pay?: number; // 주휴수당 추가
    total: number;
    deduction?: {
      type: string;
      total_deduction: number;
      net_pay: number;
      details: Array<{ label: string; amount: number }>;
    };
  };
  rows: PayrollBreakdownItem[];
  notes: string[];
}

const props = defineProps<{ visible: boolean; payroll: PayrollSummaryResponse | null }>();
const emit = defineEmits<{ (e: 'close'): void }>();

const showAll = ref(false);

const payrollMonthLabel = computed(() => {
  if (!props.payroll?.month) return '이번 달';
  const [year, month] = props.payroll.month.split('-');
  return `${year}년 ${Number(month)}월`;
});

const displayedBreakdown = computed(() => {
  if (!props.payroll?.rows) return [];
  const sorted = [...props.payroll.rows].sort((a, b) => {
     return a.date.localeCompare(b.date);
  });
  
  if (showAll.value) return sorted;
  return sorted.slice(0, 10);
});

const formatCurrency = (value: number | undefined | null = 0) => {
  const safeValue = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  return safeValue.toLocaleString('ko-KR') + '원';
};

const formatHours = (value: number | undefined | null = 0) => {
  const safeValue = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  return `${safeValue.toFixed(1)}시간`;
};

const sourceLabel = (source: string) => {
  switch (source) {
    case 'actual': return '실제';
    case 'scheduled': return '예정';
    default: return '없음';
  }
};

const sourceClass = (source: string) => {
  switch (source) {
    case 'actual': return 'bg-brand-100 text-brand-700';
    case 'scheduled': return 'bg-amber-100 text-amber-700';
    default: return 'bg-gray-100 text-gray-500';
  }
};

function close() {
  emit('close');
}
</script>

<style scoped>
/* 룩앤필 강화를 위한 스타일 (테일윈드 보조) */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-thumb {
  background: #E5E7EB;
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: #D1D5DB;
}
</style>
