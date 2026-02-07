<template>
  <div class="banner-list" aria-live="polite">
    <TransitionGroup name="banner">
      <div
        v-for="item in banner.items"
        :key="item.id"
        class="banner-item"
        :class="[item.type]"
        role="alert"
      >
        <div class="banner-content">
          <span v-if="item.title" class="banner-title">{{ item.title }}</span>
          <span class="banner-message">{{ item.message }}</span>
        </div>
        <button
          type="button"
          class="banner-close"
          aria-label="关闭"
          @click="banner.remove(item.id)"
        >
          ×
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { useBannerStore } from "@/store/banner";

const banner = useBannerStore();
</script>

<style scoped>
.banner-list {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 380px;
  pointer-events: none;
}

.banner-list :deep(.banner-item) {
  pointer-events: auto;
}

.banner-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: #fff;
  border-left: 4px solid #3b82f6;
  font-size: 14px;
  line-height: 1.4;
}

.banner-item.info {
  border-left-color: #3b82f6;
  background: #eff6ff;
}

.banner-item.success {
  border-left-color: #22c55e;
  background: #f0fdf4;
}

.banner-item.warn {
  border-left-color: #f59e0b;
  background: #fffbeb;
}

.banner-item.error {
  border-left-color: #ef4444;
  background: #fef2f2;
}

.banner-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.banner-title {
  font-weight: 600;
  color: #1f2937;
}

.banner-message {
  color: #374151;
}

.banner-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #6b7280;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  border-radius: 4px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-close:hover {
  background: rgba(0, 0, 0, 0.06);
  color: #374151;
}

/* TransitionGroup */
.banner-enter-active,
.banner-leave-active {
  transition: all 0.25s ease;
}

.banner-enter-from,
.banner-leave-to {
  opacity: 0;
  transform: translateX(24px);
}

.banner-move {
  transition: transform 0.25s ease;
}
</style>
