<template>
  <div style="display: none;" aria-hidden="true" />
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useAuthStore } from "@/store/auth";
import { useBannerStore } from "@/store/banner";
import { useMqttStatusStore } from "@/store/mqttStatus";
import { useDevicesStore, type Device } from "@/store/devices";

const auth = useAuthStore();
const banner = useBannerStore();
const mqttStatus = useMqttStatusStore();
const devices = useDevicesStore();

const lastSeenLogId = ref(0);
const firstPollDone = ref(false);

type RealtimeLogPayload = {
  id: number;
  source: string;
  level: string;
  message: string;
  created_at?: string;
};

type RealtimeInitPayload = {
  last_log_id: number;
  mqtt_connected: boolean;
  devices: Device[];
};

type RealtimeDevicesPayload = {
  items: Device[];
};

const rawApiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
const normalizedApiBaseUrl = rawApiBaseUrl
  .replace(/\/+$/, "")
  .replace(/\/api$/, "");

let stream: EventSource | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
const reconnectDelayMs = 2000;

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

function parseEventData<T>(event: Event): T | null {
  try {
    const data = (event as MessageEvent<string>).data;
    return JSON.parse(data) as T;
  } catch {
    return null;
  }
}

function buildRealtimeStreamUrl() {
  const path = "/api/realtime/stream/";
  const baseUrl = normalizedApiBaseUrl ? `${normalizedApiBaseUrl}${path}` : path;
  const accessToken = auth.accessToken;
  if (!accessToken) return baseUrl;
  const separator = baseUrl.includes("?") ? "&" : "?";
  return `${baseUrl}${separator}access_token=${encodeURIComponent(accessToken)}`;
}

function clearReconnectTimer() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
}

function closeStream() {
  if (stream) {
    stream.close();
    stream = null;
  }
}

function scheduleReconnect() {
  if (reconnectTimer || !auth.isAuthenticated) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    openRealtimeStream();
  }, reconnectDelayMs);
}

function openRealtimeStream() {
  closeStream();
  clearReconnectTimer();
  const url = buildRealtimeStreamUrl();
  stream = new EventSource(url);

  stream.addEventListener("init", (event) => {
    const payload = parseEventData<RealtimeInitPayload>(event);
    if (!payload) return;
    if (typeof payload.last_log_id === "number") {
      lastSeenLogId.value = payload.last_log_id;
    }
    if (typeof payload.mqtt_connected === "boolean") {
      mqttStatus.setConnected(payload.mqtt_connected);
    }
    if (Array.isArray(payload.devices)) {
      devices.setDevicesSnapshot(payload.devices);
    }
    firstPollDone.value = true;
  });

  stream.addEventListener("log", (event) => {
    const payload = parseEventData<RealtimeLogPayload>(event);
    if (!payload) return;
    logToBanner(payload);
  });

  stream.addEventListener("mqtt_status", (event) => {
    const payload = parseEventData<{ connected: boolean }>(event);
    if (!payload || typeof payload.connected !== "boolean") return;
    mqttStatus.setConnected(payload.connected);
  });

  stream.addEventListener("devices", (event) => {
    const payload = parseEventData<RealtimeDevicesPayload>(event);
    if (!payload || !Array.isArray(payload.items)) return;
    devices.setDevicesSnapshot(payload.items);
  });

  stream.onerror = () => {
    closeStream();
    scheduleReconnect();
  };
}

onMounted(() => {
  if (!auth.isAuthenticated) return;
  openRealtimeStream();
});

onUnmounted(() => {
  closeStream();
  clearReconnectTimer();
});
</script>
