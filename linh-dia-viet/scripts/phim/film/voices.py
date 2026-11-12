"""Tạo giọng đọc cho từng câu thoại (Edge TTS, miễn phí) + ghi độ dài."""
import asyncio, json, subprocess, sys
from pathlib import Path
import edge_tts

D = Path(__file__).parent
VOICE = {"khach": ("vi-VN-NamMinhNeural", "+4%", "+2Hz"), "thu_nhang": ("vi-VN-NamMinhNeural", "-12%", "-14Hz"),
         "kiosk": ("vi-VN-HoaiMyNeural", "+6%", "+6Hz"), "admin": ("vi-VN-HoaiMyNeural", "+2%", "-4Hz"),
         "dan_chuyen": ("vi-VN-HoaiMyNeural", "-4%", "+0Hz")}


async def main():
    lines = json.loads((D / "lines.json").read_text(encoding="utf-8"))
    dur = {}
    for k, (who, text) in lines.items():
        out = D / "voice" / f"{k}.mp3"
        if not out.exists() or "-f" in sys.argv:
            v, rate, pitch = VOICE[who]
            for attempt in range(6):  # Edge đôi khi trả rỗng: thử lại, lần cuối bỏ chỉnh cao độ
                try:
                    await edge_tts.Communicate(text, v, rate=rate, pitch=pitch if attempt < 4 else "+0Hz").save(str(out))
                    break
                except edge_tts.exceptions.NoAudioReceived:
                    out.unlink(missing_ok=True)
                    print("thử lại", k, attempt)
                    await asyncio.sleep(6)
            else:
                raise SystemExit(f"Không tạo được giọng cho {k}")
        dur[k] = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                                "-of", "csv=p=0", str(out)]).decode())
    (D / "durations.json").write_text(json.dumps(dur, indent=1))
    print(round(sum(dur.values())), "giây thoại")

asyncio.run(main())
