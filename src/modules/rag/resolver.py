import json
import re
from src.core.config import CHAT_MODEL


def resolve_query_with_history(openai_client, user_message: str, history: list[dict]) -> dict:
    """
    Resolve follow-ups into a standalone retrieval query and relevance decision.
    Falls back safely to the raw user message if parsing fails.
    """
    recent_history = history[-6:]
    history_text = "\n".join(
        f"{m.get('role', 'user')}: {m.get('content', '')}" for m in recent_history
    ) or "No history"

    resolver_prompt = f"""You are a query resolver for an ecommerce assistant.

Return STRICT JSON only:
{{
  "intent": "product",
  "is_followup": false,
  "standalone_query": "..."
}}

Rules:
- intent must be one of: product, site_info, irrelevant.
- standalone_query must be self-contained and retrieval-friendly.
- Resolve follow-up references (for example "cheapest one", "that one") using history.
- Greetings/salutations (for example hi, hello, salam, assalam o alaikum, good morning) should use intent=site_info.
- For product/search/buy/price/spec queries use intent=product.
- For locations, policies, delivery, FAQ, contact, complaints, and store/company info use intent=site_info.
- Only use intent=irrelevant for clearly off-domain requests.
- Output JSON only, no extra text.

Example:
Latest user message: "hi"
Output: {{"intent": "site_info", "is_followup": false, "standalone_query": "greeting"}}

History:
{history_text}

Latest user message:
{user_message}
"""

    try:
        response = openai_client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": resolver_prompt}],
            temperature=0,
            max_tokens=200,
        )
        raw = (response.choices[0].message.content or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()
        data = json.loads(raw)
        intent = str(data.get("intent", "product")).strip().lower()
        if intent not in {"product", "site_info", "irrelevant"}:
            intent = "product"
        return {
            "intent": intent,
            "is_followup": bool(data.get("is_followup", False)),
            "standalone_query": (data.get("standalone_query") or user_message).strip(),
        }
    except Exception:
        return {
            "intent": "product",
            "is_followup": False,
            "standalone_query": user_message,
        }


def _extract_product_reference_index(message: str) -> int | None:
    """Map product references like '#3', 'product 2', '2nd', 'first', 'last'."""
    lowered = message.lower()
    if re.search(r"\blast\b", lowered):
        return -1

    # Generic numeric references: "product 2", "2nd one", "#3", "number 4".
    numeric_match = re.search(
        r"(?:product|item|option|number|#)\s*(\d+)|\b(\d+)(?:st|nd|rd|th)\b",
        lowered,
    )
    if numeric_match:
        value = next((g for g in numeric_match.groups() if g), None)
        if value and value.isdigit():
            return max(0, int(value) - 1)

    # Minimal text ordinals to avoid heavy hardcoding.
    if re.search(r"\bfirst\b", lowered):
        return 0
    return None


def _pick_referenced_product(user_message: str, items: list[dict]) -> dict | None:
    """Pick product from latest retrieved list based on ordinal references."""
    if not items:
        return None
    ref_idx = _extract_product_reference_index(user_message)
    if ref_idx is None:
        return None
    if ref_idx == -1:
        return items[-1]
    if 0 <= ref_idx < len(items):
        return items[ref_idx]
    return None


def _prepend_focused_product(products: list[dict], focused_product: dict | None) -> list[dict]:
    """Ensure referenced product appears first in context, de-duplicated by URL."""
    if not focused_product:
        return products
    merged = [focused_product]
    focused_url = focused_product.get("url", "")
    for p in products:
        if p.get("url", "") == focused_url:
            continue
        merged.append(p)
    return merged
