<template>
  <div class="bg-white border-b">
    <div class="max-w-7xl mx-auto px-4">
      <div class="flex space-x-2 overflow-x-auto py-2">
        <router-link
          v-for="tab in subtabs"
          :key="tab.path"
          :to="tab.path"
          class="px-3 py-2 text-sm rounded-md text-gray-600"
          :class="{ 'text-brand-600 border-b-2 border-brand-600 bg-brand-50': isActive(tab.path) }">
          {{ tab.label }}
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from "vue-router";
const route = useRoute();

const base = "/labor";
const subtabs = [
  { label: "연차", path: `${base}/annual` },
  { label: "유급휴가", path: `${base}/paid-leave` },
  { label: "퇴직금", path: `${base}/retirement` },
  { label: "실업급여", path: `${base}/unemployment` },
  { label: "근로시간", path: `${base}/work-time` },
  { label: "월급", path: `${base}/salary` },
];

function isActive(path: string) {
  return route.path === path;
}
</script>

<style scoped>
</style>
