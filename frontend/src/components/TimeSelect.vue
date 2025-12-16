<template>
  <div class="relative inline-block w-28" ref="container">
    <!-- Trigger Button -->
    <button 
      type="button"
      @click="toggleDropdown"
      :disabled="disabled"
      class="w-full px-2 py-1 bg-white border rounded text-left flex items-center justify-between text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
      :class="[
        disabled ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'border-gray-300 hovered:border-gray-400 text-gray-900',
        isOpen ? 'border-brand-500 ring-2 ring-brand-500' : ''
      ]"
    >
      <span :class="modelValue ? '' : 'text-gray-400'">{{ modelValue || '--:--' }}</span>
      <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Dropdown Menu -->
    <div 
      v-if="isOpen" 
      class="absolute left-0 mt-1 w-full bg-white border border-gray-200 rounded shadow-lg z-50 max-h-48 overflow-y-auto"
    >
      <div 
        @click="selectOption(null)"
        class="px-3 py-2 text-sm text-gray-500 cursor-pointer hover:bg-gray-50"
        :class="{ 'bg-gray-100 font-medium': !modelValue }"
      >
        --:--
      </div>
      <div 
        v-for="option in options" 
        :key="option" 
        @click="selectOption(option)"
        class="px-3 py-2 text-sm text-gray-900 cursor-pointer hover:bg-brand-50 hover:text-brand-700"
        :class="{ 'bg-brand-50 text-brand-700 font-medium': modelValue === option }"
      >
        {{ option }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps<{
  modelValue: string | null;
  options: string[];
  disabled?: boolean;
}>();

const emit = defineEmits(['update:modelValue']);

const isOpen = ref(false);
const container = ref<HTMLElement | null>(null);

function toggleDropdown() {
  if (props.disabled) return;
  isOpen.value = !isOpen.value;
  
  if (isOpen.value) {
    // Scroll to selected item logic could go here if needed
  }
}

function selectOption(value: string | null) {
  emit('update:modelValue', value);
  isOpen.value = false;
}

function handleClickOutside(event: MouseEvent) {
  if (container.value && !container.value.contains(event.target as Node)) {
    isOpen.value = false;
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
/* Custom scrollbar for webkit */
.max-h-48::-webkit-scrollbar {
  width: 6px;
}
.max-h-48::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.max-h-48::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}
.max-h-48::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}
</style>
