<template>
  <div class="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-2xl mx-auto">
      <!-- 헤더 -->
      <div class="flex items-center gap-3 mb-8">
        <button 
          @click="goBack"
          class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 class="text-3xl font-bold text-gray-900">프로필 수정</h1>
      </div>

      <!-- 메인 카드 -->
      <div class="bg-white rounded-lg border border-gray-200 shadow-sm p-8">
        <form @submit.prevent="handleSubmit" class="space-y-8">
          
          <!-- 프로필 이미지 섹션 -->
          <div class="border-b border-gray-200 pb-8">
            <h2 class="text-lg font-semibold text-gray-900 mb-6">프로필 이미지</h2>
            
            <div class="flex flex-col items-center gap-6">
              <!-- 현재 프로필 이미지 -->
              <div class="w-24 h-24 rounded-full overflow-hidden shadow-md bg-gray-100">
                <img v-if="profileImage" :src="profileImage" alt="Profile" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full flex items-center justify-center text-white font-bold text-3xl bg-gradient-to-br from-brand-400 to-brand-600">
                  {{ userInitial }}
                </div>
              </div>

              <!-- 이미지 업로드 버튼 -->
              <div class="flex gap-3">
                <input 
                  type="file" 
                  ref="fileInput" 
                  accept="image/*" 
                  class="hidden" 
                  @change="handleImageUpload">
                
                <button
                  type="button"
                  @click="triggerFileInput"
                  class="px-4 py-2 text-sm font-medium text-brand-600 border border-brand-300 rounded-lg hover:bg-brand-50 transition-colors duration-200">
                  이미지 업로드
                </button>
                
                <button
                  type="button"
                  @click="removeImage"
                  class="px-4 py-2 text-sm font-medium text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
                  제거
                </button>
              </div>
              
              <p class="text-xs text-gray-500 text-center">
                JPG, PNG, GIF 형식의 파일만 가능합니다.<br/>
                최대 파일 크기: 5MB
              </p>
            </div>
          </div>

          <!-- 기본 정보 섹션 -->
          <div class="border-b border-gray-200 pb-8">
            <h2 class="text-lg font-semibold text-gray-900 mb-6">기본 정보</h2>
            
            <div class="space-y-5">
              <!-- 이름 -->
              <div>
                <label for="name" class="block text-sm font-medium text-gray-900 mb-2">
                  이름 <span class="text-red-500">*</span>
                </label>
                <input
                  id="name"
                  v-model="formData.name"
                  type="text"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all duration-200"
                  placeholder="홀길동"
                  required>
              </div>

              <!-- 이메일 -->
              <div>
                <label for="email" class="block text-sm font-medium text-gray-900 mb-2">
                  이메일 <span class="text-red-500">*</span>
                </label>
                <input
                  id="email"
                  v-model="formData.email"
                  type="email"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all duration-200"
                  placeholder="example@example.com"
                  required>
              </div>

              <!-- 전화번호 (선택) -->
              <div>
                <label for="phone" class="block text-sm font-medium text-gray-900 mb-2">
                  전화번호
                </label>
                <input
                  id="phone"
                  v-model="formData.phone"
                  type="tel"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all duration-200"
                  placeholder="010-1234-5678">
              </div>
            </div>
          </div>

          <!-- 비밀번호 변경 섹션 -->
          <div class="border-b border-gray-200 pb-8">
            <h2 class="text-lg font-semibold text-gray-900 mb-2">비밀번호 변경</h2>
            <p class="text-sm text-gray-500 mb-6">비밀번호를 변경하려면 아래 필드를 입력하세요.</p>
            
            <div class="space-y-5">
              <!-- 현재 비밀번호 -->
              <div>
                <label for="currentPassword" class="block text-sm font-medium text-gray-900 mb-2">
                  현재 비밀번호
                </label>
                <input
                  id="currentPassword"
                  v-model="formData.currentPassword"
                  type="password"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all duration-200"
                  placeholder="현재 비밀번호를 입력하세요">
              </div>

              <!-- 새 비밀번호 -->
              <div>
                <label for="newPassword" class="block text-sm font-medium text-gray-900 mb-2">
                  새 비밀번호
                </label>
                <input
                  id="newPassword"
                  v-model="formData.newPassword"
                  type="password"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all duration-200"
                  placeholder="새 비밀번호를 입력하세요"
                  @input="validatePasswordMatch">
              </div>

              <!-- 비밀번호 확인 -->
              <div>
                <label for="confirmPassword" class="block text-sm font-medium text-gray-900 mb-2">
                  비밀번호 확인
                </label>
                <input
                  id="confirmPassword"
                  v-model="formData.confirmPassword"
                  type="password"
                  class="w-full px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all duration-200"
                  :class="{ 'border-red-500 focus:ring-red-500': passwordMismatch && formData.confirmPassword }"
                  placeholder="비밀번호를 다시 입력하세요"
                  @input="validatePasswordMatch">
                
                <!-- 비밀번호 불일치 경고 -->
                <p v-if="passwordMismatch && formData.confirmPassword" class="mt-2 text-sm text-red-600">
                  비밀번호가 일치하지 않습니다.
                </p>
              </div>

              <!-- 비밀번호 요구사항 -->
              <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
                <p class="font-medium text-gray-900 mb-2">비밀번호는 다음을 만족해야 합니다:</p>
                <ul class="space-y-1 list-disc list-inside">
                  <li>8자 이상 20자 이하</li>
                  <li>영문, 숫자, 특수문자를 포함</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- 버튼 섹션 -->
          <div class="flex items-center gap-3 justify-between pt-4">
            <button
              type="button"
              @click="goBack"
              class="px-6 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200">
              취소
            </button>

            <button
              type="submit"
              :disabled="isSaving || !isFormValid"
              class="px-6 py-2.5 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 active:bg-brand-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200">
              {{ isSaving ? '저장 중...' : '저장하기' }}
            </button>
          </div>
        </form>
      </div>

      <!-- 성공 메시지 -->
      <div v-if="successMessage" class="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
        {{ successMessage }}
      </div>

      <!-- 오류 메시지 -->
      <div v-if="errorMessage" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { apiClient } from '../api';
import { useUser } from '../stores/userStore';

const { fetchMe, updateUser } = useUser();

const router = useRouter();
const fileInput = ref<HTMLInputElement | null>(null);
const isSaving = ref(false);
const successMessage = ref('');
const errorMessage = ref('');
const fieldErrors = ref<Record<string, string[]>>({});

// 폼 데이터
const formData = reactive({
  name: '',
  email: '',
  phone: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
});

// 사용자 초기값 계산
const userInitial = computed(() => {
  return formData.name ? formData.name.charAt(0) : '사용자'.charAt(0)
});

// 비밀번호 일치 확인
const passwordMismatch = computed(() => {
  return formData.newPassword && formData.confirmPassword && formData.newPassword !== formData.confirmPassword
});

// 폼 유효성 검사
const isFormValid = computed(() => {
  if (!formData.name || !formData.email) return false
  if (formData.newPassword || formData.confirmPassword) {
    if (!formData.currentPassword || !formData.newPassword || !formData.confirmPassword) return false
    if (passwordMismatch.value) return false
  }
  return true
});

// 프로필 이미지 초기값
const profileImage = ref<string | null>(null);
const selectedFile = ref<File | null>(null);
const avatarCleared = ref(false);

onMounted(async () => {
  try {
    const res = await apiClient.get('/accounts/profile/me/')
    const data = res.data
    formData.name = data.first_name || data.username || ''
    formData.email = data.email || ''
    formData.phone = data.phone_number || ''
    profileImage.value = data.avatar || null
    // update user store
    await fetchMe()
  } catch (err) {
    console.error('profile fetch error', err)
  }
})

// 파일 입력 트리거
function triggerFileInput() {
  fileInput.value?.click();
}

// 이미지 업로드 처리 (로컬 프리뷰 설정)
function handleImageUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  avatarCleared.value = false;
  
  if (file) {
    // 파일 크기 체크 (5MB)
    if (file.size > 5 * 1024 * 1024) {
      errorMessage.value = '파일 크기는 5MB 이하여야 합니다.';
      return;
    }
    
    // 파일 형식 체크
    if (!['image/jpeg', 'image/png', 'image/gif'].includes(file.type)) {
      errorMessage.value = 'JPG, PNG, GIF 형식의 파일만 가능합니다.';
      return;
    }
    selectedFile.value = file;
    const url = URL.createObjectURL(file)
    profileImage.value = url;
  }
}

// 이미지 제거
function removeImage() {
  profileImage.value = null;
  selectedFile.value = null;
  avatarCleared.value = true;
  if (fileInput.value) {
    fileInput.value.value = '';
  }
}

// 비밀번호 일치 검증
function validatePasswordMatch() {}

// 폼 제출
async function handleSubmit() {
  fieldErrors.value = {};
  if (!formData.name || !formData.email) {
    errorMessage.value = '이름과 이메일은 필수입니다.'
    return
  }

  isSaving.value = true;
  errorMessage.value = '';
  successMessage.value = '';

  try {
    // 프로필 업데이트 (multipart multipart)
    const fd = new FormData()
    fd.append('first_name', formData.name)
    fd.append('email', formData.email)
    fd.append('phone_number', formData.phone)
    if (selectedFile.value) {
      fd.append('avatar', selectedFile.value)
    }
    if (avatarCleared.value) {
      fd.append('avatar_clear', '1')
    }

    const res = await apiClient.patch('/accounts/profile/me/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })

    // 비밀번호 변경 필요 시
    if (formData.currentPassword || formData.newPassword || formData.confirmPassword) {
      const pwdRes = await apiClient.post('/accounts/profile/change-password/', {
        current_password: formData.currentPassword,
        new_password: formData.newPassword,
        new_password_confirm: formData.confirmPassword,
      })
      // 성공 시 입력 필드 초기화
      formData.currentPassword = ''
      formData.newPassword = ''
      formData.confirmPassword = ''
    }

    // 성공 처리
    successMessage.value = '프로필이 저장되었습니다.'

    // 유저 스토어 갱신
    await fetchMe()

    // 프로필 카드 즉시 반영을 위해 updateUser 호출도 가능
    // updateUser({ first_name: formData.name, avatar: res.data.avatar })

  } catch (err: any) {
    console.error('save error', err)
    if (err.response?.data) {
      const data = err.response.data
      // serializer errors
      fieldErrors.value = data
      errorMessage.value = data.detail || '저장에 실패했습니다.'
    } else {
      errorMessage.value = '저장 중 오류가 발생했습니다.'
    }
  } finally {
    isSaving.value = false;
  }
}

// 뒤로가기
function goBack() {
  router.back();
}
</script>

<style scoped>
/* 포커스 상태 스타일 향상 */
input:focus {
  outline: none;
}

/* 비활성화 상태 */
input:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}
</style>
