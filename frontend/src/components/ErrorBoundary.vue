<template>
  <div>
    <div v-if="hasError" class="p-6 bg-red-50 border border-red-200 rounded">
      <h3 class="text-lg font-semibold text-red-700">오류가 발생했습니다</h3>
      <p class="text-sm text-red-600 mt-2">{{ errorMessage }}</p>
      <button @click="reset" class="mt-4 px-4 py-2 bg-red-600 text-white rounded">다시 시도</button>
    </div>
    <div v-else>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, getCurrentInstance } from 'vue'
const hasError = ref(false)
const errorMessage = ref('')

function reset() {
  hasError.value = false
  errorMessage.value = ''
  // attempt to re-render by emitting an update on the component
  const inst = getCurrentInstance()
  if (inst && inst.proxy) {
    // force update
    // @ts-ignore
    inst.proxy.$forceUpdate?.()
  }
}

// errorCaptured hook is declared via defineEmits in script setup by using global hook
// Use the runtime API via getCurrentInstance to attach errorCaptured if needed
// But vue exposes errorCaptured as an option only in Options API. For script-setup we can use onErrorCaptured
import { onErrorCaptured } from 'vue'

onErrorCaptured((err) => {
  console.error('ErrorBoundary captured error:', err)
  hasError.value = true
  errorMessage.value = (err && err.message) ? err.message : String(err)
  // return false to stop the error from propagating further
  return false
})
</script>

<style scoped>
</style>
