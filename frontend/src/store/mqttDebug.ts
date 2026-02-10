/**
 * 调试工具 MQTT WebSocket 状态：跨路由保持连接与会话，仅在手点「断开连接」或关闭页面时断开。
 */
import { defineStore } from "pinia";
import mqtt, { type IClientOptions, type MqttClient } from "mqtt";

export type QoS = 0 | 1 | 2;

export interface LogMessage {
  direction: "in" | "out";
  topic: string;
  payload: string;
  time: string;
}

const defaultConn = () => ({
  wsUrl: (import.meta.env.VITE_MQTT_WS_URL || "ws://127.0.0.1:8083/mqtt").trim(),
  clientId: "",
  username: "",
  password: "",
  keepalive: 60,
  clean: true,
  protocolVersion: 4 as 4 | 5,
  sessionExpiry: 0,
  useTls: false,
  rejectUnauthorized: true,
  connectTimeoutSec: 10,
});

let client: MqttClient | null = null;
let connectTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
let beforeUnloadHandler: (() => void) | null = null;

function formatTime() {
  const d = new Date();
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  const ms = String(d.getMilliseconds()).padStart(3, "0");
  return `${h}:${m}:${s}.${ms}`;
}

export const useMqttDebugStore = defineStore("mqttDebug", {
  state: () => ({
    conn: defaultConn(),
    connected: false,
    connecting: false,
    connError: "",
    subTopic: "",
    subQos: 1 as QoS,
    subscriptions: [] as { topic: string; qos: QoS }[],
    pubTopic: "",
    pubPayload: "",
    pubQos: 0 as QoS,
    pubRetain: false,
    messages: [] as LogMessage[],
  }),
  actions: {
    addMessage(direction: "in" | "out", topic: string, payload: string) {
      this.messages.push({
        direction,
        topic,
        payload,
        time: formatTime(),
      });
      if (this.messages.length > 500) {
        this.messages = this.messages.slice(-400);
      }
    },
    clearMessages() {
      this.messages = [];
    },
    clearConnectTimeout() {
      if (connectTimeoutTimer != null) {
        clearTimeout(connectTimeoutTimer);
        connectTimeoutTimer = null;
      }
    },
    connect() {
      if (this.connecting || this.connected) return;
      this.connError = "";
      this.connecting = true;
      this.clearConnectTimeout();
      let url = this.conn.wsUrl.trim();
      if (!url) {
        this.connError = "请输入 WebSocket 地址";
        this.connecting = false;
        return;
      }
      if (this.conn.useTls && url.startsWith("ws://")) {
        url = "wss://" + url.slice(5);
      }
      const timeoutSec = Math.max(
        1,
        Math.min(60, Number(this.conn.connectTimeoutSec) || 10)
      );
      const options: IClientOptions = {
        clean: this.conn.clean,
        connectTimeout: timeoutSec * 1000,
        reconnectPeriod: 0,
        keepalive: Math.max(
          1,
          Math.min(65535, Number(this.conn.keepalive) || 60)
        ),
        protocolVersion: this.conn.protocolVersion === 5 ? 5 : 4,
      };
      if (this.conn.clientId.trim()) options.clientId = this.conn.clientId.trim();
      if (this.conn.username.trim()) options.username = this.conn.username.trim();
      if (this.conn.password) options.password = this.conn.password;
      if (this.conn.useTls) options.rejectUnauthorized = this.conn.rejectUnauthorized;
      if (
        this.conn.protocolVersion === 5 &&
        this.conn.sessionExpiry != null &&
        this.conn.sessionExpiry > 0
      ) {
        options.properties = { sessionExpiryInterval: this.conn.sessionExpiry };
      }

      const store = this;
      try {
        client = mqtt.connect(url, options);
        connectTimeoutTimer = setTimeout(() => {
          if (!store.connected && store.connecting && client) {
            connectTimeoutTimer = null;
            store.connError = "连接超时，请检查地址与网络后重试";
            store.connecting = false;
            try {
              client.end(true);
            } catch (_) {}
            client = null;
          }
        }, timeoutSec * 1000);

        client.on("connect", () => {
          store.clearConnectTimeout();
          store.connected = true;
          store.connecting = false;
          store.connError = "";
        });
        client.on("error", (err: Error) => {
          store.clearConnectTimeout();
          store.connError = err?.message || String(err);
          store.connecting = false;
        });
        client.on("close", () => {
          store.clearConnectTimeout();
          store.connected = false;
          client = null;
          store._removeBeforeUnload();
        });
        client.on("message", (topic: string, payload: Buffer) => {
          store.addMessage("in", topic, payload.toString());
        });

        this._addBeforeUnload();
      } catch (e) {
        this.clearConnectTimeout();
        this.connError = e instanceof Error ? e.message : String(e);
        this.connecting = false;
      }
    },
    _addBeforeUnload() {
      if (beforeUnloadHandler) return;
      beforeUnloadHandler = () => {
        if (client) {
          try {
            client.end(true);
          } catch (_) {}
          client = null;
        }
      };
      window.addEventListener("beforeunload", beforeUnloadHandler);
    },
    _removeBeforeUnload() {
      if (beforeUnloadHandler) {
        window.removeEventListener("beforeunload", beforeUnloadHandler);
        beforeUnloadHandler = null;
      }
    },
    /** 连接过程中取消，可重新修改参数再连 */
    cancelConnect() {
      this.clearConnectTimeout();
      if (client) {
        try {
          client.end(true);
        } catch (_) {}
        client = null;
      }
      this.connecting = false;
      this.connError = "已取消连接";
    },
    disconnect() {
      this.clearConnectTimeout();
      this._removeBeforeUnload();
      if (client) {
        client.end(true);
        client = null;
      }
      this.connected = false;
      this.subscriptions = [];
      this.connError = "";
    },
    subscribe() {
      const topic = this.subTopic.trim();
      if (!client || !topic) return;
      if (this.subscriptions.some((s) => s.topic === topic)) return;
      const qos = this.subQos;
      client.subscribe(topic, { qos }, (err) => {
        if (!err) {
          this.subscriptions = [...this.subscriptions, { topic, qos }];
        }
      });
      this.subTopic = "";
    },
    unsubscribe(topic: string) {
      if (!client) return;
      client.unsubscribe(topic, () => {
        this.subscriptions = this.subscriptions.filter((s) => s.topic !== topic);
      });
    },
    publish() {
      const topic = this.pubTopic.trim();
      if (!client || !topic) return;
      client.publish(
        topic,
        this.pubPayload,
        { qos: this.pubQos, retain: this.pubRetain },
        (err) => {
          if (!err) {
            this.addMessage("out", topic, this.pubPayload);
          }
        }
      );
    },
  },
});
