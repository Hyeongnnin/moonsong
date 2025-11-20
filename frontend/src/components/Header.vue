<template>
  <header class="w-full border-b bg-white">
    <div class="max-w-6xl mx-auto flex items-center justify-between px-4 py-3">
      <div class="font-semibold text-lg cursor-pointer" @click="goHome">
        노타브
      </div>
      <nav v-if="!isLoggedIn" class="flex items-center gap-4 text-sm">
        <button class="text-gray-600 hover:text-gray-900" @click="router.push('/login')">
          로그인
        </button>
        <button
          class="px-4 py-2 rounded-full bg-blue-600 text-white text-sm hover:bg-blue-700"
          @click="router.push('/signup')"
        >
          회원가입
        </button>
      </nav>
      <div v-else class="flex flex-wrap items-center gap-3 text-sm">
        <span class="font-semibold text-gray-900">
          {{ displayName }}님 환영합니다!
        </span>
        <button
          class="px-4 py-2 rounded-full bg-blue-600 text-white text-sm hover:bg-blue-700"
          @click="router.push('/rights-check')"
        >
          내 권리 알아보기
        </button>
        <button class="text-gray-600 hover:text-gray-900" @click="handleLogout">
          로그아웃
        </button>
      </div>
    </div>
  </header>
</template>
<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'

const router = useRouter()
const { isLoggedIn, displayName, logout } = useAuth()

const goHome = () => {
  router.push('/')
}

const handleLogout = () => {
  logout()
  router.push('/')
}
</script>
