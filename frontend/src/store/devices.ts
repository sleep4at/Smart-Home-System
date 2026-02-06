import { defineStore } from "pinia";
import api from "@/utils/http";

export type DeviceTypeValue =
  | "TEMP_HUMI"
  | "LIGHT"
  | "PRESSURE"
  | "LAMP_SWITCH"
  | "AC_SWITCH"
  | "PIR"
  | "FAN_SWITCH"
  | "SMOKE";

export interface Device {
  id: number;
  name: string;
  type: DeviceTypeValue;
  type_display: string;
  location: string;
  is_online: boolean;
  is_public: boolean;
  current_state: Record<string, any>;
  owner: number | null;
}

export interface DeviceTypeOption {
  value: DeviceTypeValue;
  label: string;
}

interface DevicesState {
  list: Device[];
  typeOptions: DeviceTypeOption[];
  loading: boolean;
}

export const useDevicesStore = defineStore("devices", {
  state: (): DevicesState => ({
    list: [],
    typeOptions: [],
    loading: false
  }),
  getters: {
    switches: (state) =>
      state.list.filter((d) =>
        ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(d.type)
      ),
    sensors: (state) =>
      state.list.filter(
        (d) =>
          !["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(d.type)
      )
  },
  actions: {
    async fetchDevices() {
      this.loading = true;
      try {
        const res = await api.get<Device[]>("/api/devices/");
        this.list = res.data;
      } finally {
        this.loading = false;
      }
    },
    async fetchTypes() {
      if (this.typeOptions.length) return;
      const res = await api.get<DeviceTypeOption[]>("/api/device-types/");
      this.typeOptions = res.data;
    },
    async createDevice(payload: Partial<Device>) {
      const res = await api.post<Device>("/api/devices/", payload);
      this.list.push(res.data);
    },
    async updateDevice(id: number, payload: Partial<Device>) {
      const res = await api.patch<Device>(`/api/devices/${id}/`, payload);
      const idx = this.list.findIndex((d) => d.id === id);
      if (idx >= 0) this.list[idx] = res.data;
    },
    async deleteDevice(id: number) {
      await api.delete(`/api/devices/${id}/`);
      this.list = this.list.filter((d) => d.id !== id);
    },
    async toggleDevice(id: number, state?: boolean) {
      const res = await api.post<{ current_state: any }>(
        `/api/devices/${id}/toggle/`,
        state === undefined ? {} : { state }
      );
      const idx = this.list.findIndex((d) => d.id === id);
      if (idx >= 0) {
        this.list[idx].current_state = res.data.current_state;
      }
    },
    async setTemp(id: number, temp: number) {
      const res = await api.post<{ current_state: any }>(
        `/api/devices/${id}/set_temp/`,
        { temp }
      );
      const idx = this.list.findIndex((d) => d.id === id);
      if (idx >= 0) {
        this.list[idx].current_state = res.data.current_state;
      }
    },
    async setFanSpeed(id: number, speed: 1 | 2 | 3) {
      const res = await api.post<{ current_state: any }>(
        `/api/devices/${id}/set_fan_speed/`,
        { speed }
      );
      const idx = this.list.findIndex((d) => d.id === id);
      if (idx >= 0) {
        this.list[idx].current_state = res.data.current_state;
      }
    }
  }
});

