<template>
  <div class="app-shell app-shell-fixed">
    <AdminSidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
    <main class="app-main">
      <header class="app-main-header">
        <div>
          <div class="app-main-title">{{ pageTitle }}</div>
          <div class="app-main-subtitle">管理设置</div>
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-ghost" @click="goBack">返回主页</button>
          <button class="btn btn-ghost" @click="showProfile = true">个人信息</button>
          <button class="btn btn-ghost" @click="onLogout">退出登录</button>
        </div>
      </header>
      <div class="app-main-content">
        <router-view />
      </div>
    </main>
    <ProfileDialog v-if="showProfile" @close="showProfile = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import AdminSidebar from "@/components/AdminSidebar.vue";
import ProfileDialog from "@/components/ProfileDialog.vue";
import { useAuthStore } from "@/store/auth";

const collapsed = ref(false);
const showProfile = ref(false);
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const pageTitle = computed(() => (route.meta.title as string) || "管理设置");

const goBack = () => router.push({ name: "home" });
const onLogout = () => {
  auth.logout();
  router.push({ name: "login" });
};
</script>
