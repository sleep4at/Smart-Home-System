<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div class="app-main-subtitle">场景模式（智能联动）</div>
    <p class="hint">
      这里将用于配置“如果满足某个条件，就自动控制设备”的智能联动规则，例如：
      “当卧室温度 ≥ 28℃ 时，自动开启卧室空调”。
    </p>
    <p class="hint">
      当前版本仅预留入口和展示说明，后续可以在这里增加：
      <br />- 条件（触发器）：设备、数据项（如温度）、比较符号、阈值
      <br />- 动作：要控制的目标设备及开关/模式
      <br />- 作用范围：仅限当前用户可访问的设备（包括公共设备和本人私有设备）
    </p>
  </section>
</template>

<script setup lang="ts">
</script>

