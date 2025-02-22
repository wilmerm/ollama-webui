import os
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic_settings import BaseSettings
import httpx
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)

class Settings(BaseSettings):
    debug: bool = False
    allowed_hosts: str = "*"

settings = Settings()
app = FastAPI(debug=settings.debug)

# Configurar CORS para permitir Vue
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Para desarrollo local
    allow_methods=["*"],
    allow_headers=["*"],
)


async def generate_ollama_stream(ollama_url: str, json: dict):
    async with httpx.AsyncClient() as client:  # Cliente dentro del generador
        async with client.stream(
            "POST",
            ollama_url,
            json=json,
            timeout=60,
        ) as response:
            if response.status_code != 200:
                error_detail = await response.text()
                raise HTTPException(status_code=response.status_code, detail=error_detail)

            async for chunk in response.aiter_bytes():  # Transmite chunk por chunk
                yield chunk


@app.post("/api/ollama")
async def ask_ollama(payload: dict):

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_url = f"{ollama_base_url}/api/chat"

    # El tiempo de espera es importante ajustarlo a la capacidad de la API
    # Un modelo pesado puede tardar más en responder y se puede agotar el tiempo
    default_timeout = float(os.getenv("DEFAULT_TIMEOUT", 60))

    default_model = os.getenv("DEFAULT_MODEL", "deepseek-r1:1.5b")
    model = payload.get("model", default_model)

    default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", 0.5))
    temperature = payload.get("temperature", default_temperature)

    messages = payload.get("messages", [])
    stream = payload.get("stream", False)

    logging.info(f"{model=}, {default_timeout=}, {stream=} {ollama_url=}")

    try:
        if stream:
            return StreamingResponse(
                generate_ollama_stream(
                    ollama_url,
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                        },
                    }
                ),
                media_type="application/x-ndjson",
            )
        else:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    ollama_url,
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                        },
                    },
                    timeout=default_timeout,
                )
                response_data = response.json()
                if response_data.get("error"):
                    raise HTTPException(status_code=400, detail=response_data["error"])
                return {"response": response_data["message"]["content"]}

    except HTTPException as he:
        raise he
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


dist_path = Path(__file__).parent.parent / "frontend" / "vue-app" / "dist"
app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")