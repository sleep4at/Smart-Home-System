<template>
  <div class="dialog-backdrop" @click.self="onClose">
    <div class="dialog-panel" style="max-width: 600px; max-height: 90vh; overflow-y: auto;">
      <div class="dialog-header">
        <div class="dialog-title">
          {{ rule && rule.id ? "编辑场景规则" : "创建场景规则" }}
        </div>
        <button class="btn btn-ghost" @click="onClose">✕</button>
      </div>
      <div class="dialog-body">
        <div>
          <div class="field-label">规则名称</div>
          <input
            v-model="form.name"
            class="field-input"
            placeholder="例如：温度过高自动开空调"
          />
        </div>

        <div>
          <div class="field-label">触发类型</div>
          <select v-model="form.trigger_type" class="field-select" @change="onTriggerTypeChange">
            <option value="THRESHOLD_ABOVE">高于阈值</option>
            <option value="THRESHOLD_BELOW">低于阈值</option>
            <option value="RANGE_OUT">超出范围</option>
            <option value="TIME_STATE">定时触发（时间 + 可选条件）</option>
          </select>
        </div>

        <!-- 阈值/区间类：触发设备 + 触发字段 -->
        <template v-if="form.trigger_type !== 'TIME_STATE'">
          <div>
            <div class="field-label">触发设备</div>
            <select v-model="form.trigger_device" class="field-select">
              <option disabled :value="0">请选择设备</option>
              <option v-for="d in sensorDevices" :key="d.id" :value="d.id">
                {{ d.name }} ({{ d.type_display }})
              </option>
            </select>
          </div>
          <div>
            <div class="field-label">触发字段</div>
            <select v-model="form.trigger_field" class="field-select">
              <option value="temp">温度 (temp)</option>
              <option value="humi">湿度 (humi)</option>
              <option value="light">光照 (light)</option>
              <option value="pressure">气压 (pressure)</option>
            </select>
          </div>
        </template>

        <div v-if="form.trigger_type === 'THRESHOLD_ABOVE' || form.trigger_type === 'THRESHOLD_BELOW'">
          <div class="field-label">阈值</div>
          <input
            v-model.number="form.trigger_value_single"
            type="number"
            class="field-input"
            placeholder="请输入阈值"
          />
        </div>

        <div v-if="form.trigger_type === 'RANGE_OUT'">
          <div style="display: flex; gap: 12px;">
            <div style="flex: 1;">
              <div class="field-label">最小值</div>
              <input
                v-model.number="form.trigger_value_min"
                type="number"
                class="field-input"
                placeholder="最小值"
              />
            </div>
            <div style="flex: 1;">
              <div class="field-label">最大值</div>
              <input
                v-model.number="form.trigger_value_max"
                type="number"
                class="field-input"
                placeholder="最大值"
              />
            </div>
          </div>
        </div>

        <!-- 定时触发：时间范围 + 可选“仅当某设备满足条件时才执行” -->
        <div v-if="form.trigger_type === 'TIME_STATE'" class="time-state-block">
          <div class="field-hint time-state-hint">
            在下面设定的<strong>每日时间段</strong>内，当「用于触发检查的设备」有数据上报时，会检查是否满足条件并执行动作。不选「附加条件」则到点就执行；选了则需同时满足（例如：18:00–23:00 且 人体传感器已探测 → 开灯）。
          </div>
          <div class="field-label">时间范围（每日）</div>
          <div style="display: flex; gap: 12px; margin-bottom: 12px;">
            <div style="flex: 1;">
              <input v-model="form.trigger_time_start" type="time" class="field-input" />
              <span class="field-hint-inline">开始</span>
            </div>
            <div style="flex: 1;">
              <input v-model="form.trigger_time_end" type="time" class="field-input" />
              <span class="field-hint-inline">结束</span>
            </div>
          </div>
          <div class="field-label">附加条件（可选）</div>
          <div class="field-hint" style="margin-bottom: 6px;">仅当以下设备满足状态时才执行，不选则只按时间执行</div>
          <select v-model="form.trigger_state_device" class="field-select">
            <option :value="null">不限制（到时间就执行）</option>
            <option v-for="d in stateConditionDevices" :key="d.id" :value="d.id">
              {{ d.name }} ({{ d.type_display }})
            </option>
          </select>
          <div v-if="form.trigger_state_device" style="margin-top: 8px;">
            <div class="field-label">{{ selectedStateDeviceIsPir ? "探测状态" : "开关状态" }}</div>
            <select v-if="selectedStateDeviceIsPir" v-model="form.trigger_state_detected" class="field-select">
              <option :value="true">已探测（有人时）</option>
              <option :value="false">未探测</option>
            </select>
            <select v-else v-model="form.trigger_state_on" class="field-select">
              <option :value="true">开启</option>
              <option :value="false">关闭</option>
            </select>
          </div>
          <div style="margin-top: 14px; padding-top: 12px; border-top: 1px dashed #e5e7eb;">
            <div class="field-label">用于触发检查的设备</div>
            <div class="field-hint" style="margin-bottom: 6px;">定时规则需在“某设备上报数据时”检查时间，请选择一台会定期上报的设备（如温湿度、人体感应）</div>
            <select v-model="form.trigger_device" class="field-select">
              <option disabled :value="0">请选择设备</option>
              <option v-for="d in timeTriggerDevices" :key="d.id" :value="d.id">
                {{ d.name }} ({{ d.type_display }})
              </option>
            </select>
            <div style="margin-top: 6px;">
              <div class="field-label">触发字段（任选其一，仅用于保存）</div>
              <select v-model="form.trigger_field" class="field-select">
                <option value="temp">温度 (temp)</option>
                <option value="humi">湿度 (humi)</option>
                <option value="light">光照 (light)</option>
                <option value="pressure">气压 (pressure)</option>
              </select>
            </div>
          </div>
        </div>

        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb;">
          <div class="field-label">执行设备</div>
          <select v-model="form.action_device" class="field-select">
            <option disabled :value="0">请选择设备</option>
            <option
              v-for="d in actionDevices"
              :key="d.id"
              :value="d.id"
            >
              {{ d.name }} ({{ d.type_display }})
            </option>
          </select>
        </div>

        <div>
          <div class="field-label">动作类型</div>
          <select v-model="form.action_type" class="field-select" @change="onActionTypeChange">
            <option value="TOGGLE">切换开关</option>
            <option value="SET_TEMP">设置温度（空调）</option>
            <option value="SET_FAN_SPEED">设置风扇档位</option>
            <option value="TURN_ON">开启设备</option>
            <option value="TURN_OFF">关闭设备</option>
          </select>
          <div class="field-hint" style="margin-top: 4px; color: #6b7280; font-size: 12px;">
            切换开关：根据当前状态取反（开→关，关→开）；开启/关闭设备：固定设为开或关。
          </div>
        </div>

        <div v-if="form.action_type === 'SET_TEMP'">
          <div class="field-label">目标温度 (°C)</div>
          <input
            v-model.number="form.action_temp"
            type="number"
            min="16"
            max="30"
            class="field-input"
            placeholder="16-30"
          />
        </div>

        <div v-if="form.action_type === 'SET_FAN_SPEED'">
          <div class="field-label">风扇档位</div>
          <select v-model.number="form.action_speed" class="field-select">
            <option :value="1">1档</option>
            <option :value="2">2档</option>
            <option :value="3">3档</option>
          </select>
        </div>

        <div>
          <div class="field-label">防抖时间（秒）</div>
          <input
            v-model.number="form.debounce_seconds"
            type="number"
            min="10"
            class="field-input"
            placeholder="防止频繁触发，建议60秒以上"
          />
        </div>
      </div>
      <div class="dialog-footer">
        <div v-if="errorMessage" class="dialog-error">{{ errorMessage }}</div>
        <button class="btn btn-ghost" @click="onClose">取消</button>
        <button class="btn btn-primary" @click="onSubmit">保存</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import type { Device } from "@/store/devices";
import type { SceneRule } from "@/store/scenes";

const props = defineProps<{
  rule: SceneRule | null;
  devices: Device[];
  errorMessage?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: Partial<SceneRule>): void;
  (e: "error", message: string): void;
  (e: "clear-error"): void;
}>();

const sensorDevices = computed(() =>
  props.devices.filter((d) =>
    ["TEMP_HUMI", "LIGHT", "PRESSURE"].includes(d.type)
  )
);

const switchDevices = computed(() =>
  props.devices.filter((d) =>
    ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(d.type)
  )
);

/** 定时触发时的“附加条件”可选设备：开关类 + 人体感应 */
const stateConditionDevices = computed(() =>
  props.devices.filter((d) =>
    ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH", "PIR"].includes(d.type)
  )
);

/** 定时触发时“用于触发检查”的设备：会定期或事件上报的传感器 + 人体感应 */
const timeTriggerDevices = computed(() =>
  props.devices.filter((d) =>
    ["TEMP_HUMI", "LIGHT", "PRESSURE", "PIR"].includes(d.type)
  )
);

/** 当前选中的状态设备是否为人体感应（用于显示 已探测/未探测） */
const selectedStateDeviceIsPir = computed(() => {
  if (!form.trigger_state_device) return false;
  const d = props.devices.find((x) => x.id === form.trigger_state_device);
  return d?.type === "PIR";
});

const actionDevices = computed(() =>
  props.devices.filter((d) =>
    ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(d.type)
  )
);

const emptyForm = () => ({
  name: "",
  trigger_type: "THRESHOLD_ABOVE" as SceneRule["trigger_type"],
  trigger_device: 0,
  trigger_field: "temp",
  trigger_value_single: 0,
  trigger_value_min: 0,
  trigger_value_max: 0,
  trigger_time_start: "",
  trigger_time_end: "",
  trigger_state_device: null as number | null,
  trigger_state_on: true,
  trigger_state_detected: true,
  action_device: 0,
  action_type: "TOGGLE" as SceneRule["action_type"],
  action_temp: 26,
  action_speed: 1,
  debounce_seconds: 60,
});

const form = reactive(emptyForm());

watch(
  () => props.rule,
  (val) => {
    if (val) {
      form.name = val.name;
      form.trigger_type = val.trigger_type;
      form.trigger_device = val.trigger_device;
      form.trigger_field = val.trigger_field;
      if (val.trigger_type === "RANGE_OUT" && typeof val.trigger_value === "object" && val.trigger_value !== null) {
        form.trigger_value_min = val.trigger_value.min || 0;
        form.trigger_value_max = val.trigger_value.max || 0;
      } else {
        form.trigger_value_single = typeof val.trigger_value === "number" ? val.trigger_value : 0;
      }
      form.trigger_time_start = val.trigger_time_start?.slice(0, 5) || "";
      form.trigger_time_end = val.trigger_time_end?.slice(0, 5) || "";
      form.trigger_state_device = val.trigger_state_device;
      if (val.trigger_state_value && typeof val.trigger_state_value === "object") {
        if ("motion" in val.trigger_state_value) {
          form.trigger_state_detected = !!val.trigger_state_value.motion;
        } else if ("value" in val.trigger_state_value) {
          form.trigger_state_detected = Number(val.trigger_state_value.value) > 0;
        }
        if ("on" in val.trigger_state_value) {
          form.trigger_state_on = !!val.trigger_state_value.on;
        }
      }
      form.action_device = val.action_device;
      form.action_type = val.action_type;
      if (val.action_type === "SET_TEMP") {
        form.action_temp = typeof val.action_value === "number" ? val.action_value : val.action_value?.temp || 26;
      } else if (val.action_type === "SET_FAN_SPEED") {
        form.action_speed = typeof val.action_value === "number" ? val.action_value : val.action_value?.speed || 1;
      }
      form.debounce_seconds = val.debounce_seconds;
    } else {
      Object.assign(form, emptyForm());
    }
  },
  { immediate: true }
);

watch(
  () => ({ ...form }),
  () => {
    emit("clear-error");
  },
  { deep: true }
);

const onTriggerTypeChange = () => {
  if (form.trigger_type !== "TIME_STATE") {
    form.trigger_time_start = "";
    form.trigger_time_end = "";
    form.trigger_state_device = null;
  } else {
    if (!form.trigger_device || !timeTriggerDevices.value.some((d) => d.id === form.trigger_device)) {
      form.trigger_device = timeTriggerDevices.value[0]?.id ?? 0;
    }
  }
};

const onActionTypeChange = () => {
  // 切换动作类型时重置相关字段
  form.action_temp = 26;
  form.action_speed = 1;
};

const onClose = () => emit("close");
const errorMessage = computed(() => props.errorMessage || "");

const onSubmit = () => {
  // 构建 trigger_value
  let trigger_value: number | { min: number; max: number };
  if (form.trigger_type === "RANGE_OUT") {
    trigger_value = {
      min: form.trigger_value_min,
      max: form.trigger_value_max,
    };
  } else {
    trigger_value = form.trigger_value_single;
  }

  // 构建 action_value
  let action_value: number | { temp?: number; speed?: number } | null = null;
  if (form.action_type === "SET_TEMP") {
    action_value = form.action_temp;
  } else if (form.action_type === "SET_FAN_SPEED") {
    action_value = form.action_speed;
  }

  // 构建 trigger_state_value（定时 + 附加条件）
  let trigger_state_value: Record<string, any> | null = null;
  if (form.trigger_type === "TIME_STATE" && form.trigger_state_device) {
    const stateDev = props.devices.find((d) => d.id === form.trigger_state_device);
    if (stateDev?.type === "PIR") {
      trigger_state_value = { motion: form.trigger_state_detected };
    } else {
      trigger_state_value = { on: form.trigger_state_on };
    }
  }

  if (!form.name?.trim()) {
    emit("error", "请输入规则名称。");
    return;
  }
  if (!form.trigger_device || form.trigger_device === 0) {
    emit("error", form.trigger_type === "TIME_STATE" ? "请选择用于触发检查的设备。" : "请选择触发设备。");
    return;
  }
  if (form.trigger_type === "TIME_STATE" && (!form.trigger_time_start || !form.trigger_time_end)) {
    emit("error", "请设置定时触发的开始和结束时间。");
    return;
  }
  if (!form.action_device || form.action_device === 0) {
    emit("error", "请选择执行设备。");
    return;
  }

  const payload: Partial<SceneRule> = {
    name: form.name.trim(),
    enabled: true,
    trigger_type: form.trigger_type,
    trigger_device: Number(form.trigger_device),
    trigger_field: form.trigger_field,
    trigger_value,
    trigger_time_start: form.trigger_type === "TIME_STATE" && form.trigger_time_start ? `${form.trigger_time_start}:00` : null,
    trigger_time_end: form.trigger_type === "TIME_STATE" && form.trigger_time_end ? `${form.trigger_time_end}:00` : null,
    trigger_state_device: form.trigger_type === "TIME_STATE" ? (form.trigger_state_device ? Number(form.trigger_state_device) : null) : null,
    trigger_state_value,
    action_device: Number(form.action_device),
    action_type: form.action_type,
    action_value,
    debounce_seconds: Number(form.debounce_seconds) || 60,
  };

  emit("submit", payload);
};
</script>

<style scoped>
.dialog-error {
  margin-right: auto;
  max-width: 70%;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
}

.time-state-block .time-state-hint {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: #f0f9ff;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
  color: #0c4a6e;
}
.field-hint-inline {
  display: block;
  font-size: 11px;
  color: #6b7280;
  margin-top: 2px;
}
</style>
