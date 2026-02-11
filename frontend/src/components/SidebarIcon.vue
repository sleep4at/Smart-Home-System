<template>
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.9"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path v-for="(d, idx) in paths" :key="idx" :d="d" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";

type SidebarIconName =
  | "home"
  | "history"
  | "energy"
  | "scenes"
  | "users"
  | "devices"
  | "mail"
  | "debug"
  | "logs";

const props = defineProps<{
  name: string;
}>();

const ICON_PATHS: Record<SidebarIconName, string[]> = {
  home: [
    "M3 10.5L12 3l9 7.5",
    "M5.25 9.75v10.5h13.5V9.75",
  ],
  history: [
    "M12 7.5v5.25l3 1.75",
    "M12 3.75a8.25 8.25 0 1 1-5.834 2.416",
    "M4.5 3.75v4.5H9",
  ],
  energy: [
    "M13.5 2.75L6.75 13h4.5l-1.5 8.25L17.25 11h-4.5l.75-8.25Z",
  ],
  scenes: [
    "M7 5a2 2 0 1 0 0 4a2 2 0 0 0 0-4Z",
    "M17 3a2 2 0 1 0 0 4a2 2 0 0 0 0-4Z",
    "M17 13a2 2 0 1 0 0 4a2 2 0 0 0 0-4Z",
    "M9 7h6",
    "M8.5 8.5l6 6",
  ],
  users: [
    "M9 11a3 3 0 1 0 0-6a3 3 0 0 0 0 6Z",
    "M17 10a2.5 2.5 0 1 0 0-5a2.5 2.5 0 0 0 0 5Z",
    "M3.5 19c.75-2.5 2.75-4 5.5-4s4.75 1.5 5.5 4",
    "M14.75 18.5c.5-1.65 1.75-2.7 3.75-2.95",
  ],
  devices: [
    "M9 4.75h6v14.5H9Z",
    "M11 7.5h2",
    "M11 10h2",
    "M11 12.5h2",
    "M11 15h2",
    "M7 8h2",
    "M7 12h2",
    "M7 16h2",
    "M15 8h2",
    "M15 12h2",
    "M15 16h2",
  ],
  mail: [
    "M3.75 6.75h16.5v10.5H3.75Z",
    "M4.5 7.5L12 13l7.5-5.5",
  ],
  debug: [
    "M14.5 5.5l4 4",
    "M4.75 19.25l5.75-1.25 8-8-4.5-4.5-8 8-1.25 5.75Z",
  ],
  logs: [
    "M7 4.75h10v14.5H7Z",
    "M9.5 8h5",
    "M9.5 11.5h5",
    "M9.5 15h3.5",
    "M5 8h.01",
    "M5 11.5h.01",
    "M5 15h.01",
  ],
};

const paths = computed(
  () => ICON_PATHS[props.name as SidebarIconName] || ICON_PATHS.home
);
</script>
