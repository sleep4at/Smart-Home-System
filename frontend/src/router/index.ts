import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";
import { useAuthStore } from "@/store/auth";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/LoginView.vue"),
  },
  {
    path: "/",
    component: () => import("@/layouts/MainLayout.vue"),
    children: [
      {
        path: "",
        name: "home",
        component: () => import("@/views/HomeView.vue"),
        meta: { title: "主页" },
      },
      {
        path: "history",
        name: "history",
        component: () => import("@/views/HistoryView.vue"),
        meta: { title: "历史信息" },
      },
      {
        path: "debug",
        name: "debug",
        component: () => import("@/views/DebugView.vue"),
        meta: { title: "调试信息" },
      },
      {
        path: "scenes",
        name: "scenes",
        component: () => import("@/views/ScenesView.vue"),
        meta: { title: "场景模式" },
      },
    ],
  },
  {
    path: "/admin",
    component: () => import("@/layouts/AdminLayout.vue"),
    meta: { requiresAdmin: true },
    redirect: { name: "admin-users" },
    children: [
      {
        path: "users",
        name: "admin-users",
        component: () => import("@/views/admin/UsersView.vue"),
        meta: { title: "用户管理" },
      },
      {
        path: "devices",
        name: "admin-devices",
        component: () => import("@/views/admin/DevicesView.vue"),
        meta: { title: "设备管理" },
      },
      {
        path: "alerts",
        name: "admin-alerts",
        component: () => import("@/views/admin/AlertsView.vue"),
        meta: { title: "安全告警" },
      },
      {
        path: "debug-tools",
        name: "admin-debug-tools",
        component: () => import("@/views/admin/DebugToolsView.vue"),
        meta: { title: "调试工具" },
      },
      {
        path: "console",
        name: "admin-console",
        component: () => import("@/views/admin/ConsoleView.vue"),
        meta: { title: "控制台输出" },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore();
  if (!auth.initialized) {
    await auth.bootstrap();
  }
  if (to.name === "login") {
    if (auth.isAuthenticated) next({ name: "home" });
    else next();
    return;
  }
  if (!auth.isAuthenticated) {
    next({ name: "login", query: { redirect: to.fullPath } });
    return;
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    next({ name: "home" });
    return;
  }
  next();
});

export default router;
