<template>
  <div class="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-16">
    <div class="w-full max-w-md bg-white rounded-lg shadow-sm border border-gray-200 p-8">
      <h1 class="text-2xl font-semibold text-center mb-6">로그인</h1>
      <form class="space-y-4" @submit.prevent="handleLogin">
        <div class="space-y-1">
          <label class="text-sm font-medium">아이디</label>
          <input
            v-model="username"
            type="text"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="아이디를 입력해 주세요"
            required
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">비밀번호</label>
          <input
            v-model="password"
            type="password"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="비밀번호를 입력해 주세요"
            required
          />
        </div>
        <p v-if="errorMessage" class="text-sm text-red-500 text-center">{{ errorMessage }}</p>
        <button
          type="submit"
          class="w-full h-11 rounded bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
          :disabled="isLoading"
        >
          {{ isLoading ? '로그인 중...' : '로그인' }}
        </button>
      </form>
      <p class="text-xs text-gray-500 text-center mt-4">
        아직 계정이 없으신가요?
        <button class="text-blue-600 hover:underline" @click="$router.push('/signup')">
          회원가입
        </button>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AxiosError } from 'axios'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import api from '../services/api'

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

const router = useRouter()
const { setUser } = useAuth()

const handleLogin = async () => {
  if (isLoading.value) return
  errorMessage.value = ''
  isLoading.value = true

  try {
    const { data } = await api.post('/api/accounts/login/', {
      username: username.value,
      password: password.value,
    })
    setUser(data)
    router.push('/')
  } catch (error) {
    const axiosError = error as AxiosError<{ detail?: string }>
    if (axiosError.response?.data?.detail) {
      errorMessage.value = axiosError.response.data.detail
    } else {
      errorMessage.value = '로그인에 실패했습니다. 잠시 후 다시 시도해 주세요.'
    }
  } finally {
    isLoading.value = false
  }
}
</script>
