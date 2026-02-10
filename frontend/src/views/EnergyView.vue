<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;">
      <div class="app-main-subtitle">设备能耗与电费估算</div>
      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <button
          @click="fetchEnergyAnalysis"
          :disabled="loading"
          class="field-select"
          style="width: 80px; cursor: pointer; background-color: #f3f4f6;"
          :style="{ opacity: loading ? 0.5 : 1 }"
        >
          {{ loading ? "加载中..." : "刷新" }}
        </button>
        <button
          @click="exportEnergyCsv"
          :disabled="loading || exportingCsv"
          class="field-select"
          style="width: 96px; cursor: pointer; background-color: #f3f4f6;"
          :style="{ opacity: (loading || exportingCsv) ? 0.5 : 1 }"
        >
          {{ exportingCsv ? "导出中..." : "导出CSV" }}
        </button>

        <select v-model="selectedDeviceId" class="field-select" style="width: 220px;">
          <option :value="0">全部设备</option>
          <option v-for="d in devices.list" :key="d.id" :value="d.id">
            {{ d.name }} ({{ d.type_display }})
          </option>
        </select>

        <select v-model="selectedRange" class="field-select" style="width: 120px;">
          <option value="6h">6小时</option>
          <option value="24h">24小时</option>
          <option value="3d">3天</option>
          <option value="7d">7天</option>
          <option value="30d">30天</option>
        </select>
      </div>
    </div>

    <div class="energy-cards">
      <div class="energy-card">
        <div class="energy-card-title">总能耗</div>
        <div class="energy-card-value">{{ formatKwh(total.energy_kwh) }} kWh</div>
      </div>
      <div class="energy-card">
        <div class="energy-card-title">区间预估电费</div>
        <div class="energy-card-value">¥{{ formatMoney(total.cost) }}</div>
      </div>
      <div class="energy-card">
        <div class="energy-card-title">平均功率</div>
        <div class="energy-card-value">{{ formatW(total.avg_power_w) }} W</div>
      </div>
      <div class="energy-card">
        <div class="energy-card-title">峰值功率</div>
        <div class="energy-card-value">{{ formatW(total.peak_power_w) }} W</div>
      </div>
      <div class="energy-card">
        <div class="energy-card-title">当月累计电费</div>
        <div class="energy-card-value">¥{{ formatMoney(monthly.cost_so_far) }}</div>
      </div>
      <div class="energy-card">
        <div class="energy-card-title">当月预估电费</div>
        <div class="energy-card-value">¥{{ formatMoney(monthly.projected_cost) }}</div>
      </div>
    </div>

    <div v-if="loadError" class="energy-error">{{ loadError }}</div>

    <div class="energy-panel">
      <div class="energy-panel-title">功率曲线（W）</div>
      <div v-if="powerSeries.length" class="chart-wrap">
        <v-chart :option="powerChartOption" :update-options="{ notMerge: true }" style="width: 100%; height: 100%;" />
      </div>
      <div v-else class="energy-empty">
        {{ loading ? "正在计算能耗..." : "当前范围暂无可展示数据" }}
      </div>
    </div>

    <div v-if="deviceBreakdown.length" class="energy-panel">
      <div class="energy-panel-title">设备耗电分项</div>
      <div class="chart-wrap-sm">
        <v-chart :option="breakdownChartOption" :update-options="{ notMerge: true }" style="width: 100%; height: 100%;" />
      </div>
      <div class="energy-table-wrap">
        <table class="energy-table">
          <thead>
            <tr>
              <th>设备</th>
              <th>位置</th>
              <th>类型</th>
              <th>当月运行时长(h)</th>
              <th>能耗(kWh)</th>
              <th>费用(¥)</th>
              <th>峰值功率(W)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in deviceBreakdown" :key="row.device_id">
              <td>{{ row.name }}</td>
              <td>{{ row.location || "—" }}</td>
              <td>{{ row.type_display }}</td>
              <td>{{ formatRuntimeHours(row.monthly_runtime_hours) }}</td>
              <td>{{ formatKwh(row.energy_kwh) }}</td>
              <td>{{ formatMoney(row.cost) }}</td>
              <td>{{ formatW(row.peak_power_w) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart, BarChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
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
  GridComponent,
  DataZoomComponent,
]);

interface EnergySeriesPoint {
  timestamp: string;
  power_w: number;
}

interface EnergyDeviceBreakdownItem {
  device_id: number;
  name: string;
  location: string;
  type: string;
  type_display: string;
  energy_kwh: number;
  cost: number;
  peak_power_w: number;
  avg_power_w: number;
  monthly_runtime_hours: number | null;
}

interface EnergyTotal {
  energy_kwh: number;
  cost: number;
  peak_power_w: number;
  avg_power_w: number;
}

interface MonthlyEstimate {
  month: string;
  energy_kwh_so_far: number;
  cost_so_far: number;
  projected_energy_kwh: number;
  projected_cost: number;
  elapsed_days: number;
  days_in_month: number;
  runtime_hours_by_device: Record<string, number>;
}

interface EnergyAnalysisResponse {
  range: string;
  start: string;
  end: string;
  price_per_kwh: number;
  total: EnergyTotal;
  series: EnergySeriesPoint[];
  device_breakdown: EnergyDeviceBreakdownItem[];
  monthly_estimate: MonthlyEstimate;
}

const devices = useDevicesStore();
const selectedDeviceId = ref<number>(0);
const selectedRange = ref<string>("24h");
const loading = ref(false);
const exportingCsv = ref(false);
const loadError = ref("");
const analysis = ref<EnergyAnalysisResponse | null>(null);

const total = computed<EnergyTotal>(() => {
  return (
    analysis.value?.total ?? {
      energy_kwh: 0,
      cost: 0,
      peak_power_w: 0,
      avg_power_w: 0,
    }
  );
});

const monthly = computed<MonthlyEstimate>(() => {
  return (
    analysis.value?.monthly_estimate ?? {
      month: "",
      energy_kwh_so_far: 0,
      cost_so_far: 0,
      projected_energy_kwh: 0,
      projected_cost: 0,
      elapsed_days: 0,
      days_in_month: 0,
      runtime_hours_by_device: {},
    }
  );
});

const powerSeries = computed(() => {
  const list = analysis.value?.series ?? [];
  return list
    .map((p) => {
      const t = new Date(p.timestamp).getTime();
      return [t, Number(p.power_w)] as [number, number];
    })
    .filter((p) => Number.isFinite(p[0]) && Number.isFinite(p[1]))
    .sort((a, b) => a[0] - b[0]);
});

const deviceBreakdown = computed(() => analysis.value?.device_breakdown ?? []);

const powerChartOption = computed(() => {
  if (!powerSeries.value.length) return {};
  const min = powerSeries.value[0][0];
  const max = powerSeries.value[powerSeries.value.length - 1][0];
  const pointCount = powerSeries.value.length;

  return {
    animation: true,
    animationDuration: 500,
    animationDurationUpdate: 400,
    animationEasing: "cubicOut",
    animationEasingUpdate: "cubicOut",
    // 全部设备聚合时点数较大，默认阈值会自动关闭动画。
    animationThreshold: Math.max(2000, pointCount + 100),
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const p = params?.[0];
        if (!p?.data) return "";
        const t = Array.isArray(p.data) ? p.data[0] : null;
        const v = Array.isArray(p.data) ? p.data[1] : p.data;
        const timeStr =
          typeof t === "number"
            ? new Date(t).toLocaleString("zh-CN", {
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
              })
            : "";
        return `${timeStr}<br/>功率：${formatW(v)} W`;
      },
    },
    grid: { left: "3%", right: "4%", bottom: "22%", containLabel: true },
    xAxis: {
      type: "time",
      min,
      max,
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
      name: "W",
    },
    dataZoom: [
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
    ],
    series: [
      {
        name: "功率",
        type: "line",
        step: "start",
        animation: true,
        connectNulls: true,
        showSymbol: false,
        progressive: 0,
        progressiveThreshold: 100000,
        data: powerSeries.value,
        lineStyle: { width: 2, color: "#2563eb" },
        areaStyle: { color: "rgba(37, 99, 235, 0.12)" },
      },
    ],
  };
});

const breakdownChartOption = computed(() => {
  if (!deviceBreakdown.value.length) return {};
  const names = deviceBreakdown.value.map((d) => d.name);
  const values = deviceBreakdown.value.map((d) => d.energy_kwh);
  return {
    animation: true,
    animationDuration: 500,
    animationDurationUpdate: 400,
    animationEasing: "cubicOut",
    animationEasingUpdate: "cubicOut",
    animationThreshold: Math.max(2000, values.length + 100),
    tooltip: { trigger: "axis" },
    grid: { left: "3%", right: "4%", bottom: "8%", containLabel: true },
    xAxis: {
      type: "value",
      name: "kWh",
    },
    yAxis: {
      type: "category",
      data: names,
    },
    series: [
      {
        type: "bar",
        animation: true,
        progressive: 0,
        progressiveThreshold: 100000,
        data: values,
        itemStyle: { color: "#0ea5e9" },
      },
    ],
  };
});

function formatKwh(value: number) {
  return Number.isFinite(value) ? value.toFixed(3) : "0.000";
}

function formatMoney(value: number) {
  return Number.isFinite(value) ? value.toFixed(2) : "0.00";
}

function formatW(value: number) {
  return Number.isFinite(value) ? value.toFixed(1) : "0.0";
}

function formatRuntimeHours(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return Number.isFinite(value) ? value.toFixed(2) : "—";
}

function buildQueryParams(): Record<string, string | number> {
  const params: Record<string, string | number> = {
    range: selectedRange.value,
  };
  if (selectedDeviceId.value) {
    params.device_id = selectedDeviceId.value;
  }
  return params;
}

function parseCsvFilename(contentDisposition?: string): string | null {
  if (!contentDisposition) return null;
  const filenameUtf8 = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (filenameUtf8?.[1]) {
    try {
      return decodeURIComponent(filenameUtf8[1]);
    } catch {
      return filenameUtf8[1];
    }
  }
  const filenameBasic = contentDisposition.match(/filename="?([^";]+)"?/i);
  return filenameBasic?.[1] ?? null;
}

async function fetchEnergyAnalysis() {
  loading.value = true;
  loadError.value = "";
  try {
    const res = await api.get<EnergyAnalysisResponse>("/api/energy/analysis/", {
      params: buildQueryParams(),
    });
    analysis.value = res.data;
  } catch (error) {
    console.error("获取能耗分析失败:", error);
    loadError.value = "获取能耗分析失败，请稍后重试。";
    analysis.value = null;
  } finally {
    loading.value = false;
  }
}

async function exportEnergyCsv() {
  exportingCsv.value = true;
  loadError.value = "";
  try {
    const res = await api.get("/api/energy/analysis/export.csv", {
      params: buildQueryParams(),
      responseType: "blob",
    });
    const disposition = (res.headers?.["content-disposition"] as string | undefined) ?? "";
    const filename =
      parseCsvFilename(disposition) ??
      `能耗分析_${selectedDeviceId.value || "all"}_${selectedRange.value}.csv`;
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8;" });
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);
  } catch (error) {
    console.error("导出 CSV 失败:", error);
    loadError.value = "导出 CSV 失败，请稍后重试。";
  } finally {
    exportingCsv.value = false;
  }
}

watch([selectedRange, selectedDeviceId], fetchEnergyAnalysis, { immediate: true });

watch(
  () => devices.list,
  (list) => {
    if (selectedDeviceId.value === 0) return;
    if (!list.some((d) => d.id === selectedDeviceId.value)) {
      selectedDeviceId.value = 0;
    }
  }
);

onMounted(async () => {
  if (!devices.list.length) {
    await devices.fetchDevices();
  }
});
</script>

<style scoped>
.energy-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.energy-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 12px;
  background: #fff;
}

.energy-card-title {
  color: #6b7280;
  font-size: 12px;
}

.energy-card-value {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 700;
  color: #111827;
}

.energy-panel {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

.energy-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.chart-wrap {
  width: 100%;
  height: 360px;
}

.chart-wrap-sm {
  width: 100%;
  height: 240px;
}

.energy-empty {
  color: #9ca3af;
  padding: 24px 8px;
}

.energy-error {
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
}

.energy-table-wrap {
  margin-top: 10px;
  overflow-x: auto;
}

.energy-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.energy-table th,
.energy-table td {
  border-bottom: 1px solid #e5e7eb;
  padding: 8px 10px;
  text-align: left;
  white-space: nowrap;
}

.energy-table th {
  color: #374151;
  font-weight: 600;
  background: #f9fafb;
}
</style>
