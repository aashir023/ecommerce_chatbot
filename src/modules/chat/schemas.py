from pydantic import BaseModel, Field


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