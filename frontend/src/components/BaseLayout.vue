<template>
  <div>
    <TopNav />
    <LaborSubTabs v-if="showLaborTabs" />

    <main class="max-w-7xl mx-auto px-4 py-6">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import TopNav from "./TopNav.vue";
import LaborSubTabs from "./LaborSubTabs.vue";

const route = useRoute();
const showLaborTabs = computed(() => route.path.startsWith("/labor"));
</script>

<style scoped>
</style>
