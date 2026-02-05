<template>
  <div
    style="
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at top, #e5edff 0, #f5f5f7 55%);
    "
  >
    <div
      style="
        width: 360px;
        max-width: 92vw;
        background: #ffffff;
        border-radius: 20px;
        padding: 22px 22px 18px;
        box-shadow: 0 22px 60px rgba(15, 23, 42, 0.18);
      "
    >
      <div style="margin-bottom: 16px;">
        <div style="font-size: 20px; font-weight: 600; margin-bottom: 4px;">
          智能家居控制台
        </div>
        <div style="font-size: 13px; color: #6b7280;">
          使用管理员或普通账号登录
        </div>
      </div>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div>
          <div class="field-label">用户名</div>
          <input
            v-model="username"
            class="field-input"
            placeholder="请输入用户名"
          />
        </div>
        <div>
          <div class="field-label">密码</div>
          <input
            v-model="password"
            class="field-input"
            type="password"
            placeholder="请输入密码"
          />
        </div>
      </div>
      <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
        <button class="btn btn-primary" style="width: 100%;" @click="onLogin">
          登录
        </button>
      </div>
      <div v-if="error" style="margin-top: 10px; color: #dc2626; font-size: 13px;">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/store/auth";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const username = ref("");
const password = ref("");
const error = ref("");

const onLogin = async () => {
  error.value = "";
  try {
    await auth.login(username.value, password.value);
    const redirect = (route.query.redirect as string) || "/";
    router.push(redirect);
  } catch (e) {
    error.value = "登录失败，请检查用户名或密码。";
  }
};
</script>

