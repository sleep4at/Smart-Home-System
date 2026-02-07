import { defineStore } from "pinia";
import api from "@/utils/http";

export interface EmailAlertRule {
  id: number;
  name: string;
  enabled: boolean;
  preset: string;
  trigger_device: number;
  trigger_device_name: string;
  trigger_field: string;
  trigger_value: number | null;
  trigger_above: boolean;
  recipients: string[];
  cc_list: string[];
  subject_template: string;
  body_template: string;
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
}

const PRESET_OPTIONS = [
  { value: "temp_high", label: "温度过高" },
  { value: "temp_low", label: "温度过低" },
  { value: "humi_high", label: "湿度过高" },
  { value: "humi_low", label: "湿度过低" },
  { value: "smoke", label: "烟雾告警" },
  { value: "custom", label: "自定义" },
];

export { PRESET_OPTIONS };

export const useEmailAlertsStore = defineStore("emailAlerts", {
  state: () => ({
    list: [] as EmailAlertRule[],
    loading: false,
  }),
  actions: {
    async fetchRules() {
      this.loading = true;
      try {
        const res = await api.get<EmailAlertRule[]>("/api/alerts/email-rules/");
        this.list = res.data;
      } finally {
        this.loading = false;
      }
    },
    async createRule(payload: Partial<EmailAlertRule>) {
      const res = await api.post<EmailAlertRule>("/api/alerts/email-rules/", payload);
      this.list.push(res.data);
      return res.data;
    },
    async updateRule(id: number, payload: Partial<EmailAlertRule>) {
      const res = await api.patch<EmailAlertRule>(`/api/alerts/email-rules/${id}/`, payload);
      const idx = this.list.findIndex((r) => r.id === id);
      if (idx >= 0) this.list[idx] = res.data;
      return res.data;
    },
    async deleteRule(id: number) {
      await api.delete(`/api/alerts/email-rules/${id}/`);
      this.list = this.list.filter((r) => r.id !== id);
    },
    async toggleEnabled(id: number) {
      const res = await api.post<{ enabled: boolean }>(
        `/api/alerts/email-rules/${id}/toggle_enabled/`
      );
      const idx = this.list.findIndex((r) => r.id === id);
      if (idx >= 0) this.list[idx].enabled = res.data.enabled;
    },
  },
});
