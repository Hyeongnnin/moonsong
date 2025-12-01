<template>
  <aside class="hidden lg:block bg-white border-r border-gray-200 h-screen sticky top-0 overflow-y-auto">
    <div class="p-6">
      <div class="mb-8">
        <h2 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
          근로 관리
        </h2>
        <nav class="space-y-2">
          <button
            v-for="item in navigationItems"
            :key="item.id"
            @click="goTo(item)"
            :class="[
              'w-full text-left px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              activeItem === item.id
                ? 'bg-brand-50 text-brand-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            ]"
          >
            {{ item.label }}
          </button>
        </nav>
      </div>

      <div class="border-t border-gray-200 pt-6">
        <h2 class="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-4">
          자료실
        </h2>
        <nav class="space-y-2">
          <button
            v-for="item in resourceItems"
            :key="item.id"
            @click="goTo(item)"
            :class="[
              'w-full text-left px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              activeItem === item.id
                ? 'bg-brand-50 text-brand-600'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            ]"
          >
            {{ item.label }}
          </button>
        </nav>
      </div>

      <div class="border-t border-gray-200 mt-6 pt-6">
        <p class="text-xs text-gray-500 text-center">
          v1.0.0
        </p>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

const activeItem = ref('');

const laborNav = [
  { id: 'calendar', label: '근로시간 관리', to: '/labor/annual' },
  { id: 'contract', label: '근로계약서', to: '/labor/paid-leave' },
  { id: 'salary', label: '급여 명세서', to: '/labor/salary' },
  { id: 'diagnosis', label: '진단 결과', to: '/labor/retirement' },
];

const aiNav = [
  { id: 'chat', label: 'AI 상담 시작', to: '/ai-consult' },
  { id: 'history', label: '상담 이력', to: '/ai-consult' },
];

const profileNav = [
  { id: 'profile', label: '내 정보 수정', to: '/profile-edit' },
];

const docsNav = [
  { id: 'list', label: '서류 리스트', to: '/documents' },
  { id: 'upload', label: '서류 업로드', to: '/documents' },
];

const resourceItems = [
  { id: 'guide', label: '이용 가이드' },
  { id: 'faq', label: 'FAQ' },
  { id: 'notice', label: '공지사항' },
];

const navigationItems = computed(() => {
  const p = route.path;
  if (p.startsWith('/labor') || p === '/dashboard' || p === '/') return laborNav;
  if (p.startsWith('/ai-consult')) return aiNav;
  if (p.startsWith('/profile-edit')) return profileNav;
  if (p.startsWith('/documents')) return docsNav;
  return laborNav;
});

function goTo(item: any) {
  activeItem.value = item.id;
  if (item.to) router.push(item.to).catch(() => {});
}
</script>

<style scoped>
</style>
