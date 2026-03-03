from src.modules.rag.service import generate_answer, get_history, clear_history


def generate_answer_for_chat(user_message: str, user_id: str):
    return generate_answer(user_message=user_message, user_id=user_id)


def get_chat_history(user_id: str):
    return get_history(user_id)


def clear_chat_history(user_id: str):
    clear_history(user_id)
