"""
rag_engine.py
=============
Core RAG logic:
- Maintains per-user conversation history and last retrieved products in-memory.
- Resolves user queries into standalone retrieval queries using LLM-based resolver.
- Retrieves relevant product and store info based on resolved intent.
- Constructs LLM prompt with retrieved context and conversation history.
- Generates assistant reply using LLM and updates conversation history.
"""


from openai import OpenAI
from src.core.config import OPENAI_API_KEY, CHAT_MODEL, TOP_K_RESULTS
from src.modules.rag.prompts import SYSTEM_PROMPT, build_user_message_with_context
from src.modules.rag.resolver import resolve_query_with_history, _pick_referenced_product, _prepend_focused_product
from src.modules.rag.vector_store import (
    search_products,
    search_site_info,
    format_products_for_context,
    format_site_info_for_context,
)

from src.modules.chat.history_store import (
    get_history,
    append_message,
    trim_history,
    clear_history,
    get_last_product_results,
    set_last_product_results,
)


openai_client = OpenAI(api_key=OPENAI_API_KEY)

def generate_answer(user_message: str, user_id: str = "default") -> str:
    """
    Generate a customer service response using RAG.

    Args:
        user_message: The customer's message/question.
        user_id:      Unique ID to maintain per-user conversation history.

    Returns:
        The assistant's reply as a string.
    """

    history = trim_history(user_id)

    resolution = resolve_query_with_history(openai_client, user_message, history)

    if resolution["intent"] == "irrelevant":
        assistant_reply = "I can only help with Japan Electronics products and store-related questions."
        append_message(user_id, "user", user_message)
        append_message(user_id, "assistant", assistant_reply)

        return assistant_reply

    retrieval_query = resolution["standalone_query"]
    if resolution["intent"] == "site_info":
        records = search_site_info(query=retrieval_query, top_k=TOP_K_RESULTS)
        context_block = format_site_info_for_context(records)
        context_title = "STORE CONTEXT (retrieved from website pages)"
    else:
        focused_product = _pick_referenced_product(user_message=user_message,
         items=get_last_product_results(user_id))

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
        set_last_product_results(user_id, products[:TOP_K_RESULTS])

        context_block = format_products_for_context(products)
        context_title = "PRODUCT CONTEXT (retrieved from our catalogue)"

    user_message_with_context = build_user_message_with_context(
    context_title=context_title,
    context_block=context_block,
    user_message=user_message,
)


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

    append_message(user_id, "user", user_message)
    append_message(user_id, "assistant", assistant_reply)

    return assistant_reply
