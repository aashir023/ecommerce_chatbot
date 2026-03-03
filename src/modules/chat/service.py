"""
Service layer for chat-related operations, 
including message processing, complaint handling, 
and conversation history management.
"""
from src.modules.complaints.service import (
    extract_case_id,
    track_complaint,
    is_complaint_intent,
    start_complaint_flow,
    handle_complaint_flow,
)
from src.db.repositories.chat_repo import (
    save_chat_message,
    get_chat_message_count,
    get_chat_messages,
)

from src.modules.complaints.workflow import get_state
from src.modules.rag.service import generate_answer, clear_history


def send_message(user_id: str, message: str) -> tuple[str, int, dict | None]:
    # Persist user message
    save_chat_message(user_id, "user", message)

    # 1) Tracking request path
    case_id = extract_case_id(message)
    if case_id:
        _, reply, ui_payload = track_complaint(case_id)
        save_chat_message(user_id, "assistant", reply, {"ui_payload": ui_payload} if ui_payload else None)
        return reply, _message_count_for_user(user_id), ui_payload


    # 2) Active complaint workflow path
    state = get_state(user_id)
    if state["stage"] != "idle":
        handled, reply, ui_payload = handle_complaint_flow(user_id, message)
        if handled:
            save_chat_message(user_id, "assistant", reply, {"ui_payload": ui_payload} if ui_payload else None)
            return reply, _message_count_for_user(user_id), ui_payload

    # 3) Complaint intent start
    if is_complaint_intent(message):
        reply = start_complaint_flow(user_id)
        save_chat_message(user_id, "assistant", reply)
        return reply, _message_count_for_user(user_id), None

    # 4) Normal RAG
    reply = generate_answer(user_message=message, user_id=user_id)
    save_chat_message(user_id, "assistant", reply)
    return reply, _message_count_for_user(user_id), None

def _message_count_for_user(user_id: str) -> int:
    # convert total messages to approximate user-assistant turns
    return get_chat_message_count(user_id) // 2


def fetch_history(user_id: str) -> list[dict]:
    return get_chat_messages(user_id)


def reset_history(user_id: str) -> None:
    clear_history(user_id)
