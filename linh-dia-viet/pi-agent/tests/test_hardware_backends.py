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


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="cần ffmpeg")
def test_simulated_recorder_makes_mp4_with_sound(tmp_path):
    import json
    import subprocess
    from ld_agent.camera import Camera
    from ld_agent.recorder import Recorder, grab_frame
    audio, still, out = tmp_path / "a.mp3", tmp_path / "s.jpg", tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", str(audio)], check=True)
    assert Camera("simulate").capture(still, "video", {"items": [{"name": "Hương", "unit": "bó", "qty": 1}]})
    rec = Recorder("simulate")
    assert rec.enabled and not rec.uses_camera
    assert rec.start(out, audio=audio, still=still)
    assert rec.finish() == out
    probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(out)],
                                      capture_output=True, check=True).stdout)
    assert {s["codec_type"] for s in probe["streams"]} == {"video", "audio"}
    assert grab_frame(out, tmp_path / "f.jpg", at_s=1)


def test_mic_picks_webcam_not_output_sound_card(tmp_path):
    """Card âm thanh USB (phát loa) cũng có lỗ micro → phải chọn micro của webcam."""
    from ld_agent.recorder import card_of, find_usb_mic
    a = tmp_path / "asound"
    (a / "cards").parent.mkdir()
    (a / "cards").write_text(
        " 0 [vc4hdmi        ]: vc4-hdmi - vc4-hdmi\n                      vc4-hdmi\n"
        " 1 [Device         ]: USB-Audio - USB Audio Device\n                      GeneralPlus USB Audio Device\n"
        " 2 [Camera         ]: USB-Audio - HD Web Camera\n                      Sonix HD Web Camera\n")
    for card in ("Device", "Camera"):
        (a / card).mkdir()
        (a / card / "pcm0c").mkdir()
    assert card_of("alsa/plughw:CARD=Device,DEV=0") == "Device"
    assert find_usb_mic(exclude="Device", asound=a) == "plughw:CARD=Camera,DEV=0"
    assert find_usb_mic(asound=a) == "plughw:CARD=Camera,DEV=0"  # ưu tiên tên có "camera"
    (a / "Camera" / "pcm0c").rmdir()
    assert find_usb_mic(exclude="Device", asound=a) == ""  # webcam không có micro → không lấy nhầm card loa
