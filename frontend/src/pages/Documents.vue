<template>
  <section>
    <h2 class="text-2xl font-semibold mb-4">근로서류</h2>
    <div class="p-4 bg-white rounded shadow space-y-4">
      <!-- ✅ B 프로젝트 병합: 이력서 자동 생성 탭 추가 -->
      <div class="flex gap-2 border-b border-gray-200 pb-2">
        <button @click="tab = 'resume'" :class="tabClass(tab === 'resume')">
          이력서 자동 생성
        </button>
        <button @click="tab = 'generated'" :class="tabClass(tab === 'generated')">
          나의 서류함
        </button>
        <button @click="tab = 'templates'" :class="tabClass(tab === 'templates')">
          템플릿
        </button>
      </div>

      <div v-if="tab === 'resume'">
        <ResumeGenerator @saved="onResumeSaved" />
      </div>
      <div v-else-if="tab === 'generated'">
        <GeneratedDocuments ref="docsRef" />
      </div>
      <div v-else>
        <DocumentsTemplates />
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import GeneratedDocuments from '../components/GeneratedDocuments.vue'
import DocumentsTemplates from '../components/DocumentsTemplates.vue'
import ResumeGenerator from '../components/ResumeGenerator.vue'  // ✅ B 프로젝트 병합

const docsRef = ref<InstanceType<typeof GeneratedDocuments> | null>(null)
const tab = ref<'resume' | 'generated' | 'templates'>('resume')  // ✅ B 프로젝트 병합: 기본값 변경

function onResumeSaved() {
  // 이력서 생성 후 서류함 새로고침
  docsRef.value?.reload()
}

function tabClass(isActive: boolean) {
  return [
    'px-4 py-2 text-sm font-medium rounded',
    isActive ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
  ].join(' ')
}
</script>

<style scoped>
</style>
