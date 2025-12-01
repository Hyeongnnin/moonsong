<template>
  <div ref="wrapper" class="relative w-full h-full overflow-hidden bg-transparent">
    <!-- Arrow buttons (center-left / center-right of the content area) -->
    <button
      class="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white/90 shadow flex items-center justify-center"
      :class="{ 'opacity-40 pointer-events-none': currentIndex === 0 }"
      @click="prev"
    >
      ‹
    </button>

    <button
      class="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white/90 shadow flex items-center justify-center"
      :class="{ 'opacity-40 pointer-events-none': currentIndex === slides.length - 1 }"
      @click="next"
    >
      ›
    </button>

    <div ref="track" class="h-full flex" :style="trackStyle" @mousedown="onPointerDown" @touchstart.passive="onTouchStart">
      <!-- slide 0: labor/dashboard - render specific central component depending on route -->
      <section class="flex-shrink-0 h-full slide-item">
        <component :is="centerComponent" class="h-full w-full" />
      </section>

      <!-- slide 1: AI 상담 -->
      <section class="flex-shrink-0 h-full slide-item">
        <AiConsultComp class="h-full w-full" />
      </section>

      <!-- slide 2: 근로정보 수정 -->
      <section class="flex-shrink-0 h-full slide-item">
        <ProfileEditComp class="h-full w-full" />
      </section>

      <!-- slide 3: 근로서류 -->
      <section class="flex-shrink-0 h-full slide-item">
        <DocumentsComp class="h-full w-full" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, defineAsyncComponent } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

// central components (async)
const DashboardContent = defineAsyncComponent(() => import('./DashboardContent.vue'));
const AiConsultComp = defineAsyncComponent(() => import('../pages/AiConsult.vue'));
const ProfileEditComp = defineAsyncComponent(() => import('../pages/LaborEdit.vue'));
const DocumentsComp = defineAsyncComponent(() => import('../pages/Documents.vue'));

// labor subpages mapping
const laborMap: Record<string, any> = {
  'annual': () => import('../pages/labor/Annual.vue'),
  'paid-leave': () => import('../pages/labor/PaidLeave.vue'),
  'retirement': () => import('../pages/labor/Retirement.vue'),
  'unemployment': () => import('../pages/labor/Unemployment.vue'),
  'work-time': () => import('../pages/labor/WorkTime.vue'),
  'salary': () => import('../pages/labor/Salary.vue'),
};

const slides = [
  { id: 'labor' },
  { id: 'ai' },
  { id: 'profile' },
  { id: 'documents' },
];

const wrapper = ref<HTMLElement | null>(null);
const track = ref<HTMLElement | null>(null);
const trackWidth = ref(0);

const state = reactive({ index: 0, dragging: false, startX: 0, currentTranslate: 0, prevTranslate: 0 });
const currentIndex = computed(() => state.index);

function routeToIndex(path: string) {
  if (path.startsWith('/labor') || path === '/dashboard' || path === '/') return 0;
  if (path.startsWith('/ai-consult')) return 1;
  if (path.startsWith('/profile-edit')) return 2;
  if (path.startsWith('/documents')) return 3;
  return 0;
}

function updateIndexFromRoute() {
  state.index = routeToIndex(route.path);
  state.prevTranslate = -state.index * trackWidth.value;
  state.currentTranslate = state.prevTranslate;
}

onMounted(() => {
  updateTrackWidth();
  updateIndexFromRoute();
  window.addEventListener('resize', updateTrackWidth);
});

watch(() => route.path, () => {
  const idx = routeToIndex(route.path);
  goToIndex(idx);
});

function updateTrackWidth() {
  if (!wrapper.value) return;
  trackWidth.value = wrapper.value.clientWidth;
  state.prevTranslate = -state.index * trackWidth.value;
  state.currentTranslate = state.prevTranslate;
}

const trackStyle = computed(() => {
  const transform = `translateX(${state.currentTranslate}px)`;
  const transition = state.dragging ? 'none' : 'transform 300ms ease';
  return { transform, transition } as any;
});

function clampIndex(i: number) { return Math.max(0, Math.min(slides.length - 1, i)); }

function goToIndex(i: number) {
  i = clampIndex(i);
  state.index = i;
  state.prevTranslate = -i * trackWidth.value;
  state.currentTranslate = state.prevTranslate;
  // push route according to slide
  const path = slides[i].id === 'labor' ? (route.path.startsWith('/labor') ? route.path : '/dashboard')
                : slides[i].id === 'ai' ? '/ai-consult'
                : slides[i].id === 'profile' ? '/profile-edit'
                : '/documents';
  if (route.path !== path) router.push(path).catch(() => {});
}

function prev() { if (state.index === 0) return; goToIndex(state.index - 1); }
function next() { if (state.index >= slides.length - 1) return; goToIndex(state.index + 1); }

// dragging
function onPointerDown(e: MouseEvent) { e.preventDefault(); state.dragging = true; state.startX = e.clientX; document.addEventListener('mousemove', onPointerMove); document.addEventListener('mouseup', onPointerUp); }
function onTouchStart(e: TouchEvent) { state.dragging = true; state.startX = e.touches[0].clientX; document.addEventListener('touchmove', onTouchMove, { passive: false }); document.addEventListener('touchend', onTouchEnd); }
function onPointerMove(e: MouseEvent) { if (!state.dragging) return; const dx = e.clientX - state.startX; state.currentTranslate = state.prevTranslate + dx; }
function onTouchMove(e: TouchEvent) { if (!state.dragging) return; e.preventDefault(); const dx = e.touches[0].clientX - state.startX; state.currentTranslate = state.prevTranslate + dx; }
function endDrag() { state.dragging = false; const movedBy = state.currentTranslate - state.prevTranslate; const threshold = Math.max(80, trackWidth.value * 0.15); if (movedBy > threshold) { goToIndex(state.index - 1); } else if (movedBy < -threshold) { goToIndex(state.index + 1); } else { state.currentTranslate = state.prevTranslate; } }
function onPointerUp() { if (!state.dragging) return; endDrag(); document.removeEventListener('mousemove', onPointerMove); document.removeEventListener('mouseup', onPointerUp); }
function onTouchEnd() { if (!state.dragging) return; endDrag(); document.removeEventListener('touchmove', onTouchMove); document.removeEventListener('touchend', onTouchEnd); }

// centerComponent: determine which component to render inside slide 0
const centerComponent = computed(() => {
  const p = route.path;
  if (p === '/dashboard' || p === '/') return DashboardContent;
  if (p.startsWith('/labor')) {
    const parts = p.split('/').filter(Boolean); // ['labor','annual']
    const sub = parts[1] || 'annual';
    const loader = laborMap[sub];
    if (loader) {
      return defineAsyncComponent(loader);
    }
    return defineAsyncComponent(laborMap['annual']);
  }
  // fallback to dashboard
  return DashboardContent;
});

</script>

<style scoped>
.slide-item { flex: 0 0 100%; }
</style>
