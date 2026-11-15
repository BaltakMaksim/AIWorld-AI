import asyncio
import json
import os
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

load_dotenv()

import tts

# ---------------------------------------------------------------------------
# Настройки
# ---------------------------------------------------------------------------

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")


@asynccontextmanager
async def lifespan(application: FastAPI):
    task = asyncio.create_task(tts.warmup_tts())
    yield
    task.cancel()


app = FastAPI(title="NPC Chat Server", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Модели данных
# ---------------------------------------------------------------------------


class RequestText(BaseModel):
    text: str


class ResponseText(BaseModel):
    text: str
    audio: str | None = None
    audio_format: str = "wav"


# ---------------------------------------------------------------------------
# Системный промпт
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
Ты — игровой персонаж.
Отвечай строго в формате JSON без дополнительных комментариев.
Твой ответ должен содержать ровно одно поле "text" с текстом ответа.
Пример: {"text": "Привет! Рад тебя видеть!"}"""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.post("/chat", response_model=ResponseText)
async def chat(request: RequestText):
    """Принимает JSON {"text": "..."} и возвращает текст + озвучку в base64."""

    prompt = f"{SYSTEM_PROMPT}\n\nПользователь: {request.text}"

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=120.0,
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data.get("response", "")

            parsed = _extract_json(raw)
            answer = parsed.get("text", raw)

        except httpx.HTTPStatusError as exc:
            return JSONResponse(
                status_code=exc.response.status_code,
                content={"text": f"Ошибка Ollama: {exc.response.text}", "audio": None},
            )
        except Exception as exc:
            return JSONResponse(
                status_code=500,
                content={"text": f"Ошибка: {str(exc)}", "audio": None},
            )

    audio = await tts.synthesize(answer)
    return ResponseText(text=answer, audio=audio)


# ---------------------------------------------------------------------------
# Утилиты
# ---------------------------------------------------------------------------

def _extract_json(raw: str) -> dict:
    """Пытается распарсить JSON из ответа LLM, вырезая обёртки markdown."""
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[len("```json"):]
    if raw.endswith("```"):
        raw = raw[:-3]
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Запуск
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
