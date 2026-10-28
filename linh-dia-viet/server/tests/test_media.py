import subprocess
from pathlib import Path

import pytest

from app import audio, tts
from app.storage import get_storage, signed_url, verify_signature


def _tone(path: Path, seconds: float, fmt: str = "wav"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency=300:duration={seconds}",
                    str(path)], check=True)
    return path


def test_sniff():
    assert audio.sniff_audio(b"\x1a\x45\xdf\xa3....") == "webm"
    assert audio.sniff_audio(b"OggS....") == "ogg"
    assert audio.sniff_audio(b"\x00\x00\x00\x18ftypM4A ") == "mp4"
    assert audio.sniff_audio(b"RIFF\x00\x00\x00\x00WAVEfmt ") == "wav"
    assert audio.sniff_audio(b"ID3\x04") == "mp3"
    assert audio.sniff_audio(b"<html>") is None


def test_normalize_mono_44k(tmp_path):
    out = tmp_path / "o.mp3"
    dur = audio.normalize_to_mp3(_tone(tmp_path / "a.wav", 3), out)
    st = audio.probe(out)["streams"][0]
    assert abs(dur - 3) < 0.3 and st["channels"] == 1 and st["sample_rate"] == "44100" and st["codec_name"] == "mp3"


def test_too_long_rejected(tmp_path):
    with pytest.raises(audio.AudioError):
        audio.normalize_to_mp3(_tone(tmp_path / "a.wav", 5), tmp_path / "o.mp3", max_seconds=3)


def test_not_audio_rejected(tmp_path):
    p = tmp_path / "x.mp3"
    p.write_text("không phải âm thanh")
    with pytest.raises(audio.AudioError):
        audio.normalize_to_mp3(p, tmp_path / "o.mp3")


def test_split_chunks():
    text = "Câu một dài. " * 50
    chunks = tts.split_chunks(text, 100)
    assert all(len(c.encode()) <= 100 for c in chunks)
    assert "".join(chunks).replace(" ", "") == text.replace(" ", "")


def test_tts_cache(monkeypatch, db):
    calls = []
    real = tts.FakeTTS.synthesize

    def spy(self, text, voice, dst):
        calls.append(text)
        real(self, text, voice, dst)
    monkeypatch.setattr(tts.FakeTTS, "synthesize", spy)
    k1, d1 = tts.synthesize_cached("Kính lạy chư vị năm 2026", "v1")
    k2, _ = tts.synthesize_cached("Kính lạy chư vị năm 2026", "v1")
    k3, _ = tts.synthesize_cached("Kính lạy chư vị năm 2026", "v2")
    assert k1 == k2 != k3 and len(calls) == 2
    assert "hai nghìn không trăm hai mươi sáu" in calls[0]  # TTS nhận văn bản đã chuẩn hoá
    assert get_storage().exists(k1) and d1 > 1


def test_signed_url():
    url = signed_url("tts/abc.mp3", ttl=60, now=1000)
    q = dict(x.split("=") for x in url.split("?")[1].split("&"))
    assert verify_signature("tts/abc.mp3", int(q["exp"]), q["sig"], now=1000)
    assert not verify_signature("tts/abc.mp3", int(q["exp"]), q["sig"], now=2000)  # hết hạn
    assert not verify_signature("tts/khac.mp3", int(q["exp"]), q["sig"], now=1000)


def test_voice_spec_rate_pitch(monkeypatch, tmp_path):
    """TTS_VOICE "tên,tốc độ,cao độ": Edge nhận rate/pitch; nhà cung cấp khác chỉ lấy tên giọng."""
    assert tts.split_voice("vi-VN-NamMinhNeural,-8%,-6Hz") == ("vi-VN-NamMinhNeural", {"rate": "-8%", "pitch": "-6Hz"})
    assert tts.split_voice("vi-VN-HoaiMyNeural") == ("vi-VN-HoaiMyNeural", {})
    import edge_tts
    calls = []

    class FakeCommunicate:
        def __init__(self, text, voice, **kw):
            calls.append((voice, kw))

        async def save(self, path):
            Path(path).write_bytes(b"mp3")
    monkeypatch.setattr(edge_tts, "Communicate", FakeCommunicate)
    tts.EdgeTTS().synthesize("Nam mô A Di Đà Phật", "vi-VN-NamMinhNeural,-8%,-6Hz", tmp_path / "a.mp3")
    assert calls == [("vi-VN-NamMinhNeural", {"rate": "-8%", "pitch": "-6Hz"})]
