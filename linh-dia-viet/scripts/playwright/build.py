"""Dựng video demo: tiêu đề → quay màn hình (đoạn chờ tua ×4) → thẻ giới thiệu → clip xem lại (có tiếng)."""
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).parent / "out"
W, H = 1080, 2340
def _font(*names):
    for n in names:
        if Path(n).exists():
            return n
    raise FileNotFoundError(f"Không thấy font: {names}")


FONT = _font("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FONT_R = _font("/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
m = json.loads((D / "marks.json").read_text())
ws, we = m["waitStart"], m["waitEnd"]


def card(path, lines, sub=None):
    im = Image.new("RGB", (W, H), (92, 22, 22))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H // 2 - 330, W, H // 2 + 330], fill=(122, 31, 31))
    d.rectangle([0, H // 2 + 322, W, H // 2 + 330], fill=(224, 168, 58))
    y = H // 2 - 200
    for text, size, font, color in lines:
        f = ImageFont.truetype(font, size)
        d.text((W // 2, y), text, font=f, fill=color, anchor="mm")
        y += int(size * 1.6)
    im.save(path)


card(D / "title.png", [("Linh Địa Việt", 96, FONT, (255, 225, 160)),
                       ("Lễ chùa từ xa", 60, FONT_R, "white"), ("", 30, FONT_R, "white"),
                       ("Demo quy trình khách hàng", 52, FONT, "white"),
                       ("đăng ký → sắm lễ → dâng sớ → chốt → xem lại", 40, FONT_R, (240, 220, 200))])
card(D / "clipcard.png", [("Clip xem lại", 92, FONT, (255, 225, 160)),
                          ("khách nhận trong Lịch sử lễ", 52, FONT_R, "white"), ("", 30, FONT_R, "white"),
                          ("Mâm lễ trước – trong – sau khi khấn", 44, FONT_R, (240, 220, 200)),
                          ("kèm bài khấn đã đọc tại đền (bật tiếng)", 44, FONT_R, (240, 220, 200)),
                          ("Ảnh mâm hiện là ảnh giả lập — sẽ thay bằng camera thật", 34, FONT_R, (230, 190, 150))])
# nhãn tua nhanh
im = Image.new("RGBA", (420, 90), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle([0, 0, 419, 89], radius=45, fill=(0, 0, 0, 170))
d.text((210, 45), "Tua nhanh ×4", font=ImageFont.truetype(FONT, 44), fill=(255, 225, 160), anchor="mm")
im.save(D / "ff.png")

scr = f"scale={W}:{H}:flags=lanczos,fps=25,format=yuv420p,setsar=1"
box = f"scale={W}:-2,pad={W}:{H}:0:(oh-ih)/2:color=0x5c1616,fps=25,format=yuv420p,setsar=1"
fc = (
    f"[0:v]{scr},trim=0:{ws},setpts=PTS-STARTPTS[s1];"
    f"[0:v]{scr},trim={ws}:{we},setpts=(PTS-STARTPTS)/4[s2r];"
    f"[s2r][4:v]overlay=(W-w)/2:180:shortest=1[s2];"
    f"[0:v]{scr},trim={we},setpts=PTS-STARTPTS[s3];"
    f"[1:v]fps=25,format=yuv420p,setsar=1[t];[2:v]fps=25,format=yuv420p,setsar=1[c];"
    f"[3:v]{box}[clip];"
    f"[t][s1][s2][s3][c]concat=n=5:v=1:a=0[pre];"
    f"[pre][clip]concat=n=2:v=1:a=0[v];"
    f"[3:a]adelay=0|0[ca]"
)
# độ dài phần im lặng trước clip = độ dài [pre]
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                     str(D / "screen.webm")]).decode())
pre = 3.5 + ws + (we - ws) / 4 + (dur - we) + 4.0
fc = fc.replace("[3:a]adelay=0|0[ca]", f"[3:a]aresample=44100,adelay={int(pre * 1000)}:all=1[ca]")
cmd = ["ffmpeg", "-v", "error", "-y",
       "-i", str(D / "screen.webm"),
       "-loop", "1", "-t", "3.5", "-i", str(D / "title.png"),
       "-loop", "1", "-t", "4", "-i", str(D / "clipcard.png"),
       "-i", str(D / "clip.mp4"),
       "-loop", "1", "-i", str(D / "ff.png"),
       "-filter_complex", fc, "-map", "[v]", "-map", "[ca]",
       "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest",
       str(D / "linh-dia-viet-demo.mp4")]
subprocess.run(cmd, check=True)
print("pre", round(pre, 1), "s")
