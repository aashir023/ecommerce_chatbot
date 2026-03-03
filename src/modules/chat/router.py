from fastapi import APIRouter, HTTPException

from src.modules.chat.schemas import ChatRequest, ChatResponse, HistoryResponse
from src.modules.chat.service import (
    generate_answer_for_chat,
    get_chat_history,
    clear_chat_history,
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
        reply = generate_answer_for_chat(
            user_message=request.message,
            user_id=request.user_id,
        )
        history = get_chat_history(request.user_id)
        return ChatResponse(
            user_id=request.user_id,
            reply=reply,
            message_count=len(history) // 2,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bot error: {str(e)}")



@router.get("/history/{user_id}", response_model=HistoryResponse, tags=["Chat"])
def get_conversation_history(user_id: str):
    """Retrieve the full conversation history for a user."""
    history = get_chat_history(user_id)
    return HistoryResponse(user_id=user_id, history=history)


@router.delete("/history/{user_id}")
def delete_conversation_history(user_id: str):
    """Clear the conversation history for a user (start fresh)."""
    clear_chat_history(user_id)
    return {"user_id": user_id, "message": "Conversation history cleared."}
