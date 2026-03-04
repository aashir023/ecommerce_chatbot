"""
Service layer for chat-related operations, 
including message processing, complaint handling, 
and conversation history management.
"""

from src.db.repositories.chat_repo import (
    save_chat_message,
    get_chat_messages
)

from src.modules.rag.service import generate_answer, clear_history

def send_message(user_id: str, message: str) -> str:
    save_chat_message(user_id, "user", message)
    reply = generate_answer(user_message=message, user_id=user_id)
    save_chat_message(user_id, "assistant", reply)
    return reply


def fetch_history(user_id: str) -> list[dict]:
    return get_chat_messages(user_id)


def reset_history(user_id: str) -> None:
    clear_history(user_id)
