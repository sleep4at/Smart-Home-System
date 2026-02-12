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
    <div v-if="selectedDeviceId && chartData.length" class="history-chart-wrap">
      <v-chart
        :option="chartOption"
        :update-options="{ notMerge: true }"
        :autoresize="true"
        style="width: 100%; height: 100%;"
      />
    </div>
    <div v-else style="flex: 1; display: flex; align-items: center; justify-content: center; color: #9ca3af;">
      {{ isRefreshing ? '正在同步云端数据...' : '请选择设备和时间范围查看历史数据' }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue";
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

type ParsedHistoryPoint = {
  t: number;
  data: Record<string, unknown>;
};

function parseTimestampToMs(timestamp: string): number | null {
  if (!timestamp) return null;
  // 兼容后端 6 位微秒时间戳，统一裁剪为毫秒，避免浏览器解析差异。
  const normalized = timestamp.replace(/(\.\d{3})\d+/, "$1");
  const ms = new Date(normalized).getTime();
  return Number.isFinite(ms) ? ms : null;
}

function toNumberOrNull(value: unknown): number | null {
  if (value === undefined || value === null || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

const BATTERY_EMPTY_V = 3.0;
const BATTERY_FULL_V = 4.15;

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function voltageToBatteryPercent(voltage: number): number {
  const normalized = ((voltage - BATTERY_EMPTY_V) / (BATTERY_FULL_V - BATTERY_EMPTY_V)) * 100;
  return Math.round(clamp(normalized, 0, 100) * 10) / 10;
}

function batteryVoltageFromData(data: Record<string, unknown>): number | null {
  return toNumberOrNull(data.battery_v ?? data.battery_voltage ?? data.battery);
}

function batteryPercentFromData(data: Record<string, unknown>): number | null {
  const rawPercent = toNumberOrNull(
    data.battery_pct ?? data.battery_percent ?? data.batteryPercentage
  );
  if (rawPercent !== null) {
    return Math.round(clamp(rawPercent, 0, 100) * 10) / 10;
  }
  const voltage = batteryVoltageFromData(data);
  if (voltage === null) return null;
  return voltageToBatteryPercent(voltage);
}

function inferSwitchOn(
  data: Record<string, unknown>,
  previous: boolean | null
): boolean | null {
  if (Object.prototype.hasOwnProperty.call(data, "on")) {
    return Boolean(data.on);
  }
  const power = toNumberOrNull(data.power_w ?? data.power);
  if (power !== null) {
    return power > 0;
  }
  return previous;
}

const parsedPoints = computed<ParsedHistoryPoint[]>(() =>
  chartData.value
    .map((p) => ({
      t: parseTimestampToMs(p.timestamp),
      data: (p.data ?? {}) as Record<string, unknown>,
    }))
    .filter((p): p is ParsedHistoryPoint => p.t !== null)
    .sort((a, b) => a.t - b.t)
);

const xAxisRange = computed(() => {
  if (!parsedPoints.value.length) return null;
  let min = parsedPoints.value[0].t;
  let max = parsedPoints.value[parsedPoints.value.length - 1].t;
  if (min === max) {
    min -= 60 * 1000;
    max += 60 * 1000;
  }
  return { min, max };
});

function getDataZoomOptions() {
  return [
    {
      type: "inside",
      xAxisIndex: 0,
      filterMode: "none",
      start: 0,
      end: 100,
      zoomOnMouseWheel: true,
      moveOnMouseWheel: false,
      moveOnMouseMove: true,
    },
    {
      type: "slider",
      xAxisIndex: 0,
      filterMode: "none",
      start: 0,
      end: 100,
      bottom: "2%",
    },
  ];
}

// --- 监听设备列表，实现默认选中 ---
function syncSelectedDevice(newList: { id: number }[]) {
  if (!newList.length) {
    selectedDeviceId.value = 0;
    chartData.value = [];
    return;
  }
  const currentId = Number(selectedDeviceId.value) || 0;
  const exists = newList.some((d) => d.id === currentId);
  if (!exists) {
    selectedDeviceId.value = newList[0].id;
  } else if (selectedDeviceId.value !== currentId) {
    selectedDeviceId.value = currentId;
  }
}

watch(
  () => devices.list,
  (newList) => syncSelectedDevice(newList),
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

watch([selectedDeviceId, selectedRange], fetchHistory, { immediate: true });

const selectedDevice = computed(() =>
  devices.list.find((d) => d.id === (Number(selectedDeviceId.value) || 0))
);
const selectedDeviceUpdatedAt = computed(() => selectedDevice.value?.updated_at || null);

const HISTORY_EVENT_REFRESH_MIN_INTERVAL_MS = 2500;
let lastEventRefreshAt = 0;

watch(
  selectedDeviceUpdatedAt,
  (newUpdatedAt, oldUpdatedAt) => {
    if (!selectedDeviceId.value || !newUpdatedAt || !oldUpdatedAt) return;
    if (newUpdatedAt === oldUpdatedAt) return;
    const now = Date.now();
    if (now - lastEventRefreshAt < HISTORY_EVENT_REFRESH_MIN_INTERVAL_MS) return;
    lastEventRefreshAt = now;
    fetchHistory();
  }
);

const chartOption = computed(() => {
  if (!parsedPoints.value.length || !selectedDevice.value || !xAxisRange.value) return {};
  const device = selectedDevice.value;
  const isTempHumi = device.type === "TEMP_HUMI";
  const isSwitch = ["LAMP_SWITCH", "AC_SWITCH", "FAN_SWITCH"].includes(device.type);

  if (isTempHumi) {
    const temperatures = parsedPoints.value.map((p) => [p.t, toNumberOrNull(p.data?.temp)]);
    const humidities = parsedPoints.value.map((p) => [p.t, toNumberOrNull(p.data?.humi)]);
    const batteryPercents = parsedPoints.value.map((p) => [p.t, batteryPercentFromData(p.data)]);
    const hasBatteryData = batteryPercents.some((item) => item[1] !== null);
    const legendData = ["温度(°C)", "湿度(%RH)"];
    const yAxis: any[] = [
      { type: "value", name: "温度(°C)", position: "left" },
      { type: "value", name: "湿度(%RH)", position: "right" },
    ];
    const series: any[] = [
      {
        name: "温度(°C)",
        type: "line",
        data: temperatures,
        smooth: true,
        connectNulls: true,
        showSymbol: false,
        itemStyle: { color: "#ef4444" },
      },
      {
        name: "湿度(%RH)",
        type: "line",
        yAxisIndex: 1,
        data: humidities,
        smooth: true,
        connectNulls: true,
        showSymbol: false,
        itemStyle: { color: "#3b82f6" },
      },
    ];
    if (hasBatteryData) {
      legendData.push("电量(%)");
      yAxis.push({
        type: "value",
        name: "电量(%)",
        position: "right",
        offset: 64,
        min: 0,
        max: 100,
        axisLabel: { formatter: "{value}%" },
      });
      series.push({
        name: "电量(%)",
        type: "line",
        yAxisIndex: 2,
        data: batteryPercents,
        smooth: true,
        connectNulls: true,
        showSymbol: false,
        itemStyle: { color: "#f59e0b" },
      });
    }
    return {
      title: { text: `${device.name} - 温湿度历史`, left: "center" },
      tooltip: { trigger: "axis" },
      legend: { data: legendData, bottom: "2%" },
      grid: { left: "3%", right: hasBatteryData ? "12%" : "4%", bottom: "22%", containLabel: true },
      xAxis: {
        type: "time",
        min: xAxisRange.value.min,
        max: xAxisRange.value.max,
        boundaryGap: false,
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value);
            return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
          },
        },
      },
      yAxis,
      dataZoom: getDataZoomOptions(),
      series,
    };
  }
  if (isSwitch) {
    const states: [number, number | null][] = [];
    let previousState: boolean | null = null;
    for (const p of parsedPoints.value) {
      const current = inferSwitchOn(p.data, previousState);
      if (current !== null) {
        previousState = current;
      }
      states.push([p.t, current === null ? null : current ? 1 : 0]);
    }
    return {
      title: { text: `${device.name} - 开关状态历史`, left: "center" },
      tooltip: {
        trigger: "axis",
        formatter: (params: any) => {
          const p = params?.[0];
          if (!p?.data) return "";
          const t = Array.isArray(p.data) ? p.data[0] : p.data;
          const v = Array.isArray(p.data) ? p.data[1] : p.data;
          if (v === null || v === undefined) return "";
          const timeStr = typeof t === "number" ? new Date(t).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }) : "";
          return `${timeStr}<br/>状态：${v === 1 ? "开启" : "关闭"}`;
        },
      },
      grid: { left: "3%", right: "4%", bottom: "22%", containLabel: true },
      xAxis: {
        type: "time",
        min: xAxisRange.value.min,
        max: xAxisRange.value.max,
        boundaryGap: false,
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
      visualMap: {
        show: false,
        dimension: 1,
        pieces: [
          { value: 0, color: "#94a3b8" },
          { value: 1, color: "#16a34a" },
        ],
      },
      dataZoom: getDataZoomOptions(),
      series: [
        {
          name: "开关状态",
          type: "line",
          data: states,
          step: "start",
          connectNulls: true,
          showSymbol: false,
          lineStyle: { width: 2 },
          areaStyle: { opacity: 0.35 },
          symbol: "none",
        },
      ],
    };
  }
  const firstPoint = parsedPoints.value.find((p) => Object.keys(p.data || {}).length > 0);
  const firstKey = firstPoint ? Object.keys(firstPoint.data)[0] : null;
  if (!firstKey) return {};
  const values = parsedPoints.value.map((p) => [p.t, toNumberOrNull(p.data?.[firstKey])]);
  return {
    title: { text: `${device.name} - ${firstKey}历史`, left: "center" },
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "22%", containLabel: true },
    xAxis: {
      type: "time",
      min: xAxisRange.value.min,
      max: xAxisRange.value.max,
      boundaryGap: false,
      axisLabel: {
        formatter: (value: number) => {
          const date = new Date(value);
          return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
        },
      },
    },
    yAxis: { type: "value" },
    dataZoom: getDataZoomOptions(),
    series: [
      {
        name: firstKey,
        type: "line",
        data: values,
        smooth: true,
        connectNulls: true,
        itemStyle: { color: "#2563eb" },
      },
    ],
  };
});


onMounted(async () => {
  try {
    // 历史页刷新后需要主动加载设备列表，否则下拉为空。
    await devices.fetchDevices();
  } catch (error) {
    console.error("加载设备列表失败:", error);
  }
});
</script>

<style scoped>
.history-chart-wrap {
  width: 100%;
  height: clamp(500px, 74vh, 900px);
  min-height: 500px;
}

@media (max-width: 768px) {
  .history-chart-wrap {
    height: clamp(360px, 58vh, 620px);
    min-height: 360px;
  }
}
</style>
