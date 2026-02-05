<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">用户列表 ({{ users.list.length }})</div>
      <button class="btn btn-primary" @click="openCreate">＋ 添加用户</button>
    </div>
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>角色</th>
            <th style="text-align: right;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users.list" :key="u.id">
            <td>{{ u.id }}</td>
            <td class="fw-500">{{ u.username }}</td>
            <td class="text-muted">{{ u.email || "—" }}</td>
            <td>
              <span
                class="device-tile-status"
                :class="u.is_active ? 'status-online' : 'status-offline'"
              >
                {{ u.is_active ? "激活" : "禁用" }}
              </span>
            </td>
            <td>
              <span class="badge-role" :class="{ user: !u.is_admin }">
                {{ u.is_admin ? "管理员" : "普通用户" }}
              </span>
            </td>
            <td style="text-align: right;">
              <button class="btn btn-ghost btn-sm" @click="openEdit(u)">编辑</button>
              <button
                v-if="u.id !== auth.user?.id"
                class="btn btn-ghost btn-sm text-danger"
                @click="confirmDelete(u)"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <UserEditDialog
      v-if="showDialog"
      :user="editingUser"
      @close="closeDialog"
      @submit="onSubmitUser"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useUsersStore, type User } from "@/store/users";
import { useAuthStore } from "@/store/auth";
import UserEditDialog from "@/components/UserEditDialog.vue";

const users = useUsersStore();
const auth = useAuthStore();
const showDialog = ref(false);
const editingUser = ref<User | null>(null);

onMounted(() => users.fetchUsers());

const openCreate = () => {
  editingUser.value = null;
  showDialog.value = true;
};
const openEdit = (u: User) => {
  editingUser.value = u;
  showDialog.value = true;
};
const closeDialog = () => (showDialog.value = false);
const onSubmitUser = async (payload: Partial<User> & { password?: string }) => {
  if (editingUser.value?.id) {
    await users.updateUser(editingUser.value.id, payload);
  } else {
    await users.createUser(payload);
  }
  showDialog.value = false;
};
const confirmDelete = async (u: User) => {
  if (confirm(`确定删除用户 "${u.username}" 吗？`)) {
    await users.deleteUser(u.id);
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
.text-muted {
  color: #6b7280;
}
.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}
.text-danger {
  color: #dc2626;
}
</style>
