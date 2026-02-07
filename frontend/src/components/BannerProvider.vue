<template>
  <div style="display: none;" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import api from "@/utils/http";
import { useAuthStore } from "@/store/auth";
import { useBannerStore } from "@/store/banner";
import { useLogsStore } from "@/store/logs";

const auth = useAuthStore();
const banner = useBannerStore();
const logsStore = useLogsStore();

const lastSeenLogId = ref(0);
const firstPollDone = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

function logToBanner(log: { id: number; source: string; level: string; message: string }) {
  if (log.id <= lastSeenLogId.value) return;
  lastSeenLogId.value = Math.max(lastSeenLogId.value, log.id);
  if (!firstPollDone.value) return;

  let type: "info" | "success" | "warn" | "error" = "info";
  if (log.level === "ERROR") type = "error";
  else if (log.level === "WARN") type = "warn";
  else if (log.source === "SCENE_RULE") type = "success";

  if (log.source === "MQTT_LWT") {
    banner.add({
      type: log.message.includes("离线") ? "warn" : "info",
      message: log.message,
    });
    return;
  }
  if (log.source === "ALERT") {
    banner.add({ type: "warn", message: log.message });
    return;
  }
  if (log.source === "SCENE_RULE") {
    banner.add({ type: "success", message: log.message });
    return;
  }
  if (log.source === "MQTT_GATEWAY") {
    banner.add({ type: "info", message: log.message, autoCloseMs: 5000 });
    return;
  }
  if (log.source === "EMAIL_ALERT") {
    banner.add({
      type: log.level === "ERROR" ? "error" : "success",
      message: log.message,
      autoCloseMs: 6000,
    });
    return;
  }
  banner.add({ type, message: log.message, autoCloseMs: 5000 });
}

async function fetchMqttStatus() {
  try {
    const res = await api.get<{ connected: boolean; error?: string }>("/api/mqtt/status/");
    if (res.data.connected) {
      banner.add({ type: "success", message: "MQTT Broker 已连接", autoCloseMs: 4000 });
    } else {
      banner.add({
        type: "warn",
        message: "MQTT Broker 未连接，设备状态可能无法实时更新",
        autoCloseMs: 6000,
      });
    }
  } catch {
    banner.add({
      type: "warn",
      message: "无法获取 MQTT 连接状态",
      autoCloseMs: 5000,
    });
  }
}

function pollLogs() {
  logsStore.fetchLogs({ limit: 30 }).then(() => {
    const list = logsStore.list;
    list.forEach((log) => logToBanner(log));
    const maxId = list.length ? Math.max(...list.map((l) => l.id)) : 0;
    if (maxId > lastSeenLogId.value) lastSeenLogId.value = maxId;
    if (!firstPollDone.value) firstPollDone.value = true;
  });
}

onMounted(() => {
  if (!auth.isAuthenticated) return;
  fetchMqttStatus();
  pollTimer = setInterval(pollLogs, 5000);
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
});
</script>
