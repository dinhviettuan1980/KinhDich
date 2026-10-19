"""Kênh giao tiếp server ↔ thiết bị. Mặc định MQTT; bọc sau interface DeviceBus để đổi sang WebSocket sau này.

Topic:
  ld/{device_id}/cmd     server → Pi, QoS 1 (Pi dùng phiên bền nên nhận bù khi online lại)
  ld/{device_id}/ack     Pi → server
  ld/{device_id}/status  Pi → server, retained + LWT {"online": false}
"""
import json
import logging
import queue
import ssl
import threading
from collections.abc import Callable
from typing import Protocol

log = logging.getLogger("linhdia.bus")

# handler(device_id, kind, payload) với kind ∈ {"ack", "status"}
Handler = Callable[[str, str, dict], None]


class DeviceBus(Protocol):
    def start(self, handler: Handler) -> None: ...
    def stop(self) -> None: ...
    def send(self, device_id: str, payload: dict) -> bool: ...


def parse_topic(topic: str) -> tuple[str, str] | None:
    parts = topic.split("/")
    if len(parts) == 3 and parts[0] == "ld" and parts[2] in ("ack", "status", "cmd"):
        return parts[1], parts[2]
    return None


class MqttDeviceBus:
    def __init__(self, host: str, port: int, username: str, password: str, tls: bool = False,
                 client_id: str = "ld-server"):
        import paho.mqtt.client as mqtt
        self._mqtt = mqtt
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=False)
        if username:
            self.client.username_pw_set(username, password)
        if tls:
            self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        self.host, self.port = host, port
        self.handler: Handler | None = None
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.reconnect_delay_set(1, 30)
        # Xử lý message trên luồng riêng để không chặn vòng lặp mạng của paho.
        self._q: queue.Queue = queue.Queue()
        self._worker = threading.Thread(target=self._work, daemon=True, name="mqtt-handler")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        log.info("MQTT đã kết nối (%s)", reason_code)
        client.subscribe([("ld/+/ack", 1), ("ld/+/status", 1)])

    def _on_message(self, client, userdata, msg):
        self._q.put((msg.topic, msg.payload))

    def _work(self):
        while True:
            item = self._q.get()
            if item is None:
                return
            topic, raw = item
            parsed = parse_topic(topic)
            if not parsed or not self.handler:
                continue
            try:
                payload = json.loads(raw or b"{}")
                if isinstance(payload, dict):
                    self.handler(parsed[0], parsed[1], payload)
            except Exception:
                log.exception("Lỗi xử lý message %s", topic)

    def start(self, handler: Handler) -> None:
        self.handler = handler
        self._worker.start()
        self.client.connect_async(self.host, self.port, keepalive=30)
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()
        self._q.put(None)

    def send(self, device_id: str, payload: dict) -> bool:
        info = self.client.publish(f"ld/{device_id}/cmd", json.dumps(payload), qos=1)
        return info.rc == self._mqtt.MQTT_ERR_SUCCESS


class InMemoryDeviceBus:
    """Dùng cho test và chạy thử không broker: message được xếp hàng, gọi pump() để chuyển đi."""

    def __init__(self):
        self.handler: Handler | None = None
        self.devices: dict[str, Callable[[dict], None]] = {}  # device_id → hàm nhận lệnh
        self.sent: list[tuple[str, dict]] = []
        self._to_device: list[tuple[str, dict]] = []
        self._to_server: list[tuple[str, str, dict]] = []
        self.retained_status: dict[str, dict] = {}

    def start(self, handler: Handler) -> None:
        self.handler = handler

    def stop(self) -> None:
        pass

    def send(self, device_id: str, payload: dict) -> bool:
        self.sent.append((device_id, payload))
        self._to_device.append((device_id, payload))
        return True

    # phía thiết bị
    def attach_device(self, device_id: str, on_cmd: Callable[[dict], None]) -> None:
        self.devices[device_id] = on_cmd

    def device_publish(self, device_id: str, kind: str, payload: dict) -> None:
        if kind == "status":
            self.retained_status[device_id] = payload
        self._to_server.append((device_id, kind, payload))

    def pump(self) -> int:
        n = 0
        while self._to_device or self._to_server:
            while self._to_device:
                device_id, payload = self._to_device.pop(0)
                if device_id in self.devices:  # thiết bị chưa kết nối: lệnh mất (khác MQTT phiên bền)
                    self.devices[device_id](payload)
                n += 1
            while self._to_server:
                device_id, kind, payload = self._to_server.pop(0)
                if self.handler:
                    self.handler(device_id, kind, payload)
                n += 1
        return n


_bus: DeviceBus | None = None


def get_bus() -> DeviceBus:
    global _bus
    if _bus is None:
        from .config import get_settings
        s = get_settings()
        if s.device_bus == "mqtt":
            _bus = MqttDeviceBus(s.mqtt_host, s.mqtt_port, s.mqtt_username, s.mqtt_password, s.mqtt_tls)
        else:
            _bus = InMemoryDeviceBus()
    return _bus


def set_bus(bus: DeviceBus | None) -> None:
    global _bus
    _bus = bus
