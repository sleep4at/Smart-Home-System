<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
      <div class="app-main-subtitle">控制台输出（系统调试日志）</div>
      <div style="display: flex; gap: 8px; align-items: center;">
        <select v-model="filterSource" class="field-select" style="width: 140px;">
          <option value="">全部来源</option>
          <option value="MQTT_GATEWAY">MQTT 网关</option>
          <option value="MQTT_LWT">设备上下线</option>
          <option value="ALERT">安全告警</option>
          <option value="SCENE_RULE">场景联动</option>
          <option value="SYSTEM">系统</option>
        </select>
        <select v-model="filterLevel" class="field-select" style="width: 100px;">
          <option value="">全部级别</option>
          <option value="INFO">信息</option>
          <option value="WARN">警告</option>
          <option value="ERROR">错误</option>
        </select>
        <button class="btn btn-ghost" @click="refreshLogs">刷新</button>
      </div>
    </div>
    <div class="debug-console">
      <div
        v-for="log in filteredLogs"
        :key="log.id"
        class="debug-line"
      >
        <span class="debug-time">{{ formatTime(log.created_at) }}</span>
        <span :class="['debug-level', log.level.toLowerCase()]">[{{ log.level }}]</span>
        <span class="debug-source">{{ log.source }}</span>
        <span class="debug-message">{{ log.message }}</span>
        <span v-if="log.data && Object.keys(log.data).length" class="debug-data">
          {{ formatData(log.data) }}
        </span>
      </div>
      <div v-if="!filteredLogs.length" class="debug-empty">暂无日志</div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useLogsStore } from "@/store/logs";

const logs = useLogsStore();
const filterSource = ref("");
const filterLevel = ref("");

const filteredLogs = computed(() => logs.list);

function formatTime(timestamp: string) {
  const d = new Date(timestamp);
  const y = d.getFullYear();
  const M = String(d.getMonth() + 1).padStart(2, "0");
  const D = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  return `${y}-${M}-${D} ${h}:${m}:${s}`;
}

function formatData(data: Record<string, unknown>) {
  if (!data || typeof data !== "object") return "";
  const parts: string[] = [];
  if (data.payload && typeof data.payload === "object") {
    const p = data.payload as Record<string, unknown>;
    const kv = Object.entries(p)
      .map(([k, v]) => {
        if (k === "temp" && v != null) return `温度 ${v}°C`;
        if (k === "humi" && v != null) return `湿度 ${v}%`;
        if (k === "on" && v != null) return v ? "开" : "关";
        if (k === "speed" && v != null) return `档位 ${v}`;
        return `${k}=${v}`;
      })
      .filter(Boolean);
    if (kv.length) parts.push(kv.join(", "));
  }
  if (data.topic) parts.push(String(data.topic));
  return parts.length ? " | " + parts.join(" ") : "";
}

function refreshLogs() {
  logs.fetchLogs({
    limit: 300,
    source: filterSource.value || undefined,
    level: filterLevel.value || undefined,
  });
}

watch([filterSource, filterLevel], () => {
  refreshLogs();
});

onMounted(refreshLogs);
const t = setInterval(() => refreshLogs(), 3000);
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
  max-height: 70vh;
  overflow-y: auto;
  box-shadow: var(--shadow-soft);
}

.debug-line {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 12px;
  align-items: baseline;
  flex-wrap: wrap;
}

.debug-time {
  color: #64748b;
  min-width: 160px;
  white-space: nowrap;
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
  min-width: 100px;
}

.debug-message {
  flex: 1;
  min-width: 0;
}

.debug-data {
  color: #94a3b8;
  font-size: 12px;
}

.debug-empty {
  color: #64748b;
  text-align: center;
  padding: 40px;
}
</style>
