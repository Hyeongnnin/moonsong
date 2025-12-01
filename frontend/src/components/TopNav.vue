<template>
  <nav class="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
    <div class="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16 gap-4">
        
        <!-- LEFT: Logo -->
        <div class="flex-shrink-0">
          <router-link to="/" class="flex items-center gap-2 hover:opacity-80 active:opacity-70 transition-opacity">
            <img src="@/assets/logo.svg" alt="NOTAV" class="h-8 w-8 sm:h-9 sm:w-9" />
            <span class="hidden sm:inline font-bold text-gray-900 text-base sm:text-lg">Notav</span>
          </router-link>
        </div>

        <!-- CENTER: Logo/Brand area -->
        <div class="flex-1 flex items-center justify-center">
          <!-- Note: Tab menu removed - section switching now happens in MainLayout -->
        </div>

        <!-- RIGHT: User Menu / Auth Buttons -->
        <div class="flex-shrink-0 flex items-center gap-3 relative">
          <button v-if="!isLoggedIn"
            @click="navigateTo('/login')"
            class="hidden sm:inline-flex px-3 py-1.5 text-sm rounded-full border border-gray-200 text-gray-700 hover:border-brand-600 hover:text-brand-600 hover:bg-brand-50 transition-colors duration-200">
            로그인
          </button>
          <button v-if="!isLoggedIn"
            @click="navigateTo('/signup')"
            class="inline-flex px-4 py-2 text-sm font-medium rounded-full bg-brand-600 text-white hover:bg-brand-700 active:bg-brand-800 transition-colors duration-200">
            가입
          </button>

          <!-- User Profile Dropdown (when logged in) -->
          <div v-if="isLoggedIn" class="flex items-center gap-3 pl-3 border-l border-gray-200 relative">
            <div class="flex items-center gap-3 cursor-pointer group">
              <div class="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0 group-hover:bg-brand-600 transition-colors duration-200">
                U
              </div>
              <span class="hidden sm:inline text-sm font-medium text-gray-900 group-hover:text-brand-600 transition-colors duration-200">사용자</span>
              <button 
                @click="isProfileDropdownOpen = !isProfileDropdownOpen"
                class="text-gray-600 hover:text-brand-600 transition-colors duration-200"
                :class="{ 'rotate-180': isProfileDropdownOpen }">
                <svg class="w-5 h-5 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            <!-- Profile Dropdown Menu -->
            <div v-if="isProfileDropdownOpen" class="absolute top-full right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-100 py-2 z-10 animate-in fade-in slide-in-from-top-2 duration-150">
              <button 
                @click="navigateTo('/profile')"
                class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-brand-50 hover:text-brand-600 transition-colors duration-150">
                프로필 보기
              </button>
              <button 
                @click="navigateTo('/settings')"
                class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-brand-50 hover:text-brand-600 transition-colors duration-150">
                설정
              </button>
              <hr class="my-2 border-gray-100" />
              <button 
                @click="handleLogout"
                class="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 transition-colors duration-150">
                로그아웃
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { ref, onMounted, onUnmounted } from "vue";

const router = useRouter();
const isLoggedIn = ref(false);
const isMdScreen = ref(window.innerWidth >= 768);
const isProfileDropdownOpen = ref(false);

function navigateTo(path: string) {
  isProfileDropdownOpen.value = false;
  router.push(path);
}

function handleLogout() {
  localStorage.removeItem("access_token");
  isLoggedIn.value = false;
  isProfileDropdownOpen.value = false;
  router.push("/login");
}

// Handle window resize for responsive design
function handleResize() {
  isMdScreen.value = window.innerWidth >= 768;
}

// Close dropdowns when clicking outside
function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement;
  const profileSection = document.querySelector('.border-l.border-gray-200');
  
  if (profileSection && !profileSection.contains(target)) {
    isProfileDropdownOpen.value = false;
  }
}

onMounted(() => {
  window.addEventListener("resize", handleResize);
  document.addEventListener("click", handleClickOutside);
  
  // Check if user is logged in
  const token = localStorage.getItem("access_token");
  isLoggedIn.value = !!token;
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  document.removeEventListener("click", handleClickOutside);
});
</script>

<style scoped>
/* Smooth transitions */
:deep(.router-link-active) {
  transition: all 0.2s ease-in-out;
}

/* Logo image */
img {
  user-select: none;
  -webkit-user-drag: none;
  will-change: opacity;
}

/* Button transitions */
button {
  will-change: background-color, color, border-color;
}

/* Animation classes for dropdown */
@keyframes slideInFromTop {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-in {
  animation: slideInFromTop 0.15s ease-out;
}

/* Mobile menu animation */
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.fade-in {
  animation: fadeIn 0.15s ease-out;
}

/* Smooth dropdown rotation */
svg {
  will-change: transform;
}

/* Enhance focus states for accessibility */
:focus-visible {
  outline: 2px solid var(--color-brand-600);
  outline-offset: 2px;
}
</style>
