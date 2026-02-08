import { defineStore } from "pinia";
import api from "@/utils/http";

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
      const access = localStorage.getItem("accessToken");
      const refresh = localStorage.getItem("refreshToken");
      if (access) {
        this.accessToken = access;
        this.refreshToken = refresh;
        try {
          const res = await api.get<UserInfo>("/api/auth/me/");
          this.user = res.data;
        } catch {
          this.accessToken = null;
          this.refreshToken = null;
          this.user = null;
          localStorage.removeItem("accessToken");
          localStorage.removeItem("refreshToken");
        }
      }
      this.initialized = true;
    },
    async login(username: string, password: string) {
      const res = await api.post("/api/auth/token/", { username, password });
      this.accessToken = res.data.access;
      this.refreshToken = res.data.refresh;
      localStorage.setItem("accessToken", this.accessToken!);
      localStorage.setItem("refreshToken", this.refreshToken!);
      const me = await api.get<UserInfo>("/api/auth/me/");
      this.user = me.data;
    },
    logout() {
      this.accessToken = null;
      this.refreshToken = null;
      this.user = null;
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
    },
    /** 仅更新 access token（用于 token 刷新后），由 http 拦截器调用 */
    setAccessToken(access: string) {
      this.accessToken = access;
      localStorage.setItem("accessToken", access);
    }
  }
});

