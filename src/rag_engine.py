"""
rag_engine.py
=============
Core RAG logic:
  1. Retrieve relevant products from Pinecone (via vector_db.py)
  2. Build a prompt with product context + conversation history
  3. Call the OpenAI chat model and return the reply

Conversation history is stored per user_id in memory.
For production, swap the in-memory dict for Redis or a DB.
"""

import json
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

# ── In-memory conversation store: {user_id: [{"role":..., "content":...}]} ───
_conversation_history: dict[str, list[dict]] = defaultdict(list)
MAX_HISTORY_TURNS = 10   # keep last N user+assistant pairs to avoid huge prompts


# ── System prompt ─────────────────────────────────────────────────────────────

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
- Be concise but warm — like a knowledgeable salesperson
- Always mention the product URL when recommending a specific product
- For store info (locations, policies, contact), answer directly from context without adding links unless the user explicitly asks for a link
- If you don't know something or the product isn't in the context, say so honestly \
  and suggest the customer contact the store directly

Important:
- Prices are in Pakistani Rupees (Rs.)
- Only recommend products that appear in the PRODUCT CONTEXT — do not invent products
- For factual store details, rely on retrieved STORE CONTEXT instead of memory
- If the customer asks about something not in the context, let them know and offer to help them find it
"""


# ── Query resolver ────────────────────────────────────────────────────────────

def resolve_query_with_history(user_message: str, history: list[dict]) -> dict:
    """
    Resolve follow-ups into a standalone retrieval query and relevance decision.
    Falls back safely to the raw user message if parsing fails.
    """
    recent_history = history[-6:]  # keep resolver context small and recent
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
- Resolve follow-up references (e.g. "cheapest one", "that one") using history.
- Greetings/salutations (e.g., hi, hello, salam, assalam o alaikum, good morning) should use intent=site_info.
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


# ── Main function ─────────────────────────────────────────────────────────────

def generate_answer(user_message: str, user_id: str = "default") -> str:
    """
    Generate a customer service response using RAG.

    Args:
        user_message: The customer's message/question.
        user_id:      Unique ID to maintain per-user conversation history.

    Returns:
        The assistant's reply as a string.
    """

    # 1. Load history and trim to last N turns (each turn = 1 user + 1 assistant)
    history = _conversation_history[user_id]
    if len(history) > MAX_HISTORY_TURNS * 2:
        _conversation_history[user_id] = history[-(MAX_HISTORY_TURNS * 2):]
        history = _conversation_history[user_id]

    # 2. Resolve follow-ups into standalone retrieval query + relevance gating
    resolution = resolve_query_with_history(user_message, history)
    if resolution["intent"] == "irrelevant":
        assistant_reply = "I can only help with Japan Electronics products and store-related questions."
        _conversation_history[user_id].append({"role": "user", "content": user_message})
        _conversation_history[user_id].append({"role": "assistant", "content": assistant_reply})
        return assistant_reply

    # 3. Retrieve context based on resolved intent
    retrieval_query = resolution["standalone_query"]
    if resolution["intent"] == "site_info":
        records = search_site_info(query=retrieval_query, top_k=TOP_K_RESULTS)
        context_block = format_site_info_for_context(records)
        context_title = "STORE CONTEXT (retrieved from website pages)"
    else:
        products = search_products(query=retrieval_query, top_k=TOP_K_RESULTS)
        context_block = format_products_for_context(products)
        context_title = "PRODUCT CONTEXT (retrieved from our catalogue)"

    # 4. Build the messages list for the API call
    user_message_with_context = f"""{context_title}:
{context_block}

---
Customer message: {user_message}"""

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": user_message_with_context}]
    )

    # 5. Call the LLM
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,      # slightly creative but mostly factual
        max_tokens=600,
    )

    assistant_reply = response.choices[0].message.content.strip()

    # 6. Save turn to history (store clean user message, not the context-stuffed one)
    _conversation_history[user_id].append({"role": "user", "content": user_message})
    _conversation_history[user_id].append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


def clear_history(user_id: str) -> None:
    """Clear conversation history for a user (e.g. when they start a new session)."""
    _conversation_history.pop(user_id, None)


def get_history(user_id: str) -> list[dict]:
    """Return the conversation history for a user."""
    return _conversation_history.get(user_id, [])
