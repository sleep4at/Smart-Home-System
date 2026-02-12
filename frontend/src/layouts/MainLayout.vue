<template>
  <div class="app-shell app-shell-fixed">
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
            <span class="mqtt-indicator" :class="mqtt.loading ? 'checking' : (mqtt.connected ? 'connected' : 'disconnected')">
              <span class="mqtt-dot" />
              {{ mqtt.loading ? "检查中…" : (mqtt.connected ? "MQTT 已连接" : "MQTT 未连接") }}
            </span>
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
import Sidebar from "@/components/Sidebar.vue";
import ProfileDialog from "@/components/ProfileDialog.vue";
import { useAuthStore } from "@/store/auth";
import { useMqttStatusStore } from "@/store/mqttStatus";

const collapsed = ref(false);
const showProfile = ref(false);
const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const mqtt = useMqttStatusStore();

const pageTitle = computed(() => (route.meta.title as string) || "主页");

const goToAdmin = () => router.push({ name: "admin-users" });
const onLogout = () => {
  auth.logout();
  router.push({ name: "login" });
};
</script>

<style scoped>
.mqtt-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: 12px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  background: var(--mqtt-bg, #f3f4f6);
  color: var(--mqtt-fg, #6b7280);
}
.mqtt-indicator.connected {
  --mqtt-bg: #ecfdf5;
  --mqtt-fg: #059669;
}
.mqtt-indicator.checking {
  --mqtt-bg: #eff6ff;
  --mqtt-fg: #2563eb;
}
.mqtt-indicator.disconnected {
  --mqtt-bg: #fef2f2;
  --mqtt-fg: #dc2626;
}
.mqtt-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.mqtt-indicator.connected .mqtt-dot {
  box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.3);
}
.mqtt-indicator.checking .mqtt-dot {
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.3);
}
.mqtt-indicator.disconnected .mqtt-dot {
  box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.3);
}
</style>
