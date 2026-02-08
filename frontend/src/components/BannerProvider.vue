<template>
  <div style="display: none;" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import api from "@/utils/http";
import { useAuthStore } from "@/store/auth";
import { useBannerStore } from "@/store/banner";
import { useMqttStatusStore } from "@/store/mqttStatus";

const auth = useAuthStore();
const banner = useBannerStore();
const mqttStatus = useMqttStatusStore();

const lastSeenLogId = ref(0);
const firstPollDone = ref(false);
let pollTimer: ReturnType<typeof setInterval> | null = null;

function logToBanner(log: { id: number; source: string; level: string; message: string }) {
  if (log.id <= lastSeenLogId.value) return;
  lastSeenLogId.value = Math.max(lastSeenLogId.value, log.id);
  if (!firstPollDone.value) return;

  // 仅展示重要消息：设备上下线、安全告警、场景联动、邮件告警。不展示温湿度/开关等常规上报。
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
  if (log.source === "EMAIL_ALERT") {
    banner.add({
      type: log.level === "ERROR" ? "error" : "success",
      message: log.message,
      autoCloseMs: 6000,
    });
    return;
  }
  // MQTT_GATEWAY（温湿度、开关状态等）不弹横幅
  if (log.source === "MQTT_GATEWAY") return;
  // 其他来源仅警告/错误时展示
  if (log.level === "WARN" || log.level === "ERROR") {
    const type = log.level === "ERROR" ? "error" : "warn";
    banner.add({ type, message: log.message, autoCloseMs: 6000 });
  }
}

function updateMqttStatus() {
  mqttStatus.fetchStatus();
}

function pollLogs() {
  // 仅拉取最新日志用于横幅，不写入全局 logsStore，避免覆盖控制台页面的筛选结果
  api.get<{ id: number; source: string; level: string; message: string }[]>("/api/logs/system/", {
    params: { limit: 30 },
  }).then((res) => {
    const list = res.data || [];
    list.forEach((log) => logToBanner(log));
    const maxId = list.length ? Math.max(...list.map((l) => l.id)) : 0;
    if (maxId > lastSeenLogId.value) lastSeenLogId.value = maxId;
    if (!firstPollDone.value) firstPollDone.value = true;
  });
}

let mqttTimer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  if (!auth.isAuthenticated) return;
  updateMqttStatus();
  pollTimer = setInterval(pollLogs, 5000);
  mqttTimer = setInterval(updateMqttStatus, 3000); // 每 3 秒刷新 MQTT 状态，供主页指示器实时显示
});

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer);
  if (mqttTimer) clearInterval(mqttTimer);
});
</script>
