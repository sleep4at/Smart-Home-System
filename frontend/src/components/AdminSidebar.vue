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
        :class="$route.name === item.route ? 'active' : 'inactive'"
      >
        <span class="sidebar-label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";

defineProps<{ collapsed: boolean }>();
defineEmits<{ (e: "toggle"): void }>();

const items = [
  { route: "admin-users", label: "用户管理" },
  { route: "admin-devices", label: "设备管理" },
  { route: "admin-email-alerts", label: "邮件告警" },
  { route: "admin-debug-tools", label: "调试工具" },
  { route: "admin-console", label: "日志信息" },
];
</script>
