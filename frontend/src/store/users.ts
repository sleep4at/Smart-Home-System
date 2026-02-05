import { defineStore } from "pinia";
import api from "@/utils/http";

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  is_admin: boolean;
}

export const useUsersStore = defineStore("users", {
  state: () => ({
    list: [] as User[],
    loading: false,
  }),
  actions: {
    async fetchUsers() {
      this.loading = true;
      try {
        const res = await api.get<User[]>("/api/users/");
        this.list = res.data;
      } finally {
        this.loading = false;
      }
    },
    async createUser(payload: Partial<User> & { password?: string }) {
      const res = await api.post<User>("/api/users/", payload);
      this.list.push(res.data);
      return res.data;
    },
    async updateUser(id: number, payload: Partial<User> & { password?: string }) {
      const res = await api.patch<User>(`/api/users/${id}/`, payload);
      const idx = this.list.findIndex((u) => u.id === id);
      if (idx >= 0) this.list[idx] = res.data;
      return res.data;
    },
    async deleteUser(id: number) {
      await api.delete(`/api/users/${id}/`);
      this.list = this.list.filter((u) => u.id !== id);
    },
  },
});
