import os
import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import httpx
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def build_timeout(default_seconds: float) -> httpx.Timeout:
    # Separate connect and read windows for large model responses.
    return httpx.Timeout(connect=10.0, read=default_seconds, write=10.0, pool=10.0)


def extract_ollama_error(status_code: int, body: str) -> str:
    try:
        payload = json.loads(body)
        if isinstance(payload, dict) and payload.get("error"):
            return str(payload["error"])
    except Exception:
        pass

    if body:
        return body[:300]
    return f"Ollama returned status {status_code}"

class Message(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=10000)

class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(0.5, ge=0.0, le=2.0)
    stream: Optional[bool] = False

    @field_validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError("Messages cannot be empty")
        return v

logging.basicConfig(level=logging.INFO)

class Settings(BaseSettings):
    debug: bool = False
    # allwed all hosts
    allowed_hosts: str = "*"
    # allowed all origins for CORS
    cors_origins: str = "*"

settings = Settings()
app = FastAPI(debug=settings.debug)

# Parse allowed hosts and CORS origins
allowed_hosts_list = [host.strip() for host in settings.allowed_hosts.split(",")]
cors_origins_list = [origin.strip() for origin in settings.cors_origins.split(",")]

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts_list
)

# Configure CORS with specific origins (not wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # Only allow necessary methods
    allow_headers=["*"],  # Only allow necessary headers
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src *;"
    )
    return response


async def generate_ollama_stream(ollama_url: str, payload: dict, timeout: float = 60.0):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            ollama_url,
            json=payload,
            timeout=build_timeout(timeout),
        ) as response:
            if response.status_code != 200:
                error_detail = await response.text()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=extract_ollama_error(response.status_code, error_detail),
                )

            async for chunk in response.aiter_bytes():  # Transmite chunk por chunk
                yield chunk


@app.get("/api/models")
async def get_models():
    """
    Get available models from Ollama API.
    Returns a list of models with their details and running status.
    """
    ollama_base_url = get_ollama_base_url()

    try:
        async with httpx.AsyncClient() as client:
            # List of available models
            list_resp = await client.get(
                f"{ollama_base_url}/api/tags",
                timeout=build_timeout(10),
            )
            if list_resp.status_code != 200:
                raise HTTPException(status_code=503, detail="Ollama API is not available")

            # List of running models
            ps_resp = await client.get(
                f"{ollama_base_url}/api/ps",
                timeout=build_timeout(10),
            )
            if ps_resp.status_code != 200:
                raise HTTPException(status_code=503, detail="Ollama API is not available")

        available_models = list_resp.json().get("models", [])
        running_models = {m["name"] for m in ps_resp.json().get("models", [])}

        # Prepare the response with model details
        models_info = []
        for model in available_models:
            models_info.append({
                "name": model.get("name"),
                "id": model.get("digest", ""),
                "size": model.get("size", ""),
                "modified": model.get("modified_at", ""),
                "running": model.get("name") in running_models
            })

        return {
            "models": models_info,
            "running_models": list(running_models)
        }

    except HTTPException as he:
        raise he
    except httpx.ConnectError:
        logging.error("Cannot connect to Ollama service")
        raise HTTPException(status_code=503, detail="AI service unavailable")
    except httpx.TimeoutException as e:
        logging.error(f"Request timeout to Ollama service: {e}")
        raise HTTPException(status_code=504, detail="AI service timeout")
    except Exception as e:
        logging.error(f"Unexpected error: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/ollama")
async def ask_ollama(request: ChatRequest):

    ollama_base_url = get_ollama_base_url()
    ollama_url = f"{ollama_base_url}/api/chat"

    # El tiempo de espera es importante ajustarlo a la capacidad de la API
    # Un modelo pesado puede tardar más en responder y se puede agotar el tiempo
    default_timeout = float(os.getenv("DEFAULT_TIMEOUT", 60))

    default_model = os.getenv("DEFAULT_MODEL", "llama3.3")
    model = request.model or default_model

    default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", 0.5) or 0.5)
    temperature = request.temperature if request.temperature is not None else default_temperature

    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    stream = request.stream

    logging.info(f"Request: model={model}, timeout={default_timeout}, stream={stream}")

    try:
        if stream:
            return StreamingResponse(
                generate_ollama_stream(
                    ollama_url,
                    payload={
                        "model": model,
                        "messages": messages,
                        "stream": True,
                        "options": {
                            "temperature": temperature,
                        },
                    },
                    timeout=default_timeout,
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
                    timeout=build_timeout(default_timeout),
                )
                if response.status_code != 200:
                    error_text = response.text
                    detail = extract_ollama_error(response.status_code, error_text)
                    logging.error(f"Ollama API error ({response.status_code}): {detail}")
                    raise HTTPException(status_code=response.status_code, detail=detail)

                response_data = response.json()
                if response_data.get("error"):
                    detail = str(response_data["error"])
                    logging.error(f"Ollama API error: {detail}")
                    raise HTTPException(status_code=400, detail=detail)

                content = response_data.get("message", {}).get("content")
                if content is None:
                    raise HTTPException(status_code=502, detail="Invalid AI service response")

                return {"response": content}

    except HTTPException as he:
        raise he
    except httpx.TimeoutException:
        logging.error("Request timeout to Ollama service")
        raise HTTPException(status_code=504, detail="AI service timeout")
    except httpx.ConnectError:
        logging.error("Cannot connect to Ollama service")
        raise HTTPException(status_code=503, detail="AI service unavailable")
    except Exception as e:
        logging.error(f"Unexpected error: {type(e).__name__}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


dist_path = Path(__file__).parent.parent / "frontend" / "vue-app" / "dist"
if dist_path.exists():
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        index_file = dist_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"detail": "Not Found"}
