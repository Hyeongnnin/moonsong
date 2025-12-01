<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 pt-16">
    <div class="w-full max-w-md px-4">
      <div class="bg-white shadow-lg rounded-2xl border border-gray-100 p-8">
        <h2 class="text-2xl font-semibold text-gray-900 mb-2">로그인</h2>
        <p class="text-sm text-gray-500 mb-6">
          가입하신 아이디와 비밀번호를 입력해주세요.
        </p>

        <div class="flex mb-6 rounded-full border border-gray-200 bg-gray-50 p-1 text-sm">
          <button
            type="button"
            class="flex-1 py-2 rounded-full transition-colors"
            :class="userType === 'individual' ? 'bg-white text-brand-600 shadow-sm' : 'text-gray-500'"
            @click="userType = 'individual'"
          >
            개인회원
          </button>
          <button
            type="button"
            class="flex-1 py-2 rounded-full transition-colors"
            :class="userType === 'expert' ? 'bg-white text-brand-600 shadow-sm' : 'text-gray-500'"
            @click="userType = 'expert'"
          >
            전문가 회원
          </button>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
            <input
              v-model="username"
              type="text"
              autocomplete="username"
              required
              class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              placeholder="아이디를 입력하세요"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
            <input
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
              class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              placeholder="비밀번호를 입력하세요"
            />
          </div>

          <div class="flex items-center justify-between text-xs text-gray-500">
            <label class="inline-flex items-center gap-2">
              <input
                v-model="rememberId"
                type="checkbox"
                class="rounded border-gray-300 text-brand-600 focus:ring-brand-500"
              />
              <span>아이디 저장</span>
            </label>
            <button type="button" class="hover:underline">
              아이디 / 비밀번호 찾기
            </button>
          </div>

          <button
            type="submit"
            class="w-full inline-flex justify-center items-center px-4 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
            :disabled="loading"
          >
            <span v-if="!loading">로그인</span>
            <span v-else>로그인 중...</span>
          </button>
        </form>

        <p v-if="errorMessage" class="mt-3 text-sm text-red-600">
          {{ errorMessage }}
        </p>

        <div class="mt-6 border-t pt-4 text-sm text-gray-600">
          <p>아직 계정이 없으신가요?</p>
          <button
            type="button"
            class="mt-2 w-full inline-flex justify-center items-center px-4 py-2 rounded-lg border border-gray-300 text-gray-800 hover:bg-gray-50"
            @click="$emit('navigate', 'signup')"
          >
            회원가입 하러가기
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { login } from "../api";

const emit = defineEmits<{
  (e: "navigate", page: "landing" | "login" | "signup" | "dashboard"): void;
  (e: "logged-in", token: string): void;
}>();

type UserType = "individual" | "expert";

const userType = ref<UserType>("individual");
const username = ref("");
const password = ref("");
const rememberId = ref(false);
const loading = ref(false);
const errorMessage = ref("");

watch(rememberId, (val) => {
  if (typeof window === "undefined") return;
  if (val) {
    window.localStorage.setItem("saved_username", username.value);
  } else {
    window.localStorage.removeItem("saved_username");
  }
});

if (typeof window !== "undefined") {
  const saved = window.localStorage.getItem("saved_username");
  if (saved) {
    username.value = saved;
    rememberId.value = true;
  }
}

async function handleLogin() {
  loading.value = true;
  errorMessage.value = "";

  try {
    const data = await login(username.value, password.value);
    // 토큰을 로컬스토리지에 저장하여 axios 인터셉터가 모든 요청에 자동 첨부하도록 함
    try {
      window.localStorage.setItem("access", data.access);
      if (data.refresh) window.localStorage.setItem("refresh", data.refresh);
    } catch {}
    emit("logged-in", data.access);
    emit("navigate", "dashboard");
  } catch (error: any) {
    errorMessage.value =
      error?.response?.data?.detail ||
      "로그인에 실패했습니다. 아이디와 비밀번호를 다시 확인해주세요.";
  } finally {
    loading.value = false;
  }
}
</script>
