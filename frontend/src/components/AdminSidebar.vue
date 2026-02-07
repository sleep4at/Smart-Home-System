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
        <span class="icon">{{ item.icon }}</span>
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
  { route: "admin-users", label: "用户管理", icon: "👥" },
  { route: "admin-devices", label: "设备管理", icon: "📱" },
  { route: "admin-alerts", label: "安全告警", icon: "⚠️" },
  { route: "admin-email-alerts", label: "邮件告警", icon: "📧" },
  { route: "admin-debug-tools", label: "调试工具", icon: "🔧" },
  { route: "admin-console", label: "控制台输出", icon: "🖥" },
];
</script>
