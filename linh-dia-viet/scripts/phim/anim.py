"""Nhân vật hoạt hình tự vẽ (PIL) cho phim demo: thủ nhang, khách, kiosk, admin, người dẫn chuyện.
Miệng mấp máy theo âm lượng tiếng nói, mắt chớp, người lắc nhẹ."""
import array
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_B = "C:/Windows/Fonts/arialbd.ttf"
FONT_R = "C:/Windows/Fonts/arial.ttf"
SKIN = (246, 205, 170)
INK = (60, 35, 25)

CHARS = {
    # thủ nhang: ông cụ khăn xếp, áo the nâu, râu bạc, cầm tờ sớ
    "thu_nhang": dict(skin=(238, 196, 160), hair="khanxep", hair_col=(225, 225, 225), outfit=(120, 66, 34),
                      collar=(235, 205, 120), beard=True, brows=(220, 220, 220), prop="scroll", wrinkles=True),
    # khách: anh An, sơ mi xanh, cầm điện thoại
    "khach": dict(skin=SKIN, hair="short", hair_col=(35, 28, 25), outfit=(52, 110, 190), collar=(240, 240, 245),
                  brows=(35, 28, 25), prop="phone"),
    # kiosk: chị Lan, tóc búi, tạp dề đỏ, bưng mâm quả
    "kiosk": dict(skin=SKIN, hair="bun", hair_col=(40, 25, 20), outfit=(196, 52, 52), collar=(250, 230, 180),
                  brows=(40, 25, 20), prop="tray", lips=(205, 70, 80)),
    # admin: chị Mai, kính, áo xám, tai nghe, laptop
    # người dẫn chuyện: cô gái áo dài đỏ
    "dan_chuyen": dict(skin=SKIN, hair="long", hair_col=(25, 18, 16), outfit=(178, 34, 52), collar=(178, 34, 52),
                       brows=(25, 18, 16), prop=None, lips=(200, 60, 70)),
    "admin": dict(skin=SKIN, hair="long", hair_col=(30, 22, 20), outfit=(85, 95, 110), collar=(230, 235, 240),
                  brows=(30, 22, 20), prop="laptop", glasses=True, headset=True, lips=(200, 80, 90)),
}


def _ell(d, cx, cy, rx, ry, **kw):
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], **kw)


def character(kind: str, mouth: float = 0.0, blink: bool = False, t: float = 0.0, w: int = 600, h: int = 800) -> Image.Image:
    """Ảnh RGBA nhân vật; mouth 0..1 độ mở miệng."""
    c = CHARS[kind]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, hy = w // 2, 300
    out, skin = c["outfit"], c["skin"]
    # tóc dài phía sau
    if c["hair"] == "long":
        d.rounded_rectangle([cx - 150, hy - 120, cx + 150, hy + 230], radius=90, fill=c["hair_col"])
    # thân
    d.rounded_rectangle([cx - 190, 470, cx + 190, h + 60], radius=110, fill=out, outline=INK, width=4)
    d.polygon([(cx - 60, 470), (cx, 560), (cx + 60, 470)], fill=c["collar"], outline=INK)
    if kind == "thu_nhang":  # hàng khuy áo the
        for i in range(4):
            _ell(d, cx + 30, 590 + i * 45, 7, 7, fill=(235, 205, 120))
    if kind == "kiosk":  # tạp dề
        d.rounded_rectangle([cx - 120, 560, cx + 120, h], radius=30, fill=(250, 245, 235), outline=INK, width=3)
    # cổ + đầu
    d.rectangle([cx - 45, 400, cx + 45, 480], fill=skin)
    _ell(d, cx - 128, hy + 10, 22, 32, fill=skin, outline=INK, width=3)  # tai
    _ell(d, cx + 128, hy + 10, 22, 32, fill=skin, outline=INK, width=3)
    _ell(d, cx, hy, 130, 150, fill=skin, outline=INK, width=4)
    # tóc / khăn
    hc = c["hair_col"]
    if c["hair"] == "khanxep":
        d.chord([cx - 138, hy - 185, cx + 138, hy - 15], 180, 360, fill=(45, 45, 80), outline=INK, width=4)
        mid, rx, ry = hy - 100, 138, 85
        for y in range(hy - 170, hy - 100, 16):  # các nếp khăn trong phạm vi khăn
            half = rx * math.sqrt(max(0.0, 1 - ((y - mid) / ry) ** 2)) - 8
            d.line([cx - half, y, cx + half, y], fill=(85, 85, 135), width=4)
        d.rectangle([cx - 136, hy - 104, cx + 136, hy - 96], fill=(35, 35, 65))
        _ell(d, cx - 120, hy + 20, 10, 24, fill=hc)  # tóc mai bạc
        _ell(d, cx + 120, hy + 20, 10, 24, fill=hc)
    elif c["hair"] == "short":
        d.chord([cx - 135, hy - 160, cx + 135, hy - 10], 180, 360, fill=hc)
        d.polygon([(cx - 130, hy - 60), (cx - 40, hy - 120), (cx + 60, hy - 70), (cx + 130, hy - 60), (cx + 120, hy - 120),
                   (cx - 120, hy - 120)], fill=hc)
    elif c["hair"] == "bun":
        _ell(d, cx, hy - 165, 60, 50, fill=hc, outline=INK, width=3)
        d.chord([cx - 135, hy - 160, cx + 135, hy - 5], 180, 360, fill=hc)
        d.rectangle([cx - 40, hy - 215, cx + 40, hy - 205], fill=(220, 180, 60))  # trâm cài
    elif c["hair"] == "long":
        d.chord([cx - 140, hy - 165, cx + 140, hy + 10], 180, 360, fill=hc)
        d.polygon([(cx - 135, hy - 40), (cx - 20, hy - 110), (cx - 135, hy - 110)], fill=hc)
    # lông mày, mắt
    bc = c["brows"]
    by = hy - 45 + (2 if mouth > 0.5 else 0)
    d.line([cx - 85, by, cx - 30, by - 8], fill=bc, width=9)
    d.line([cx + 30, by - 8, cx + 85, by], fill=bc, width=9)
    for ex in (cx - 55, cx + 55):
        if blink:
            d.arc([ex - 22, hy - 15, ex + 22, hy + 15], 20, 160, fill=INK, width=5)
        else:
            _ell(d, ex, hy, 22, 25, fill="white", outline=INK, width=3)
            _ell(d, ex + 3, hy + 3, 11, 13, fill=(45, 30, 25))
            _ell(d, ex + 7, hy - 3, 4, 4, fill="white")
    if c.get("glasses"):
        for ex in (cx - 55, cx + 55):
            d.rounded_rectangle([ex - 38, hy - 30, ex + 38, hy + 30], radius=14, outline=(30, 30, 30), width=5)
        d.line([cx - 17, hy - 5, cx + 17, hy - 5], fill=(30, 30, 30), width=5)
    if c.get("wrinkles"):
        d.arc([cx - 60, hy - 95, cx + 60, hy - 65], 200, 340, fill=(190, 140, 110), width=3)
        d.arc([cx - 50, hy - 80, cx + 50, hy - 55], 200, 340, fill=(190, 140, 110), width=3)
    # mũi, má
    d.arc([cx - 18, hy + 25, cx + 18, hy + 55], 20, 160, fill=(170, 110, 85), width=4)
    _ell(d, cx - 85, hy + 60, 22, 14, fill=(244, 160, 150))
    _ell(d, cx + 85, hy + 60, 22, 14, fill=(244, 160, 150))
    # miệng
    my = hy + 90
    if mouth > 0.08:
        oh = 6 + mouth * 32
        _ell(d, cx, my, 30 - mouth * 6, oh, fill=(120, 30, 35), outline=INK, width=3)
        d.chord([cx - 18, my + oh * 0.2, cx + 18, my + oh], 180, 360, fill=(230, 110, 110))
    else:
        d.arc([cx - 30, my - 15, cx + 30, my + 12], 20, 160, fill=c.get("lips", INK), width=6)
    if c.get("beard"):
        d.polygon([(cx - 70, my - 22), (cx - 10, my - 30), (cx - 5, my - 18), (cx - 60, my - 8)], fill=(235, 235, 235))
        d.polygon([(cx + 70, my - 22), (cx + 10, my - 30), (cx + 5, my - 18), (cx + 60, my - 8)], fill=(235, 235, 235))
        d.polygon([(cx - 40, my + 30 + mouth * 20), (cx + 40, my + 30 + mouth * 20), (cx, my + 120 + mouth * 20)],
                  fill=(240, 240, 240), outline=(200, 200, 200))
    if c.get("headset"):
        d.arc([cx - 145, hy - 170, cx + 145, hy + 60], 190, 350, fill=(40, 40, 40), width=12)
        _ell(d, cx - 138, hy + 10, 20, 34, fill=(40, 40, 40))
        d.line([cx - 135, hy + 40, cx - 60, my + 10], fill=(40, 40, 40), width=6)
        _ell(d, cx - 58, my + 10, 9, 9, fill=(40, 40, 40))
    # đạo cụ
    p = c["prop"]
    if p == "scroll":
        sy = 560 + int(4 * math.sin(t * 2))
        d.rectangle([cx - 150, sy, cx + 150, sy + 170], fill=(250, 236, 196), outline=INK, width=3)
        for x in (cx - 160, cx + 150):
            d.rounded_rectangle([x, sy - 12, x + 12, sy + 182], radius=6, fill=(160, 90, 40), outline=INK, width=2)
        for i in range(5):
            d.line([cx - 120, sy + 25 + i * 28, cx + 120 - (i % 2) * 40, sy + 25 + i * 28], fill=(170, 40, 40), width=6)
        for hx in (cx - 165, cx + 165):
            _ell(d, hx, sy + 90, 30, 30, fill=skin, outline=INK, width=3)
    elif p == "phone":
        d.line([cx + 130, 620, cx + 175, 500], fill=out, width=60)
        d.rounded_rectangle([cx + 135, 360, cx + 225, 520], radius=14, fill=(30, 30, 35), outline=INK, width=3)
        d.rounded_rectangle([cx + 143, 372, cx + 217, 505], radius=8, fill=(255, 225, 160))
        _ell(d, cx + 180, 530, 34, 30, fill=skin, outline=INK, width=3)
    elif p == "tray":
        ty = 560
        d.ellipse([cx - 210, ty + 40, cx + 210, ty + 110], fill=(205, 160, 60), outline=INK, width=3)
        for i, col in enumerate([(240, 140, 30), (90, 170, 60), (230, 60, 50), (250, 200, 50), (240, 140, 30)]):
            _ell(d, cx - 120 + i * 60, ty + 40 - (i % 2) * 18, 34, 32, fill=col, outline=INK, width=2)
        for hx in (cx - 200, cx + 200):
            _ell(d, hx, ty + 85, 28, 26, fill=skin, outline=INK, width=3)
    elif p == "laptop":
        d.polygon([(cx - 200, 640), (cx + 200, 640), (cx + 240, 700), (cx - 240, 700)], fill=(170, 175, 185), outline=INK)
        d.rectangle([cx - 190, 500, cx + 190, 640], fill=(60, 65, 75), outline=INK, width=3)
        d.rectangle([cx - 175, 512, cx + 175, 628], fill=(120, 200, 140))
        for i in range(4):
            d.rectangle([cx - 160, 525 + i * 26, cx - 20 + i * 30, 537 + i * 26], fill=(240, 250, 240))
    # lắc nhẹ
    ang = 1.5 * math.sin(t * 1.3)
    return im.rotate(ang, resample=Image.BICUBIC, center=(cx, h))


def envelope(audio: Path, fps: float) -> list[float]:
    """Âm lượng chuẩn hoá 0..1 cho từng khung hình."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = array.array("h", raw)
    step = int(8000 / fps)
    vals = []
    for i in range(0, len(a), step):
        chunk = a[i:i + step]
        vals.append(math.sqrt(sum(x * x for x in chunk) / max(1, len(chunk))))
    top = sorted(vals)[int(len(vals) * 0.95)] if vals else 1
    return [min(1.0, v / (top or 1)) for v in vals]


def mouth_at(env: list[float], i: int) -> float:
    if i >= len(env):
        return 0.0
    v = env[i]
    return 0.0 if v < 0.12 else min(1.0, 0.25 + v * 0.9) * (0.75 + 0.25 * math.sin(i * 2.1))


def blink_at(i: int, fps: float) -> bool:
    return (i % int(fps * 3.7)) < max(1, int(fps * 0.12))


def temple_backdrop(w: int, h: int) -> Image.Image:
    """Nội thất điện thờ: tường đỏ, câu đối, hoành phi, đèn lồng."""
    im = Image.new("RGB", (w, h), (120, 28, 24))
    d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / h
        d.line([0, y, w, y], fill=(int(140 - 50 * k), int(36 - 14 * k), int(28 - 10 * k)))
    d.rectangle([w * 0.2, 30, w * 0.8, 120], fill=(70, 20, 10), outline=(230, 180, 70), width=6)
    f = ImageFont.truetype(FONT_B, 54)
    d.text((w / 2, 75), "PHÚC  ĐỨC  VIÊN  MÃN", font=f, fill=(240, 200, 90), anchor="mm")
    for x in (40, w - 110):
        d.rectangle([x, 150, x + 70, h - 220], fill=(70, 20, 10), outline=(230, 180, 70), width=4)
    for x in (w * 0.12, w * 0.88):
        _ell(d, x, 200, 46, 58, fill=(230, 60, 40), outline=(250, 200, 80), width=4)
        d.line([x, 120, x, 142], fill=(250, 200, 80), width=4)
        d.line([x, 258, x, 300], fill=(250, 200, 80), width=4)
    d.rectangle([0, h - 220, w, h], fill=(95, 50, 25))
    d.rectangle([0, h - 225, w, h - 205], fill=(150, 90, 40))
    return im


def temple_clip(tray_jpg: Path, audio: Path, temple: str, start_clock: float, out: Path, fps: float = 10,
                size=(1280, 720)) -> Path:
    """Clip tại đền: mâm lễ bên trái, ông thủ nhang hoạt hình đọc sớ bên phải, đồng hồ chạy theo giờ thật."""
    from datetime import datetime
    w, h = size
    base = temple_backdrop(w, h)
    tray = Image.open(tray_jpg).convert("RGB")
    tray.thumbnail((560, 420))
    bd = ImageDraw.Draw(base)
    tx, ty = 70, h - 220 - tray.height + 60
    bd.rectangle([tx - 10, ty - 10, tx + tray.width + 10, ty + tray.height + 10], fill=(230, 180, 70))
    base.paste(tray, (tx, ty))
    f_cap = ImageFont.truetype(FONT_B, 30)
    f_clk = ImageFont.truetype(FONT_B, 34)
    env = envelope(audio, fps)
    frames = out.with_suffix(".frames")
    frames.mkdir(parents=True, exist_ok=True)
    n = len(env) + int(fps * 1.5)
    smoke = [(i * 37 % 60) for i in range(8)]
    for i in range(n):
        t = i / fps
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        # khói hương bay lên từ mâm
        for k, off in enumerate(smoke):
            yy = (t * 40 + off * 5 + k * 30) % 260
            d.ellipse([tx + 120 + 25 * math.sin(t + k) - 10, ty - yy - 10, tx + 120 + 25 * math.sin(t + k) + 10,
                       ty - yy + 10], fill=(240, 240, 240, max(0, 120 - int(yy / 2))))
        ch = character("thu_nhang", mouth_at(env, i), blink_at(i, fps), t).resize((450, 600))
        im.paste(ch, (w - 520, h - 600), ch)
        d.rounded_rectangle([20, h - 70, w - 20, h - 20], radius=14, fill=(0, 0, 0, 150))
        d.text((40, h - 45), f"Thủ nhang đọc sớ · {temple}", font=f_cap, fill=(255, 225, 160), anchor="lm")
        clock = datetime.fromtimestamp(start_clock + t).strftime("%H:%M:%S")
        d.rounded_rectangle([w - 230, 140, w - 30, 195], radius=12, fill=(0, 0, 0, 160))
        d.text((w - 130, 168), "● " + clock, font=f_clk, fill=(255, 90, 80), anchor="mm")
        im.save(frames / f"{i:05d}.jpg", quality=88)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps), "-i", str(frames / "%05d.jpg"), "-i", str(audio),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-pix_fmt", "yuv420p", "-c:a", "aac",
                    "-b:a", "96k", "-movflags", "+faststart", "-shortest", str(out)], check=True)
    for p in frames.iterdir():
        p.unlink()
    frames.rmdir()
    return out


if __name__ == "__main__":
    import sys
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    row = Image.new("RGB", (2400, 800), (250, 240, 225))
    for i, k in enumerate(CHARS):
        ch = character(k, mouth=0.6 if i % 2 else 0, t=i)
        row.paste(ch, (i * 600, 0), ch)
    row.save(outdir / "characters.png")
