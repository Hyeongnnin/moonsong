<template>
  <header class="fixed top-0 inset-x-0 bg-white/80 backdrop-blur border-b z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
      <div class="flex items-center gap-2">
        <span class="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600 text-white font-bold">
          N
        </span>
        <div class="flex flex-col leading-tight">
          <span class="font-semibold text-gray-900">Notav</span>
          <span class="text-xs text-gray-500">근로환경 통합 관리 플랫폼</span>
        </div>
      </div>

      <nav class="hidden md:flex items-center gap-6 text-sm">
        <button class="text-gray-600 hover:text-gray-900" @click="$emit('navigate', 'landing')">
          홈
        </button>
        <button class="text-gray-600 hover:text-gray-900" @click="$emit('navigate', 'signup')">
          회원가입
        </button>
      </nav>

      <div class="flex items-center gap-3">
        <button
          class="hidden sm:inline-flex items-center px-3 py-1.5 text-sm rounded-full border border-gray-200 text-gray-700 hover:bg-gray-50"
          @click="$emit('navigate', 'signup')"
        >
          무료 진단 시작
        </button>
        <button
          class="inline-flex items-center px-4 py-2 text-sm font-medium rounded-full bg-brand-600 text-white hover:bg-brand-700"
          @click="$emit('navigate', 'login')"
        >
          로그인
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  currentPage: "landing" | "login" | "signup" | "dashboard";
}>();

defineEmits<{
  (e: "navigate", page: "landing" | "login" | "signup" | "dashboard"): void;
}>();
</script>
