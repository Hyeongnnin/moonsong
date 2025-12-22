<template>
  <div
    v-if="visible"
    class="fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
  >
    <div class="absolute inset-0 bg-black/40" @click="close"></div>
    <div
      class="relative z-10 w-full max-w-2xl bg-white rounded-2xl shadow-2xl p-6 overflow-y-auto max-h-[90vh]"
      @click.stop
    >
      <div class="flex items-start justify-between mb-6">
        <div>
          <p class="text-xs font-medium text-gray-500">{{ payrollMonthLabel }}</p>
          <h3 class="text-2xl font-semibold text-gray-900 mt-1">급여 계산 근거</h3>
        </div>
        <button
          type="button"
          class="text-gray-500 hover:text-gray-700 transition"
          @click="close"
        >
          ✕
        </button>
      </div>

      <div v-if="hasData" class="space-y-6">
        <!-- Summary -->
        <section class="p-4 rounded-xl bg-brand-50 border border-brand-100">
          <p class="text-sm text-gray-600 mb-1">이번 달 예상 급여</p>
          <p class="text-3xl font-bold text-brand-700">{{ formatCurrency(payroll?.estimated_salary) }}</p>
          <div class="mt-4 grid grid-cols-3 gap-4 text-sm text-gray-800">
            <div>
              <p class="text-xs text-gray-500 mb-1">총 근로시간</p>
              <p class="font-semibold">{{ formatHours(payroll?.total_hours) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">근로일수</p>
              <p class="font-semibold">{{ formatDays(payroll?.total_work_days) }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">시급</p>
              <p class="font-semibold">{{ formatCurrency(payroll?.hourly_wage) }}</p>
            </div>
          </div>
        </section>

        <!-- Calculation method -->
        <section>
          <h4 class="text-sm font-semibold text-gray-800 mb-2">계산 방식</h4>
          <p class="text-sm text-gray-600 leading-relaxed">
            기본급 = (총 근로시간 - 연장 - 야간 - 휴일) × 시급
          </p>
          <p class="text-xs text-gray-500 mt-2">
            추가수당이 발생하면 연장 · 야간 · 휴일 · 주휴 순서로 가산됩니다.
          </p>
        </section>

        <!-- Breakdown -->
        <section>
          <h4 class="text-sm font-semibold text-gray-800 mb-3">상세 내역</h4>
          <div v-if="breakdownRows.length > 0" class="space-y-3">
            <div
              v-for="row in breakdownRows"
              :key="row.key"
              class="flex items-start justify-between p-3 bg-gray-50 rounded-lg border border-gray-100"
            >
              <div>
                <p class="text-sm font-medium text-gray-800">{{ row.label }}</p>
                <p class="text-xs text-gray-500 mt-1">{{ row.formula }}</p>
              </div>
              <p class="text-base font-semibold text-gray-900 whitespace-nowrap">{{ formatCurrency(row.amount) }}</p>
            </div>
          </div>
          <div v-else class="text-sm text-gray-500 bg-gray-50 rounded-lg p-3 border border-dashed border-gray-200">
            표시할 추가 수당이 없습니다.
          </div>
        </section>

        <!-- Notes -->
        <section class="text-xs text-gray-500 space-y-1">
          <p>· 예상액이며 실제 지급액과 차이가 있을 수 있습니다.</p>
          <p>· 공휴일, 주휴, 4대 보험 및 기타 수당 적용 여부에 따라 달라질 수 있습니다.</p>
        </section>
      </div>

      <div v-else class="text-center text-gray-500 py-10">
        <p class="text-sm font-medium">아직 계산할 급여 정보가 없습니다.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface PayrollBreakdown {
  base_hours: number;
  overtime_hours: number;
  night_hours: number;
  holiday_hours: number;
  weekly_holiday_hours: number;
  base_pay: number;
  overtime_pay: number;
  night_pay: number;
  holiday_pay: number;
  weekly_holiday_pay: number;
}

interface MonthlyPayrollResponse {
  month?: string;
  total_hours?: number;
  total_work_days?: number;
  estimated_salary?: number;
  hourly_wage?: number;
  breakdown?: PayrollBreakdown;
}

const props = defineProps<{ visible: boolean; payroll: MonthlyPayrollResponse | null }>();
const emit = defineEmits<{ (e: 'close'): void }>();

const hasData = computed(() => !!props.payroll);

const payrollMonthLabel = computed(() => {
  if (!props.payroll?.month) return '이번 달';
  const [year, month] = props.payroll.month.split('-');
  if (!year || !month) return props.payroll.month;
  return `${year}년 ${Number(month)}월`;
});

const breakdownRows = computed(() => {
  const breakdown = props.payroll?.breakdown;
  if (!breakdown) return [] as Array<{ key: string; label: string; formula: string; amount: number }>;
  const hourly = props.payroll?.hourly_wage ?? 0;
  const rows: Array<{ key: string; label: string; formula: string; amount: number }> = [];
  const pushRow = (key: string, label: string, hours?: number, amount?: number, extra?: string) => {
    const safeHours = typeof hours === 'number' ? hours : 0;
    const safeAmount = typeof amount === 'number' ? amount : 0;
    if (safeHours <= 0 && safeAmount <= 0) {
      return;
    }
    const hoursText = `${safeHours.toFixed(1)}시간`;
    const baseFormula = `${hoursText} × ${formatCurrency(hourly)}`;
    const detail = extra ? `${baseFormula} ${extra}` : baseFormula;
    rows.push({
      key,
      label,
      formula: `${detail} = ${formatCurrency(safeAmount)}`,
      amount: safeAmount,
    });
  };

  pushRow('base', '기본 근로', breakdown.base_hours, breakdown.base_pay);
  pushRow('overtime', '연장 근로', breakdown.overtime_hours, breakdown.overtime_pay, '× 0.5(가산)');
  pushRow('night', '야간 근로', breakdown.night_hours, breakdown.night_pay, '× 0.5(가산)');
  pushRow('holiday', '휴일 근로', breakdown.holiday_hours, breakdown.holiday_pay, '× 1.0(휴일)');
  pushRow('weekly', '주휴수당', breakdown.weekly_holiday_hours, breakdown.weekly_holiday_pay);

  return rows;
});

const formatCurrency = (value: number | undefined | null = 0) => {
  const safeValue = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  return safeValue.toLocaleString('ko-KR') + '원';
};

const formatHours = (value: number | undefined | null = 0) => {
  const safeValue = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  return `${safeValue.toFixed(1)}시간`;
};

const formatDays = (value: number | undefined | null = 0) => {
  const safeValue = typeof value === 'number' && !Number.isNaN(value) ? value : 0;
  return `${safeValue}일`;
};

function close() {
  emit('close');
}
</script>
