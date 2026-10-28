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
from .recorder import Recorder
from .transport import MqttTransport


def build(cfg: Config) -> Agent:
    if cfg.simulate:
        player, camera = SimPlayer(cfg.simulate_play_seconds), Camera("simulate")
    else:
        player = ProcessPlayer(cfg.player, cfg.audio_device)
        camera = Camera(cfg.camera, cfg.camera_device, cfg.photo_width, cfg.photo_height, cfg.jpeg_quality)
    recorder = Recorder(camera.kind, cfg.camera_device, cfg.audio_in, cfg.video_size, cfg.video_fps, cfg.record_max_seconds,
                        audio_out=cfg.audio_device)
    return Agent(cfg, MqttTransport(cfg), httpx.Client(follow_redirects=True), player, camera, recorder=recorder)


def hardware_test(cfg: Config, args) -> int:
    """Kiểm tra phần cứng khi lắp đặt (không cần server)."""
    import subprocess
    import tempfile
    if args.test_camera:
        cam = Camera(cfg.camera, cfg.camera_device, cfg.photo_width, cfg.photo_height, cfg.jpeg_quality)
        ok = cam.capture(args.test_camera, "test")
        logging.info("Chụp ảnh (%s): %s", cfg.camera, f"OK → {args.test_camera}" if ok else "LỖI")
        if not ok:
            return 1
    if args.test_video:
        rec = Recorder(cfg.camera, cfg.camera_device, cfg.audio_in, cfg.video_size, cfg.video_fps, 10,
                       audio_out=cfg.audio_device)
        if not rec.uses_camera:
            logging.error("Quay video cần LD_CAMERA=fswebcam hoặc ffmpeg (webcam USB)")
            return 1
        logging.info("Quay thử 10 giây — webcam %s, micro '%s'", cfg.camera_device, rec.audio_in or "KHÔNG THẤY")
        ok = rec.start(args.test_video) and rec.finish(timeout=40) is not None
        logging.info("Quay video: %s", f"OK → {args.test_video}" if ok else "LỖI")
        if not ok:
            return 1
    if args.test_speaker:
        tone = Path(tempfile.gettempdir()) / "ld-test-tone.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=660:duration=3", str(tone)],
                       check=True)
        player = ProcessPlayer(cfg.player, cfg.audio_device)
        vol = min(cfg.volume_default, cfg.volume_max)
        logging.info("Phát âm thử bằng %s, âm lượng %s, thiết bị '%s'", cfg.player, vol, cfg.audio_device or "mặc định")
        player.start(tone, vol, time.time())
        while player.is_playing(time.time()):
            time.sleep(0.2)
        err = player.result()
        logging.info("Loa: %s", err or "OK")
        if err:
            return 1
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ld_agent", description="Linh Địa Việt – agent Raspberry Pi")
    ap.add_argument("--env", type=Path, default=None, help="file cấu hình .env")
    ap.add_argument("--simulate", action="store_true", help="không cần loa/camera thật: chỉ in log, tạo ảnh giả")
    ap.add_argument("--test-speaker", action="store_true", help="phát âm thử 3 giây qua loa rồi thoát")
    ap.add_argument("--test-camera", type=Path, metavar="FILE.jpg", help="chụp 1 ảnh ra file rồi thoát")
    ap.add_argument("--test-video", type=Path, metavar="FILE.mp4", help="quay 10 giây video + tiếng micro rồi thoát")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = Config.load(args.env, simulate=True if args.simulate else None)
    if args.test_speaker or args.test_camera or args.test_video:
        return hardware_test(cfg, args)
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
