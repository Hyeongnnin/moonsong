<template>
  <div>
    <Header @navigate="onNavigate" />
    <main class="pt-16">
      <router-view v-slot="{ Component }">
        <component :is="Component" @navigate="onNavigate" @logged-in="onLoggedIn" />
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import Header from "./Header.vue";

const router = useRouter();

function onNavigate(page: string) {
  // map the event strings to routes
  if (page === "landing") router.push("/");
  else if (page === "login") router.push("/login");
  else if (page === "signup") router.push("/signup");
  else if (page === "dashboard") router.push("/dashboard");
}

function onLoggedIn(token: string) {
  // store JWT for axios interceptor compatibility
  try {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("access", token);
      window.localStorage.setItem("access_token", token);
    }
  } catch (e) {}
  router.push("/dashboard");
}
</script>

<style scoped>
</style>
