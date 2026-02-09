<template>
  <RouterView />
  <BannerList v-if="auth.initialized && auth.isAuthenticated" />
  <BannerProvider v-if="auth.initialized && auth.isAuthenticated" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { RouterView, useRouter } from "vue-router";
import { useAuthStore } from "@/store/auth";
import BannerList from "@/components/BannerList.vue";
import BannerProvider from "@/components/BannerProvider.vue";

const auth = useAuthStore();
const router = useRouter();

/** 失去焦点超过此时间（分钟）则视为会话过期，需重新登录 */
const INACTIVITY_EXPIRE_MINUTES = 30;

function setupInactivityLogout() {
  let inactiveSince: number | null = null;

  async function onVisibilityChange() {
    if (document.visibilityState === "hidden") {
      if (auth.isAuthenticated) inactiveSince = Date.now();
    } else {
      if (
        inactiveSince !== null &&
        (Date.now() - inactiveSince) >= INACTIVITY_EXPIRE_MINUTES * 60 * 1000
      ) {
        auth.logout();
        router.push({ name: "login" });
        inactiveSince = null;
        return;
      }
      inactiveSince = null;
      // 标签页重新可见时校验 token（后端重启后旧 token 会 401，需重新登录）
      if (auth.isAuthenticated) {
        const stillValid = await auth.revalidate();
        if (!stillValid) router.push({ name: "login" });
      }
    }
  }

  document.addEventListener("visibilitychange", onVisibilityChange);
  return () => document.removeEventListener("visibilitychange", onVisibilityChange);
}

let teardown: (() => void) | null = null;
onMounted(() => {
  teardown = setupInactivityLogout();
});
onUnmounted(() => {
  if (teardown) teardown();
});
</script>

