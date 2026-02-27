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

from collections import defaultdict

from openai import OpenAI

from src.config import OPENAI_API_KEY, CHAT_MODEL, TOP_K_RESULTS
from src.vector_db import search_products, format_products_for_context

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
- Location 1: Gul Noor Market, Shop 15, Murree Rd, Rawalpindi, Pakistan
- Location 2: Ajaib & Sons Plaza, Jinnah Ave, Block G, Blue Area, Islamabad, Pakistan
- Phone / WhatsApp: +92 309 0040002
- Email: info@japanelectronics.pk
- Complaints: +92 304 1111984
- Website: https://japanelectronics.com.pk
- Delivery: All across Pakistan
- Policy: 7-day replacement guarantee, secure payments

Your role:
- Help customers find the right product for their needs and budget
- Answer questions about prices, specs, availability, and brands
- Recommend products based on the PRODUCT CONTEXT provided below
- Be concise but warm — like a knowledgeable salesperson
- Always mention the product URL when recommending a specific item
- If you don't know something or the product isn't in the context, say so honestly \
  and suggest the customer contact the store directly

Important:
- Prices are in Pakistani Rupees (Rs.)
- Only recommend products that appear in the PRODUCT CONTEXT — do not invent products
- If the customer asks about something not in the context, let them know and offer to help them find it
"""


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

    # 1. Retrieve relevant products
    products = search_products(query=user_message, top_k=TOP_K_RESULTS)
    product_context = format_products_for_context(products)

    # 2. Build the messages list for the API call
    history = _conversation_history[user_id]

    # Trim history to last N turns (each turn = 1 user + 1 assistant message)
    if len(history) > MAX_HISTORY_TURNS * 2:
        _conversation_history[user_id] = history[-(MAX_HISTORY_TURNS * 2):]
        history = _conversation_history[user_id]

    # The user message includes the retrieved context so the model can reference it
    user_message_with_context = f"""PRODUCT CONTEXT (retrieved from our catalogue):
{product_context}

---
Customer message: {user_message}"""

    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": user_message_with_context}]
    )

    # 3. Call the LLM
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
        temperature=0.4,      # slightly creative but mostly factual
        max_tokens=600,
    )

    assistant_reply = response.choices[0].message.content.strip()

    # 4. Save turn to history (store clean user message, not the context-stuffed one)
    _conversation_history[user_id].append({"role": "user", "content": user_message})
    _conversation_history[user_id].append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


def clear_history(user_id: str) -> None:
    """Clear conversation history for a user (e.g. when they start a new session)."""
    _conversation_history.pop(user_id, None)


def get_history(user_id: str) -> list[dict]:
    """Return the conversation history for a user."""
    return _conversation_history.get(user_id, [])