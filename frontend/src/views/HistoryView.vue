<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">历史数据图表</div>
      <div style="display: flex; gap: 8px;">
        <!-- 添加手动刷新按钮 -->
        <button 
          @click="fetchHistory" 
          :disabled="isRefreshing"
          class="field-select" 
          style="width: 80px; cursor: pointer; background-color: #f3f4f6; transition: all 0.2s;"
          :style="{ opacity: isRefreshing ? 0.5 : 1 }"
        >
          {{ isRefreshing ? '加载中...' : '刷新' }}
        </button>

        <select v-model="selectedDeviceId" class="field-select" style="width: 200px;">
          <option :value="0">选择设备</option>
          <option v-for="d in devices.list" :key="d.id" :value="d.id">
            {{ d.name }} ({{ d.type_display }})
          </option>
        </select>
        <select v-model="selectedRange" class="field-select" style="width: 120px;">
          <option value="6h">6小时</option>
          <option value="24h">24小时</option>
          <option value="3d">3天</option>
          <option value="7d">7天</option>
        </select>
      </div>
    </div>
    <div v-if="selectedDeviceId && chartData.length" style="flex: 1; min-height: 400px;">
      <v-chart :option="chartOption" style="width: 100%; height: 100%;" />
    </div>
    <div v-else style="flex: 1; display: flex; align-items: center; justify-content: center; color: #9ca3af;">
      {{ isRefreshing ? '正在同步云端数据...' : '请选择设备和时间范围查看历史数据' }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, BarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import api from "@/utils/http";
import { useDevicesStore } from "@/store/devices";

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent,
]);

const devices = useDevicesStore();
const selectedDeviceId = ref<number>(0);
const selectedRange = ref<string>("6h");
const chartData = ref<{ timestamp: string; data: Record<string, unknown> }[]>([]);

const isRefreshing = ref(false);

// --- 监听设备列表，实现默认选中 ---
watch(
  () => devices.list,
  async (newList) => {
    // 只有当目前没选设备，且列表里真的有设备时才执行
    if (selectedDeviceId.value === 0 && newList.length > 0) {
      selectedDeviceId.value = newList[0].id;
      // 【关键修改点】在 ID 改变后，显式调用一次拉取函数
      // 确保组件重新挂载时，只要有 ID 就能出图表
      await fetchHistory(); 
    }
  },
  { immediate: true }
);
// ------------------------------------------

async function fetchHistory() {
  if (!selectedDeviceId.value) {
    chartData.value = [];
    return;
  }

  isRefreshing.value = true;  // 开始加载

  try {
    const res = await api.get<{ points: { timestamp: string; data: Record<string, unknown> }[] }>(
      `/api/devices/${selectedDeviceId.value}/history/`,
      { params: { range: selectedRange.value } }
    );
    chartData.value = res.data.points || [];
  } catch (error) {
    console.error("获取历史数据失败:", error);
    chartData.value = [];
  } finally {
    // 模拟一个微小的延迟，防止闪烁
    setTimeout(() => {
      isRefreshing.value = false;
    }, 300);
  }
}

watch([selectedDeviceId, selectedRange], fetchHistory);

const selectedDevice = computed(() =>
  devices.list.find((d) => d.id === selectedDeviceId.value)
);

const chartOption = computed(() => {
  if (!chartData.value.length || !selectedDevice.value) return {};
  const device = selectedDevice.value;
  const isTempHumi = device.type === "TEMP_HUMI";
  const isSwitch = ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(device.type);
  const times = chartData.value.map((p) => {
    const date = new Date(p.timestamp);
    return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
  });

  if (isTempHumi) {
    // 将数据映射为 [时间戳, 数值] 的二维数组
    const temperatures = chartData.value.map((p) => [new Date(p.timestamp).getTime(), p.data?.temp]);
    const humidities = chartData.value.map((p) => [new Date(p.timestamp).getTime(), p.data?.humi]);
    // const temperatures = chartData.value.map((p) => (p.data?.temp as number) ?? null);
    // const humidities = chartData.value.map((p) => (p.data?.humi as number) ?? null);
    return {
      title: { text: `${device.name} - 温湿度历史`, left: "center" },
      tooltip: { trigger: "axis" },
      legend: { data: ["温度(°C)", "湿度(%RH)"], bottom: "2%" },
      grid: { left: "3%", right: "4%", bottom: "22%", containLabel: true },
      xAxis: {
        type: "time",
        boundaryGap: false,
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
          },
        },
      },
      yAxis: [
        { type: "value", name: "温度(°C)", position: "left" },
        { type: "value", name: "湿度(%RH)", position: "right" },
      ],
      dataZoom: [
        { type: "inside", xAxisIndex: 0, start: 0, end: 100 },
        { type: "slider", xAxisIndex: 0, start: 0, end: 100, bottom: "2%" },
      ],
      series: [
        { name: "温度(°C)", type: "line", data: temperatures, smooth: true, showSymbol: false, itemStyle: { color: "#ef4444" } },
        { name: "湿度(%RH)", type: "line", yAxisIndex: 1, data: humidities, smooth: true, showSymbol: false, itemStyle: { color: "#3b82f6" } },
      ],
    };
  }
  if (isSwitch) {
    const states = chartData.value.map((p) => [new Date(p.timestamp).getTime(), p.data?.on ? 1 : 0]);
    return {
      title: { text: `${device.name} - 开关状态历史`, left: "center" },
      tooltip: {
        trigger: "axis",
        formatter: (params: any) => {
          const p = params?.[0];
          if (!p?.data) return "";
          const t = Array.isArray(p.data) ? p.data[0] : p.data;
          const v = Array.isArray(p.data) ? p.data[1] : p.data;
          const timeStr = typeof t === "number" ? new Date(t).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }) : "";
          return `${timeStr}<br/>状态：${v === 1 ? "开启" : "关闭"}`;
        },
      },
      grid: { left: "3%", right: "4%", bottom: "22%", containLabel: true },
      xAxis: {
        type: "time",
        boundaryGap: true,
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
          },
        },
      },
      yAxis: {
        type: "value",
        min: 0,
        max: 1,
        interval: 1,
        splitNumber: 1,
        name: "状态",
        axisLabel: {
          formatter: (value: number) => (value === 1 ? "开启" : value === 0 ? "关闭" : ""),
        },
      },
      dataZoom: [
        { type: "inside", xAxisIndex: 0, start: 0, end: 100 },
        { type: "slider", xAxisIndex: 0, start: 0, end: 100, bottom: "2%" },
      ],
      series: [
        {
          name: "开关状态",
          type: "bar",
          data: states,
          barMaxWidth: 24,
          itemStyle: {
            color: (params: any) => (Array.isArray(params.data) && params.data[1] === 1 ? "#16a34a" : "#94a3b8"),
          },
        },
      ],
    };
  }
  const firstKey = chartData.value[0]?.data ? Object.keys(chartData.value[0].data)[0] : null;
  if (!firstKey) return {};
  const values = chartData.value.map((p) => [new Date(p.timestamp).getTime(), (p.data?.[firstKey] as number) ?? null]);
  return {
    title: { text: `${device.name} - ${firstKey}历史`, left: "center" },
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "22%", containLabel: true },
    xAxis: {
      type: "time",
      boundaryGap: false,
      axisLabel: {
        formatter: (value: number) => {
          const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
        },
      },
    },
    yAxis: { type: "value" },
    dataZoom: [
      { type: "inside", xAxisIndex: 0, start: 0, end: 100 },
      { type: "slider", xAxisIndex: 0, start: 0, end: 100, bottom: "2%" },
    ],
    series: [{ name: firstKey, type: "line", data: values, smooth: true, itemStyle: { color: "#2563eb" } }],
  };
});


// --- 自动刷新逻辑 ---
let timer: any = null;

onMounted(async () => {
  if (selectedDeviceId.value !== 0) {
    await fetchHistory();
  }

  // 每 15 秒自动执行一次获取数据的函数
  timer = setInterval(() => {
    // 只有当用户选了设备时才自动刷新，避免无效请求
    if (selectedDeviceId.value !== 0) {
      fetchHistory();
    }
  }, 15000); // 15000 毫秒 = 15 秒
});

onUnmounted(() => {
  // 当页面销毁（切换到其他菜单）时，必须清除定时器
  if (timer) {
    clearInterval(timer);
  }
});
// ------------------
</script>
