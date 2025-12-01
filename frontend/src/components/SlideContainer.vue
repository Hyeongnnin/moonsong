<template>
  <div ref="wrapper" class="relative w-full h-full overflow-hidden">
    <!-- Arrow buttons -->
    <button
      class="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white shadow flex items-center justify-center"
      :class="{ 'opacity-40 pointer-events-none': currentIndex === 0 }"
      @click="prev"
    >
      ‹
    </button>

    <button
      class="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 rounded-full bg-white shadow flex items-center justify-center"
      :class="{ 'opacity-40 pointer-events-none': currentIndex === slides.length - 1 }"
      @click="next"
    >
      ›
    </button>

    <!-- Slides wrapper -->
    <div
      ref="track"
      class="h-full flex will-change-transform"
      :style="trackStyle"
      @mousedown="onPointerDown"
      @touchstart.passive="onTouchStart"
    >
      <section v-for="(slide, i) in slides" :key="slide.path" class="flex-shrink-0 h-full slide-item">
        <component :is="slide.component" class="h-full w-full" />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, defineAsyncComponent } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

// slides: order matters
const slides = [
  { path: '/dashboard', component: defineAsyncComponent(() => import('../components/MainDashboard.vue')) },
  { path: '/ai-consult', component: defineAsyncComponent(() => import('../pages/AiConsult.vue')) },
  { path: '/profile-edit', component: defineAsyncComponent(() => import('../pages/LaborEdit.vue')) },
  { path: '/documents', component: defineAsyncComponent(() => import('../pages/Documents.vue')) },
];

const track = ref<HTMLElement | null>(null);
const wrapper = ref<HTMLElement | null>(null);
const state = reactive({
  index: 0,
  dragging: false,
  startX: 0,
  currentTranslate: 0,
  prevTranslate: 0,
});

const currentIndex = computed(() => state.index);

function routeToIndex(path: string) {
  // consider '/labor/*' as index 0 as well
  if (path.startsWith('/labor') || path === '/dashboard' || path === '/') return 0;
  const idx = slides.findIndex(s => s.path === path);
  return idx >= 0 ? idx : 0;
}

function updateIndexFromRoute() {
  state.index = routeToIndex(route.path);
  state.prevTranslate = -state.index * (trackWidth.value);
  state.currentTranslate = state.prevTranslate;
}

// width of a single slide (the visible wrapper width)
const trackWidth = ref(0);
onMounted(() => {
  updateTrackWidth();
  updateIndexFromRoute();
  window.addEventListener('resize', updateTrackWidth);
});

watch(() => route.path, () => {
  // when route changes (e.g., via top nav click), animate to new index
  const idx = routeToIndex(route.path);
  goToIndex(idx);
});

function updateTrackWidth() {
  if (!wrapper.value) return;
  trackWidth.value = wrapper.value.clientWidth;
  // when width changes, keep translation consistent
  state.prevTranslate = -state.index * trackWidth.value;
  state.currentTranslate = state.prevTranslate;
}

const trackStyle = computed(() => {
  const transform = `translateX(${state.currentTranslate}px)`;
  const transition = state.dragging ? 'none' : 'transform 300ms ease';
  return {
    transform,
    transition,
  } as any;
});

function clampIndex(i: number) {
  return Math.max(0, Math.min(slides.length - 1, i));
}

function goToIndex(i: number) {
  i = clampIndex(i);
  state.index = i;
  state.prevTranslate = -i * trackWidth.value;
  state.currentTranslate = state.prevTranslate;
  // push route
  const path = slides[i].path;
  if (route.path !== path) router.push(path).catch(() => {});
}

function prev() {
  if (state.index === 0) return;
  goToIndex(state.index - 1);
}

function next() {
  if (state.index >= slides.length - 1) return;
  goToIndex(state.index + 1);
}

// Pointer / touch handling
function onPointerDown(e: MouseEvent) {
  e.preventDefault();
  state.dragging = true;
  state.startX = e.clientX;
  document.addEventListener('mousemove', onPointerMove);
  document.addEventListener('mouseup', onPointerUp);
}

function onTouchStart(e: TouchEvent) {
  state.dragging = true;
  state.startX = e.touches[0].clientX;
  document.addEventListener('touchmove', onTouchMove, { passive: false });
  document.addEventListener('touchend', onTouchEnd);
}

function onPointerMove(e: MouseEvent) {
  if (!state.dragging) return;
  const dx = e.clientX - state.startX;
  state.currentTranslate = state.prevTranslate + dx;
}

function onTouchMove(e: TouchEvent) {
  if (!state.dragging) return;
  e.preventDefault();
  const dx = e.touches[0].clientX - state.startX;
  state.currentTranslate = state.prevTranslate + dx;
}

function endDrag() {
  state.dragging = false;
  const movedBy = state.currentTranslate - state.prevTranslate; // negative when moved left
  const threshold = Math.max(80, trackWidth.value * 0.15);
  if (movedBy > threshold) {
    // dragged right -> go to previous
    goToIndex(state.index - 1);
  } else if (movedBy < -threshold) {
    // dragged left -> next
    goToIndex(state.index + 1);
  } else {
    // snap back
    state.currentTranslate = state.prevTranslate;
  }
}

function onPointerUp() {
  if (!state.dragging) return;
  endDrag();
  document.removeEventListener('mousemove', onPointerMove);
  document.removeEventListener('mouseup', onPointerUp);
}

function onTouchEnd() {
  if (!state.dragging) return;
  endDrag();
  document.removeEventListener('touchmove', onTouchMove);
  document.removeEventListener('touchend', onTouchEnd);
}

</script>

<style scoped>
.will-change-transform { will-change: transform; }
/* make each slide take full width */
section.slide-item { flex: 0 0 100%; }
</style>
