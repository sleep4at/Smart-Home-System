<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="sidebar-logo" v-if="!collapsed">管理设置</div>
      <button class="sidebar-toggle" @click="$emit('toggle')">
        <span v-if="collapsed">›</span>
        <span v-else>‹</span>
      </button>
    </div>
    <nav class="sidebar-nav">
      <RouterLink
        v-for="item in items"
        :key="item.route"
        :to="{ name: item.route }"
        class="sidebar-item"
        :title="item.label"
        :class="$route.name === item.route ? 'active' : 'inactive'"
      >
        <span class="icon" aria-hidden="true">
          <SidebarIcon :name="item.icon" />
        </span>
        <span class="sidebar-label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
import SidebarIcon from "@/components/SidebarIcon.vue";

defineProps<{ collapsed: boolean }>();
defineEmits<{ (e: "toggle"): void }>();

const items = [
  { route: "admin-users", label: "用户管理", icon: "users" },
  { route: "admin-devices", label: "设备管理", icon: "devices" },
  { route: "admin-email-alerts", label: "邮件告警", icon: "mail" },
  { route: "admin-debug-tools", label: "调试工具", icon: "debug" },
  { route: "admin-console", label: "日志信息", icon: "logs" },
];
</script>
