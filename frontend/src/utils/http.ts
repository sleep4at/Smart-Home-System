import axios, { type InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth";

const api = axios.create({
  baseURL: ""
});

api.interceptors.request.use((config) => {
  const auth = useAuthStore();
  if (auth.accessToken) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${auth.accessToken}`;
  }
  return config;
});

/** 用于刷新 token 的请求，不携带过期 access，避免循环 401 */
let refreshPromise: Promise<string> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    const auth = useAuthStore();

    // 若是刷新 token 的请求本身失败，直接登出并跳转登录
    if (originalRequest.url?.includes("/api/auth/token/refresh/")) {
      auth.logout();
      window.location.href = "/login";
      return Promise.reject(error);
    }

    // 已重试过仍 401，不再刷新，登出并跳转
    if (originalRequest._retry) {
      auth.logout();
      window.location.href = "/login";
      return Promise.reject(error);
    }

    if (!auth.refreshToken) {
      auth.logout();
      window.location.href = "/login";
      return Promise.reject(error);
    }

    if (!refreshPromise) {
      refreshPromise = axios
        .post<{ access: string }>(`${api.defaults.baseURL || ""}/api/auth/token/refresh/`, {
          refresh: auth.refreshToken
        })
        .then((res) => {
          const access = res.data.access;
          auth.setAccessToken(access);
          return access;
        })
        .finally(() => {
          refreshPromise = null;
        });
    }

    try {
      const newAccess = await refreshPromise;
      originalRequest._retry = true;
      originalRequest.headers.Authorization = `Bearer ${newAccess}`;
      return api.request(originalRequest);
    } catch (e) {
      auth.logout();
      window.location.href = "/login";
      return Promise.reject(e);
    }
  }
);

export default api;

