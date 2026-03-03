"""
This module provides functionality to parse customer complaint
messages using OpenAI's language model.
It defines a function `parse_complaint_message` that
takes a user message and an optional state dictionary,
constructs a prompt for the AI model,
and processes the response to extract relevant information
such as intent, order number, invoice number, case ID, category, summary, and confidence level.
"""

import json
from typing import Any

from openai import OpenAI

from src.core.config import OPENAI_API_KEY, CHAT_MODEL
from src.modules.complaints.prompts import (
    COMPLAINT_AI_SYSTEM_PROMPT,
    COMPLAINT_AI_USER_TEMPLATE,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)


def _safe_result() -> dict[str, Any]:
    return {
        "intent": "general",
        "order_no": None,
        "invoice_no": None,
        "case_id": None,
        "category": None,
        "summary": None,
        "confidence": 0.0,
        "ok": False,
    }


def parse_complaint_message(message: str, state: dict | None = None) -> dict[str, Any]:
    state = state or {}

    prompt = COMPLAINT_AI_USER_TEMPLATE.format(
        stage=state.get("stage", "idle"),
        known_order_no=state.get("order_no"),
        known_invoice_no=state.get("invoice_no"),
        known_category=state.get("category"),
        known_summary=state.get("summary"),
        message=message,
    )

    try:
        resp = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            temperature=0,
            max_tokens=220,
            messages=[
                {"role": "system", "content": COMPLAINT_AI_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()

        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        data = json.loads(raw)

        intent = str(data.get("intent", "general")).strip().lower()
        if intent not in {"complaint_create", "complaint_track", "general"}:
            intent = "general"

        confidence = data.get("confidence", 0.0)
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        result = {
            "intent": intent,
            "order_no": data.get("order_no"),
            "invoice_no": data.get("invoice_no"),
            "case_id": data.get("case_id"),
            "category": data.get("category"),
            "summary": data.get("summary"),
            "confidence": confidence,
            "ok": True,
        }
        return result

    except Exception:
        return _safe_result()
