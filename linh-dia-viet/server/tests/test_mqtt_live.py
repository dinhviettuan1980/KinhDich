"""Kiểm tra với Mosquitto thật (docker compose). Chạy: MQTT_TEST_HOST=localhost MQTT_TEST_PASSWORD=...
MQTT_TEST_DEVICE_TOKEN=... pytest -m mqtt"""
import os
import time

import pytest

from app.device_bus import MqttDeviceBus
from ld_agent.config import Config
from ld_agent.transport import MqttTransport

HOST = os.environ.get("MQTT_TEST_HOST")
pytestmark = [pytest.mark.mqtt, pytest.mark.skipif(not HOST, reason="cần MQTT_TEST_HOST")]


def wait(cond, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


def test_cmd_ack_status_and_acl():
    dev_id = os.environ.get("MQTT_TEST_DEVICE_ID", "pi-demo-01")
    got = []
    bus = MqttDeviceBus(HOST, 1883, "ld-server", os.environ["MQTT_TEST_PASSWORD"], client_id="ld-server-test")
    bus.start(lambda d, k, p: got.append((d, k, p)))
    cmds = []
    tr = MqttTransport(Config(device_id=dev_id, device_token=os.environ["MQTT_TEST_DEVICE_TOKEN"], mqtt_host=HOST))
    tr.start(cmds.append)
    try:
        assert wait(lambda: tr.connected() and bus.client.is_connected())
        time.sleep(0.5)
        assert bus.send(dev_id, {"type": "test_tone"})
        assert wait(lambda: cmds == [{"type": "test_tone"}])
        done = []
        assert tr.publish_ack({"job_id": "x", "state": "received"}, lambda: done.append(1))
        tr.publish_status({"online": True, "net": "wifi"})
        assert wait(lambda: (dev_id, "ack", {"job_id": "x", "state": "received"}) in got and done)
        assert wait(lambda: any(k == "status" and d == dev_id for d, k, _ in got))
        # ACL: thiết bị không được giả danh thiết bị khác
        tr.c.publish("ld/pi-khac/ack", '{"job_id":"y","state":"done"}', qos=1)
        time.sleep(1)
        assert not any(d == "pi-khac" for d, _, _ in got)
    finally:
        tr.stop()
        bus.stop()
    # LWT/retained: trạng thái offline cuối cùng được giữ lại
