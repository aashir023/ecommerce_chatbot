"""
main.py
=======
FastAPI app exposing the chatbot as a REST API.

Endpoints:
  POST /chat           → send a message, get a reply
  DELETE /chat/history → clear conversation history for a user
  GET  /health         → health check
  GET  /               → serve the frontend UI

Run with:
    python run_server.py
  or
    uvicorn src.main:app --reload
"""
import logging
import time
from fastapi import Request

from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.modules.complaints.router import router as complaints_router
from src.modules.chat.router import router as chat_router
from pydantic import BaseModel

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Japan Electronics Customer Service Chatbot",
    description="AI-powered product assistant for japanelectronics.com.pk",
    version="1.0.0",
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
req_logger = logging.getLogger("uvicorn.error")
req_logger.setLevel(logging.INFO)

# Allow all origins for development — tighten this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_every_request(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    if request.url.path in {"/health", "/chat"}:
        req_logger.info(
        "[REQ] %s %s -> %s (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# Register routers for different modules
app.include_router(chat_router)
app.include_router(complaints_router)


class HealthResponse(BaseModel):
    status: str
    message: str

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "japan-electronics-helper-main" / "dist"
INDEX_HTML = FRONTEND_DIR / "index.html"

app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="frontend-assets")

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["UI"])
def frontend():
    if not INDEX_HTML.exists():
        raise HTTPException(status_code=404, detail="Frontend file not found.")
    return FileResponse(INDEX_HTML)


@app.get("/info", tags=["Info"])
def root():
    return {
        "name": "Japan Electronics Customer Service Bot",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", response_model=HealthResponse, tags=["Info"])
def health_check():
    return HealthResponse(status="ok", message="Bot is running")


@app.head("/health", tags=["Info"])
def health_check_head():
    return Response(status_code=200)

@app.get("/{full_path:path}", include_in_schema=False)
def spa_fallback(full_path: str):
    target = FRONTEND_DIR / full_path
    if target.exists() and target.is_file():
        return FileResponse(target)
    return FileResponse(INDEX_HTML)
