<template>
  <div class="device-tile">
    <div class="device-tile-header">
      <div class="device-tile-title">
        {{ device.name || "未命名设备" }}
      </div>
      <div
        class="device-tile-status"
        :class="device.is_online ? 'status-online' : 'status-offline'"
      >
        <span class="dot" />
        <span>{{ device.is_online ? "已连接" : "离线" }}</span>
      </div>
    </div>
    <div class="device-tile-body">
      <div v-if="isTempHumi" class="device-metrics">
        <div class="metric-main">
          {{ temperatureText }}
        </div>
        <div class="metric-sub">
          {{ humidityText }}
        </div>
      </div>
      <div v-else-if="isSwitch" class="device-metrics">
        <div class="metric-main">
          {{ switchLabel }}
        </div>
        <div class="metric-sub">
          {{ device.type_display }}
        </div>
      </div>
      <div v-else class="device-metrics">
        <div class="metric-main">{{ device.type_display }}</div>
        <div class="metric-sub">
          {{ extraInfo }}
        </div>
      </div>
    </div>
    <div class="device-tile-footer">
      <div v-if="isSwitch">
        <button
          class="toggle-switch"
          :class="{ on: isOn }"
          @click="toggle"
          :disabled="!canControl"
          :title="!canControl ? '无权限控制该设备' : ''"
        >
          <span class="toggle-thumb" />
        </button>
      </div>
      <div v-else></div>
      <div>
        <button
          v-if="isAdmin"
          class="btn btn-ghost"
          @click="$emit('edit', device)"
        >
          编辑
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Device } from "@/store/devices";
import { useAuthStore } from "@/store/auth";

const props = defineProps<{
  device: Device;
}>();

const emit = defineEmits<{
  (e: "toggle", device: Device): void;
  (e: "edit", device: Device): void;
}>();

const auth = useAuthStore();

const isAdmin = computed(() => auth.isAdmin);
const isTempHumi = computed(() => props.device.type === "TEMP_HUMI");
const isSwitch = computed(() =>
  ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(props.device.type)
);

const isOn = computed(
  () => !!(props.device.current_state && props.device.current_state.on)
);

const canControl = computed(() => {
  // 离线时禁止操作；后端仍然会做二次权限校验
  return props.device.is_online;
});

const temperatureText = computed(() => {
  const t = props.device.current_state?.temp;
  return t !== undefined ? `${t}°C` : "暂无温度数据";
});

const humidityText = computed(() => {
  const h = props.device.current_state?.humi;
  return h !== undefined ? `${h}%RH` : "暂无湿度数据";
});

const switchLabel = computed(() => (isOn.value ? "已开启" : "已关闭"));

const extraInfo = computed(() => {
  if (props.device.location) return props.device.location;
  return "—";
});

const toggle = () => {
  emit("toggle", props.device);
};
</script>

