"""Clip xem lại của một lễ: ảnh mâm (trước lễ → lúc khấn → sau lễ) ghép với bài khấn đã phát, ra MP4.
Tạo khi khách mở xem lần đầu rồi lưu lại. Khi có camera quay video thật, thay bằng clip thiết bị gửi lên."""
import logging
import subprocess
import tempfile
from pathlib import Path

from .audio import duration_of
from .models import Order
from .storage import get_storage

log = logging.getLogger("linhdia.clips")

INTRO_S, OUTRO_S = 3.0, 4.0
SIZE = (1280, 960)


def audio_key_of(order: Order) -> str | None:
    return order.audio_key or (order.prayer.audio_key if order.prayer.kind == "recorded" else None)


def can_build(order: Order) -> bool:
    return order.status == "completed" and bool(order.photos) and bool(audio_key_of(order))


def build(order: Order) -> str:
    """Tạo clip, trả về storage key. Ảnh thiếu pha nào thì dùng ảnh gần nhất."""
    st = get_storage()
    photos = {e.note: st.local_path(e.path) for e in order.evidence if e.kind == "photo"}
    order_ = [p for p in ("before", "start", "after") if p in photos] or list(photos)
    first, mid, last = photos[order_[0]], photos.get("start", photos[order_[len(order_) // 2]]), photos[order_[-1]]
    audio = st.local_path(audio_key_of(order))
    speech = max(1.0, duration_of(audio))
    w, h = SIZE
    fit = f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=5"
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "clip.mp4"
        cmd = ["ffmpeg", "-v", "error", "-y",
               "-loop", "1", "-t", str(INTRO_S), "-i", str(first),
               "-loop", "1", "-t", f"{speech:.2f}", "-i", str(mid),
               "-loop", "1", "-t", str(OUTRO_S), "-i", str(last),
               "-i", str(audio),
               "-filter_complex",
               f"[0:v]{fit}[a];[1:v]{fit}[b];[2:v]{fit}[c];[a][b][c]concat=n=3:v=1:a=0,format=yuv420p[v];"
               f"[3:a]adelay={int(INTRO_S * 1000)}:all=1,apad[s]",
               "-map", "[v]", "-map", "[s]", "-t", f"{INTRO_S + speech + OUTRO_S:.2f}",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-tune", "stillimage",
               "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True, timeout=180, capture_output=True)
        return st.put_file(out, f"clips/{order.id}.mp4")
