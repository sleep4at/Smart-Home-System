<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">已添加设备 {{ devices.list.length }} 个</div>
      <button v-if="auth.isAdmin" class="btn btn-primary" @click="openCreate">
        ＋ 添加设备
      </button>
    </div>
    <div class="tile-grid">
      <button
        v-if="auth.isAdmin"
        class="device-tile add-tile"
        @click="openCreate"
      >
        <div class="add-tile-icon">＋</div>
        <div class="add-tile-label">添加新设备</div>
      </button>
      <DeviceTile
        v-for="d in devices.list"
        :key="d.id"
        :device="d"
        @toggle="onToggle"
        @edit="openEdit"
      />
    </div>
    <DeviceEditDialog
      v-if="showDialog"
      :device="editingDevice"
      :type-options="devices.typeOptions"
      @close="closeDialog"
      @submit="onSubmitDevice"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { useDevicesStore } from "@/store/devices";
import { useAuthStore } from "@/store/auth";
import DeviceTile from "@/components/DeviceTile.vue";
import DeviceEditDialog from "@/components/DeviceEditDialog.vue";
import type { Device } from "@/store/devices";

const devices = useDevicesStore();
const auth = useAuthStore();
const showDialog = ref(false);
const editingDevice = ref<Device | null>(null);

let refreshTimer: ReturnType<typeof setInterval> | null = null;
onMounted(async () => {
  await devices.fetchDevices();
  if (auth.isAdmin) await devices.fetchTypes();
  refreshTimer = setInterval(() => devices.fetchDevices(), 5000);
});
onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});

const openCreate = () => {
  editingDevice.value = null;
  showDialog.value = true;
};
const openEdit = (device: Device) => {
  if (!auth.isAdmin) return;
  editingDevice.value = device;
  showDialog.value = true;
};
const closeDialog = () => (showDialog.value = false);
const onSubmitDevice = async (payload: Partial<Device>) => {
  if (!auth.isAdmin) return;
  if (editingDevice.value?.id) {
    await devices.updateDevice(editingDevice.value.id, payload);
  } else {
    await devices.createDevice(payload);
  }
  showDialog.value = false;
};
const onToggle = async (device: Device) => {
  await devices.toggleDevice(device.id);
};
</script>

<style scoped>
.add-tile {
  border: 1px dashed #d1d5db;
  box-shadow: none;
  justify-content: center;
  align-items: center;
}
.add-tile-icon {
  font-size: 34px;
  color: #9ca3af;
  margin-bottom: 4px;
}
.add-tile-label {
  font-size: 13px;
  color: #6b7280;
}
</style>
