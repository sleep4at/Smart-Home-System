<template>
  <section style="display: flex; flex-direction: column; gap: 16px; flex: 1;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div class="app-main-subtitle">邮件告警规则（共 {{ emailAlerts.list.length }} 条）</div>
      <button class="btn btn-primary" @click="openCreate">＋ 新建规则</button>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>预设</th>
            <th>触发设备</th>
            <th>触发条件</th>
            <th>收件人</th>
            <th>状态</th>
            <th>最后触发</th>
            <th style="text-align: right;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in emailAlerts.list" :key="r.id">
            <td class="fw-500">{{ r.name }}</td>
            <td>{{ presetLabel(r.preset) }}</td>
            <td>{{ r.trigger_device_name }}</td>
            <td>
              {{ r.trigger_field }} {{ r.trigger_above ? "≥" : "≤" }} {{ r.trigger_value ?? "—" }}
            </td>
            <td>{{ (r.recipients || []).join(", ") || "—" }}</td>
            <td>
              <span
                class="device-tile-status"
                :class="r.enabled ? 'status-online' : 'status-offline'"
              >
                {{ r.enabled ? "启用" : "禁用" }}
              </span>
            </td>
            <td class="text-muted">
              {{ r.last_triggered_at ? formatTime(r.last_triggered_at) : "—" }}
            </td>
            <td style="text-align: right;">
              <button class="btn btn-ghost btn-sm" @click="openEdit(r)">编辑</button>
              <button class="btn btn-ghost btn-sm" @click="toggleEnabled(r)">
                {{ r.enabled ? "禁用" : "启用" }}
              </button>
              <button class="btn btn-ghost btn-sm text-danger" @click="confirmDelete(r)">
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!emailAlerts.list.length">
            <td colspan="8" style="text-align: center; padding: 24px;">
              暂无邮件告警规则，点击"新建规则"添加
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <EmailAlertRuleDialog
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
import { useEmailAlertsStore, type EmailAlertRule, PRESET_OPTIONS } from "@/store/emailAlerts";
import { useDevicesStore } from "@/store/devices";
import EmailAlertRuleDialog from "@/components/EmailAlertRuleDialog.vue";

const emailAlerts = useEmailAlertsStore();
const devices = useDevicesStore();

const showDialog = ref(false);
const editingRule = ref<EmailAlertRule | null>(null);

function presetLabel(preset: string) {
  return PRESET_OPTIONS.find((p) => p.value === preset)?.label ?? preset;
}

function formatTime(timestamp: string) {
  const d = new Date(timestamp);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")} ${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

onMounted(async () => {
  await Promise.all([emailAlerts.fetchRules(), devices.fetchDevices()]);
});

const openCreate = () => {
  editingRule.value = null;
  showDialog.value = true;
};

const openEdit = (r: EmailAlertRule) => {
  editingRule.value = r;
  showDialog.value = true;
};

const closeDialog = () => (showDialog.value = false);

const onSubmitRule = async (payload: Partial<EmailAlertRule>) => {
  if (editingRule.value?.id) {
    await emailAlerts.updateRule(editingRule.value.id, payload);
  } else {
    await emailAlerts.createRule(payload);
  }
  showDialog.value = false;
};

const toggleEnabled = async (r: EmailAlertRule) => {
  await emailAlerts.toggleEnabled(r.id);
};

const confirmDelete = async (r: EmailAlertRule) => {
  if (confirm(`确定删除邮件告警规则 "${r.name}" 吗？`)) {
    await emailAlerts.deleteRule(r.id);
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
</style>
