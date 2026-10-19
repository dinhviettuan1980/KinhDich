"""Kiểm tra lớp gọi phần cứng bằng chương trình giả trong PATH (không cần Pi thật)."""
import os
import shutil
import stat
import time

import pytest

from ld_agent.camera import Camera
from ld_agent.player import ProcessPlayer


def fake_bin(tmp_path, name, body):
    p = tmp_path / "bin" / name
    p.parent.mkdir(exist_ok=True)
    p.write_text("#!/bin/sh\n" + body)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return p.parent


@pytest.mark.parametrize("kind,binary", [("rpicam", "rpicam-still"), ("fswebcam", "fswebcam")])
def test_camera_backends(tmp_path, monkeypatch, kind, binary):
    src = tmp_path / "src.jpg"
    Camera("simulate").capture(src)
    # chương trình giả: chép ảnh mẫu vào đối số cuối (rpicam dùng -o FILE ở cuối, fswebcam FILE ở cuối)
    bindir = fake_bin(tmp_path, binary, f'for a; do last="$a"; done; cp "{src}" "$last"\necho "$@" > "{tmp_path}/args"\n')
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    dst = tmp_path / "out" / "a.jpg"
    assert Camera(kind, width=800, height=600, quality=70).capture(dst)
    assert dst.read_bytes() == src.read_bytes()
    args = (tmp_path / "args").read_text()
    assert "800" in args and "600" in args


def test_camera_failure_returns_false(tmp_path, monkeypatch):
    bindir = fake_bin(tmp_path, "rpicam-still", "exit 1\n")
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    assert not Camera("rpicam").capture(tmp_path / "a.jpg")
    assert not Camera("none").capture(tmp_path / "b.jpg")


def test_mpv_command_has_volume_and_device(tmp_path, monkeypatch):
    bindir = fake_bin(tmp_path, "mpv", f'echo "$@" > "{tmp_path}/args"\n')
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    p = ProcessPlayer("mpv", "alsa/plughw:1,0")
    p.start(tmp_path / "x.mp3", 42, time.time())
    while p.is_playing(time.time()):
        time.sleep(0.05)
    assert p.result() is None
    args = (tmp_path / "args").read_text()
    assert "--volume=42" in args and "--audio-device=alsa/plughw:1,0" in args and "--no-video" in args


def test_player_error_reported(tmp_path, monkeypatch):
    bindir = fake_bin(tmp_path, "mpv", 'echo "no audio device" >&2; exit 2\n')
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    p = ProcessPlayer("mpv")
    p.start(tmp_path / "x.mp3", 50, time.time())
    while p.is_playing(time.time()):
        time.sleep(0.05)
    assert "no audio device" in p.result()


def test_stop_kills_player(tmp_path, monkeypatch):
    bindir = fake_bin(tmp_path, "mpv", "sleep 30\n")
    monkeypatch.setenv("PATH", f"{bindir}:{os.environ['PATH']}")
    p = ProcessPlayer("mpv")
    p.start(tmp_path / "x.mp3", 50, time.time())
    assert p.is_playing(time.time())
    p.stop()
    assert not p.is_playing(time.time())


@pytest.mark.skipif(not shutil.which("ffplay"), reason="không có ffplay")
def test_real_ffplay_plays_short_file(tmp_path):
    import subprocess
    f = tmp_path / "t.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=0.5", str(f)], check=True)
    p = ProcessPlayer("ffplay")
    p.start(f, 0, time.time())  # âm lượng 0: không làm ồn khi chạy test
    end = time.time() + 15
    while p.is_playing(time.time()) and time.time() < end:
        time.sleep(0.1)
    p.stop()
    assert p.result() is None
