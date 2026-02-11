import { defineStore } from "pinia";
import api from "@/utils/http";

export const useMqttStatusStore = defineStore("mqttStatus", {
  state: () => ({
    connected: false,
    loading: false,
    lastChecked: null as number | null,
  }),
  actions: {
    setConnected(connected: boolean) {
      this.connected = connected;
      this.loading = false;
      this.lastChecked = Date.now();
    },
    async fetchStatus() {
      // 仅首次请求时置为 loading，避免轮询时界面在「检查中」与「已连接」间闪烁
      if (this.lastChecked === null) this.loading = true;
      try {
        const res = await api.get<{ connected: boolean; error?: string }>("/api/mqtt/status/");
        this.connected = res.data.connected === true;
        this.lastChecked = Date.now();
      } catch {
        this.connected = false;
        this.lastChecked = Date.now();
      } finally {
        this.loading = false;
      }
    },
  },
});
