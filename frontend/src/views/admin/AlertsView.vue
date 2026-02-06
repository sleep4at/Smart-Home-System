<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">安全告警</div>
      <button class="btn btn-ghost" @click="refreshAlerts">刷新</button>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>级别</th>
            <th>来源</th>
            <th>消息</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="log in alerts" :key="log.id">
            <td>{{ formatTime(log.created_at) }}</td>
            <td>{{ log.level }}</td>
            <td>{{ log.source }}</td>
            <td>{{ log.message }}</td>
          </tr>
          <tr v-if="!alerts.length">
            <td colspan="4" style="text-align: center; padding: 24px;">暂无安全告警</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useLogsStore } from "@/store/logs";

const logs = useLogsStore();

const alerts = computed(() =>
  logs.list.filter((l) => l.source === "ALERT" || l.level === "WARN" || l.level === "ERROR")
);

function formatTime(timestamp: string) {
  const d = new Date(timestamp);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hours = String(d.getHours()).padStart(2, "0");
  const minutes = String(d.getMinutes()).padStart(2, "0");
  const seconds = String(d.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

function refreshAlerts() {
  logs.fetchLogs();
}

onMounted(refreshAlerts);
</script>

