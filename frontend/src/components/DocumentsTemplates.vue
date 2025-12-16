<template>
  <div class="p-4">
    <h2 class="text-xl font-semibold mb-4">문서 템플릿</h2>
    <div v-if="loading" class="text-sm text-gray-500">로딩 중...</div>
    <div v-else>
      <ul class="space-y-3">
        <li v-for="t in templates" :key="t.id" class="p-3 border rounded">
          <div class="flex justify-between items-start">
            <div>
              <div class="font-medium">{{ t.name }}</div>
              <div class="text-xs text-gray-500">{{ t.doc_type }}</div>
              <div class="text-sm mt-2">{{ t.description }}</div>
            </div>
          </div>
        </li>
      </ul>
      <div v-if="templates.length === 0" class="text-sm text-gray-500 mt-3">사용 가능한 템플릿이 없습니다.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { fetchTemplates, type DocumentTemplate } from '../api'

const templates = ref<DocumentTemplate[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    loading.value = true
    templates.value = await fetchTemplates()
  } catch (e: any) {
    console.error('템플릿 가져오기 실패', e?.response?.data || e)
    alert('템플릿을 로드하지 못했습니다.')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
</style>
