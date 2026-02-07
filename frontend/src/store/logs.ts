import { defineStore } from "pinia";
import api from "@/utils/http";

export interface SystemLog {
  id: number;
  level: "INFO" | "WARN" | "ERROR";
  source: string;
  message: string;
  data: unknown;
  user: number | null;
  created_at: string;
}

export const useLogsStore = defineStore("logs", {
  state: () => ({
    list: [] as SystemLog[],
    loading: false,
  }),
  actions: {
    async fetchLogs(params?: { limit?: number; source?: string; level?: string }) {
      this.loading = true;
      try {
        const res = await api.get<SystemLog[]>("/api/logs/system/", { params });
        this.list = res.data;
      } finally {
        this.loading = false;
      }
    },
  },
});
