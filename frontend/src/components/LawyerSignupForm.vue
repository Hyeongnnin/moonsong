<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-24">
    <div class="w-full max-w-2xl bg-white rounded-lg shadow-sm border border-gray-200 p-8 md:p-12">
      <div class="mb-8">
        <div class="text-center mb-4">
          <div class="inline-block px-4 py-1 bg-orange-100 text-orange-700 rounded-full mb-2">
            노타브
          </div>
        </div>
        <h1 class="text-3xl text-center mb-2">변호사 등록 제안 회원가입</h1>
        <div class="w-full h-px bg-gray-300 mt-6"></div>
      </div>

      <form class="space-y-6" @submit.prevent="handleSubmit">
        <!-- 아이디 -->
        <div class="space-y-2">
          <label class="text-base">
            아이디 <span class="text-red-500">*</span>
          </label>
          <div class="flex gap-2">
            <input
              v-model="form.username"
              type="text"
              placeholder="아이디를 입력해 주세요"
              class="flex-1 h-12 bg-gray-50 border rounded px-3"
              required
            />
            <button
              type="button"
              class="px-6 bg-gray-200 text-gray-700 hover:bg-gray-300 h-12 whitespace-nowrap rounded"
              @click="checkUsername"
            >
              중복 확인
            </button>
          </div>
        </div>

        <!-- 비밀번호 -->
        <div class="space-y-2">
          <label class="text-base">
            비밀번호 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.password"
            type="password"
            placeholder="비밀번호를 입력해 주세요"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
            required
          />
        </div>

        <!-- 비밀번호 확인 -->
        <div class="space-y-2">
          <label class="text-base">
            비밀번호 확인 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="passwordConfirm"
            type="password"
            placeholder="다시 한 번 입력해 주세요"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
            required
          />
          <p v-if="passwordConfirm && form.password !== passwordConfirm" class="text-sm text-red-500">
            비밀번호가 일치하지 않습니다.
          </p>
        </div>

        <!-- 이메일 -->
        <div class="space-y-2">
          <label class="text-base">
            이메일 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.email"
            type="email"
            placeholder="이메일을 입력해 주세요"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
            required
          />
        </div>

        <!-- 이름 -->
        <div class="space-y-2">
          <label class="text-base">
            이름 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.name"
            type="text"
            placeholder="이름을 입력해 주세요"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
            required
          />
        </div>

        <!-- 휴대폰번호 -->
        <div class="space-y-2">
          <label class="text-base">
            휴대폰번호 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.phone_number"
            type="tel"
            placeholder="휴대폰 번호 '-' 제외하고 입력"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
          />
        </div>

        <!-- 생년월일 -->
        <div class="space-y-2">
          <label class="text-base">
            생년월일 <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.birth_date"
            type="text"
            maxlength="8"
            placeholder="YYYYMMDD 형식, 8자리"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
            @input="onlyNumber('birth_date')"
          />
        </div>

        <!-- 성별 -->
        <div class="space-y-3">
          <label class="text-base">
            성별 <span class="text-red-500">*</span>
          </label>
          <div class="flex gap-6">
            <label class="flex items-center gap-2">
              <input type="radio" value="male" v-model="form.gender" />
              <span>남성</span>
            </label>
            <label class="flex items-center gap-2">
              <input type="radio" value="female" v-model="form.gender" />
              <span>여성</span>
            </label>
          </div>
        </div>

        <!-- 자격증명 -->
        <div class="space-y-2">
          <label class="text-base">
            자격증명 (면허번호) <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.license_number"
            type="text"
            placeholder="노무사 면허번호를 입력해 주세요"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
            required
          />
        </div>

        <!-- 사무소명 -->
        <div class="space-y-2">
          <label class="text-base">
            사무소명 (선택)
          </label>
          <input
            v-model="form.office_name"
            type="text"
            placeholder="사무소명을 입력해 주세요"
            class="h-12 bg-gray-50 border rounded px-3 w-full"
          />
        </div>

        <!-- 경력사항 -->
        <div class="space-y-2">
          <label class="text-base">
            경력사항
          </label>
          <textarea
            v-model="form.career"
            placeholder="주요 경력사항을 입력해 주세요 (여러 줄 입력 가능)"
            class="min-h-[100px] bg-gray-50 border rounded px-3 py-2 w-full resize-none text-sm"
          />
        </div>

        <!-- 자기소개 -->
        <div class="space-y-2">
          <label class="text-base">
            자기소개
          </label>
          <textarea
            v-model="form.introduction"
            placeholder="간단한 자기소개를 입력해 주세요"
            class="min-h-[100px] bg-gray-50 border rounded px-3 py-2 w-full resize-none text-sm"
          />
        </div>

        <!-- 등록경로 -->
        <div class="space-y-2">
          <label class="text-base">
            등록경로
          </label>
          <select v-model="form.signup_source" class="h-12 bg-gray-50 border rounded px-3 w-full text-sm">
            <option value="">선택해 주세요</option>
            <option value="recommendation">지인 추천</option>
            <option value="search">인터넷 검색</option>
            <option value="advertisement">광고</option>
            <option value="association">노무사 협회</option>
            <option value="other">기타</option>
          </select>
        </div>

        <div class="pt-6">
          <button
            type="submit"
            class="w-full bg-gray-300 text-gray-700 hover:bg-blue-600 hover:text-white h-14 rounded transition-colors"
          >
            가입신청
          </button>
          <p class="text-sm text-gray-500 text-center mt-4">
            ※ 가입 신청 후 관리자 승인이 완료되면 서비스를 이용하실 수 있습니다.
          </p>
        </div>
      </form>

      <div class="mt-8 text-center">
        <p class="text-gray-600">
          이미 계정이 있으신가요?
          <button class="text-blue-600 hover:underline" @click="$router.push('/login')">
            로그인
          </button>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AxiosError } from 'axios'
import { reactive, ref } from 'vue'
import api from '../services/api'

const form = reactive({
  username: '',
  password: '',
  email: '',
  name: '',
  phone_number: '',
  birth_date: '',
  gender: '',
  license_number: '',
  office_name: '',
  career: '',
  introduction: '',
  signup_source: '',
})

const passwordConfirm = ref('')

const onlyNumber = (key: 'birth_date') => {
  form[key] = form[key].replace(/\D/g, '').slice(0, 8)
}

const checkUsername = () => {
  if (!form.username) return
  alert('사용 가능한 아이디라고 가정 (백엔드 검증은 추후 구현 가능)')
}

const handleSubmit = async () => {
  if (form.password !== passwordConfirm.value) {
    alert('비밀번호가 일치하지 않습니다.')
    return
  }

  try {
    await api.post('/api/accounts/lawyer-signup/', form)
    alert('회원가입 신청이 완료되었습니다. 관리자 승인 후 이용 가능합니다.')
  } catch (error) {
    const axiosError = error as AxiosError
    console.error('lawyer signup failed', axiosError)
    alert('회원가입 중 오류가 발생했습니다.')
  }
}
</script>
