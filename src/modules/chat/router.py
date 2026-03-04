import logging
from fastapi import APIRouter, HTTPException, Request
from src.modules.chat.schemas import ChatRequest, ChatResponse, HistoryResponse
from src.modules.chat.service import (
    send_message,
    fetch_history,
    reset_history,
)

router = APIRouter(prefix="/chat", tags=["Chat"])
chat_logger = logging.getLogger("uvicorn.error")

@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest, raw_request: Request):
    raw_request.state.chat_user_id = request.user_id
    chat_logger.info("[CHAT_HIT] user_id=%s msg_len=%d", request.user_id, len(request.message))
    try:
        reply = send_message(
            user_id=request.user_id,
            message=request.message,
        )
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot error: {str(e)}")


@router.get("/history/{user_id}", response_model=HistoryResponse, tags=["Chat"])
def get_conversation_history(user_id: str):
    """Retrieve the full conversation history for a user."""
    history = fetch_history(user_id)
    return HistoryResponse(user_id=user_id, history=history)


@router.delete("/history/{user_id}")
def delete_conversation_history(user_id: str):
    """Clear the conversation history for a user (start fresh)."""
    reset_history(user_id)
    return {"user_id": user_id, "message": "Conversation history cleared."}
