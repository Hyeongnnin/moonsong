<template>
  <header class="fixed top-0 inset-x-0 bg-white/80 backdrop-blur border-b z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-20">





      <div class="flex items-center gap-3 cursor-pointer" @click="$emit('navigate', 'landing')">
        <img src="@/assets/logo.png" alt="Notav" class="h-10 w-auto" />
      </div>




      <div class="flex items-center gap-3">
        <button
          class="hidden sm:inline-flex items-center px-3 py-1.5 text-sm rounded-full border border-gray-200 text-gray-700 hover:bg-gray-50"
          @click="$emit('navigate', 'signup')"
        >
          회원가입
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
  currentPage?: "landing" | "login" | "signup" | "dashboard";
}>();

defineEmits<{
  (e: "navigate", page: "landing" | "login" | "signup" | "dashboard"): void;
}>();
</script>
