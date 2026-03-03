"""
History store for conversation context and last retrieved products.
"""
from collections import defaultdict

MAX_HISTORY_TURNS = 10

_conversation_history: dict[str, list[dict]] = defaultdict(list)
_last_product_results: dict[str, list[dict]] = defaultdict(list)


def get_history(user_id: str) -> list[dict]:
    return _conversation_history.get(user_id, [])


def append_message(user_id: str, role: str, content: str) -> None:
    _conversation_history[user_id].append({"role": role, "content": content})


def trim_history(user_id: str) -> list[dict]:
    history = _conversation_history[user_id]
    if len(history) > MAX_HISTORY_TURNS * 2:
        _conversation_history[user_id] = history[-(MAX_HISTORY_TURNS * 2):]
    return _conversation_history[user_id]


def clear_history(user_id: str) -> None:
    _conversation_history.pop(user_id, None)
    _last_product_results.pop(user_id, None)


def get_last_product_results(user_id: str) -> list[dict]:
    return _last_product_results.get(user_id) or []


def set_last_product_results(user_id: str, items: list[dict]) -> None:
    _last_product_results[user_id] = items
