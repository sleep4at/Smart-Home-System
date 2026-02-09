import { defineStore } from "pinia";
import api from "@/utils/http";

const AUTH_STORAGE_KEY_ACCESS = "accessToken";
const AUTH_STORAGE_KEY_REFRESH = "refreshToken";
/** 使用 sessionStorage：关闭浏览器标签/窗口后会话失效，下次打开会要求重新登录 */
const authStorage = sessionStorage;

export interface UserInfo {
  id: number;
  username: string;
  email: string;
  is_admin: boolean;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserInfo | null;
  initialized: boolean;
}

/** 请求 /api/auth/me/ 的超时时间（毫秒），避免后端未启动时长时间挂起 */
const BOOTSTRAP_ME_TIMEOUT = 8000;

export const useAuthStore = defineStore("auth", {
  state: (): AuthState => ({
    accessToken: null,
    refreshToken: null,
    user: null,
    initialized: false
  }),
  getters: {
    isAuthenticated: (state) => !!state.accessToken && !!state.user,
    isAdmin: (state) => !!state.user?.is_admin
  },
  actions: {
    async bootstrap() {
      const access = authStorage.getItem(AUTH_STORAGE_KEY_ACCESS);
      const refresh = authStorage.getItem(AUTH_STORAGE_KEY_REFRESH);
      if (access) {
        this.accessToken = access;
        this.refreshToken = refresh;
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), BOOTSTRAP_ME_TIMEOUT);
          const res = await api.get<UserInfo>("/api/auth/me/", {
            signal: controller.signal
          });
          clearTimeout(timeoutId);
          this.user = res.data;
        } catch {
          this.accessToken = null;
          this.refreshToken = null;
          this.user = null;
          authStorage.removeItem(AUTH_STORAGE_KEY_ACCESS);
          authStorage.removeItem(AUTH_STORAGE_KEY_REFRESH);
        }
      }
      this.initialized = true;
    },
    async login(username: string, password: string) {
      const res = await api.post("/api/auth/token/", { username, password });
      this.accessToken = res.data.access;
      this.refreshToken = res.data.refresh;
      authStorage.setItem(AUTH_STORAGE_KEY_ACCESS, this.accessToken!);
      authStorage.setItem(AUTH_STORAGE_KEY_REFRESH, this.refreshToken!);
      const me = await api.get<UserInfo>("/api/auth/me/");
      this.user = me.data;
    },
    logout() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      authStorage.removeItem(AUTH_STORAGE_KEY_ACCESS);
      authStorage.removeItem(AUTH_STORAGE_KEY_REFRESH);
    },
    /** 仅更新 access token（用于 token 刷新后），由 http 拦截器调用 */
    setAccessToken(access: string) {
      this.accessToken = access;
      authStorage.setItem(AUTH_STORAGE_KEY_ACCESS, access);
    }
  }
});

