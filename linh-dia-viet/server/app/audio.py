"""Xử lý âm thanh bằng ffmpeg: kiểm tra định dạng thật, chuẩn hoá loudnorm, MP3 mono 44.1kHz."""
import json
import subprocess
import tempfile
from pathlib import Path

from .config import get_settings


class AudioError(ValueError):
    pass


# Chữ ký đầu file của các định dạng ghi âm chấp nhận (không tin đuôi file / content-type).
def sniff_audio(head: bytes) -> str | None:
    if head.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    if head.startswith(b"OggS"):
        return "ogg"
    if head[4:8] == b"ftyp":
        return "mp4"
    if head.startswith(b"RIFF") and head[8:12] == b"WAVE":
        return "wav"
    if head.startswith(b"ID3") or (len(head) > 1 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
        return "mp3"
    return None


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        raise AudioError("File không phải âm thanh hợp lệ")
    info = json.loads(r.stdout or "{}")
    streams = info.get("streams", [])
    if not any(s.get("codec_type") == "audio" for s in streams):
        raise AudioError("File không có kênh âm thanh")
    if any(s.get("codec_type") == "video" and s.get("disposition", {}).get("attached_pic") != 1 for s in streams):
        raise AudioError("Chỉ nhận file âm thanh")
    return info


def duration_of(path: Path) -> float:
    try:
        return float(probe(path)["format"]["duration"])
    except (KeyError, ValueError):
        # webm từ MediaRecorder thường thiếu duration trong header → giải mã ra wav để đo.
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.wav"
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(path), "-ac", "1", "-ar", "8000", str(out)],
                               capture_output=True, timeout=120)
            if r.returncode != 0:
                raise AudioError("Không đọc được file âm thanh")
            return float(probe(out)["format"]["duration"])


def normalize_to_mp3(src: Path, dst: Path, max_seconds: int | None = None) -> float:
    """Chuẩn hoá âm lượng (EBU R128), MP3 mono 44.1kHz. Trả về thời lượng (giây)."""
    max_seconds = max_seconds or get_settings().max_audio_seconds
    probe(src)
    dur = duration_of(src)
    if dur > max_seconds + 1:
        raise AudioError(f"Bài khấn dài quá {max_seconds // 60} phút")
    if dur < 1:
        raise AudioError("Bản ghi quá ngắn")
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vn", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "128k", "-t", str(max_seconds), str(dst)],
        capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise AudioError("Không chuyển đổi được âm thanh")
    return float(probe(dst)["format"]["duration"])


def concat_mp3(parts: list[Path], dst: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in parts:
            f.write(f"file '{p.resolve()}'\n")
        lst = f.name
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", str(dst)],
                   check=True, timeout=120)
    Path(lst).unlink(missing_ok=True)


def sine(dst: Path, seconds: float, freq: int = 440) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={seconds}",
                    "-ac", "1", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "64k", str(dst)], check=True, timeout=60)
