"""Ảnh mâm lễ GIẢ LẬP (LD_CAMERA=simulate): ghép hình từng lễ vật của đơn lên mâm, vẽ khung "nhận diện" quanh
từng món như camera thật đã nhận ra. Chỉ để demo khi chưa có camera — ảnh luôn ghi rõ "ẢNH GIẢ LẬP".

Hình lễ vật lấy từ font emoji màu (Noto Color Emoji trên Pi: apt install fonts-noto-color-emoji); thiếu font thì
vẽ khối màu có chữ. Hương (nhang) không có emoji nên vẽ tay."""
import io
import math
import random
import unicodedata
import zlib
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 960

EMOJI_FONTS = [("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109),
               ("/System/Library/Fonts/Apple Color Emoji.ttc", 160)]
TEXT_FONTS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/Library/Fonts/Arial Unicode.ttf"]

# từ khoá (không dấu) trong tên lễ vật → emoji; "huong" vẽ tay
ICONS = [("huong", None), ("nhang", None), ("nen", "🕯️"), ("hoa", "💐"), ("qua", "🍊"), ("trau", "🌿"),
         ("cau", "🌿"), ("oan", "🍙"), ("xoi", "🍚"), ("ga", "🐓"), ("ruou", "🍶"), ("banh", "🍬"),
         ("keo", "🍬"), ("vang", "🧧"), ("ma", "🧧"), ("nuoc", "💧"), ("tra", "🍵"), ("chuoi", "🍌")]
FRUITS = ["🍊", "🍎", "🍌", "🍇", "🍐"]
BOX = [(46, 204, 113), (52, 152, 219), (241, 196, 15), (231, 76, 60), (155, 89, 182), (26, 188, 156)]


def _plain(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower().replace("đ", "d"))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def icon_for(name: str) -> str | None | bool:
    """Emoji cho lễ vật; None = vẽ hương; False = không biết (vẽ khối có chữ)."""
    words = _plain(name).replace("(", " ").replace(")", " ").split()
    for key, emo in ICONS:
        if key in words:
            return emo
    return False


@lru_cache(maxsize=None)
def _text_font(size: int):
    for p in TEXT_FONTS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:  # Pillow cũ
        return ImageFont.load_default()


@lru_cache(maxsize=None)
def _emoji_font():
    for p, size in EMOJI_FONTS:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size), size
            except OSError:
                continue
    return None, 0


@lru_cache(maxsize=256)
def _emoji(ch: str, px: int) -> Image.Image | None:
    font, size = _emoji_font()
    if not font:
        return None
    im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
    try:
        ImageDraw.Draw(im).text((size // 2, size // 2), ch, font=font, embedded_color=True)
    except Exception:
        return None
    bbox = im.getbbox()
    if not bbox:
        return None
    im = im.crop(bbox)
    scale = px / max(im.size)
    return im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)


def _incense(px: int, lit: bool) -> Image.Image:
    """Bó hương: thân đỏ, chân tre, đầu đỏ rực khi đã thắp."""
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, base = px // 2, int(px * 0.95)
    for i in range(-5, 6):
        top = (cx + i * px // 22, int(px * 0.12) + abs(i) * 2)
        foot = (cx + i * px // 60, base)
        mid = (foot[0] + (top[0] - foot[0]) * 0.35, foot[1] + (top[1] - foot[1]) * 0.35)
        d.line([foot, mid], fill=(214, 170, 90), width=max(2, px // 45))
        d.line([mid, top], fill=(150, 30, 30), width=max(3, px // 32))
        if lit:
            r = max(2, px // 40)
            d.ellipse([top[0] - r, top[1] - r, top[0] + r, top[1] + r], fill=(255, 120, 20))
    d.rectangle([cx - px // 9, int(px * 0.62), cx + px // 9, int(px * 0.7)], fill=(200, 40, 40))  # dây buộc đỏ
    return im


def _block(label: str, px: int) -> Image.Image:
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, px - 4, px - 4], radius=px // 6, fill=(240, 220, 170), outline=(150, 100, 40), width=3)
    d.text((px // 2, px // 2), label[:10], font=_text_font(max(12, px // 7)), fill=(90, 50, 20), anchor="mm")
    return im


def _item_sprite(name: str, px: int, lit: bool, k: int) -> Image.Image:
    emo = icon_for(name)
    if emo is None:
        return _incense(px, lit)
    if emo == "🍊":  # ngũ quả: 5 loại quả xếp chồng
        fr = [_emoji(f, int(px * 0.55)) for f in FRUITS]
        if all(fr):
            im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
            for f, (fx, fy) in zip(fr, [(0.0, 0.42), (0.45, 0.42), (0.22, 0.12), (0.05, 0.0), (0.42, 0.02)][::-1]):
                im.paste(f, (int(fx * px), int(fy * px)), f)
            return im
    return (_emoji(emo, px) if emo else None) or _block(name, px)


def _scene(seed: int) -> Image.Image:
    """Bàn thờ: nền đỏ trầm, mặt bàn gỗ, mâm đồng."""
    im = Image.new("RGB", (W, H), (92, 22, 22))
    d = ImageDraw.Draw(im)
    for y in range(0, int(H * 0.35)):  # vách sau sẫm dần
        c = int(60 + 40 * y / (H * 0.35))
        d.line([(0, y), (W, y)], fill=(c + 20, c // 4, c // 4))
    d.rectangle([0, int(H * 0.35), W, H], fill=(105, 58, 28))  # mặt bàn gỗ
    rnd = random.Random(seed)
    for _ in range(40):  # vân gỗ
        y = rnd.randint(int(H * 0.36), H)
        d.line([(0, y), (W, y + rnd.randint(-8, 8))], fill=(95, 50, 24), width=2)
    cx, cy, rx, ry = W // 2, int(H * 0.64), int(W * 0.44), int(H * 0.30)
    d.ellipse([cx - rx + 10, cy - ry + 22, cx + rx + 10, cy + ry + 22], fill=(60, 30, 14))  # bóng mâm
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(196, 150, 60), outline=(120, 85, 25), width=6)
    d.ellipse([cx - rx + 30, cy - ry + 22, cx + rx - 30, cy + ry - 22], fill=(214, 172, 80))
    return im


def _slots(n: int) -> list[tuple[int, int]]:
    """n vị trí trên mặt mâm (elip), hàng sau → hàng trước."""
    cx, cy, rx, ry = W // 2, int(H * 0.64), int(W * 0.36), int(H * 0.21)
    rows = 1 if n <= 4 else 2 if n <= 9 else 3
    per = math.ceil(n / rows)
    out = []
    for r in range(rows):
        k = min(per, n - len(out))
        y = cy - ry + (2 * ry) * (r + 0.5) / rows
        half = rx * math.sqrt(max(0.0, 1 - ((y - cy) / (ry * 1.25)) ** 2))
        for i in range(k):
            out.append((int(cx - half + 2 * half * (i + 0.5) / k), int(y)))
    return out


def render(tray: dict | None, phase: str, when: datetime | None = None) -> bytes:
    """tray = {"items": [{"name","unit","qty"}], "temple": ...} (gửi kèm lệnh phát, không có dữ liệu cá nhân)."""
    when = when or datetime.now()
    items = [i for i in (tray or {}).get("items") or [] if int(i.get("qty") or 0) > 0]
    seed = zlib.crc32(repr([(i.get("name"), i.get("qty")) for i in items]).encode()) & 0xFFFF
    im = _scene(seed)
    d = ImageDraw.Draw(im)
    lit = phase in ("start", "after")
    if items:
        slots = _slots(len(items))
        px = max(90, min(190, int(560 / math.sqrt(len(items)))))
        for n, (it, (x, y)) in enumerate(sorted(zip(items, slots), key=lambda p: p[1][1])):
            q = int(it["qty"])
            show = min(q, 3)
            group, boxes = [], []
            for k in range(show):  # 1–3 hình chồng nhẹ lên nhau; nhiều hơn ghi ×N
                sp = _item_sprite(it.get("name", ""), int(px * (1 if show == 1 else 0.78)), lit, k)
                ox = int((k - (show - 1) / 2) * sp.width * 0.55)
                pos = (x + ox - sp.width // 2, y - sp.height + px // 3)
                im.paste(sp, pos, sp)
                boxes.append((pos[0], pos[1], pos[0] + sp.width, pos[1] + sp.height))
                group.append(sp)
            x0, y0 = min(b[0] for b in boxes) - 6, min(b[1] for b in boxes) - 6
            x1, y1 = max(b[2] for b in boxes) + 6, max(b[3] for b in boxes) + 6
            col = BOX[n % len(BOX)]
            d.rectangle([x0, y0, x1, y1], outline=col, width=4)
            conf = 0.9 + (seed + n * 7) % 10 / 100
            label = f"{it.get('name', '')} ×{q} · {conf:.0%}"
            f = _text_font(22)
            tw = d.textlength(label, font=f)
            d.rectangle([x0, y0 - 30, x0 + tw + 14, y0], fill=col)
            d.text((x0 + 7, y0 - 15), label, font=f, fill=(20, 20, 20), anchor="lm")
    else:
        d.text((W // 2, int(H * 0.64)), "(mâm trống)", font=_text_font(40), fill=(110, 70, 20), anchor="mm")

    # dải tiêu đề + chân ảnh
    names = {"before": "TRƯỚC LỄ", "start": "BẮT ĐẦU KHẤN", "after": "SAU LỄ", "test": "CHỤP THỬ"}
    d.rectangle([0, 0, W, 64], fill=(0, 0, 0))
    d.text((20, 32), f"ẢNH GIẢ LẬP · {names.get(phase, phase.upper())}", font=_text_font(30),
           fill=(255, 210, 120), anchor="lm")
    d.text((W - 20, 32), when.strftime("%H:%M:%S %d/%m/%Y"), font=_text_font(26), fill=(255, 255, 255), anchor="rm")
    who = (tray or {}).get("temple") or ""
    found = f"Nhận diện: {len(items)}/{len(items)} món khớp đơn" if items else ""
    if who or found:
        d.rectangle([0, H - 56, W, H], fill=(0, 0, 0))
        d.text((20, H - 28), who, font=_text_font(26), fill=(255, 255, 255), anchor="lm")
        d.text((W - 20, H - 28), found, font=_text_font(26), fill=(120, 230, 140), anchor="rm")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82)
    return buf.getvalue()
