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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.rag_engine import generate_answer, clear_history, get_history

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Japan Electronics Customer Service Bot",
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


# ── Request / Response schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: str = Field(
        default="anonymous",
        description="Unique user/session ID to maintain conversation history",
        examples=["user_123", "session_abc"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The customer's message or question",
        examples=["Do you have a 1.5 ton Haier AC in stock?"],
    )


class ChatResponse(BaseModel):
    user_id: str
    reply: str
    message_count: int   # how many turns in this user's history so far


class HistoryResponse(BaseModel):
    user_id: str
    history: list[dict]


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


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Send a customer message and receive an AI-generated reply.

    The bot will:
    - Search the product catalogue for relevant items
    - Use conversation history to handle follow-up questions
    - Respond as a helpful Japan Electronics customer service agent
    """
    try:
        reply = generate_answer(
            user_message=request.message,
            user_id=request.user_id,
        )
        history = get_history(request.user_id)
        return ChatResponse(
            user_id=request.user_id,
            reply=reply,
            message_count=len(history) // 2,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot error: {str(e)}")


@app.get("/chat/history/{user_id}", response_model=HistoryResponse, tags=["Chat"])
def get_conversation_history(user_id: str):
    """Retrieve the full conversation history for a user."""
    history = get_history(user_id)
    return HistoryResponse(user_id=user_id, history=history)


@app.delete("/chat/history/{user_id}", tags=["Chat"])
def delete_conversation_history(user_id: str):
    """Clear the conversation history for a user (start fresh)."""
    clear_history(user_id)
    return {"user_id": user_id, "message": "Conversation history cleared."}
