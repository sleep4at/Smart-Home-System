import { defineStore } from "pinia";
import api from "@/utils/http";

export interface SceneRule {
  id: number;
  name: string;
  enabled: boolean;
  owner: number;
  owner_username: string;
  trigger_type: "THRESHOLD_ABOVE" | "THRESHOLD_BELOW" | "RANGE_OUT" | "TIME_STATE";
  trigger_device: number;
  trigger_device_detail?: any;
  trigger_field: string;
  trigger_value: number | { min: number; max: number };
  trigger_time_start: string | null;
  trigger_time_end: string | null;
  trigger_state_device: number | null;
  trigger_state_device_detail?: any;
  trigger_state_value: Record<string, any> | null;
  action_device: number;
  action_device_detail?: any;
  action_type: "TOGGLE" | "SET_TEMP" | "SET_FAN_SPEED" | "TURN_ON" | "TURN_OFF";
  action_value: number | { temp?: number; speed?: number } | null;
  debounce_seconds: number;
  created_at: string;
  updated_at: string;
  last_triggered_at: string | null;
}

interface ScenesState {
  list: SceneRule[];
  loading: boolean;
}

export const useScenesStore = defineStore("scenes", {
  state: (): ScenesState => ({
    list: [],
    loading: false,
  }),
  actions: {
    async fetchScenes() {
      this.loading = true;
      try {
        const res = await api.get<SceneRule[]>("/api/scenes/");
        this.list = res.data;
      } finally {
        this.loading = false;
      }
    },
    async createScene(payload: Partial<SceneRule>) {
      const res = await api.post<SceneRule>("/api/scenes/", payload);
      this.list.push(res.data);
      return res.data;
    },
    async updateScene(id: number, payload: Partial<SceneRule>) {
      const res = await api.patch<SceneRule>(`/api/scenes/${id}/`, payload);
      const idx = this.list.findIndex((r) => r.id === id);
      if (idx >= 0) this.list[idx] = res.data;
      return res.data;
    },
    async deleteScene(id: number) {
      await api.delete(`/api/scenes/${id}/`);
      this.list = this.list.filter((r) => r.id !== id);
    },
    async toggleEnabled(id: number) {
      const res = await api.post<{ enabled: boolean }>(
        `/api/scenes/${id}/toggle_enabled/`
      );
      const idx = this.list.findIndex((r) => r.id === id);
      if (idx >= 0) this.list[idx].enabled = res.data.enabled;
    },
  },
});
