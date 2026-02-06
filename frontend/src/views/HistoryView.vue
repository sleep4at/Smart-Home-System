<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">历史数据图表</div>
      <div style="display: flex; gap: 8px;">
        <select v-model="selectedDeviceId" class="field-select" style="width: 200px;">
          <option :value="0">选择设备</option>
          <option v-for="d in devices.list" :key="d.id" :value="d.id">
            {{ d.name }} ({{ d.type_display }})
          </option>
        </select>
        <select v-model="selectedRange" class="field-select" style="width: 120px;">
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
      请选择设备和时间范围查看历史数据
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import api from "@/utils/http";
import { useDevicesStore } from "@/store/devices";

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const devices = useDevicesStore();
const selectedDeviceId = ref<number>(0);
const selectedRange = ref<string>("24h");
const chartData = ref<{ timestamp: string; data: Record<string, unknown> }[]>([]);

// --- 新增代码部分：监听设备列表，实现默认选中 ---
watch(
  () => devices.list,
  (newList) => {
    // 如果当前还没选设备，且设备列表里有数据
    if (selectedDeviceId.value === 0 && newList.length > 0) {
      selectedDeviceId.value = newList[0].id;
    }
  },
  { immediate: true } // 立即执行一次，防止进入页面时列表已经加载好了
);
// ------------------------------------------

async function fetchHistory() {
  if (!selectedDeviceId.value) {
    chartData.value = [];
    return;
  }
  try {
    const res = await api.get<{ points: { timestamp: string; data: Record<string, unknown> }[] }>(
      `/api/devices/${selectedDeviceId.value}/history/`,
      { params: { range: selectedRange.value } }
    );
    chartData.value = res.data.points || [];
  } catch {
    chartData.value = [];
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
      legend: { data: ["温度(°C)", "湿度(%RH)"], bottom: 0 },
      grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
      // xAxis: { type: "category", data: times, boundaryGap: false },
      xAxis: { type: "time", boundaryGap: false,
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
          }
        }
      },
      yAxis: [
        { type: "value", name: "温度(°C)", position: "left" },
        { type: "value", name: "湿度(%RH)", position: "right" },
      ],
      series: [
      { 
        name: "温度(°C)", 
        type: "line", 
        data: temperatures, // 现在是二维数组
        smooth: true, 
        showSymbol: true, // 建议关闭数据点，在大跨度下更好看
        itemStyle: { color: "#ef4444" } 
      },
      { 
        name: "湿度(%RH)", 
        type: "line", 
        yAxisIndex: 1, 
        data: humidities, 
        smooth: true, 
        showSymbol: true,
        itemStyle: { color: "#3b82f6" } 
      },
    ],
      // series: [
      //   { name: "温度(°C)", type: "line", data: temperatures, smooth: true, itemStyle: { color: "#ef4444" } },
      //   { name: "湿度(%RH)", type: "line", yAxisIndex: 1, data: humidities, smooth: true, itemStyle: { color: "#3b82f6" } },
      // ],
    };
  }
  if (isSwitch) {
    const states = chartData.value.map((p) => [new Date(p.timestamp).getTime(), p.data?.on ? 1 : 0]);
    // const states = chartData.value.map((p) => ((p.data?.on as boolean) ? 1 : 0));
    return {
      title: { text: `${device.name} - 开关状态历史`, left: "center" },
      tooltip: { trigger: "axis" },
      grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
      // xAxis: { type: "category", data: times, boundaryGap: false },
      xAxis: { 
      type: "time", 
      boundaryGap: false,
      axisLabel: {
        formatter: (value: number) => {
          const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
        }
      }
    },
      yAxis: {
        type: "value",
        min: 0,
        max: 1,
        name: "状态",
        axisLabel: { formatter: (value: number) => (value === 1 ? "开启" : "关闭") },
      },
      series: [
        { name: "开关状态", type: "line", step: "start", data: states, itemStyle: { color: "#16a34a" }, areaStyle: {} },
      ],
    };
  }
  const firstKey = chartData.value[0]?.data ? Object.keys(chartData.value[0].data)[0] : null;
  if (!firstKey) return {};
  const values = chartData.value.map((p) => [new Date(p.timestamp).getTime(), (p.data?.[firstKey] as number) ?? null]);
  // const values = chartData.value.map((p) => (p.data?.[firstKey] as number) ?? null);
  return {
    title: { text: `${device.name} - ${firstKey}历史`, left: "center" },
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
    // xAxis: { type: "category", data: times, boundaryGap: false },
    xAxis: { 
      type: "time", 
      boundaryGap: false,
      axisLabel: {
        formatter: (value: number) => {
          const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
        }
      }
    },
    yAxis: { type: "value" },
    series: [{ name: firstKey, type: "line", data: values, smooth: true, itemStyle: { color: "#2563eb" } }],
  };
});
</script>
