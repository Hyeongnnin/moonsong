<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 pt-20">
    <div class="w-full max-w-md px-4">
      <div class="bg-white shadow-lg rounded-2xl border border-gray-100 p-8">
        <div class="flex justify-center mb-6">
          <img src="@/assets/logo.png" alt="Notav" class="h-10 w-auto mb-2 opacity-80" />
        </div>
        <h2 class="text-2xl font-semibold text-gray-900 mb-6 text-center">계정 찾기</h2>

        <!-- Tabs -->
        <div class="flex border-b border-gray-200 mb-6">
          <button
            class="flex-1 py-2 text-sm font-medium border-b-2 transition-colors duration-200"
            :class="activeTab === 'id' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'id'"
          >
            아이디 찾기
          </button>
          <button
            class="flex-1 py-2 text-sm font-medium border-b-2 transition-colors duration-200"
            :class="activeTab === 'pw' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'"
            @click="activeTab = 'pw'"
          >
            비밀번호 찾기
          </button>
        </div>

        <!-- Find ID Form -->
        <div v-if="activeTab === 'id'" class="space-y-4">
          <p class="text-sm text-gray-500 mb-2">
            가입 시 등록한 이름과 이메일을 입력해주세요.
          </p>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">이름</label>
            <input
              v-model="findIdxName"
              type="text"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              placeholder="이름 입력"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">이메일</label>
            <input
              v-model="findIdxEmail"
              type="email"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
              placeholder="이메일 입력"
            />
          </div>

          <div v-if="findIdResult" class="p-3 bg-blue-50 text-blue-700 rounded-lg text-sm">
            <p class="font-medium">회원님의 아이디:</p>
            <ul class="list-disc list-inside mt-1">
              <li v-for="id in findIdResult" :key="id">{{ id }}</li>
            </ul>
          </div>
          <div v-if="findIdError" class="p-3 bg-red-50 text-red-600 rounded-lg text-sm">
            {{ findIdError }}
          </div>

          <button
            @click="handleFindId"
            :disabled="loading"
            class="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-60 transition-colors"
          >
            {{ loading ? '확인 중...' : '아이디 찾기' }}
          </button>
        </div>

        <!-- Find PW Form -->
        <div v-else class="space-y-4">
          <div v-if="!pwVerified">
            <p class="text-sm text-gray-500 mb-4">
              비밀번호를 재설정하기 위해 본인 확인이 필요합니다.
            </p>
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">아이디</label>
                <input
                  v-model="findPwId"
                  type="text"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="아이디 입력"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">이름</label>
                <input
                  v-model="findPwName"
                  type="text"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="이름 입력"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">이메일</label>
                <input
                  v-model="findPwEmail"
                  type="email"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="이메일 입력"
                />
              </div>
            </div>

             <div v-if="findPwError" class="mt-3 p-3 bg-red-50 text-red-600 rounded-lg text-sm">
              {{ findPwError }}
            </div>

            <button
              @click="handleVerifyUser"
              :disabled="loading"
              class="mt-4 w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-60 transition-colors"
            >
              {{ loading ? '확인 중...' : '확인' }}
            </button>
          </div>

          <!-- Reset Password Form (Shown after verification) -->
          <div v-else class="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
             <p class="text-sm text-green-600 font-medium mb-4">
              본인 확인이 완료되었습니다. 새 비밀번호를 설정해주세요.
            </p>
             <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">새 비밀번호</label>
                <input
                  v-model="newPassword"
                  type="password"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="새 비밀번호"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">새 비밀번호 확인</label>
                <input
                  v-model="newPasswordConfirm"
                  type="password"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="새 비밀번호 확인"
                />
              </div>

             <div v-if="resetError" class="p-3 bg-red-50 text-red-600 rounded-lg text-sm">
              {{ resetError }}
            </div>
             <div v-if="resetSuccess" class="p-3 bg-green-50 text-green-600 rounded-lg text-sm">
              {{ resetSuccess }}
            </div>

             <button
              @click="handleResetPassword"
              :disabled="loading"
              class="w-full py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-60 transition-colors"
            >
              {{ loading ? '변경 중...' : '비밀번호 변경 완료' }}
            </button>
          </div>
        </div>

        <!-- Back to Login -->
        <div class="mt-6 border-t pt-4 text-center">
          <button
            @click="router.push('/login')"
            class="text-sm text-gray-600 hover:text-brand-600 hover:underline transition-colors"
          >
            로그인 페이지로 돌아가기
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { apiClient } from '../api';

const router = useRouter();
const activeTab = ref<'id'|'pw'>('id');
const loading = ref(false);

// Find ID State
const findIdxName = ref('');
const findIdxEmail = ref('');
const findIdResult = ref<string[] | null>(null);
const findIdError = ref('');

// Find PW State
const findPwId = ref('');
const findPwName = ref('');
const findPwEmail = ref('');
const pwVerified = ref(false);
const findPwError = ref('');

// Reset PW State
const newPassword = ref('');
const newPasswordConfirm = ref('');
const resetError = ref('');
const resetSuccess = ref('');

// --- Handlers ---

async function handleFindId() {
  if (!findIdxName.value || !findIdxEmail.value) {
    findIdError.value = '이름과 이메일을 모두 입력해주세요.';
    return;
  }
  loading.value = true;
  findIdError.value = '';
  findIdResult.value = null;

  try {
    const res = await apiClient.post('/accounts/find-id/', {
      name: findIdxName.value,
      email: findIdxEmail.value
    });
    findIdResult.value = res.data.ids;
  } catch (e: any) {
    findIdError.value = e.response?.data?.detail || '아이디 찾기에 실패했습니다.';
  } finally {
    loading.value = false;
  }
}

async function handleVerifyUser() {
   if (!findPwId.value || !findPwName.value || !findPwEmail.value) {
    findPwError.value = '모든 정보를 입력해주세요.';
    return;
  }
  loading.value = true;
  findPwError.value = '';

  try {
    await apiClient.post('/accounts/verify-user/', {
      username: findPwId.value,
      name: findPwName.value,
      email: findPwEmail.value
    });
    pwVerified.value = true;
  } catch (e: any) {
    findPwError.value = e.response?.data?.detail || '정보가 일치하는 사용자를 찾을 수 없습니다.';
  } finally {
    loading.value = false;
  }
}

async function handleResetPassword() {
  if (!newPassword.value || !newPasswordConfirm.value) {
    resetError.value = '새 비밀번호를 입력해주세요.';
    return;
  }
  if (newPassword.value !== newPasswordConfirm.value) {
    resetError.value = '비밀번호가 일치하지 않습니다.';
    return;
  }
  loading.value = true;
  resetError.value = '';
  resetSuccess.value = '';

  try {
    await apiClient.post('/accounts/reset-password/', {
      username: findPwId.value,
      name: findPwName.value,
      email: findPwEmail.value,
      new_password: newPassword.value,
      new_password_confirm: newPasswordConfirm.value
    });
    resetSuccess.value = '비밀번호가 변경되었습니다. 로그인 페이지로 이동합니다.';
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } catch (e: any) {
    resetError.value = e.response?.data?.detail || '비밀번호 변경에 실패했습니다.';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* Optional: fade in animation */
.animate-in {
  animation-duration: 0.3s;
  animation-fill-mode: both;
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.fade-in { animation-name: fadeIn; }

@keyframes slideInFromBottom {
  from { transform: translateY(10px); }
  to { transform: translateY(0); }
}
.slide-in-from-bottom-2 { animation-name: slideInFromBottom; }
</style>
