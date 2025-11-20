<template>
  <div class="min-h-screen bg-gray-50">
    <Header />
    <router-view />
  </div>
</template>

<script setup lang="ts">
import Header from './components/Header.vue'
</script>
