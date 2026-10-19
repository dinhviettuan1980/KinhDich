"""Chạy agent: python -m ld_agent [--simulate] [--env /etc/linh-dia-viet/agent.env]"""
import argparse
import logging
import signal
import sys
import time
from pathlib import Path

import httpx

from .agent import Agent
from .camera import Camera
from .config import Config
from .player import ProcessPlayer, SimPlayer
from .transport import MqttTransport


def build(cfg: Config) -> Agent:
    if cfg.simulate:
        player, camera = SimPlayer(cfg.simulate_play_seconds), Camera("simulate")
    else:
        player = ProcessPlayer(cfg.player, cfg.audio_device)
        camera = Camera(cfg.camera, cfg.camera_device, cfg.photo_width, cfg.photo_height, cfg.jpeg_quality)
    return Agent(cfg, MqttTransport(cfg), httpx.Client(follow_redirects=True), player, camera)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ld_agent", description="Linh Địa Việt – agent Raspberry Pi")
    ap.add_argument("--env", type=Path, default=None, help="file cấu hình .env")
    ap.add_argument("--simulate", action="store_true", help="không cần loa/camera thật: chỉ in log, tạo ảnh giả")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = Config.load(args.env, simulate=True if args.simulate else None)
    if not cfg.device_token:
        logging.error("Thiếu LD_DEVICE_TOKEN")
        return 2
    agent = build(cfg)
    stopping = False

    def _stop(*_):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)
    agent.start()
    logging.info("Agent %s chạy (%s), server %s", cfg.device_id, "giả lập" if cfg.simulate else "thật", cfg.server_url)
    while not stopping:
        try:
            agent.tick()
        except Exception:
            logging.exception("Lỗi trong vòng lặp")
        time.sleep(0.5)
    agent.player.stop()
    agent.transport.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
