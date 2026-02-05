<template>
  <div class="dialog-backdrop" @click.self="onClose">
    <div class="dialog-panel">
      <div class="dialog-header">
        <div class="dialog-title">{{ user?.id ? "编辑用户" : "添加用户" }}</div>
        <button class="btn btn-ghost" @click="onClose">✕</button>
      </div>
      <div class="dialog-body">
        <div>
          <div class="field-label">用户名</div>
          <input
            v-model="form.username"
            class="field-input"
            placeholder="请输入用户名"
            :disabled="!!user?.id"
          />
        </div>
        <div>
          <div class="field-label">邮箱</div>
          <input
            v-model="form.email"
            class="field-input"
            type="email"
            placeholder="可选"
          />
        </div>
        <div>
          <div class="field-label">密码</div>
          <input
            v-model="form.password"
            class="field-input"
            type="password"
            :placeholder="user?.id ? '留空则不修改' : '请输入密码'"
          />
        </div>
        <div>
          <div class="field-label">状态</div>
          <select v-model="form.is_active" class="field-select">
            <option :value="true">激活</option>
            <option :value="false">禁用</option>
          </select>
        </div>
        <div>
          <div class="field-label">角色</div>
          <select v-model="form.is_staff" class="field-select">
            <option :value="false">普通用户</option>
            <option :value="true">管理员</option>
          </select>
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
import { reactive, watch } from "vue";
import type { User } from "@/store/users";

const props = defineProps<{ user: User | null }>();
const emit = defineEmits<{
  (e: "close"): void;
  (e: "submit", payload: Partial<User> & { password?: string }): void;
}>();

const emptyForm = () => ({
  username: "",
  email: "",
  password: "",
  is_active: true,
  is_staff: false,
});

const form = reactive(emptyForm());

watch(
  () => props.user,
  (val) => {
    if (val) {
      form.username = val.username;
      form.email = val.email || "";
      form.password = "";
      form.is_active = val.is_active;
      form.is_staff = !!val.is_staff || !!val.is_superuser;
    } else {
      Object.assign(form, emptyForm());
    }
  },
  { immediate: true }
);

const onClose = () => emit("close");
const onSubmit = () => {
  const payload: Partial<User> & { password?: string } = {
    username: form.username,
    email: form.email,
    is_active: form.is_active,
    is_staff: form.is_staff,
  };
  if (form.password) payload.password = form.password;
  emit("submit", payload);
};
</script>
