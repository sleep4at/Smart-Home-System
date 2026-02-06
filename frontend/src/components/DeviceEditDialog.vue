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
          <div class="field-label">设备 ID</div>
          <input
            :value="form.id || '自动生成'"
            class="field-input"
            style="background-color: #f3f4f6; cursor: not-allowed;"
            disabled
          />
        </div>
        
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
        <div>
          <div class="field-label">可见性</div>
          <select v-model="form.is_public" class="field-select">
            <option :value="true">公共设备（所有用户可见）</option>
            <option :value="false">私人设备（仅所属用户 + 管理员）</option>
          </select>
        </div>
        <div v-if="props.showOwnerField">
          <div class="field-label">所属用户</div>
          <select
            v-model="form.owner"
            class="field-select"
            :disabled="form.is_public || !(props.users && props.users.length)"
          >
            <option :value="null">未指定（公共设备或仅管理员操作）</option>
            <option
              v-for="u in props.users || []"
              :key="u.id"
              :value="u.id"
            >
              {{ u.username }} <span v-if="u.is_admin">（管理员）</span>
            </option>
          </select>
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
import type { User } from "@/store/users";

const props = defineProps<{
  device: Device | null;
  typeOptions: DeviceTypeOption[];
  users?: User[];
  showOwnerField?: boolean; // 是否显示"所属用户"字段（管理员设备管理页面显示，主页不显示）
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: Partial<Device>): void;
}>();

// 在表单对象中增加 id 字段
const emptyForm = () => ({
  id: undefined as number | undefined,
  name: "",
  type: "" as any,
  location: "",
  is_public: false,
  owner: null as number | null,
});

const form = reactive(emptyForm());

// 当切换为公共设备时，自动清空 owner，避免产生矛盾配置
watch(
  () => form.is_public,
  (val) => {
    if (val) {
      form.owner = null;
    }
  }
);

watch(
  () => props.device,
  (val) => {
    if (val) {
      // 同步 ID 数据
      form.id = val.id;
      form.name = val.name;
      form.type = val.type;
      form.location = val.location;
      form.is_public = !!val.is_public;
      form.owner = val.owner ?? null;
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
    location: form.location,
    is_public: form.is_public,
    owner: form.owner,
  });
};
</script>


