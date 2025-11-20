<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-24">
    <div class="w-full max-w-xl bg-white rounded-lg shadow-sm border border-gray-200 p-8 md:p-10">
      <h1 class="text-2xl font-semibold text-center mb-6">일반 회원 가입</h1>
      <form class="space-y-4" @submit.prevent="handleSubmit">
        <div class="space-y-1">
          <label class="text-sm font-medium">아이디</label>
          <input
            v-model="form.username"
            type="text"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="아이디를 입력해 주세요"
            required
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">비밀번호</label>
          <input
            v-model="form.password"
            type="password"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="비밀번호를 입력해 주세요"
            required
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">비밀번호 확인</label>
          <input
            v-model="passwordConfirm"
            type="password"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="다시 한 번 입력해 주세요"
            required
          />
          <p v-if="passwordConfirm && form.password !== passwordConfirm" class="text-xs text-red-500">
            비밀번호가 일치하지 않습니다.
          </p>
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">이메일</label>
          <input
            v-model="form.email"
            type="email"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="이메일을 입력해 주세요"
            required
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">이름</label>
          <input
            v-model="form.name"
            type="text"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="이름을 입력해 주세요"
            required
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">휴대폰 번호</label>
          <input
            v-model="form.phone_number"
            type="tel"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="'-' 없이 숫자만 입력"
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">생년월일</label>
          <input
            v-model="form.birth_date"
            type="text"
            maxlength="8"
            class="w-full h-11 border rounded px-3 bg-gray-50"
            placeholder="YYYYMMDD"
            @input="onlyNumber('birth_date')"
          />
        </div>
        <div class="space-y-1">
          <label class="text-sm font-medium">성별</label>
          <div class="flex gap-6">
            <label class="flex items-center gap-2 text-sm">
              <input type="radio" value="male" v-model="form.gender" />
              <span>남성</span>
            </label>
            <label class="flex items-center gap-2 text-sm">
              <input type="radio" value="female" v-model="form.gender" />
              <span>여성</span>
            </label>
          </div>
        </div>
        <p v-if="errorMessage" class="text-sm text-red-500 text-center">{{ errorMessage }}</p>
        <button
          type="submit"
          class="w-full h-11 rounded bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
          :disabled="isSubmitting"
        >
          {{ isSubmitting ? '가입 처리 중...' : '회원가입' }}
        </button>
      </form>
      <p class="text-xs text-gray-500 text-center mt-4">
        이미 계정이 있으신가요?
        <button class="text-blue-600 hover:underline" @click="$router.push('/login')">
          로그인
        </button>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AxiosError } from 'axios'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import api from '../services/api'

const form = reactive({
  username: '',
  password: '',
  email: '',
  name: '',
  phone_number: '',
  birth_date: '',
  gender: '',
})

const passwordConfirm = ref('')
const isSubmitting = ref(false)
const errorMessage = ref('')

const router = useRouter()
const { setUser } = useAuth()

const onlyNumber = (key: 'birth_date') => {
  form[key] = form[key].replace(/\D/g, '').slice(0, 8)
}

const handleSubmit = async () => {
  if (form.password !== passwordConfirm.value) {
    errorMessage.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  if (isSubmitting.value) return

  errorMessage.value = ''
  isSubmitting.value = true

  try {
    const { data } = await api.post('/api/accounts/personal-signup/', form)
    setUser(data)
    router.push('/')
  } catch (error) {
    const axiosError = error as AxiosError<Record<string, string[]>>
    if (axiosError.response?.data) {
      const messages = Object.values(axiosError.response.data).flat()
      errorMessage.value = messages[0] || '회원가입 중 오류가 발생했습니다.'
    } else {
      errorMessage.value = '회원가입 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>
