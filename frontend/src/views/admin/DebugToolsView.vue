<template>
  <section class="debug-tools">
    <div class="app-main-subtitle">MQTT WebSocket调试工具</div>
    <p class="tool-desc">用于调试MQTT连接：连接Broker后订阅/发布主题。</p>

    <!-- 连接信息 -->
    <div class="panel">
      <div class="panel-title">连接信息</div>
      <div class="form-section">
        <div class="form-row form-row-full">
          <label class="form-label">WebSocket 地址</label>
          <input
            v-model="conn.wsUrl"
            type="text"
            class="field-input"
            placeholder="ws://127.0.0.1:8083/mqtt 或 wss://..."
            :disabled="connected"
          />
        </div>
        <div class="form-grid form-grid-3">
          <div class="form-field">
            <label class="form-label">Client ID</label>
            <input
              v-model="conn.clientId"
              type="text"
              class="field-input"
              placeholder="可选，默认自动生成"
              :disabled="connected"
            />
          </div>
          <div class="form-field">
            <label class="form-label">用户名</label>
            <input
              v-model="conn.username"
              type="text"
              class="field-input"
              placeholder="可选"
              :disabled="connected"
            />
          </div>
          <div class="form-field">
            <label class="form-label">密码</label>
            <input
              v-model="conn.password"
              type="password"
              class="field-input"
              placeholder="可选"
              :disabled="connected"
            />
          </div>
        </div>
        <div class="form-grid form-grid-3">
          <div class="form-field">
            <label class="form-label">Keepalive (秒)</label>
            <input
              v-model.number="conn.keepalive"
              type="number"
              min="1"
              max="65535"
              class="field-input field-num"
              :disabled="connected"
            />
          </div>
          <div class="form-field form-field-check">
            <label class="form-label">Clean Session</label>
            <label class="form-check">
              <input v-model="conn.clean" type="checkbox" :disabled="connected" />
              <span>开启</span>
            </label>
          </div>
          <div class="form-field">
            <label class="form-label">连接超时 (秒)</label>
            <input
              v-model.number="conn.connectTimeoutSec"
              type="number"
              min="1"
              max="60"
              class="field-input field-num"
              :disabled="connected"
            />
          </div>
        </div>
        <div class="form-grid form-grid-3">
          <div class="form-field">
            <label class="form-label">协议版本</label>
            <select v-model.number="conn.protocolVersion" class="field-select" :disabled="connected">
              <option :value="4">MQTT 3.1.1</option>
              <option :value="5">MQTT 5</option>
            </select>
          </div>
          <div v-if="conn.protocolVersion === 5" class="form-field">
            <label class="form-label">会话过期 (秒)</label>
            <input
              v-model.number="conn.sessionExpiry"
              type="number"
              min="0"
              class="field-input field-num"
              placeholder="0=断开即过期"
              :disabled="connected"
            />
          </div>
          <div class="form-field form-field-check">
            <label class="form-label">TLS</label>
            <label class="form-check">
              <input v-model="conn.useTls" type="checkbox" :disabled="connected" />
              <span>使用 WSS</span>
            </label>
          </div>
        </div>
        <div v-if="conn.useTls" class="form-grid form-grid-3">
          <div class="form-field form-field-check">
            <label class="form-label">证书验证</label>
            <label class="form-check">
              <input v-model="conn.rejectUnauthorized" type="checkbox" :disabled="connected" />
              <span>验证服务端证书</span>
            </label>
          </div>
        </div>
        <div class="form-row form-row-actions">
          <button
            v-if="!connected && !connecting"
            class="btn btn-primary"
            @click="connect"
          >
            连接
          </button>
          <template v-else-if="connecting">
            <button class="btn btn-primary" disabled>连接中…</button>
            <button class="btn btn-ghost" @click="cancelConnect">取消连接</button>
          </template>
          <button v-else class="btn btn-ghost" @click="disconnect">断开连接</button>
          <span v-if="connected" class="status connected">已连接</span>
          <span v-else-if="connError" class="status error">{{ connError }}</span>
        </div>
      </div>
    </div>

    <!-- 订阅主题 -->
    <div class="panel">
      <div class="panel-title">订阅主题</div>
      <div class="form-section">
        <div class="form-row form-row-inline">
          <div class="form-field form-field-flex">
            <label class="form-label">主题</label>
            <input
              v-model="subTopic"
              type="text"
              class="field-input"
              placeholder="例如：home/+/state 或 home/1/state"
              :disabled="!connected"
              @keydown.enter="subscribe"
            />
          </div>
          <div class="form-field form-field-narrow">
            <label class="form-label">QoS</label>
            <select v-model.number="subQos" class="field-select" :disabled="!connected">
              <option :value="0">0</option>
              <option :value="1">1</option>
              <option :value="2">2</option>
            </select>
          </div>
          <button
            class="btn btn-primary btn-align-end"
            :disabled="!connected || !subTopic.trim()"
            @click="subscribe"
          >
            订阅
          </button>
        </div>
        <div v-if="subscriptions.length" class="sub-list">
          <div
            v-for="sub in subscriptions"
            :key="sub.topic"
            class="sub-item"
          >
            <span class="sub-topic">{{ sub.topic }}</span>
            <span class="sub-qos">QoS {{ sub.qos }}</span>
            <button
              class="btn btn-ghost btn-sm"
              :disabled="!connected"
              @click="unsubscribe(sub.topic)"
            >
              取消订阅
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 发布主题 -->
    <div class="panel">
      <div class="panel-title">发布主题</div>
      <div class="form-section">
        <div class="form-row form-row-full">
          <label class="form-label">主题</label>
          <input
            v-model="pubTopic"
            type="text"
            class="field-input"
            placeholder="例如：home/1/cmd"
            :disabled="!connected"
          />
        </div>
        <div class="form-row form-row-full">
          <label class="form-label">消息内容</label>
          <textarea
            v-model="pubPayload"
            class="field-input field-payload"
            placeholder='JSON：{"on": true} 或纯文本'
            rows="3"
            :disabled="!connected"
          />
        </div>
        <div class="form-row form-row-inline">
          <div class="form-field form-field-narrow">
            <label class="form-label">QoS</label>
            <select v-model.number="pubQos" class="field-select" :disabled="!connected">
              <option :value="0">0</option>
              <option :value="1">1</option>
              <option :value="2">2</option>
            </select>
          </div>
          <div class="form-field form-field-check">
            <label class="form-label">保留</label>
            <label class="form-check">
              <input v-model="pubRetain" type="checkbox" :disabled="!connected" />
              <span>保留消息</span>
            </label>
          </div>
          <button
            class="btn btn-primary btn-align-end"
            :disabled="!connected || !pubTopic.trim()"
            @click="publish"
          >
            发布
          </button>
        </div>
      </div>
    </div>

    <!-- 消息记录：已发布与已接收 -->
    <div class="panel messages-panel">
      <div class="panel-title">消息记录（已发布 / 已接收）</div>
      <div class="messages-toolbar">
        <button class="btn btn-ghost btn-sm" @click="clearMessages">清空</button>
      </div>
      <div ref="messagesEl" class="messages-list">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="message-line"
          :class="msg.direction"
        >
          <span class="msg-time">{{ msg.time }}</span>
          <span class="msg-dir">{{ msg.direction === "in" ? "收" : "发" }}</span>
          <span class="msg-topic">{{ msg.topic }}</span>
          <span class="msg-payload">{{ msg.payload }}</span>
        </div>
        <div v-if="!messages.length" class="messages-empty">暂无消息，连接后订阅/发布即可在此查看</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useMqttDebugStore } from "@/store/mqttDebug";

const store = useMqttDebugStore();
const {
  conn,
  connected,
  connecting,
  connError,
  subTopic,
  subQos,
  subscriptions,
  pubTopic,
  pubPayload,
  pubQos,
  pubRetain,
  messages,
} = storeToRefs(store);

const messagesEl = ref<HTMLElement | null>(null);
watch(
  () => messages.value.length,
  () => {
    nextTick(() => {
      if (messagesEl.value) {
        messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
      }
    });
  }
);

const connect = () => store.connect();
const cancelConnect = () => store.cancelConnect();
const disconnect = () => store.disconnect();
const subscribe = () => store.subscribe();
const unsubscribe = (topic: string) => store.unsubscribe(topic);
const publish = () => store.publish();
const clearMessages = () => store.clearMessages();
</script>

<style scoped>
.debug-tools {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
  min-height: 0;
  max-width: 920px;
}
.tool-desc {
  color: var(--text-muted, #6b7280);
  font-size: 0.9rem;
  margin: 0;
}
.panel {
  background: var(--panel-bg, #f9fafb);
  border: 1px solid var(--panel-border, #e5e7eb);
  border-radius: 8px;
  padding: 20px;
}
.panel-title {
  font-weight: 600;
  margin-bottom: 16px;
  font-size: 0.95rem;
}

/* 统一表单区块 */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.form-label {
  display: block;
  font-size: 0.8125rem;
  color: #4b5563;
  margin-bottom: 4px;
  font-weight: 500;
}
.form-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}
.form-row-full {
  flex-direction: column;
  align-items: stretch;
}
.form-row-full .form-label {
  margin-bottom: 4px;
}
.form-row-full .field-input {
  width: 100%;
}
.form-row-inline {
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px;
}
.form-row-actions {
  align-items: center;
  padding-top: 4px;
}
.form-grid {
  display: grid;
  gap: 4px 8px;
  align-items: end;
}
.form-grid-2 {
  grid-template-columns: repeat(2, minmax(100px, 180px));
}
.form-grid-3 {
  grid-template-columns: repeat(3, minmax(90px, 160px));
}
.form-grid-4 {
  grid-template-columns: repeat(4, minmax(80px, 140px));
}
.form-grid-5 {
  grid-template-columns: repeat(5, minmax(70px, 120px));
}
.form-grid .form-field {
  min-width: 0;
}
.form-grid .field-input.field-num,
.form-grid .field-select {
  max-width: 100%;
}
.form-grid .form-field .field-input.field-num {
  max-width: 72px;
}
.form-grid .form-field .field-select {
  max-width: 130px;
}
@media (max-width: 720px) {
  .form-grid-2,
  .form-grid-3 { grid-template-columns: 1fr; }
  .form-grid-4,
  .form-grid-5 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
.form-field {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.form-field-flex {
  flex: 1;
  min-width: 120px;
}
.form-field-narrow {
  width: 88px;
  flex-shrink: 0;
}
.form-field-check .form-check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.875rem;
  font-weight: normal;
  color: #374151;
  cursor: pointer;
  margin-top: 6px;
}
.form-field-check .form-check input {
  margin: 0;
}
.field-input,
.field-select {
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  background: #fff;
}
.field-input:disabled,
.field-select:disabled {
  background: #f3f4f6;
  color: #9ca3af;
}
.field-input.field-num {
  width: 100%;
  max-width: 100px;
}
.field-input.field-payload {
  width: 100%;
  resize: vertical;
  font-family: ui-monospace, monospace;
  font-size: 0.8125rem;
  min-height: 72px;
}
.btn-align-end {
  align-self: flex-end;
}
.status {
  font-size: 0.875rem;
  margin-left: 8px;
}
.status.connected {
  color: #059669;
}
.status.error {
  color: #dc2626;
}

/* 订阅列表 */
.sub-list {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.sub-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 0.875rem;
}
.sub-topic {
  font-family: ui-monospace, monospace;
  word-break: break-all;
  flex: 1;
  min-width: 0;
}
.sub-qos {
  color: #6b7280;
  font-size: 0.8rem;
  flex-shrink: 0;
}

/* 消息记录 */
.messages-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 280px;
}
.messages-toolbar {
  margin-bottom: 8px;
}
.messages-list {
  flex: 1;
  min-height: 220px;
  max-height: 400px;
  overflow-y: auto;
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 6px;
  padding: 12px;
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
}
.message-line {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  padding: 4px 0;
  border-bottom: 1px solid #334155;
  align-items: baseline;
}
.message-line:last-child {
  border-bottom: none;
}
.message-line.in .msg-dir {
  color: #34d399;
}
.message-line.out .msg-dir {
  color: #60a5fa;
}
.msg-time {
  color: #94a3b8;
  flex-shrink: 0;
}
.msg-dir {
  font-weight: 600;
  width: 20px;
}
.msg-topic {
  color: #c4b5fd;
  word-break: break-all;
}
.msg-payload {
  color: #e2e8f0;
  word-break: break-all;
  flex: 1;
  min-width: 0;
}
.messages-empty {
  color: #64748b;
  padding: 24px;
  text-align: center;
}
.btn-sm {
  padding: 4px 10px;
  font-size: 0.8rem;
}
</style>
