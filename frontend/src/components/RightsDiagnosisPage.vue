<template>
  <div class="bg-gray-50 py-16 px-4 min-h-screen">
    <div class="max-w-5xl mx-auto">
      <div class="text-center mb-12">
        <p class="text-sm font-semibold text-blue-600 mb-2">AI 기반 노동법 진단</p>
        <h1 class="text-3xl md:text-4xl font-bold text-gray-900 mb-3">회사 노동법 위험도 진단</h1>
        <p class="text-gray-600">
          {{ greeting }} 근로자님의 정보로 사업장 위험도를 분석하고, 개선해야 할 항목을 알려드립니다.
        </p>
      </div>

      <div class="grid md:grid-cols-2 gap-8">
        <section class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <h2 class="text-xl font-semibold text-gray-900 mb-6">사업장 정보 입력</h2>
          <form class="space-y-5" @submit.prevent="runDiagnosis">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">회사명</label>
              <input v-model="form.companyName" type="text" class="input" placeholder="예: 노타브 컴퍼니" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">업종</label>
              <input v-model="form.industry" type="text" class="input" placeholder="예: IT 서비스" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">상시 근로자 수</label>
                <input v-model.number="form.employeeCount" type="number" min="1" class="input" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">주 평균 근로시간</label>
                <input v-model.number="form.weeklyHours" type="number" min="1" class="input" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">주당 연장근로 시간</label>
                <input v-model.number="form.weeklyOvertime" type="number" min="0" class="input" />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">연장수당 지급</label>
                <select v-model="form.providesOvertimePay" class="input">
                  <option :value="true">예</option>
                  <option :value="false">아니오</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">근로계약서 작성 여부</label>
                <select v-model="form.hasWrittenContract" class="input">
                  <option :value="true">예</option>
                  <option :value="false">아니오</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">연차/휴가 제공</label>
                <select v-model="form.providesPaidLeave" class="input">
                  <option :value="true">예</option>
                  <option :value="false">아니오</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">안전/보건 교육 실시</label>
              <select v-model="form.hasSafetyTraining" class="input">
                <option :value="true">예</option>
                <option :value="false">아니오</option>
              </select>
            </div>
            <button
              type="submit"
              class="w-full h-12 rounded-xl bg-blue-600 text-white font-semibold hover:bg-blue-700 transition"
              :disabled="isAnalyzing"
            >
              {{ isAnalyzing ? '진단 중...' : '노동법 진단하기' }}
            </button>
          </form>
        </section>

        <section class="space-y-6">
          <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">진단 결과 요약</h2>
            <div v-if="results.length" class="space-y-4">
              <div :class="['rounded-xl p-4', riskBannerClass]">
                <p class="text-sm font-semibold uppercase tracking-wide">{{ riskLabel }}</p>
                <p class="text-lg font-semibold mt-1">{{ summaryMessage }}</p>
                <p class="text-sm opacity-80">위험 수준을 낮추기 위해 권장 조치들을 확인해 주세요.</p>
              </div>
              <ul class="space-y-3">
                <li
                  v-for="item in results"
                  :key="item.title"
                  class="border rounded-xl p-4 flex flex-col gap-1"
                  :class="resultBorderClass(item.status)"
                >
                  <div class="flex items-center justify-between">
                    <p class="font-semibold text-gray-900">{{ item.title }}</p>
                    <span :class="statusPillClass(item.status)">{{ statusLabel(item.status) }}</span>
                  </div>
                  <p class="text-sm text-gray-600">{{ item.message }}</p>
                  <p class="text-sm text-blue-600">{{ item.action }}</p>
                </li>
              </ul>
            </div>
            <p v-else class="text-gray-500">
              사업장 정보를 입력하면 위험도를 분석해 드립니다. (연장근로, 근로계약서, 연차 사용 여부 등)
            </p>
          </div>

          <div class="bg-blue-50 border border-blue-100 rounded-2xl p-6">
            <h3 class="text-lg font-semibold text-blue-900 mb-2">다음 단계</h3>
            <p class="text-sm text-blue-800 mb-3">
              위험 지표가 높게 나타났다면 전문가와 상담해 구체적인 대응 전략을 마련해 보세요.
            </p>
            <ul class="text-sm text-blue-900 list-disc list-inside space-y-1">
              <li>연장/야간수당 산정 방식 검토</li>
              <li>근로계약서 필수 기재 항목 확인</li>
              <li>50인 이상 사업장 의무 교육 이행 여부 점검</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useAuth } from '../composables/useAuth'

type ResultStatus = 'safe' | 'warning' | 'danger'

interface DiagnosisResult {
  title: string
  status: ResultStatus
  message: string
  action: string
}

const { displayName } = useAuth()

const greeting = computed(() => {
  if (!displayName.value) {
    return '노타브'
  }
  return `${displayName.value}`
})

const form = reactive({
  companyName: '',
  industry: '',
  employeeCount: 5,
  weeklyHours: 40,
  weeklyOvertime: 5,
  providesOvertimePay: true,
  providesPaidLeave: true,
  hasWrittenContract: true,
  hasSafetyTraining: true,
})

const results = ref<DiagnosisResult[]>([])
const riskLevel = ref<ResultStatus>('safe')
const isAnalyzing = ref(false)

const statusLabel = (status: ResultStatus) => {
  if (status === 'danger') return '위험'
  if (status === 'warning') return '주의'
  return '양호'
}

const statusPillClass = (status: ResultStatus) => {
  if (status === 'danger') {
    return 'text-red-700 bg-red-100 px-3 py-1 rounded-full text-xs font-semibold'
  }
  if (status === 'warning') {
    return 'text-amber-700 bg-amber-100 px-3 py-1 rounded-full text-xs font-semibold'
  }
  return 'text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full text-xs font-semibold'
}

const resultBorderClass = (status: ResultStatus) => {
  if (status === 'danger') return 'border-red-200 bg-red-50'
  if (status === 'warning') return 'border-amber-200 bg-amber-50'
  return 'border-emerald-200 bg-emerald-50'
}

const summaryMessage = computed(() => {
  if (!results.value.length) return ''
  if (riskLevel.value === 'danger') {
    return '즉시 개선이 필요한 항목이 있습니다.'
  }
  if (riskLevel.value === 'warning') {
    return '법 위반 위험 요소가 발견되었습니다.'
  }
  return '전반적으로 양호한 편이지만 계속 관리가 필요합니다.'
})

const riskBannerClass = computed(() => {
  if (riskLevel.value === 'danger') return 'bg-red-600 text-white'
  if (riskLevel.value === 'warning') return 'bg-amber-500 text-white'
  return 'bg-emerald-500 text-white'
})

const riskLabel = computed(() => {
  if (riskLevel.value === 'danger') return 'High Risk'
  if (riskLevel.value === 'warning') return 'Needs Attention'
  return 'Good'
})

const runDiagnosis = () => {
  isAnalyzing.value = true
  const newResults: DiagnosisResult[] = []

  if (form.weeklyHours > 52) {
    newResults.push({
      title: '근로시간 상한 초과',
      status: 'danger',
      message: '주당 52시간을 초과하여 근무하고 있습니다.',
      action: '연장근로 한도를 재조정하거나 교대제 도입을 검토하세요.',
    })
  } else if (form.weeklyHours > 40) {
    newResults.push({
      title: '연장근로 관리 필요',
      status: form.providesOvertimePay ? 'warning' : 'danger',
      message: '연장근로가 발생하고 있어 추가 관리가 필요합니다.',
      action: '연장근로수당, 주휴수당 지급 내역을 점검하세요.',
    })
  } else {
    newResults.push({
      title: '법정 근로시간 준수',
      status: 'safe',
      message: '법정 근로시간을 준수하고 있습니다.',
      action: '근로일지 및 스케줄을 지속 관리하세요.',
    })
  }

  if (form.weeklyOvertime > 0 && !form.providesOvertimePay) {
    newResults.push({
      title: '연장/야간수당 미지급',
      status: 'danger',
      message: '연장근로가 발생하지만 수당이 지급되지 않고 있습니다.',
      action: '통상임금 산정 방식과 지급 내역을 즉시 확인하세요.',
    })
  } else if (form.weeklyOvertime > 0) {
    newResults.push({
      title: '연장수당 지급 중',
      status: 'warning',
      message: '연장근로가 지속 발생하고 있습니다.',
      action: '연장근로 사유를 기록하고, 인력 충원을 검토하세요.',
    })
  }

  if (!form.hasWrittenContract) {
    newResults.push({
      title: '근로계약서 미작성',
      status: 'warning',
      message: '근로계약서 미작성은 500만 원 이하 벌금 대상입니다.',
      action: '필수 기재 항목(임금, 소정근로시간 등)이 포함된 서면 계약을 즉시 체결하세요.',
    })
  }

  if (!form.providesPaidLeave) {
    newResults.push({
      title: '연차/휴가 관리 미흡',
      status: 'warning',
      message: '연차 사용 촉진 및 대체휴일 부여 절차를 마련해야 합니다.',
      action: '연차사용계획서, 대체휴일 운영규정을 정비하세요.',
    })
  }

  if (form.employeeCount >= 50 && !form.hasSafetyTraining) {
    newResults.push({
      title: '법정 의무교육 미이행',
      status: 'danger',
      message: '50인 이상 사업장은 연 1회 이상 안전/보건 교육이 의무입니다.',
      action: '교육기관과 일정을 확정하고, 이수 명부를 보관하세요.',
    })
  } else if (!form.hasSafetyTraining) {
    newResults.push({
      title: '안전교육 필요',
      status: 'warning',
      message: '근로자 안전보건 교육을 정기적으로 실시해야 합니다.',
      action: '교육 이수 증빙자료를 마련하고 정기 스케줄을 수립하세요.',
    })
  }

  const hasDanger = newResults.some((item) => item.status === 'danger')
  const hasWarning = newResults.some((item) => item.status === 'warning')

  riskLevel.value = hasDanger ? 'danger' : hasWarning ? 'warning' : 'safe'
  results.value = newResults
  isAnalyzing.value = false
}
</script>

<style scoped>
.input {
  @apply w-full h-11 border rounded-xl px-3 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-200;
}
</style>
