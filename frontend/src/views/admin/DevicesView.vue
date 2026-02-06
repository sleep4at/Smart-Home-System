<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">设备管理（共 {{ devices.list.length }} 个）</div>
      <button class="btn btn-primary" @click="openCreate">＋ 添加设备</button>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>类型</th>
            <th>位置</th>
            <th>状态</th>
            <th>可见性</th>
            <th>所属用户</th>
            <th style="text-align: right;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in devices.list" :key="d.id">
            <td>{{ d.id }}</td>
            <td class="fw-500">{{ d.name || "未命名设备" }}</td>
            <td>{{ d.type_display }}</td>
            <td>{{ d.location || "—" }}</td>
            <td>
              <span
                class="device-tile-status"
                :class="d.is_online ? 'status-online' : 'status-offline'"
              >
                {{ d.is_online ? "在线" : "离线" }}
              </span>
            </td>
            <td>
              <span class="badge-role" :class="d.is_public ? 'public' : 'private'">
                {{ d.is_public ? "公共设备" : "私人设备" }}
              </span>
            </td>
            <td>
              {{ ownerName(d.owner) }}
            </td>
            <td style="text-align: right;">
              <button class="btn btn-ghost btn-sm" @click="openEdit(d)">编辑</button>
              <button class="btn btn-ghost btn-sm text-danger" @click="confirmDelete(d)">
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!devices.list.length">
            <td colspan="8" style="text-align: center; padding: 24px;">暂无设备</td>
          </tr>
        </tbody>
      </table>
    </div>
    <DeviceEditDialog
      v-if="showDialog"
      :device="editingDevice"
      :type-options="devices.typeOptions"
      :users="users.list"
      :show-owner-field="true"
      @close="closeDialog"
      @submit="onSubmitDevice"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useDevicesStore, type Device } from "@/store/devices";
import { useUsersStore } from "@/store/users";
import DeviceEditDialog from "@/components/DeviceEditDialog.vue";

const devices = useDevicesStore();
const users = useUsersStore();

const showDialog = ref(false);
const editingDevice = ref<Device | null>(null);

onMounted(async () => {
  await Promise.all([devices.fetchDevices(), devices.fetchTypes(), users.fetchUsers()]);
});

const ownerName = (ownerId: number | null) => {
  if (!ownerId) return "未指定";
  const u = users.list.find((x) => x.id === ownerId);
  return u ? u.username : `用户 #${ownerId}`;
};

const openCreate = () => {
  editingDevice.value = null;
  showDialog.value = true;
};
const openEdit = (d: Device) => {
  editingDevice.value = d;
  showDialog.value = true;
};
const closeDialog = () => (showDialog.value = false);

const onSubmitDevice = async (payload: Partial<Device>) => {
  if (editingDevice.value?.id) {
    await devices.updateDevice(editingDevice.value.id, payload);
  } else {
    await devices.createDevice(payload);
  }
  showDialog.value = false;
};

const confirmDelete = async (d: Device) => {
  if (confirm(`确定删除设备 "${d.name || "未命名设备"}"(ID: ${d.id}) 吗？`)) {
    await devices.deleteDevice(d.id);
  }
};
</script>

<style scoped>
.table-wrap {
  background: #fff;
  border-radius: var(--radius-large);
  padding: 16px;
  box-shadow: var(--shadow-soft);
  overflow-x: auto;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}
.data-table td {
  padding: 12px;
  font-size: 14px;
  border-bottom: 1px solid #f3f4f6;
}
.fw-500 {
  font-weight: 500;
}
.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}
.text-danger {
  color: #dc2626;
}
.badge-role {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  background-color: #e5e7eb;
  color: #374151;
}
.badge-role.public {
  background-color: #dcfce7;
  color: #166534;
}
.badge-role.private {
  background-color: #fee2e2;
  color: #b91c1c;
}
</style>
