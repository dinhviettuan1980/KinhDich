"""Chuyển văn bản thành giọng đọc. Nhà cung cấp chọn qua TTS_PROVIDER: edge | google | fpt | fake.

Kết quả được cache theo hash(provider + giọng + văn bản đã chuẩn hoá), lưu ở storage key `tts/<hash>.mp3`
(đã chuẩn hoá loudnorm, MP3 mono 44.1kHz).
"""
import asyncio
import base64
import hashlib
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Protocol

import httpx

from . import audio
from .config import get_settings
from .prayer_text import normalize_for_tts
from .storage import get_storage


class TTSError(RuntimeError):
    pass


class TTSProvider(Protocol):
    name: str
    max_chunk_bytes: int

    def synthesize(self, text: str, voice: str, dst: Path) -> None:
        """Ghi file âm thanh (mp3) cho một đoạn văn bản ngắn."""


class EdgeTTS:
    # edge-tts chạy gần bằng thời gian thực (VPS: ~22s cho 33s audio) → cắt theo câu và gọi song song rồi nối lại.
    name, max_chunk_bytes = "edge", 3000
    concurrency = 4
    one_sentence_per_chunk = True

    def synthesize(self, text, voice, dst):
        self.synthesize_all([text], voice, [dst])

    def synthesize_all(self, texts, voice, dsts):
        import edge_tts

        async def run():
            sem = asyncio.Semaphore(self.concurrency)

            async def one(text, dst):
                async with sem:
                    for attempt in range(5):  # dịch vụ thỉnh thoảng trả NoAudioReceived khi gọi dồn dập
                        try:
                            await edge_tts.Communicate(text, voice).save(str(dst))
                            return
                        except Exception:
                            if attempt == 4:
                                raise
                            await asyncio.sleep(0.7 * 2 ** attempt)  # 0.7, 1.4, 2.8, 5.6s
            await asyncio.gather(*(one(t, d) for t, d in zip(texts, dsts)))
        asyncio.run(run())


class GoogleTTS:
    """Google Cloud Text-to-Speech (REST + API key). Giọng ví dụ: vi-VN-Wavenet-A."""
    name, max_chunk_bytes = "google", 4800

    def synthesize(self, text, voice, dst):
        key = get_settings().google_tts_api_key
        if not key:
            raise TTSError("Thiếu GOOGLE_TTS_API_KEY")
        r = httpx.post("https://texttospeech.googleapis.com/v1/text:synthesize", params={"key": key}, timeout=60,
                       json={"input": {"text": text}, "voice": {"languageCode": "vi-VN", "name": voice},
                             "audioConfig": {"audioEncoding": "MP3"}})
        if r.status_code != 200:
            raise TTSError(f"Google TTS lỗi {r.status_code}")
        dst.write_bytes(base64.b64decode(r.json()["audioContent"]))


class FptTTS:
    """FPT.AI TTS v5: trả về URL bất đồng bộ, phải chờ file sẵn sàng. Giọng ví dụ: banmai, leminh."""
    name, max_chunk_bytes = "fpt", 4500

    def synthesize(self, text, voice, dst):
        key = get_settings().fpt_tts_api_key
        if not key:
            raise TTSError("Thiếu FPT_TTS_API_KEY")
        r = httpx.post("https://api.fpt.ai/hmi/tts/v5", content=text.encode(), timeout=30,
                       headers={"api_key": key, "voice": voice, "speed": "0"})
        url = r.json().get("async") if r.status_code == 200 else None
        if not url:
            raise TTSError(f"FPT TTS lỗi {r.status_code}")
        for _ in range(30):
            f = httpx.get(url, timeout=30)
            if f.status_code == 200 and len(f.content) > 1000:
                dst.write_bytes(f.content)
                return
            time.sleep(2)
        raise TTSError("FPT TTS quá thời gian chờ")


class FakeTTS:
    """Dùng cho test/dev offline: tạo âm báo có độ dài tỉ lệ với văn bản."""
    name, max_chunk_bytes = "fake", 100_000

    def synthesize(self, text, voice, dst):
        audio.sine(dst, seconds=max(1.5, min(len(text) / 60, 20)))


PROVIDERS = {"edge": EdgeTTS, "google": GoogleTTS, "fpt": FptTTS, "fake": FakeTTS}


def get_provider() -> TTSProvider:
    name = get_settings().tts_provider
    if name not in PROVIDERS:
        raise TTSError(f"TTS_PROVIDER không hỗ trợ: {name}")
    return PROVIDERS[name]()


def split_chunks(text: str, max_bytes: int, pack: bool = True) -> list[str]:
    """Cắt theo câu để mỗi đoạn không vượt giới hạn byte của nhà cung cấp.
    pack=False: mỗi câu một đoạn (để gọi song song)."""
    sentences = re.split(r"(?<=[.!?…])\s+|\n+", text)
    chunks, cur = [], ""
    for s in filter(None, (x.strip() for x in sentences)):
        cand = f"{cur} {s}".strip()
        if pack and len(cand.encode()) <= max_bytes:
            cur = cand
            continue
        if cur:
            chunks.append(cur)
        while len(s.encode()) > max_bytes:  # câu quá dài: cắt cứng theo từ
            cut = s[: max_bytes // 3].rsplit(" ", 1)[0] or s[: max_bytes // 3]
            chunks.append(cut)
            s = s[len(cut):].strip()
        cur = s
    if cur:
        chunks.append(cur)
    return chunks


def cache_key(text: str, voice: str, provider: str) -> str:
    h = hashlib.sha256(f"{provider}\x00{voice}\x00{text}".encode()).hexdigest()[:40]
    return f"tts/{h}.mp3"


_inflight: dict[str, threading.Lock] = {}
_inflight_guard = threading.Lock()


def synthesize_cached(text: str, voice: str | None = None) -> tuple[str, float]:
    """Trả về (storage key, thời lượng giây). Gọi nhà cung cấp chỉ khi chưa có trong cache.
    Cùng một bài đang được tạo ở luồng khác (vd tạo sẵn lúc đặt đơn) thì chờ luồng đó, không tạo lại."""
    provider = get_provider()
    voice = voice or get_settings().tts_voice
    spoken = normalize_for_tts(text)
    key = cache_key(spoken, voice, provider.name)
    storage = get_storage()
    with _inflight_guard:
        lock = _inflight.setdefault(key, threading.Lock())
    with lock:
        if storage.exists(key):
            return key, audio.duration_of(storage.local_path(key))
        dur = _synthesize(provider, spoken, voice, key)
    with _inflight_guard:
        _inflight.pop(key, None)
    return key, dur


def _synthesize(provider, spoken: str, voice: str, key: str) -> float:
    storage = get_storage()
    with tempfile.TemporaryDirectory() as d:
        chunks = split_chunks(spoken, provider.max_chunk_bytes,
                              pack=not getattr(provider, "one_sentence_per_chunk", False))
        parts = [Path(d) / f"part{i}.mp3" for i in range(len(chunks))]
        if hasattr(provider, "synthesize_all"):
            provider.synthesize_all(chunks, voice, parts)
        else:
            for chunk, p in zip(chunks, parts):
                provider.synthesize(chunk, voice, p)
        if not parts:
            raise TTSError("Văn bản trống")
        raw = Path(d) / "raw.mp3"
        if len(parts) == 1:
            raw = parts[0]
        else:
            audio.concat_mp3(parts, raw)
        out = Path(d) / "out.mp3"
        dur = audio.normalize_to_mp3(raw, out)
        storage.put_file(out, key)
    return dur
