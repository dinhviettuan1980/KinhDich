"""Kênh nhận lệnh / gửi ACK, status. MQTT trên thiết bị thật; InMemory cho test tích hợp."""
import json
import logging
import ssl
from collections.abc import Callable

log = logging.getLogger("ld_agent.transport")


class Transport:
    def start(self, on_cmd: Callable[[dict], None]) -> None: ...
    def connected(self) -> bool: ...
    def publish_ack(self, payload: dict, on_done: Callable[[], None]) -> bool: ...
    def publish_status(self, payload: dict) -> None: ...
    def stop(self) -> None: ...


class MqttTransport(Transport):
    def __init__(self, cfg):
        import paho.mqtt.client as mqtt
        self.mqtt = mqtt
        self.cfg = cfg
        self.base = f"ld/{cfg.device_id}"
        # Phiên bền (clean_session=False) + QoS 1: broker giữ lệnh khi Pi mất mạng, giao bù khi kết nối lại.
        self.c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cfg.device_id, clean_session=False)
        self.c.username_pw_set(cfg.device_id, cfg.device_token)
        if cfg.mqtt_tls:
            self.c.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        self.c.will_set(f"{self.base}/status", json.dumps({"online": False}), qos=1, retain=True)
        self.c.reconnect_delay_set(1, 60)
        self.c.on_connect = self._on_connect
        self.c.on_disconnect = lambda *a: log.warning("Mất kết nối MQTT")
        self.c.on_message = self._on_message
        self.c.on_publish = self._on_publish
        self._ok = False
        self._inflight: dict[int, Callable[[], None]] = {}
        self.on_cmd = None

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        self._ok = not reason_code.is_failure
        log.info("MQTT kết nối: %s", reason_code)
        if self._ok:
            client.subscribe(f"{self.base}/cmd", qos=1)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload or b"{}")
        except ValueError:
            log.error("Lệnh không phải JSON")
            return
        if self.on_cmd and isinstance(payload, dict):
            self.on_cmd(payload)

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        cb = self._inflight.pop(mid, None)
        if cb:
            cb()

    def start(self, on_cmd):
        self.on_cmd = on_cmd
        self.c.connect_async(self.cfg.mqtt_host, self.cfg.mqtt_port, keepalive=30)
        self.c.loop_start()

    def connected(self):
        return self._ok and self.c.is_connected()

    def publish_ack(self, payload, on_done):
        info = self.c.publish(f"{self.base}/ack", json.dumps(payload), qos=1)
        if info.rc != self.mqtt.MQTT_ERR_SUCCESS:
            return False
        self._inflight[info.mid] = on_done
        return True

    def publish_status(self, payload):
        self.c.publish(f"{self.base}/status", json.dumps(payload), qos=1, retain=True)

    def stop(self):
        self.publish_status({"online": False})
        self.c.loop_stop()
        self.c.disconnect()


class InMemoryTransport(Transport):
    """Nối agent với InMemoryDeviceBus của server (test tích hợp không cần broker)."""

    def __init__(self, bus, device_id: str):
        self.bus, self.device_id, self.online = bus, device_id, True

    def start(self, on_cmd):
        self.bus.attach_device(self.device_id, lambda p: on_cmd(p) if self.online else None)

    def connected(self):
        return self.online

    def publish_ack(self, payload, on_done):
        if not self.online:
            return False
        self.bus.device_publish(self.device_id, "ack", payload)
        on_done()
        return True

    def publish_status(self, payload):
        if self.online:
            self.bus.device_publish(self.device_id, "status", payload)
