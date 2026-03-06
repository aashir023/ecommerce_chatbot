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

import re
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

IN_STOCK_FILTER = {"availability": {"$eq": "In Stock"}}


def _and_filters(a: dict | None, b: dict | None) -> dict | None:
    if a and b:
        return {"$and": [a, b]}
    return a or b


def _only_in_stock(items: list[dict]) -> list[dict]:
    return [p for p in items if str(p.get("availability", "")).strip().lower() == "in stock"]

def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _matches_target_type(product: dict, target_product_type: str) -> bool:
    target = _normalize_text(target_product_type)
    if not target:
        return True

    haystack = " ".join(
        [
            str(product.get("category", "") or ""),
            str(product.get("name", "") or ""),
            str(product.get("specs_summary", "") or ""),
        ]
    )
    haystack = _normalize_text(haystack)
    if not haystack:
        return False

    # Token overlap check (language-agnostic enough when resolver normalizes to retrieval-friendly phrase).
    tokens = [t for t in re.findall(r"[a-z0-9]+", target) if len(t) >= 2]
    if not tokens:
        return target in haystack

    return all(t in haystack for t in tokens)


def _dedupe_products(items: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for p in items:
        key = str(p.get("product_id") or p.get("url") or p.get("name") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out

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
    is_comparison = bool(resolution.get("is_comparison", False))
    comparison_brands = resolution.get("comparison_brands") or []
    target_product_type = str(resolution.get("target_product_type") or "").strip()

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
        focused_product = None
        products = []

        if is_comparison:
            # Strict comparison retrieval: fetch per requested brand first.
            per_brand = []
            for brand in comparison_brands:
                brand_filters = {"brand": {"$eq": brand}}
                brand_query = " ".join(
                    part for part in [brand, target_product_type, retrieval_query] if part
                )
                brand_hits = search_products(
                    query=brand_query,
                    top_k=max(TOP_K_RESULTS, 4),
                    filters=_and_filters(brand_filters, IN_STOCK_FILTER),
                )
                per_brand.extend(brand_hits)

            products = _dedupe_products(per_brand)

            if target_product_type:
                products = [p for p in products if _matches_target_type(p, target_product_type)]

            # Comparison top-up: if strict entity retrieval is too narrow, add broader semantic hits.
            if len(products) < 2:
                topup = search_products(
                    query=retrieval_query,
                    top_k=max(TOP_K_RESULTS * 2, 12),
                    filters=IN_STOCK_FILTER,
                )
                products = _dedupe_products(products + topup)
                if target_product_type:
                    products = [p for p in products if _matches_target_type(p, target_product_type)]
            
        else:
            focused_product = _pick_referenced_product(
                user_message=user_message,
                items=get_last_product_results(user_id),
            )

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
                    products = search_products(
                        query=focused_query,
                        top_k=1,
                        filters=_and_filters(focused_filters, IN_STOCK_FILTER),
                    )

            # Fallback to normal semantic retrieval if lock was not possible.
            if not products:
                if focused_product and focused_product.get("name"):
                    # Keep retrieval grounded in referenced product while preserving user wording.
                    retrieval_query = f"{focused_product['name']} {user_message}"
                products = search_products(
                    query=retrieval_query,
                    top_k=TOP_K_RESULTS,
                    filters=IN_STOCK_FILTER,
                )

        products = _prepend_focused_product(products, focused_product)
        products = _only_in_stock(products)
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
