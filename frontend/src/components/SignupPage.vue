<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 pt-16">
    <div class="w-full max-w-lg px-4">
      <div class="bg-white shadow-lg rounded-2xl border border-gray-100 p-8 space-y-6">
        <div>
          <h2 class="text-2xl font-semibold text-gray-900 mb-2">회원가입</h2>
          <p class="text-sm text-gray-500">
            아래에서 회원 유형을 선택한 뒤, 기본 정보를 입력해주세요.
          </p>
        </div>

        <div class="flex rounded-full border border-gray-200 bg-gray-50 p-1 text-sm">
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

        <form @submit.prevent="handleSignup" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
            <input
              v-model="username"
              data-field="username"
              type="text"
              required
              :class="[
                'w-full px-3 py-2 rounded-lg text-sm focus:outline-none',
                fieldErrors.username
                  ? 'border-red-600 ring-2 ring-red-100 outline-none'
                  : 'border border-gray-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
              ]"
              @input="clearError('username')"
              placeholder="사용하실 아이디를 입력하세요"
            />
            <p v-if="fieldErrors.username" class="mt-1 text-sm text-red-600">
              {{ fieldErrors.username.join(' ') }}
            </p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">이메일</label>
            <input
              v-model="email"
              data-field="email"
              type="email"
              required
              :class="[
                'w-full px-3 py-2 rounded-lg text-sm focus:outline-none',
                fieldErrors.email
                  ? 'border-red-600 ring-2 ring-red-100 outline-none'
                  : 'border border-gray-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
              ]"
              @input="clearError('email')"
              placeholder="example@email.com"
            />
            <p v-if="fieldErrors.email" class="mt-1 text-sm text-red-600">
              {{ fieldErrors.email.join(' ') }}
            </p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">비밀번호</label>
            <input
              v-model="password"
              data-field="password"
              type="password"
              required
              :class="[
                'w-full px-3 py-2 rounded-lg text-sm focus:outline-none',
                fieldErrors.password
                  ? 'border-red-600 ring-2 ring-red-100 outline-none'
                  : 'border border-gray-300 focus:ring-2 focus:ring-brand-500 focus:border-brand-500',
              ]"
              @input="clearError('password')"
              placeholder="8자 이상, 영문/숫자/기호 조합"
            />
            <p v-if="fieldErrors.password" class="mt-1 text-sm text-red-600">
              {{ fieldErrors.password.join(' ') }}
            </p>
          </div>

          <button
            type="submit"
            class="w-full inline-flex justify-center items-center px-4 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-60"
            :disabled="loading"
          >
            <span v-if="!loading">가입하기</span>
            <span v-else>가입 처리 중...</span>
          </button>
        </form>

        <p v-if="message" class="mt-2 text-sm" :class="messageType === 'error' ? 'text-red-600' : 'text-green-600'">
          {{ message }}
        </p>

        <div class="pt-2 text-sm text-gray-600">
          <button
            type="button"
            class="hover:underline"
            @click="$emit('navigate', 'login')"
          >
            이미 계정이 있으신가요? 로그인하기
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick } from "vue";
import { signup } from "../api";

const emit = defineEmits<{
  (e: "navigate", page: "landing" | "login" | "signup" | "dashboard"): void;
}>();

type UserType = "individual" | "expert";

const userType = ref<UserType>("individual");
const username = ref("");
const email = ref("");
const password = ref("");
const loading = ref(false);
const message = ref("");
const messageType = ref<"error" | "success">("success");

const fieldErrors = reactive<Record<string, string[]>>({});

function clearFieldErrors() {
  Object.keys(fieldErrors).forEach((k) => {
    delete (fieldErrors as any)[k];
  });
}

function clearError(key: string) {
  delete (fieldErrors as any)[key];
  // clear summary message when user starts to fix
  message.value = "";
}

async function handleSignup() {
  loading.value = true;
  message.value = "";
  messageType.value = "error";
  clearFieldErrors();

  try {
    await signup(username.value, email.value, password.value);
    messageType.value = "success";
    message.value = "가입이 완료되었습니다. 이제 로그인할 수 있어요.";
  } catch (error: any) {
    // Network / CORS failures may not have a response
    if (!error?.response) {
      console.error("Signup request failed (no response)", error);
      message.value = "서버에 연결할 수 없습니다. 네트워크 또는 CORS 설정을 확인해주세요.";
      return;
    }

    const data = error?.response?.data;
    if (data?.detail) {
      message.value = data.detail;
    } else if (data && typeof data === "object") {
      // Populate fieldErrors for per-field display
      for (const [k, v] of Object.entries(data)) {
        if (Array.isArray(v)) {
          (fieldErrors as any)[k] = v.map(String);
        } else if (typeof v === "string") {
          (fieldErrors as any)[k] = [v];
        } else if (v && typeof v === "object") {
          (fieldErrors as any)[k] = [JSON.stringify(v)];
        }
      }
      // also set a combined message for summary and focus first error
      const parts: string[] = [];
      Object.values(fieldErrors).forEach((arr) => parts.push(...arr));
      message.value = parts.join(" ") || "입력하신 정보를 다시 확인해주세요.";
      // focus first invalid input
      await nextTick();
      const firstKey = Object.keys(fieldErrors)[0];
      if (firstKey) {
        const el = document.querySelector(`[data-field="${firstKey}"]`) as HTMLElement | null;
        el?.focus();
      }
    } else {
      message.value = "가입 중 오류가 발생했습니다. 입력하신 정보를 다시 확인해주세요.";
    }
  } finally {
    loading.value = false;
  }
}
</script>
