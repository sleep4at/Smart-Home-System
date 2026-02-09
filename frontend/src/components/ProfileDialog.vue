<template>
  <div class="dialog-backdrop" @click.self="onClose">
    <div class="dialog-panel">
      <div class="dialog-header">
        <div class="dialog-title">个人信息</div>
        <button class="btn btn-ghost" @click="onClose">✕</button>
      </div>
      <div class="dialog-body">
        <div>
          <div class="field-label">用户名</div>
          <input
            :value="auth.user?.username"
            class="field-input"
            readonly
            disabled
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
          <div class="field-label">当前密码</div>
          <input
            v-model="form.currentPassword"
            class="field-input"
            type="password"
            placeholder="修改密码时请输入原密码"
            autocomplete="current-password"
          />
        </div>
        <div>
          <div class="field-label">新密码</div>
          <input
            v-model="form.newPassword"
            class="field-input"
            type="password"
            placeholder="请输入新密码"
            autocomplete="new-password"
          />
        </div>
        <div>
          <div class="field-label">确认新密码</div>
          <input
            v-model="form.confirmPassword"
            class="field-input"
            type="password"
            placeholder="再次输入新密码"
            autocomplete="new-password"
          />
        </div>
        <p v-if="errorMsg" class="profile-error">{{ errorMsg }}</p>
      </div>
      <div class="dialog-footer">
        <button class="btn btn-ghost" @click="onClose">取消</button>
        <button class="btn btn-primary" :disabled="isSubmitting" @click="onSubmit">
          {{ isSubmitting ? "保存中…" : "保存" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from "vue";
import api from "@/utils/http";
import { useAuthStore } from "@/store/auth";

const auth = useAuthStore();
const emit = defineEmits<{ (e: "close"): void }>();

const form = reactive({
  email: "",
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
});
const errorMsg = ref("");
const isSubmitting = ref(false);

watch(
  () => auth.user,
  (u) => {
    form.email = u?.email ?? "";
    form.currentPassword = "";
    form.newPassword = "";
    form.confirmPassword = "";
    errorMsg.value = "";
  },
  { immediate: true }
);

function onClose() {
  emit("close");
}

async function onSubmit() {
  errorMsg.value = "";
  const { email, currentPassword, newPassword, confirmPassword } = form;
  if (newPassword) {
    if (!currentPassword) {
      errorMsg.value = "修改密码前请输入当前密码";
      return;
    }
    if (newPassword !== confirmPassword) {
      errorMsg.value = "两次输入的新密码不一致";
      return;
    }
  }
  const hasChange = newPassword || email !== (auth.user?.email ?? "");
  if (!hasChange) {
    emit("close");
    return;
  }
  isSubmitting.value = true;
  try {
    const payload: { email?: string; current_password?: string; password?: string } = {};
    if (email !== (auth.user?.email ?? "")) payload.email = email;
    if (newPassword) {
      payload.current_password = currentPassword;
      payload.password = newPassword;
    }
    await api.patch("/api/auth/me/", payload);
    await auth.revalidate();
    emit("close");
  } catch (e: unknown) {
    const data = (e as { response?: { data?: Record<string, string[]> } })?.response?.data;
    if (data?.current_password?.length) {
      errorMsg.value = data.current_password[0];
    } else if (data?.password?.length) {
      errorMsg.value = data.password[0];
    } else if (data?.email?.length) {
      errorMsg.value = data.email[0];
    } else {
      errorMsg.value = "保存失败，请重试";
    }
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<style scoped>
.profile-error {
  font-size: 13px;
  color: #dc2626;
  margin: 4px 0 0;
}
</style>
