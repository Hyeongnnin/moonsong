<template>
  <section class="space-y-4">
    <h2 class="text-2xl font-semibold mb-4">근로서류</h2>
    <div class="space-y-4 mt-4">
      <!-- 탭 -->
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

      <!-- 탭 컨텐츠 -->
      <div v-if="tab === 'resume'">
        <ResumeFormCard @preview="openPreview" @generated="onGenerated" />
      </div>
      <div v-else-if="tab === 'generated'">
        <GeneratedDocuments ref="docsRef" />
      </div>
      <div v-else>
        <DocumentsTemplates />
      </div>
    </div>

    <!-- 미리보기 모달 (완전 격리) -->
    <ResumePreviewModal 
      v-if="showPreview" 
      :data="previewData" 
      @close="showPreview = false" 
    />
  </section>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import ResumeFormCard from '../components/ResumeFormCard.vue'
import ResumePreviewModal from '../components/ResumePreviewModal.vue'
import GeneratedDocuments from '../components/GeneratedDocuments.vue'
import DocumentsTemplates from '../components/DocumentsTemplates.vue'

const tab = ref<'resume' | 'generated' | 'templates'>('resume')
const showPreview = ref(false)
const previewData = ref<any>(null)
const docsRef = ref<InstanceType<typeof GeneratedDocuments> | null>(null)

function openPreview(data: any) {
  previewData.value = data
  showPreview.value = true
}

function onGenerated() {
  tab.value = 'generated'
  docsRef.value?.reload()
}

function tabClass(isActive: boolean) {
  return [
    'px-4 py-2 text-sm font-medium rounded transition-colors',
    isActive ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
  ].join(' ')
}
</script>

<style scoped>
</style>
