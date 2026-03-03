from fastapi import APIRouter, HTTPException

from src.modules.chat.schemas import ChatRequest, ChatResponse, HistoryResponse
from src.modules.chat.service import (
    send_message,
    fetch_history,
    reset_history,
)

router = APIRouter(prefix="/chat", tags=["Chat"])



@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Send a customer message and receive an AI-generated reply.

    The bot will:
    - Search the product catalogue for relevant items
    - Use conversation history to handle follow-up questions
    - Respond as a helpful Japan Electronics customer service agent
    """
    try:
        reply, message_count, ui_payload = send_message(
            user_id=request.user_id,
            message=request.message,
        )
        return ChatResponse(
            user_id=request.user_id,
            reply=reply,
            message_count=message_count,
            ui_payload=ui_payload,
        )

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
