<template>
  <div class="app-shell">
    <Sidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
    <main class="app-main">
      <header class="app-main-header">
        <div>
          <div class="app-main-title">{{ pageTitle }}</div>
          <div class="app-main-subtitle">
            智能家居 · {{ auth.user?.username }}（
            <span class="badge-role" :class="{ user: !auth.isAdmin }">
              {{ auth.isAdmin ? "管理员" : "普通用户" }}
            </span>
            ）
          </div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button
            v-if="auth.isAdmin"
            class="btn btn-primary"
            @click="goToAdmin"
          >
            管理设置
          </button>
          <button class="btn btn-ghost" @click="onLogout">退出登录</button>
        </div>
      </header>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import Sidebar from "@/components/Sidebar.vue";
import { useAuthStore } from "@/store/auth";

const collapsed = ref(false);
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const pageTitle = computed(() => (route.meta.title as string) || "主页");

const goToAdmin = () => router.push({ name: "admin-users" });
const onLogout = () => {
  auth.logout();
  router.push({ name: "login" });
};
</script>
