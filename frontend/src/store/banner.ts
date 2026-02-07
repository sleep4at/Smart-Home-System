import { defineStore } from "pinia";

export type BannerType = "info" | "success" | "warn" | "error";

export interface BannerItem {
  id: number;
  type: BannerType;
  title?: string;
  message: string;
  createdAt: number;
  autoCloseMs?: number;
}

let nextId = 1;

export const useBannerStore = defineStore("banner", {
  state: () => ({
    items: [] as BannerItem[],
  }),
  actions: {
    add(payload: {
      type?: BannerType;
      title?: string;
      message: string;
      autoCloseMs?: number;
    }) {
      const item: BannerItem = {
        id: nextId++,
        type: payload.type ?? "info",
        title: payload.title,
        message: payload.message,
        createdAt: Date.now(),
        autoCloseMs: payload.autoCloseMs ?? 6000,
      };
      this.items.push(item);
      if (item.autoCloseMs && item.autoCloseMs > 0) {
        setTimeout(() => this.remove(item.id), item.autoCloseMs);
      }
      return item.id;
    },
    remove(id: number) {
      this.items = this.items.filter((i) => i.id !== id);
    },
    clear() {
      this.items = [];
    },
  },
});
