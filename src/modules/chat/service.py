"""
Service layer for chat-related operations, 
including message processing, complaint handling, 
and conversation history management.
"""
import json
from src.db.repositories.chat_repo import (
    save_chat_message,
    get_chat_messages
)

from src.modules.rag.service import generate_answer, clear_history, openai_client
from src.core.config import CHAT_MODEL


def _detect_form_action(message: str) -> str | None:
    prompt = f"""You are an intent classifier for customer support chat.

Return STRICT JSON only:
{{"action": "open_complaint_form"}}
or
{{"action": "open_schedule_form"}}
or
{{"action": null}}

Rules:
- open_complaint_form: user reports product issue/problem/fault/defect/damage, wants complaint, return/exchange due to issue, etc.
- open_schedule_form: user asks technician visit, installation, repair visit, home service, schedule appointment, etc.
- Understand English + Roman Urdu + mixed language.
- If unclear, return null.
- Output JSON only.

User message:
{message}
"""
    try:
        resp = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=30,
        )
        raw = (resp.choices[0].message.content or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()
        data = json.loads(raw)
        action = data.get("action")
        if action in {"open_complaint_form", "open_schedule_form"}:
            return action
        return None
    except Exception:
        return None

def _build_action_reply(message: str, action: str) -> str:
    target = "complaint form" if action == "open_complaint_form" else "technician schedule form"
    prompt = f"""You are a customer support assistant.

Write one short, warm, personalized reply to this customer message:
"{message}"

Goal:
- If complaint action: guide user to open/fill complaint form in chat.
- If schedule action: guide user to open/fill technician visit form in chat.
- Match user language style (English or Roman Urdu).
- If replying in Roman Urdu, use Pakistani Roman Urdu wording only (avoid Hindi vocabulary like "kripya", "sahayata", "bharein", "taake").
- Do not use markdown.
- Max 2 short sentences.
"""
    try:
        resp = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=80,
        )
        text = (resp.choices[0].message.content or "").strip()
        if text:
            return text
    except Exception:
        pass

    # safe fallback
    if action == "open_complaint_form":
        return "I can help you log a complaint right away. Please use the complaint form below."
    return "I can help you schedule a technician visit. Please use the schedule form below."


def send_message(user_id: str, message: str) -> dict:
    save_chat_message(user_id, "user", message)

    action = _detect_form_action(message)

    if action in {"open_complaint_form", "open_schedule_form"}:
        reply = _build_action_reply(message, action)
    else:
        reply = generate_answer(user_message=message, user_id=user_id)

    save_chat_message(user_id, "assistant", reply)
    return {"reply": reply, "action": action}

def fetch_history(user_id: str) -> list[dict]:
    return get_chat_messages(user_id)


def reset_history(user_id: str) -> None:
    clear_history(user_id)
