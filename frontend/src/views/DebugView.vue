<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">系统调试日志</div>
      <button class="btn btn-ghost" @click="refreshLogs">刷新</button>
    </div>
    <div class="debug-console">
      <div
        v-for="log in logs.list"
        :key="log.id"
        class="debug-line"
      >
        <span class="debug-time">{{ formatTime(log.created_at) }}</span>
        <span :class="['debug-level', log.level.toLowerCase()]">[{{ log.level }}]</span>
        <span class="debug-source">{{ log.source }}</span>
        <span>{{ log.message }}</span>
      </div>
      <div v-if="!logs.list.length" class="debug-empty">暂无日志</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { useLogsStore } from "@/store/logs";

const logs = useLogsStore();

function formatTime(timestamp: string) {
  const d = new Date(timestamp);
  const year = d.getFullYear();
  // 月份从 0 开始，所以需要 +1
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  const seconds = String(d.getSeconds()).padStart(2, "0");

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

// function formatTime(timestamp: string) {
//   const d = new Date(timestamp);
//   return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
// }

function refreshLogs() {
  logs.fetchLogs();
}

onMounted(refreshLogs);
const t = setInterval(refreshLogs, 3000);
onUnmounted(() => clearInterval(t));
</script>

<style scoped>
.debug-console {
  background: #1e293b;
  border-radius: var(--radius-large);
  padding: 16px;
  font-family: "Courier New", monospace;
  font-size: 13px;
  color: #e2e8f0;
  max-height: 600px;
  overflow-y: auto;
  box-shadow: var(--shadow-soft);
}
.debug-line {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 12px;
}
.debug-time {
  color: #64748b;
  min-width: 160px;
  white-space: nowrap;  /* 不换行 */
}
.debug-level {
  min-width: 50px;
}
.debug-level.info {
  color: #10b981;
}
.debug-level.warn {
  color: #f59e0b;
}
.debug-level.error {
  color: #ef4444;
}
.debug-source {
  color: #94a3b8;
  min-width: 120px;
}
.debug-empty {
  color: #64748b;
  text-align: center;
  padding: 40px;
}
</style>
