<template>
  <div class="dialog-backdrop" @click.self="onClose">
    <div class="dialog-panel" style="max-width: 560px; max-height: 90vh; overflow-y: auto;">
      <div class="dialog-header">
        <div class="dialog-title">
          {{ rule?.id ? "编辑邮件告警规则" : "新建邮件告警规则" }}
        </div>
        <button class="btn btn-ghost" @click="onClose">✕</button>
      </div>
      <div class="dialog-body">
        <div>
          <div class="field-label">规则名称</div>
          <input
            v-model="form.name"
            class="field-input"
            placeholder="例如：客厅温度过高告警"
          />
        </div>

        <div>
          <div class="field-label">预设类型</div>
          <select v-model="form.preset" class="field-select" @change="applyPreset">
            <option
              v-for="opt in PRESET_OPTIONS"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div>
          <div class="field-label">触发设备</div>
          <select v-model="form.trigger_device" class="field-select">
            <option disabled :value="0">
              {{ form.preset === "smoke" ? "请选择烟雾传感器" : "请选择设备" }}
            </option>
            <option
              v-for="d in triggerDeviceOptions"
              :key="d.id"
              :value="d.id"
            >
              {{ d.name }} ({{ d.type_display }})
            </option>
          </select>
        </div>

        <template v-if="form.preset !== 'smoke'">
          <div>
            <div class="field-label">触发字段</div>
            <select v-model="form.trigger_field" class="field-select">
              <option value="temp">温度 (temp)</option>
              <option value="humi">湿度 (humi)</option>
              <option value="light">光照 (light)</option>
              <option value="pressure">气压 (pressure)</option>
            </select>
          </div>
          <div>
            <div class="field-label">触发条件</div>
            <div style="display: flex; gap: 12px; align-items: center;">
              <select v-model="form.trigger_above" class="field-select" style="width: 120px;">
                <option :value="true">高于阈值</option>
                <option :value="false">低于阈值</option>
              </select>
              <input
                v-model.number="form.trigger_value"
                type="number"
                step="0.1"
                class="field-input"
                placeholder="阈值"
                style="flex: 1;"
              />
            </div>
          </div>
        </template>
        <div v-else>
          <div class="field-label">触发条件</div>
          <div class="field-static">触发</div>
        </div>

        <div>
          <div class="field-label">收件邮箱（多个用逗号或换行分隔）</div>
          <textarea
            v-model="form.recipientsText"
            class="field-input"
            rows="3"
            placeholder="admin@example.com, user@example.com"
          />
        </div>

        <div>
          <div class="field-label">抄送（可选，逗号或换行分隔）</div>
          <textarea
            v-model="form.ccText"
            class="field-input"
            rows="2"
            placeholder="可选"
          />
        </div>

        <div>
          <div class="field-label">邮件主题（可用 {preset} {device_name} {value} {time}）</div>
          <input
            v-model="form.subject_template"
            class="field-input"
            placeholder="[智能家居告警] {preset} - {device_name}"
          />
        </div>

        <div>
          <div class="field-label">邮件正文模板（可用 {preset} {device_name} {value} {time}）</div>
          <textarea
            v-model="form.body_template"
            class="field-input"
            rows="4"
            placeholder="触发设备：{device_name}&#10;触发条件：{preset}&#10;当前值：{value}&#10;时间：{time}"
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
import type { EmailAlertRule } from "@/store/emailAlerts";
import { PRESET_OPTIONS } from "@/store/emailAlerts";

const props = defineProps<{
  rule: EmailAlertRule | null;
  devices: Device[];
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: Partial<EmailAlertRule>): void;
}>();

const sensorDevices = computed(() =>
  props.devices.filter((d) =>
    ["TEMP_HUMI", "LIGHT", "PRESSURE", "SMOKE"].includes(d.type)
  )
);

/** 烟雾告警仅能选烟雾传感器，其他预设可选所有传感器 */
const triggerDeviceOptions = computed(() => {
  if (form.preset === "smoke") {
    return props.devices.filter((d) => d.type === "SMOKE");
  }
  return sensorDevices.value;
});

function parseEmails(text: string): string[] {
  return text
    .split(/[\n,;]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

const PRESET_DEFAULTS: Record<string, { subject: string; body: string }> = {
  temp_high: {
    subject: "[智能家居告警] 温度过高 - {device_name}",
    body: "触发设备：{device_name}\n触发条件：温度过高\n当前温度：{value}°C\n时间：{time}\n请及时处理。",
  },
  temp_low: {
    subject: "[智能家居告警] 温度过低 - {device_name}",
    body: "触发设备：{device_name}\n触发条件：温度过低\n当前温度：{value}°C\n时间：{time}\n请及时处理。",
  },
  humi_high: {
    subject: "[智能家居告警] 湿度过高 - {device_name}",
    body: "触发设备：{device_name}\n触发条件：湿度过高\n当前湿度：{value}%RH\n时间：{time}\n请及时处理。",
  },
  humi_low: {
    subject: "[智能家居告警] 湿度过低 - {device_name}",
    body: "触发设备：{device_name}\n触发条件：湿度过低\n当前湿度：{value}%RH\n时间：{time}\n请及时处理。",
  },
  smoke: {
    subject: "[智能家居告警] 烟雾告警 - {device_name}",
    body: "危险！触发设备：{device_name}\n烟雾/可燃气体检测异常。\n时间：{time}\n请立即确认并处理。",
  },
  custom: {
    subject: "[智能家居告警] {preset} - {device_name}",
    body: "触发设备：{device_name}\n触发条件：{preset}\n当前值：{value}\n时间：{time}",
  },
};

const emptyForm = () => ({
  name: "",
  preset: "temp_high" as string,
  trigger_device: 0,
  trigger_field: "temp",
  trigger_value: null as number | null,
  trigger_above: true,
  recipientsText: "",
  ccText: "",
  subject_template: PRESET_DEFAULTS.temp_high.subject,
  body_template: PRESET_DEFAULTS.temp_high.body,
});

const form = reactive(emptyForm());

function applyPreset() {
  const def = PRESET_DEFAULTS[form.preset] || PRESET_DEFAULTS.custom;
  form.subject_template = def.subject;
  form.body_template = def.body;
  if (form.preset === "temp_high" || form.preset === "temp_low") {
    form.trigger_field = "temp";
    form.trigger_above = form.preset === "temp_high";
  } else if (form.preset === "humi_high" || form.preset === "humi_low") {
    form.trigger_field = "humi";
    form.trigger_above = form.preset === "humi_high";
  } else if (form.preset === "smoke") {
    form.trigger_field = "smoke";
    form.trigger_value = 1;
    form.trigger_above = true;
    const smokeDevices = props.devices.filter((d) => d.type === "SMOKE");
    if (!smokeDevices.some((d) => d.id === form.trigger_device)) {
      form.trigger_device = smokeDevices[0]?.id ?? 0;
    }
  }
}

watch(
  () => props.rule,
  (val) => {
    if (val) {
      form.name = val.name;
      form.preset = val.preset;
      form.trigger_device = val.trigger_device;
      form.trigger_field = val.trigger_field;
      form.trigger_value = val.trigger_value;
      form.trigger_above = val.trigger_above;
      form.recipientsText = (val.recipients || []).join(", ");
      form.ccText = (val.cc_list || []).join(", ");
      form.subject_template = val.subject_template;
      form.body_template = val.body_template;
    } else {
      Object.assign(form, emptyForm());
      applyPreset();
    }
  },
  { immediate: true }
);

const onClose = () => emit("close");

const onSubmit = () => {
  const payload: Partial<EmailAlertRule> = {
    name: form.name,
    enabled: true,
    preset: form.preset,
    trigger_device: form.trigger_device,
    trigger_field: form.preset === "smoke" ? "smoke" : form.trigger_field,
    trigger_value: form.preset === "smoke" ? 1 : form.trigger_value,
    trigger_above: form.preset === "smoke" ? true : form.trigger_above,
    recipients: parseEmails(form.recipientsText),
    cc_list: parseEmails(form.ccText),
    subject_template: form.subject_template,
    body_template: form.body_template,
  };
  emit("submit", payload);
};
</script>

<style scoped>
.field-static {
  padding: 8px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 14px;
  color: #374151;
}
</style>
