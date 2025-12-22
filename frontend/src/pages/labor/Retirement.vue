<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <div class="mb-6">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">퇴직금 상세 정보</h2>
      <p class="text-sm text-gray-600">입력하신 근로 정보를 바탕으로 산출된 퇴직금 예상 내역입니다.</p>
    </div>

    <!-- 주 메인 카드 -->
    <div class="grid md:grid-cols-2 gap-6">
      <SeverancePayCard :activeJob="activeJob" />
      
      <div class="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h4 class="text-sm font-bold text-blue-900 mb-3 flex items-center gap-2">
           <span class="text-lg">💡</span> 퇴직금 지급 안내
        </h4>
        <ul class="space-y-3 text-xs text-blue-800 leading-relaxed">
          <li class="flex gap-2">
            <span class="font-bold text-blue-900">•</span>
            <span>재직기간 1년 이상, 1주 소정근로시간 15시간 이상의 근로자가 퇴직할 때 발생합니다.</span>
          </li>
          <li class="flex gap-2">
             <span class="font-bold text-blue-900">•</span>
             <span>평균임금 산정 시 최근 3개월(90일)간 지급된 임금총액을 그 기간의 총 일수로 나누어 계산합니다.</span>
          </li>
          <li class="flex gap-2">
             <span class="font-bold text-blue-900">•</span>
             <span>평균임금이 통상임금보다 적을 경우 통상임금을 평균임금으로 적용합니다.</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SeverancePayCard from '../../components/SeverancePayCard.vue';
import { useJob } from '../../stores/jobStore';

const { activeJob } = useJob();
</script>

<style scoped>
</style>
