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
            <option value="TIME_STATE">时间+状态组合</option>
          </select>
        </div>

        <div>
          <div class="field-label">触发设备</div>
          <select v-model="form.trigger_device" class="field-select">
            <option disabled :value="0">请选择设备</option>
            <option
              v-for="d in sensorDevices"
              :key="d.id"
              :value="d.id"
            >
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

        <div v-if="form.trigger_type === 'TIME_STATE'">
          <div style="display: flex; gap: 12px;">
            <div style="flex: 1;">
              <div class="field-label">开始时间</div>
              <input
                v-model="form.trigger_time_start"
                type="time"
                class="field-input"
              />
            </div>
            <div style="flex: 1;">
              <div class="field-label">结束时间</div>
              <input
                v-model="form.trigger_time_end"
                type="time"
                class="field-input"
              />
            </div>
          </div>
          <div style="margin-top: 12px;">
            <div class="field-label">状态设备（可选）</div>
            <select v-model="form.trigger_state_device" class="field-select">
              <option :value="null">不限制</option>
              <option
                v-for="d in switchDevices"
                :key="d.id"
                :value="d.id"
              >
                {{ d.name }} ({{ d.type_display }})
              </option>
            </select>
          </div>
          <div v-if="form.trigger_state_device" style="margin-top: 12px;">
            <div class="field-label">状态值</div>
            <select v-model="form.trigger_state_on" class="field-select">
              <option :value="true">开启</option>
              <option :value="false">关闭</option>
            </select>
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
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: Partial<SceneRule>): void;
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
      form.trigger_state_on = val.trigger_state_value?.on ?? true;
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

const onTriggerTypeChange = () => {
  // 切换触发类型时重置相关字段
  if (form.trigger_type !== "TIME_STATE") {
    form.trigger_time_start = "";
    form.trigger_time_end = "";
    form.trigger_state_device = null;
  }
};

const onActionTypeChange = () => {
  // 切换动作类型时重置相关字段
  form.action_temp = 26;
  form.action_speed = 1;
};

const onClose = () => emit("close");

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

  // 构建 trigger_state_value
  let trigger_state_value: Record<string, any> | null = null;
  if (form.trigger_type === "TIME_STATE" && form.trigger_state_device) {
    trigger_state_value = { on: form.trigger_state_on };
  }

  const payload: Partial<SceneRule> = {
    name: form.name,
    enabled: true,
    trigger_type: form.trigger_type,
    trigger_device: form.trigger_device,
    trigger_field: form.trigger_field,
    trigger_value,
    trigger_time_start: form.trigger_type === "TIME_STATE" && form.trigger_time_start ? `${form.trigger_time_start}:00` : null,
    trigger_time_end: form.trigger_type === "TIME_STATE" && form.trigger_time_end ? `${form.trigger_time_end}:00` : null,
    trigger_state_device: form.trigger_type === "TIME_STATE" ? form.trigger_state_device : null,
    trigger_state_value,
    action_device: form.action_device,
    action_type: form.action_type,
    action_value,
    debounce_seconds: form.debounce_seconds,
  };

  emit("submit", payload);
};
</script>
