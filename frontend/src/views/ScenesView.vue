<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">场景模式（智能联动）</div>
      <button class="btn btn-primary" @click="openCreate">＋ 创建规则</button>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>触发条件</th>
            <th>执行动作</th>
            <th>状态</th>
            <th>最后触发</th>
            <th style="text-align: right;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rule in scenes.list" :key="rule.id">
            <td class="fw-500">{{ rule.name }}</td>
            <td>
              <div class="trigger-info">
                {{ formatTrigger(rule) }}
              </div>
            </td>
            <td>
              <div class="action-info">
                {{ formatAction(rule) }}
              </div>
            </td>
            <td>
              <span
                class="device-tile-status"
                :class="rule.enabled ? 'status-online' : 'status-offline'"
              >
                {{ rule.enabled ? "启用" : "禁用" }}
              </span>
            </td>
            <td class="text-muted">
              {{ rule.last_triggered_at ? formatTime(rule.last_triggered_at) : "—" }}
            </td>
            <td style="text-align: right;">
              <button class="btn btn-ghost btn-sm" @click="openEdit(rule)">编辑</button>
              <button
                class="btn btn-ghost btn-sm"
                @click="toggleEnabled(rule)"
              >
                {{ rule.enabled ? "禁用" : "启用" }}
              </button>
              <button
                class="btn btn-ghost btn-sm text-danger"
                @click="confirmDelete(rule)"
              >
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!scenes.list.length">
            <td colspan="6" style="text-align: center; padding: 24px;">
              暂无场景规则，点击"创建规则"开始配置智能联动
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <SceneRuleDialog
      v-if="showDialog"
      :rule="editingRule"
      :devices="devices.list"
      @close="closeDialog"
      @submit="onSubmitRule"
    />
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useScenesStore, type SceneRule } from "@/store/scenes";
import { useDevicesStore } from "@/store/devices";
import SceneRuleDialog from "@/components/SceneRuleDialog.vue";

const scenes = useScenesStore();
const devices = useDevicesStore();

const showDialog = ref(false);
const editingRule = ref<SceneRule | null>(null);

onMounted(async () => {
  await Promise.all([scenes.fetchScenes(), devices.fetchDevices()]);
});

const formatTrigger = (rule: SceneRule) => {
  const device = devices.list.find((d) => d.id === rule.trigger_device);
  const deviceName = device?.name || `设备 #${rule.trigger_device}`;
  const field = rule.trigger_field === "temp" ? "温度" : rule.trigger_field === "humi" ? "湿度" : rule.trigger_field;

  if (rule.trigger_type === "THRESHOLD_ABOVE") {
    const threshold = typeof rule.trigger_value === "number" ? rule.trigger_value : rule.trigger_value?.value || 0;
    return `${deviceName} 的${field} > ${threshold}`;
  } else if (rule.trigger_type === "THRESHOLD_BELOW") {
    const threshold = typeof rule.trigger_value === "number" ? rule.trigger_value : rule.trigger_value?.value || 0;
    return `${deviceName} 的${field} < ${threshold}`;
  } else if (rule.trigger_type === "RANGE_OUT") {
    const range = typeof rule.trigger_value === "object" && rule.trigger_value !== null ? rule.trigger_value : { min: 0, max: 0 };
    return `${deviceName} 的${field} 不在 [${range.min}, ${range.max}] 范围内`;
  } else if (rule.trigger_type === "TIME_STATE") {
    const timeStr = rule.trigger_time_start && rule.trigger_time_end
      ? `${rule.trigger_time_start.slice(0, 5)} - ${rule.trigger_time_end.slice(0, 5)}`
      : "";
    const stateDevice = rule.trigger_state_device
      ? devices.list.find((d) => d.id === rule.trigger_state_device)?.name || `设备 #${rule.trigger_state_device}`
      : "";
    return `${timeStr} 且 ${stateDevice} 状态匹配`;
  }
  return "未知触发条件";
};

const formatAction = (rule: SceneRule) => {
  const device = devices.list.find((d) => d.id === rule.action_device);
  const deviceName = device?.name || `设备 #${rule.action_device}`;

  if (rule.action_type === "SET_TEMP") {
    const temp = typeof rule.action_value === "number" ? rule.action_value : rule.action_value?.temp || 26;
    return `${deviceName} 设置温度为 ${temp}°C`;
  } else if (rule.action_type === "SET_FAN_SPEED") {
    const speed = typeof rule.action_value === "number" ? rule.action_value : rule.action_value?.speed || 1;
    return `${deviceName} 设置档位为 ${speed}`;
  } else if (rule.action_type === "TURN_ON") {
    return `开启 ${deviceName}`;
  } else if (rule.action_type === "TURN_OFF") {
    return `关闭 ${deviceName}`;
  } else if (rule.action_type === "TOGGLE") {
    return `切换 ${deviceName} 开关`;
  }
  return "未知动作";
};

const formatTime = (timestamp: string) => {
  const d = new Date(timestamp);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
};

const openCreate = () => {
  editingRule.value = null;
  showDialog.value = true;
};

const openEdit = (rule: SceneRule) => {
  editingRule.value = rule;
  showDialog.value = true;
};

const closeDialog = () => {
  showDialog.value = false;
};

const onSubmitRule = async (payload: Partial<SceneRule>) => {
  if (editingRule.value?.id) {
    await scenes.updateScene(editingRule.value.id, payload);
  } else {
    await scenes.createScene(payload);
  }
  showDialog.value = false;
};

const toggleEnabled = async (rule: SceneRule) => {
  await scenes.toggleEnabled(rule.id);
};

const confirmDelete = async (rule: SceneRule) => {
  if (confirm(`确定删除场景规则 "${rule.name}" 吗？`)) {
    await scenes.deleteScene(rule.id);
  }
};
</script>

<style scoped>
.table-wrap {
  background: #fff;
  border-radius: var(--radius-large);
  padding: 16px;
  box-shadow: var(--shadow-soft);
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 8px 12px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}

.data-table td {
  padding: 12px;
  font-size: 14px;
  border-bottom: 1px solid #f3f4f6;
}

.fw-500 {
  font-weight: 500;
}

.text-muted {
  color: #6b7280;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.text-danger {
  color: #dc2626;
}

.trigger-info,
.action-info {
  font-size: 13px;
  line-height: 1.5;
}
</style>
