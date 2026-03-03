"""
main.py
=======
FastAPI app exposing the chatbot as a REST API.

Endpoints:
  POST /chat           → send a message, get a reply
  DELETE /chat/history → clear conversation history for a user
  GET  /health         → health check
  GET  /               → API info

Run with:
    python run_server.py
  or
    uvicorn src.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from src.modules.chat.router import router as chat_router
from pydantic import BaseModel
# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Japan Electronics Customer Service Chatbot",
    description="AI-powered product assistant for japanelectronics.com.pk",
    version="1.0.0",
)

# Allow all origins for development — tighten this in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the chat router with all its endpoints
app.include_router(chat_router)

class HealthResponse(BaseModel):
    status: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


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
