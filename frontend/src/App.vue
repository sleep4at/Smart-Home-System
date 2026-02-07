<template>
  <RouterView />
  <BannerList v-if="auth.initialized && auth.isAuthenticated" />
  <BannerProvider v-if="auth.initialized && auth.isAuthenticated" />
</template>

<script setup lang="ts">
import { RouterView } from "vue-router";
import { useAuthStore } from "@/store/auth";
import BannerList from "@/components/BannerList.vue";
import BannerProvider from "@/components/BannerProvider.vue";

const auth = useAuthStore();
</script>

