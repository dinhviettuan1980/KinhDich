"""Mâm lễ hoạt hình: ảnh "camera" tại đền và clip thủ nhang đọc sớ cạnh mâm."""
import math
import subprocess
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import anim
from anim import FONT_B, INK, _ell


def _item(d, name: str, x: int, y: int):
    """Vẽ 1 lễ vật, đáy tại (x, y)."""
    n = name.lower()
    if "hương" in n:
        d.rounded_rectangle([x - 45, y - 60, x + 45, y], radius=12, fill=(150, 110, 60), outline=INK, width=3)
        for k in range(9):
            xx = x - 28 + k * 7
            d.line([xx, y - 60, xx + (k - 4) * 3, y - 150], fill=(190, 40, 40), width=4)
            _ell(d, xx + (k - 4) * 3, y - 152, 3, 3, fill=(255, 140, 40))
    elif "nến" in n:
        for xx in (x - 25, x + 25):
            d.rectangle([xx - 12, y - 110, xx + 12, y], fill=(210, 40, 40), outline=INK, width=2)
            _ell(d, xx, y - 125, 8, 16, fill=(255, 200, 60))
    elif "hoa" in n:
        d.polygon([(x - 30, y), (x + 30, y), (x + 22, y - 80), (x - 22, y - 80)], fill=(70, 130, 170), outline=INK)
        for k, (dx, dy) in enumerate([(-35, -120), (0, -140), (35, -120), (-18, -165), (18, -165)]):
            d.line([x, y - 80, x + dx, y + dy], fill=(60, 140, 60), width=4)
            _ell(d, x + dx, y + dy, 20, 20, fill=(250, 200, 40) if k % 2 else (240, 120, 40), outline=INK, width=2)
    elif "quả" in n:
        d.ellipse([x - 80, y - 20, x + 80, y + 10], fill=(225, 225, 230), outline=INK, width=2)
        for dx, dy, col in [(-45, -30, (240, 140, 30)), (0, -35, (90, 170, 60)), (45, -30, (230, 60, 50)),
                            (-22, -70, (250, 200, 50)), (22, -70, (200, 60, 120))]:
            _ell(d, x + dx, y + dy, 30, 28, fill=col, outline=INK, width=2)
    elif "gà" in n:
        d.ellipse([x - 90, y - 20, x + 90, y + 10], fill=(225, 225, 230), outline=INK, width=2)
        _ell(d, x, y - 50, 75, 45, fill=(235, 175, 60), outline=INK, width=3)
        _ell(d, x + 70, y - 95, 25, 22, fill=(235, 175, 60), outline=INK, width=3)
        d.polygon([(x + 60, y - 118), (x + 70, y - 135), (x + 80, y - 118)], fill=(220, 40, 40))
        d.polygon([(x + 93, y - 97), (x + 110, y - 92), (x + 93, y - 88)], fill=(240, 170, 40))
    elif "xôi" in n:
        d.ellipse([x - 80, y - 20, x + 80, y + 10], fill=(225, 225, 230), outline=INK, width=2)
        d.chord([x - 60, y - 90, x + 60, y + 10], 180, 360, fill=(215, 50, 40), outline=INK, width=3)
    elif "rượu" in n or "nước" in n:
        col = (230, 240, 250) if "rượu" in n else (180, 220, 250)
        d.rounded_rectangle([x - 22, y - 120, x + 22, y], radius=10, fill=col, outline=INK, width=3)
        d.rectangle([x - 8, y - 150, x + 8, y - 120], fill=col, outline=INK, width=2)
        d.rectangle([x - 22, y - 80, x + 22, y - 50], fill=(200, 50, 50))
    else:  # bánh kẹo, oản, trầu cau, vàng mã…: hộp quà
        d.rectangle([x - 50, y - 70, x + 50, y], fill=(230, 80, 80), outline=INK, width=3)
        d.rectangle([x - 8, y - 70, x + 8, y], fill=(250, 210, 80))
        d.rectangle([x - 50, y - 42, x + 50, y - 30], fill=(250, 210, 80))


def _xs(n, w):
    step = (w - 560) / max(1, n)  # chừa bên phải cho thủ nhang
    return [int(80 + step * (k + 0.5)) for k in range(n)]


def photo(items: list[dict], temple: str, phase: str, when: float, size=(1280, 720), header=True) -> Image.Image:
    """Ảnh camera tại đền: ban thờ + mâm lễ đúng các món đang bày, có giờ chụp."""
    w, h = size
    im = anim.temple_backdrop(w, h)
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([40, h - 260, w - 40, h - 205], fill=(130, 70, 30), outline=INK, width=3)
    shown = [i for i in items if int(i.get("qty") or 0) > 0]
    f = ImageFont.truetype(FONT_B, 22)
    for x, it in zip(_xs(len(shown), w), shown):
        _item(d, it["name"], x, h - 235)
        label = f'{it["name"]} ×{it["qty"]}'
        d.rounded_rectangle([x - 90, h - 190, x + 90, h - 156], radius=10, fill=(255, 245, 220, 235))
        d.text((x, h - 173), label, font=f, fill=INK, anchor="mm")
    if header:
        f2 = ImageFont.truetype(FONT_B, 26)
        tag = {"before": "TRƯỚC LỄ", "start": "LÚC KHẤN", "after": "SAU LỄ"}.get(phase, phase.upper())
        d.rectangle([0, 0, w, 46], fill=(0, 0, 0, 170))
        d.text((20, 23), f"CAMERA · {temple} · {tag}", font=f2, fill=(255, 225, 160), anchor="lm")
        d.text((w - 20, 23), datetime.fromtimestamp(when).strftime("%H:%M:%S %d/%m/%Y"), font=f2, fill="white",
               anchor="rm")
    return im


def clip(items: list[dict], audio: Path, temple: str, start_clock: float, out: Path, fps: float = 10,
         size=(1280, 720)) -> Path:
    """Clip tại đền: thủ nhang hoạt hình đọc sớ cạnh mâm lễ, đồng hồ chạy theo giờ thật."""
    w, h = size
    shown = [i for i in items if int(i.get("qty") or 0) > 0]
    base = photo(shown, temple, "start", start_clock, size, header=False)
    hx = _xs(len(shown), w)[0] if shown else 200
    f_cap, f_clk = ImageFont.truetype(FONT_B, 30), ImageFont.truetype(FONT_B, 34)
    env = anim.envelope(audio, fps)
    frames = out.with_suffix(".frames")
    frames.mkdir(parents=True, exist_ok=True)
    for i in range(len(env) + int(fps * 1.5)):
        t = i / fps
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        for k in range(8):  # khói hương
            yy = (t * 40 + k * 33) % 220
            sx = hx + 20 * math.sin(t * 1.3 + k)
            d.ellipse([sx - 9, h - 400 - yy - 9, sx + 9, h - 400 - yy + 9], fill=(240, 240, 240, max(0, 130 - int(yy / 2))))
        ch = anim.character("thu_nhang", anim.mouth_at(env, i), anim.blink_at(i, fps), t).resize((390, 520))
        im.paste(ch, (w - 420, h - 520), ch)
        d.rounded_rectangle([20, h - 70, w - 440, h - 20], radius=14, fill=(0, 0, 0, 150))
        d.text((40, h - 45), f"Thủ nhang đọc sớ · {temple}", font=f_cap, fill=(255, 225, 160), anchor="lm")
        d.rounded_rectangle([20, 140, 240, 195], radius=12, fill=(0, 0, 0, 170))
        d.text((130, 168), "● " + datetime.fromtimestamp(start_clock + t).strftime("%H:%M:%S"), font=f_clk,
               fill=(255, 90, 80), anchor="mm")
        im.save(frames / f"{i:05d}.jpg", quality=88)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(frames / "%05d.jpg"), "-i", str(audio),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-b:a", "96k", "-movflags", "+faststart", "-shortest", str(out)], check=True)
    for p in frames.iterdir():
        p.unlink()
    frames.rmdir()
    return out
