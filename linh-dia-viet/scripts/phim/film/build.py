"""Dựng phim hoạt hình cho nhà đầu tư: nhân vật nói (miệng theo giọng) + màn hình app thật trong khung điện thoại.
Đầu vào: seg/*.webm + marks.json (record.js), voice/*.mp3 (voices.py), clip tại đền (devsim, ../dev-work)."""
import json
import math
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).parent
sys.path.insert(0, str(D.parent))
import anim  # noqa: E402

W, H, FPS = 1920, 1080, 12
F_B, F_R = anim.FONT_B, anim.FONT_R
LINES = json.loads((D / "lines.json").read_text(encoding="utf-8"))
DUR = json.loads((D / "durations.json").read_text())
M = json.loads((D / "marks.json").read_text())
TMP = D / "build"
OUT = D / "linh-dia-viet-phim-dau-tu.mp4"
ENV = {}  # độ lớn tiếng từng câu thoại theo khung hình

ROLE = {  # màu nền, tên hiện trên nhãn
    "khach": ((232, 241, 252), "KHÁCH HÀNG", "anh An"),
    "thu_nhang": ((250, 236, 214), "THỦ NHANG", "Đền Ngọc Sơn"),
    "kiosk": ((252, 230, 228), "KIOSK BÁN LỄ", "chị Lan"),
    "admin": ((228, 236, 240), "QUẢN TRỊ VIÊN", "chị Mai"),
    "dan_chuyen": ((250, 240, 225), "", ""),
}
PHONE = (1330, 40, 470, 1018)  # x, y, rộng, cao của màn hình điện thoại


def font(size, bold=True):
    return ImageFont.truetype(F_B if bold else F_R, size)


def run(cmd):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *cmd], check=True)


def duration(p: Path) -> float:
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                          str(p)]).decode())


def env(line_id):
    if line_id not in ENV:
        ENV[line_id] = anim.envelope(D / "voice" / f"{line_id}.mp3", FPS)
    return ENV[line_id]


def backdrop(color, label=None, phone=True):
    im = Image.new("RGB", (W, H), color)
    d = ImageDraw.Draw(im)
    for y in range(H):  # nền chuyển màu nhẹ
        k = y / H
        d.line([0, y, W, y], fill=tuple(int(c * (1 - 0.12 * k)) for c in color))
    for i in range(7):  # hoạ tiết mây tròn trang trí
        x, y = 80 + i * 170, H - 60 - (i % 2) * 30
        d.ellipse([x - 70, y - 40, x + 70, y + 40], fill=tuple(max(0, c - 14) for c in color))
    if phone:
        x, y, w, h = PHONE
        d.rounded_rectangle([x - 22, y - 26, x + w + 22, y + h + 26], radius=52, fill=(25, 25, 30))
        d.rounded_rectangle([x + w // 2 - 50, y - 14, x + w // 2 + 50, y - 4], radius=5, fill=(60, 60, 66))
    if label:
        role, who = label
        d.rounded_rectangle([40, 30, 40 + 22 * len(role) + 200, 100], radius=35, fill=(122, 31, 31))
        d.text((70, 65), role, font=font(36), fill=(255, 225, 160), anchor="lm")
        d.text((40 + 22 * len(role) + 230, 65), who, font=font(34, False), fill=(90, 50, 40), anchor="lm")
    return im


def bubble(d: ImageDraw.ImageDraw, text: str, box, tail_x):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=34, fill="white", outline=(122, 31, 31), width=5)
    d.polygon([(tail_x - 30, y1 - 3), (tail_x + 30, y1 - 3), (tail_x - 10, y1 + 55)], fill="white")
    d.line([(tail_x - 30, y1), (tail_x - 10, y1 + 55), (tail_x + 30, y1)], fill=(122, 31, 31), width=5)
    width = max(18, int((x1 - x0 - 80) / 21))
    lines = textwrap.wrap(text, width)
    f = font(40 if len(lines) <= 3 else 34, False)
    lh = f.size * 1.3
    y = (y0 + y1) / 2 - lh * (len(lines) - 1) / 2
    for ln in lines:
        d.text(((x0 + x1) / 2, y), ln, font=f, fill=(40, 25, 20), anchor="mm")
        y += lh


def speech_at(lines, t):
    """(id, i_khung) của câu đang nói ở thời điểm t; lines = [(id, t_bắt_đầu)]."""
    for lid, st in lines:
        if st <= t < st + DUR[lid] + 0.4:
            return lid, int((t - st) * FPS)
    return None, 0


def render_layer(name, dur, draw):
    """Vẽ từng khung hình (PIL) → video không tiếng."""
    fd = TMP / f"{name}_frames"
    shutil.rmtree(fd, ignore_errors=True)
    fd.mkdir(parents=True)
    for i in range(int(dur * FPS) + 1):
        draw(i / FPS, i).save(fd / f"{i:05d}.jpg", quality=90)
    out = TMP / f"{name}_layer.mp4"
    run(["-framerate", str(FPS), "-i", str(fd / "%05d.jpg"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-pix_fmt", "yuv420p", str(out)])
    shutil.rmtree(fd)
    return out


def voice_track(name, lines, dur, extra=()):
    """Ghép các câu thoại đúng thời điểm (+ âm thanh phụ) thành 1 track."""
    ins, parts = [], []
    for k, (lid, st) in enumerate(lines):
        ins += ["-i", str(D / "voice" / f"{lid}.mp3")]
        parts.append(f"[{k + 1}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={int(st * 1000)}:all=1[a{k}]")
    for path, st, vol in extra:
        k = len(parts)
        ins += ["-i", str(path)]
        parts.append(f"[{k + 1}:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol},adelay={int(st * 1000)}:all=1[a{k}]")
    out = TMP / f"{name}_voice.m4a"
    mix = "".join(f"[a{k}]" for k in range(len(parts)))
    fc = ";".join(parts + [f"[0:a]{mix}amix=inputs={len(parts) + 1}:normalize=0:duration=first[m]"])
    run(["-f", "lavfi", "-t", f"{dur:.2f}", "-i", "anullsrc=r=44100:cl=stereo", *ins, "-filter_complex", fc,
         "-map", "[m]", "-c:a", "aac", "-b:a", "160k", str(out)])
    return out


def mux(name, layer, audio, screen=None, screen_trim=None):
    """layer (nền + nhân vật) + màn hình điện thoại (tuỳ chọn) + tiếng → đoạn phim chuẩn."""
    out = TMP / f"{name}.mp4"
    if screen:
        x, y, w, h = PHONE
        a, b = screen_trim
        fc = (f"[1:v]trim={a}:{b},setpts=PTS-STARTPTS,fps=25,scale={w}:{h}[s];"
              f"[0:v]fps=25[l];[l][s]overlay={x}:{y}:shortest=1,format=yuv420p[v]")
        run(["-i", str(layer), "-i", str(screen), "-i", str(audio), "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-r", "25", "-c:a", "aac", "-b:a", "160k",
             "-ar", "44100", "-shortest", str(out)])
    else:
        run(["-i", str(layer), "-i", str(audio), "-filter_complex", "[0:v]fps=25,format=yuv420p[v]", "-map", "[v]",
             "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-r", "25", "-c:a", "aac",
             "-b:a", "160k", "-ar", "44100", "-shortest", str(out)])
    return out


def phone_scene(name, seg, lines, a, b, label_role=None):
    """Cảnh 1 vai: lines = [(id, t)] tính từ đầu đoạn [a, b] của video seg."""
    role = label_role or M[seg]["who"]
    color, title, who = ROLE[role]
    base = backdrop(color, (title, who))
    dur = b - a

    def draw(t, i):
        im = base.copy()
        lid, k = speech_at(lines, t)
        speaker = LINES[lid][0] if lid else role
        ch = anim.character(speaker, anim.mouth_at(env(lid), k) if lid else 0, anim.blink_at(i, FPS), t)
        im.paste(ch, (330, 290), ch)
        if lid:
            d = ImageDraw.Draw(im)
            bubble(d, LINES[lid][1], (60, 120, 1270, 300), 630)
            if speaker != role:  # người khác chen vào (vd thủ nhang trong cảnh cảnh báo)
                d.text((1240, 330), f"— {ROLE[speaker][1].lower()} —", font=font(28, False), fill=(120, 60, 50), anchor="rm")
        return im
    layer = render_layer(name, dur, draw)
    audio = voice_track(name, lines, dur)
    return mux(name, layer, audio, D / "seg" / f"{seg}.webm", (a, b))


def seg_lines(seg, a=0.0):
    return [(lid, st - a) for lid, st in M[seg]["lines"]]


def card_scene(name, lines, dur, title, subtitle=None, bullets=(), people=True):
    base = backdrop((122, 31, 31), phone=False)
    d = ImageDraw.Draw(base)
    d.text((W / 2, 150), title, font=font(96), fill=(255, 225, 160), anchor="mm")
    if subtitle:
        d.text((W / 2, 250), subtitle, font=font(48, False), fill="white", anchor="mm")
    y = 330
    for bl in bullets:
        d.text((260, y), "• " + bl, font=font(40, False), fill=(250, 235, 210), anchor="lm")
        y += 66
    names = [("khach", "Khách hàng"), ("thu_nhang", "Thủ nhang"), ("kiosk", "Kiosk bán lễ"), ("admin", "Quản trị viên")]

    def draw(t, i):
        im = base.copy()
        dd = ImageDraw.Draw(im)
        if people:
            for j, (k, label) in enumerate(names):
                bob = int(8 * math.sin(t * 2 + j))
                ch = anim.character(k, 0, anim.blink_at(i + j * 7, FPS), t + j).resize((330, 440))
                x = 210 + j * 400
                im.paste(ch, (x, H - 520 + bob), ch)
                dd.rounded_rectangle([x + 40, H - 80, x + 290, H - 30], radius=25, fill=(255, 225, 160))
                dd.text((x + 165, H - 55), label, font=font(30), fill=(122, 31, 31), anchor="mm")
        lid, k = speech_at(lines, t)
        if lid:
            dd.rounded_rectangle([160, 400 if not bullets else y + 10, W - 160, (400 if not bullets else y + 10) + 120],
                                 radius=30, fill=(0, 0, 0))
            yy = (400 if not bullets else y + 10) + 60
            wrapped = textwrap.wrap(LINES[lid][1], 70)
            for n, ln in enumerate(wrapped):
                dd.text((W / 2, yy + (n - (len(wrapped) - 1) / 2) * 44), ln, font=font(36, False), fill="white",
                        anchor="mm")
        return im
    layer = render_layer(name, dur, draw)
    return mux(name, layer, voice_track(name, lines, dur))


def latest_clip(dev):
    clips = sorted((D.parent / "dev-work" / dev).glob("*.mp4"), key=lambda p: p.stat().st_mtime)
    return clips[-1]


def temple_scene(name, dur=26.0):
    """3 đền cùng lúc: 3 khung thủ nhang hoạt hình, đồng hồ giờ thật trên từng khung."""
    temples = [("pi-phu-tay-ho", "Phủ Tây Hồ", "Raspberry Pi"),
               ("phone-chua-tran-quoc", "Chùa Trấn Quốc", "Điện thoại Android"),
               ("pi-demo-01", "Đền Ngọc Sơn", "Raspberry Pi")]
    base = backdrop((70, 18, 16), phone=False)
    d = ImageDraw.Draw(base)
    d.text((W / 2, 110), "Cùng một giờ, tại 3 nơi", font=font(80), fill=(255, 225, 160), anchor="mm")
    pw, ph = 600, 338
    xs = [30 + k * (pw + 30) for k in range(3)]
    for x, (_, tname, kind) in zip(xs, temples):
        d.text((x + pw / 2, 270), tname, font=font(44), fill="white", anchor="mm")
        d.text((x + pw / 2, 320), kind, font=font(30, False), fill=(240, 200, 180), anchor="mm")
        d.rectangle([x - 6, 354, x + pw + 6, 360 + ph + 6], fill=(230, 180, 70))
    d.text((W / 2, 800), "Thiết bị tại mỗi đền tự phát bài khấn đúng giờ hẹn, chụp ảnh và quay video mâm lễ.",
           font=font(36, False), fill="white", anchor="mm")
    lines = [("n3", 1.0), ("n4", 15.0)]
    st = speech_at

    def draw(t, i):
        im = base.copy()
        lid, _ = st(lines, t)
        if lid:
            dd = ImageDraw.Draw(im)
            dd.rounded_rectangle([160, 880, W - 160, 1000], radius=30, fill=(0, 0, 0))
            dd.text((W / 2, 940), LINES[lid][1], font=font(36, False), fill="white", anchor="mm")
        return im
    layer = render_layer(name, dur, draw)
    clips = [latest_clip(dev) for dev, _, _ in temples]
    audio = voice_track(name, lines, dur, extra=[(clips[2], 0, 0.55), (clips[0], 0, 0.08), (clips[1], 0, 0.08)])
    out = TMP / f"{name}.mp4"
    fc = "[0:v]fps=25[b];" + "".join(
        f"[{k + 1}:v]trim=0:{dur},setpts=PTS-STARTPTS,fps=25,scale={pw}:{ph}[c{k}];" for k in range(3))
    fc += f"[b][c0]overlay={xs[0]}:360[x0];[x0][c1]overlay={xs[1]}:360[x1];[x1][c2]overlay={xs[2]}:360,format=yuv420p[v]"
    run(["-i", str(layer), *sum((["-i", str(c)] for c in clips), []), "-i", str(audio), "-filter_complex", fc,
         "-map", "[v]", "-map", "4:a", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-r", "25", "-c:a", "aac",
         "-b:a", "160k", "-ar", "44100", "-t", f"{dur}", str(out)])
    return out


def fast_scene(name, seg, a, b, target=6.0):
    """Đoạn chờ tới giờ khấn: tua nhanh trong khung điện thoại."""
    color, title, who = ROLE["khach"]
    base = backdrop(color, (title, who))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle([100, 420, 1200, 640], radius=40, fill=(122, 31, 31))
    d.text((650, 490), "▶▶  Tua nhanh tới giờ khấn", font=font(54), fill=(255, 225, 160), anchor="mm")
    d.text((650, 575), "Trang “Lễ đồng thời” tự cập nhật trạng thái từng đền", font=font(34, False), fill="white",
           anchor="mm")
    layer = TMP / f"{name}_layer.mp4"
    base.save(TMP / f"{name}.png")
    run(["-loop", "1", "-framerate", "25", "-t", f"{target}", "-i", str(TMP / f"{name}.png"), "-c:v", "libx264",
         "-pix_fmt", "yuv420p", str(layer)])
    speed = (b - a) / target
    x, y, w, h = PHONE
    out = TMP / f"{name}.mp4"
    fc = (f"[1:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{speed},fps=25,scale={w}:{h}[s];"
          f"[0:v][s]overlay={x}:{y}:shortest=1,format=yuv420p[v]")
    run(["-i", str(layer), "-i", str(D / "seg" / f"{seg}.webm"), "-f", "lavfi", "-t", f"{target}", "-i",
         "anullsrc=r=44100:cl=stereo", "-filter_complex", fc, "-map", "[v]", "-map", "2:a", "-c:v", "libx264",
         "-preset", "medium", "-crf", "21", "-r", "25", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-t", f"{target}",
         str(out)])
    return out


def main():
    TMP.mkdir(exist_ok=True)
    parts = []
    gap = 0.6
    # Mở đầu
    t = 1.0
    ln = []
    for lid in ("n1", "n2"):
        ln.append((lid, t)); t += DUR[lid] + gap
    parts.append(card_scene("p00_mo_dau", ln, t + 0.5, "Linh Địa Việt", "Dâng lễ từ xa · khấn nhiều đền cùng lúc"))
    # Khách đặt lễ
    s = M["khach1"]
    parts.append(phone_scene("p01_khach", "khach1", seg_lines("khach1"), 0, s["end"]))
    parts.append(phone_scene("p02_thu_nhang", "thu_nhang", seg_lines("thu_nhang"), 0, M["thu_nhang"]["end"]))
    parts.append(phone_scene("p03_kiosk", "kiosk", seg_lines("kiosk"), 0, M["kiosk"]["end"]))
    c = M["cho_le"]
    parts.append(fast_scene("p04_cho", "cho_le", 0, c["marks"]["played"] + 2))
    parts.append(temple_scene("p05_den"))
    parts.append(phone_scene("p06_xong", "cho_le", [], c["marks"]["waitEnd"] - 0.5, c["end"]))
    parts.append(phone_scene("p07_canh_bao", "canh_bao", seg_lines("canh_bao"), 0, M["canh_bao"]["end"]))
    parts.append(phone_scene("p08_xem_lai", "khach2", seg_lines("khach2"), 0, M["khach2"]["end"]))
    parts.append(phone_scene("p09_admin", "admin", seg_lines("admin"), 0, M["admin"]["end"]))
    t, ln = 1.0, []
    for lid in ("n5", "n6"):
        ln.append((lid, t)); t += DUR[lid] + gap
    parts.append(card_scene("p10_ket", ln, t + 1.5, "Đã chứng minh được", None, bullets=[
        "Khấn đồng thời nhiều đền: thiết bị thật lệch nhau 0,13 giây",
        "Tìm đền theo nhu cầu và vị trí, đặt lễ chỉ vài chạm",
        "AI đếm lễ vật trên ảnh, báo thiếu cho đúng người",
        "4 vai rõ ràng: khách · thủ nhang · kiosk · quản trị"], people=False))
    lst = TMP / "list.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts))
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(OUT)])
    print(OUT, round(duration(OUT), 1), "giây")


if __name__ == "__main__":
    main()
