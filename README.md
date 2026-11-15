# AI NPC Chat Server

FastAPI-сервер для общения с игровым персонажем (NPC) через локальную LLM (Ollama) с озвучкой Edge TTS.

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Скопируйте шаблон и при необходимости измените значения:

```bash
cp .env.example .env
```

### Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `TTS_VOICE` | Голос Edge TTS | `ru-RU-DmitryNeural` |
| `OLLAMA_URL` | Адрес Ollama API | `http://localhost:11434` |
| `OLLAMA_MODEL` | Имя модели Ollama | `qwen2.5:7b` |

## Запуск

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API

### POST /chat

```json
{ "text": "Привет!" }
```

Ответ:

```json
{ "text": "...", "audio": "<base64 wav>", "audio_format": "wav" }
```
