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
        :title="item.label"
        :class="[
          $route.name === item.route ? 'active' : 'inactive',
        ]"
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

defineProps<{
  collapsed: boolean;
}>();

defineEmits<{
  (e: "toggle"): void;
}>();

const items = [
  { route: "home", label: "主页", icon: "home" },
  { route: "history", label: "历史数据", icon: "history" },
  { route: "energy", label: "能耗分析", icon: "energy" },
  { route: "scenes", label: "场景模式", icon: "scenes" },
];
</script>
