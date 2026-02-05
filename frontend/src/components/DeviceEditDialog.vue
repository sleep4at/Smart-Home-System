<template>
  <div class="dialog-backdrop" @click.self="onClose">
    <div class="dialog-panel">
      <div class="dialog-header">
        <div class="dialog-title">
          {{ device && device.id ? "编辑设备" : "添加设备" }}
        </div>
        <button class="btn btn-ghost" @click="onClose">✕</button>
      </div>
      <div class="dialog-body">
        <div>
          <div class="field-label">设备名称</div>
          <input
            v-model="form.name"
            class="field-input"
            placeholder="例如 客厅温湿度传感器"
          />
        </div>
        <div>
          <div class="field-label">设备类型</div>
          <select v-model="form.type" class="field-select">
            <option disabled value="">请选择类型</option>
            <option
              v-for="t in typeOptions"
              :key="t.value"
              :value="t.value"
            >
              {{ t.label }}
            </option>
          </select>
        </div>
        <div>
          <div class="field-label">位置 / 房间</div>
          <input
            v-model="form.location"
            class="field-input"
            placeholder="例如 客厅 / 卧室 / 书房"
          />
        </div>
      </div>
      <div class="dialog-footer">
        <button class="btn btn-ghost" @click="onClose">取消</button>
        <button class="btn btn-primary" @click="onSubmit">
          保存
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import type { Device, DeviceTypeOption } from "@/store/devices";

const props = defineProps<{
  device: Device | null;
  typeOptions: DeviceTypeOption[];
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: Partial<Device>): void;
}>();

const emptyForm = () => ({
  name: "",
  type: "" as any,
  location: ""
});

const form = reactive(emptyForm());

watch(
  () => props.device,
  (val) => {
    if (val) {
      form.name = val.name;
      form.type = val.type;
      form.location = val.location;
    } else {
      Object.assign(form, emptyForm());
    }
  },
  { immediate: true }
);

const onClose = () => emit("close");

const onSubmit = () => {
  emit("submit", {
    name: form.name,
    type: form.type,
    location: form.location
  });
};
</script>

