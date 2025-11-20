<template>
  <div class="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-16">
    <div class="w-full max-w-xl bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <h1 class="text-2xl font-semibold text-center mb-6">회원 유형 선택</h1>
      <p class="text-sm text-gray-600 text-center mb-8">
        일반 회원과 노무사 회원 중 회원 유형을 선택해 주세요.
      </p>
      <div class="grid md:grid-cols-2 gap-4">
        <button
          class="border rounded-xl p-6 text-left hover:border-blue-500 hover:bg-blue-50"
          @click="$router.push('/signup/personal')"
        >
          <h2 class="font-semibold mb-2">일반 회원</h2>
          <p class="text-xs text-gray-600">
            근로현장 법률 진단을 받고 노무사 상담을 이용하고 싶은 아르바이트생·청년 회원
          </p>
        </button>
        <button
          class="border rounded-xl p-6 text-left hover:border-blue-500 hover:bg-blue-50"
          @click="$router.push('/signup/lawyer')"
        >
          <h2 class="font-semibold mb-2">노무사 회원</h2>
          <p class="text-xs text-gray-600">
            근로 상담과 사건 진행을 희망하는 의뢰인과 매칭되고 싶은 공인노무사/사무소 회원
          </p>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts"></script>
