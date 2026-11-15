"""Модуль озвучки (TTS) на базе Edge TTS."""
import asyncio
import base64
import io
import os
import wave

import edge_tts
import miniaudio

TTS_VOICE = os.getenv("TTS_VOICE", "ru-RU-DmitryNeural")
TTS_RETRIES = 3
TTS_SAMPLE_RATE = 24000


async def synthesize(text: str) -> str | None:
    """Возвращает base64 WAV для переданного текста либо None при неудаче."""
    if not text or not text.strip():
        return None

    for attempt in range(TTS_RETRIES):
        try:
            communicate = edge_tts.Communicate(text, TTS_VOICE)
            buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer += chunk.get("data", b"")
            if buffer:
                return base64.b64encode(_mp3_to_wav(bytes(buffer))).decode("ascii")
        except Exception:
            pass
        await asyncio.sleep(1.0 * (attempt + 1))

    return None


def _mp3_to_wav(mp3: bytes) -> bytes:
    """Перекодирует mp3 в несжатый PCM WAV (моно 24 кГц, 16 бит)."""
    decoded = miniaudio.decode(
        mp3,
        output_format=miniaudio.SampleFormat.SIGNED16,
        nchannels=1,
        sample_rate=TTS_SAMPLE_RATE,
    )

    container = io.BytesIO()
    with wave.open(container, "wb") as wav_file:
        wav_file.setnchannels(decoded.nchannels)
        wav_file.setsampwidth(decoded.sample_width)
        wav_file.setframerate(decoded.sample_rate)
        wav_file.writeframes(bytes(decoded.samples))
    return container.getvalue()


async def warmup_tts() -> None:
    """Прогревает Edge TTS, чтобы первый реальный запрос не упал."""
    for _ in range(TTS_RETRIES):
        try:
            communicate = edge_tts.Communicate("Привет", TTS_VOICE)
            async for _ in communicate.stream():
                continue
            return
        except Exception:
            await asyncio.sleep(1.0)
