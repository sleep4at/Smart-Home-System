# MQTT LWT（Last Will Testament）格式说明

## 主题格式

设备需要发布 LWT 消息到以下主题：

```
{TOPIC_PREFIX}/{device_id}/lwt
```

其中：
- `{TOPIC_PREFIX}` 默认为 `home`（可在 Django settings 的 `MQTT_CONFIG.TOPIC_PREFIX` 中配置）
- `{device_id}` 为设备的数据库 ID（整数）

**示例：**
- 设备 ID 为 1：`home/1/lwt`
- 设备 ID 为 5：`home/5/lwt`

## Payload 格式

LWT 消息的 payload 可以是以下任意格式：

### 字符串格式（推荐）

- **离线**：`"offline"` 或 `"0"` 或 `"false"`（不区分大小写）
- **在线**：`"online"` 或 `"1"` 或 `"true"` 或其他任何字符串

### JSON 格式（可选）

```json
"offline"
```
或
```json
"online"
```

## 工作原理

1. **设备连接 MQTT Broker 时**：
   - 设备应设置自己的 LWT 主题为 `home/{device_id}/lwt`，payload 为 `"offline"`
   - 当设备异常断开连接时，Broker 会自动发布 LWT 消息，通知网关设备已离线

2. **设备正常上线时**：
   - 设备应主动发布一条 `home/{device_id}/lwt` 消息，payload 为 `"online"`，表示设备已连接

3. **网关处理逻辑**：
   - 收到 `home/{device_id}/lwt` 主题的消息时
   - 如果 payload 为 `"offline"`、`"0"` 或 `"false"`（不区分大小写），则将设备 `is_online` 设为 `False`
   - 否则设为 `True`
   - 同时记录一条系统日志（`MQTT_LWT` 来源）

## 示例代码（Python paho-mqtt）

```python
import paho.mqtt.client as mqtt

device_id = 1
topic_prefix = "home"
lwt_topic = f"{topic_prefix}/{device_id}/lwt"

client = mqtt.Client()
# 设置 LWT：当异常断开时，Broker 会发布 "offline" 消息
client.will_set(lwt_topic, "offline", qos=1, retain=False)

client.connect("broker_host", 1883, 60)
client.loop_start()

# 设备上线时，主动发布在线消息
client.publish(lwt_topic, "online", qos=1, retain=False)
```

## 注意事项

- LWT 消息的 QoS 建议设为 1，确保消息至少送达一次
- 设备正常断开连接时，Broker 不会触发 LWT
- 只有异常断开（网络中断、进程崩溃等）才会触发 LWT
- 设备正常上线时，建议主动发布一条 `"online"` 消息，确保状态同步
