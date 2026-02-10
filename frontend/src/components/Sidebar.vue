<template>
  <aside class="sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <div class="sidebar-logo" v-if="!collapsed">智能家居</div>
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
        :class="[
          $route.name === item.route ? 'active' : 'inactive',
        ]"
      >
        <span class="sidebar-label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink, useRoute } from "vue-router";

defineProps<{
  collapsed: boolean;
}>();

defineEmits<{
  (e: "toggle"): void;
}>();

const route = useRoute();

const items = [
  { route: "home", label: "主页" },
  { route: "history", label: "历史数据" },
  { route: "scenes", label: "场景模式" },
];
</script>
