"""
rag_engine.py
=============
Core RAG logic:
  1. Retrieve relevant products from Pinecone (via vector_db.py)
  2. Build a prompt with product context + conversation history
  3. Call the chat model and return the reply

Conversation history is stored per user_id in memory.
For production, swap the in-memory dict for Redis or a DB.
"""

import json
import re
from collections import defaultdict

from openai import OpenAI

from src.config import OPENAI_API_KEY, CHAT_MODEL, TOP_K_RESULTS
from src.vector_db import (
    search_products,
    search_site_info,
    format_products_for_context,
    format_site_info_for_context,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# In-memory stores.
_conversation_history: dict[str, list[dict]] = defaultdict(list)
_last_product_results: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY_TURNS = 10  # last N user+assistant pairs


SYSTEM_PROMPT = """You are a helpful and friendly customer service assistant for Japan Electronics, \
one of Pakistan's best home appliances and electronics stores, established in 1984.

Japan Electronics sells a wide range of products including:
Air Conditioners, Refrigerators, LED TVs, Washing Machines, Microwaves, Air Fryers, \
Geysers, Kitchen Appliances, Deep Freezers, Water Dispensers, and more.

Store Info:
- For locations, contact details, policies, delivery, and FAQs, use only the retrieved STORE CONTEXT.

Your role:
- Help customers find the right product for their needs and budget
- Answer questions about prices, specs, availability, and brands
- Recommend products based on the PRODUCT CONTEXT provided below
- If the user greets you, respond politely once, then continue without repeating greetings in every reply.
- Be concise but warm, like a knowledgeable salesperson
- Always mention the product URL when recommending a specific product
- For store info (locations, policies, contact), answer directly from context without adding links unless the user explicitly asks for a link
- If you don't know something or the product isn't in the context, say so honestly and suggest the customer contact the store directly

Important:
- Prices are in Pakistani Rupees (Rs.)
- Only recommend products that appear in the PRODUCT CONTEXT. Do not invent products.
- For factual store details, rely on retrieved STORE CONTEXT instead of memory.
- If user asks for a specific product spec (for example model, warranty, HDMI, size), answer from Key Specs when available.
- If the requested spec is missing in context, politely say it is not listed in current catalogue data.
- If a specific referenced product is provided in context, do not answer with a different product.
"""


def resolve_query_with_history(user_message: str, history: list[dict]) -> dict:
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


def _pick_referenced_product(user_message: str, user_id: str) -> dict | None:
    """Pick product from latest retrieved list based on ordinal references."""
    items = _last_product_results.get(user_id) or []
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


def generate_answer(user_message: str, user_id: str = "default") -> str:
    """
    Generate a customer service response using RAG.

    Args:
        user_message: The customer's message/question.
        user_id:      Unique ID to maintain per-user conversation history.

    Returns:
        The assistant's reply as a string.
    """
    history = _conversation_history[user_id]
    if len(history) > MAX_HISTORY_TURNS * 2:
        _conversation_history[user_id] = history[-(MAX_HISTORY_TURNS * 2):]
        history = _conversation_history[user_id]

    resolution = resolve_query_with_history(user_message, history)
    if resolution["intent"] == "irrelevant":
        assistant_reply = "I can only help with Japan Electronics products and store-related questions."
        _conversation_history[user_id].append({"role": "user", "content": user_message})
        _conversation_history[user_id].append({"role": "assistant", "content": assistant_reply})
        return assistant_reply

    retrieval_query = resolution["standalone_query"]
    if resolution["intent"] == "site_info":
        records = search_site_info(query=retrieval_query, top_k=TOP_K_RESULTS)
        context_block = format_site_info_for_context(records)
        context_title = "STORE CONTEXT (retrieved from website pages)"
    else:
        focused_product = _pick_referenced_product(user_message=user_message, user_id=user_id)

        products = []
        if focused_product:
            # Minimal safe lock: when user references "first/last/that one",
            # retrieve only that product via metadata filter.
            focused_filters = None
            if focused_product.get("product_id"):
                focused_filters = {"product_id": {"$eq": str(focused_product["product_id"])}}
            elif focused_product.get("url"):
                focused_filters = {"url": {"$eq": focused_product["url"]}}

            if focused_filters:
                focused_query = focused_product.get("name") or retrieval_query
                products = search_products(query=focused_query, top_k=1, filters=focused_filters)

        # Fallback to normal semantic retrieval if lock was not possible.
        if not products:
            if focused_product and focused_product.get("name"):
                # Keep retrieval grounded in referenced product while preserving user wording.
                retrieval_query = f"{focused_product['name']} {user_message}"
            products = search_products(query=retrieval_query, top_k=TOP_K_RESULTS)

        products = _prepend_focused_product(products, focused_product)
        _last_product_results[user_id] = products[:TOP_K_RESULTS]

        context_block = format_products_for_context(products)
        context_title = "PRODUCT CONTEXT (retrieved from our catalogue)"

    user_message_with_context = f"""{context_title}:
{context_block}

---
Customer message: {user_message}"""

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": user_message_with_context}]
    )

    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,
        max_tokens=900,
    )

    assistant_reply = response.choices[0].message.content.strip()
    finish_reason = response.choices[0].finish_reason
    print(f"[LLM] finish_reason={finish_reason}, completion_tokens={getattr(getattr(response, 'usage', None), 'completion_tokens', None)}")

    _conversation_history[user_id].append({"role": "user", "content": user_message})
    _conversation_history[user_id].append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


def clear_history(user_id: str) -> None:
    """Clear conversation history for a user."""
    _conversation_history.pop(user_id, None)
    _last_product_results.pop(user_id, None)


def get_history(user_id: str) -> list[dict]:
    """Return the conversation history for a user."""
    return _conversation_history.get(user_id, [])
