from collections import defaultdict


# Very simple in-memory workflow state per user
# stages: idle -> awaiting_order -> awaiting_category -> awaiting_summary -> ready_to_create
_state: dict[str, dict] = defaultdict(lambda: {
    "stage": "idle",
    "order_no": None,
    "invoice_no": None,
    "category": None,
    "summary": None,
})


def get_state(user_id: str) -> dict:
    return _state[user_id]


def set_stage(user_id: str, stage: str) -> None:
    _state[user_id]["stage"] = stage


def update_state(user_id: str, **kwargs) -> None:
    _state[user_id].update(kwargs)


def reset_state(user_id: str) -> None:
    _state[user_id] = {
        "stage": "idle",
        "order_no": None,
        "invoice_no": None,
        "category": None,
        "summary": None,
    }
