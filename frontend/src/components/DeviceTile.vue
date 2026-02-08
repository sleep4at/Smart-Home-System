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
      <div v-else-if="isAC" class="device-metrics">
        <div class="metric-main">
          {{ acTempText }}
        </div>
        <div class="metric-sub">
          {{ device.type_display }}
        </div>
      </div>
      <div v-else-if="isFan" class="device-metrics">
        <div class="metric-main">
          {{ fanSpeedText }}
        </div>
        <div class="metric-sub">
          {{ device.type_display }}
        </div>
      </div>
      <div v-else-if="isLight" class="device-metrics">
        <div class="metric-main">
          {{ lightText }}
        </div>
        <div class="metric-sub">
          {{ device.type_display }}
        </div>
      </div>
      <div v-else-if="isPressure" class="device-metrics">
        <div class="metric-main">
          {{ pressureText }}
        </div>
        <div class="metric-sub">
          {{ device.type_display }}
        </div>
      </div>
      <div v-else-if="isLampSwitch" class="device-metrics">
        <div class="metric-main">
          {{ switchLabel }}
        </div>
        <div class="metric-sub">
          {{ device.type_display }}
        </div>
      </div>
      <div v-else-if="isSmoke" class="device-metrics">
        <div class="metric-main">{{ device.type_display }}</div>
        <div class="smoke-status" :class="smokeStatusClass">
          {{ smokeStatusText }}
        </div>
      </div>
      <div v-else-if="isPir" class="device-metrics">
        <div class="metric-main">{{ device.type_display }}</div>
        <div class="pir-status" :class="pirStatusClass">
          {{ pirStatusText }}
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
      <div v-if="isAC" class="ac-controls">
        <div class="temp-control">
          <button
            class="temp-btn"
            @click="adjustTemp(-1)"
            :disabled="!canControl"
          >
            −
          </button>
          <span class="temp-display">{{ currentTemp }}°C</span>
          <button
            class="temp-btn"
            @click="adjustTemp(1)"
            :disabled="!canControl"
          >
            +
          </button>
        </div>
        <button
          class="toggle-switch"
          :class="{ on: isOn }"
          @click="toggle"
          :disabled="!canControl"
        >
          <span class="toggle-thumb" />
        </button>
      </div>
      <div v-else-if="isFan" class="fan-controls">
        <div class="speed-control">
          <button
            v-for="s in [1, 2, 3]"
            :key="s"
            class="speed-btn"
            :class="{ active: currentSpeed === s }"
            @click="setSpeed(s)"
            :disabled="!canControl"
          >
            {{ s }}
          </button>
        </div>
        <button
          class="toggle-switch"
          :class="{ on: isOn }"
          @click="toggle"
          :disabled="!canControl"
        >
          <span class="toggle-thumb" />
        </button>
      </div>
      <div v-else-if="isLampSwitch">
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
import { useDevicesStore } from "@/store/devices";
import { useBannerStore } from "@/store/banner";

const props = defineProps<{
  device: Device;
}>();

const emit = defineEmits<{
  (e: "toggle", device: Device): void;
  (e: "edit", device: Device): void;
}>();

const auth = useAuthStore();
const devicesStore = useDevicesStore();
const banner = useBannerStore();

const isAdmin = computed(() => auth.isAdmin);
const isTempHumi = computed(() => props.device.type === "TEMP_HUMI");
const isAC = computed(() => props.device.type === "AC_SWITCH");
const isFan = computed(() => props.device.type === "FAN_SWITCH");
const isLight = computed(() => props.device.type === "LIGHT");
const isPressure = computed(() => props.device.type === "PRESSURE");
const isLampSwitch = computed(() => props.device.type === "LAMP_SWITCH");
const isSmoke = computed(() => props.device.type === "SMOKE");
const isPir = computed(() => props.device.type === "PIR");
const isSwitch = computed(() =>
  ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(props.device.type)
);

/** 人体感应：根据 payload 的 motion / pir / value 判断是否已探测 */
const pirDetected = computed(() => {
  const s = props.device.current_state;
  if (!s || typeof s !== "object") return false;
  if (s.motion === true || s.pir === true) return true;
  const v = s.value;
  if (v !== undefined && v !== null) return Number(v) > 0;
  return false;
});

/** 人体感应状态文案：离线固定「未探测」，在线按探测结果显示「未探测」/「已探测」 */
const pirStatusText = computed(() => {
  if (!props.device.is_online) return "未探测";
  return pirDetected.value ? "已探测" : "未探测";
});

/** 人体感应状态样式类 */
const pirStatusClass = computed(() => {
  if (!props.device.is_online) return "pir-idle";
  return pirDetected.value ? "pir-detected" : "pir-idle";
});

/** 烟雾传感器二值：根据 payload 的 smoke / alarm / value 判断是否触发 */
const smokeTriggered = computed(() => {
  const s = props.device.current_state;
  if (!s || typeof s !== "object") return false;
  if (s.smoke === true || s.alarm === true) return true;
  const v = s.value;
  if (v !== undefined && v !== null) return Number(v) > 0;
  return false;
});

/** 烟雾传感器状态文案：离线显示「未获取」，在线按触发与否显示「正常」/「警告」 */
const smokeStatusText = computed(() => {
  if (!props.device.is_online) return "未获取";
  return smokeTriggered.value ? "警告" : "正常";
});

/** 烟雾传感器状态样式类 */
const smokeStatusClass = computed(() => {
  if (!props.device.is_online) return "smoke-unknown";
  return smokeTriggered.value ? "smoke-warning" : "smoke-normal";
});

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

const lightText = computed(() => {
  const l = props.device.current_state?.light;
  return l !== undefined && l !== null ? `${l} Lux` : "暂无光照数据";
});

const pressureText = computed(() => {
  const p = props.device.current_state?.pressure;
  return p !== undefined && p !== null ? `${p} hPa` : "暂无气压数据";
});

const acTempText = computed(() => {
  const t = props.device.current_state?.temp;
  return t !== undefined ? `${t}°C` : "未设置";
});

const currentTemp = computed(() => {
  return props.device.current_state?.temp ?? 26;
});

const currentSpeed = computed(() => {
  return props.device.current_state?.speed ?? 1;
});

const fanSpeedText = computed(() => {
  const s = currentSpeed.value;
  return `档位 ${s}`;
});

const switchLabel = computed(() => (isOn.value ? "已开启" : "已关闭"));

const extraInfo = computed(() => {
  if (props.device.location) return props.device.location;
  return "—";
});

const toggle = () => {
  emit("toggle", props.device);
};

const adjustTemp = async (delta: number) => {
  if (!canControl.value) return;
  const newTemp = Math.max(16, Math.min(30, currentTemp.value + delta));
  await devicesStore.setTemp(props.device.id, newTemp);
  banner.add({
    type: "success",
    message: `指令已下发：${props.device.name} -> ${newTemp}°C`,
  });
};

const setSpeed = async (speed: 1 | 2 | 3) => {
  if (!canControl.value) return;
  await devicesStore.setFanSpeed(props.device.id, speed);
  banner.add({
    type: "success",
    message: `指令已下发：${props.device.name} -> ${speed}档`,
  });
};
</script>

<style scoped>
.ac-controls,
.fan-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.temp-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.temp-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid #d1d5db;
  background: #fff;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.temp-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.temp-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.temp-display {
  min-width: 50px;
  text-align: center;
  font-weight: 500;
  font-size: 14px;
}

.speed-control {
  display: flex;
  gap: 4px;
}

.speed-btn {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 1px solid #d1d5db;
  background: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.speed-btn:hover:not(:disabled) {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.speed-btn.active {
  background: #3b82f6;
  color: #fff;
  border-color: #3b82f6;
}

.speed-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.smoke-status {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  margin-top: 4px;
}
.smoke-status.smoke-normal {
  background: #dcfce7;
  color: #166534;
}
.smoke-status.smoke-warning {
  background: #fee2e2;
  color: #b91c1c;
}
.smoke-status.smoke-unknown {
  background: #f3f4f6;
  color: #6b7280;
}

.pir-status {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 500;
  margin-top: 4px;
}
.pir-status.pir-idle {
  background: #f3f4f6;
  color: #6b7280;
}
.pir-status.pir-detected {
  background: #dbeafe;
  color: #1d4ed8;
}
</style>

