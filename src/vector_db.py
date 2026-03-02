"""
vector_db.py
============
Handles connecting to Pinecone and performing similarity searches.
Used by rag_engine.py to retrieve relevant products for a query.
"""

from functools import lru_cache

from openai import OpenAI
from pinecone import Pinecone

from src.config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL,
    TOP_K_RESULTS,
)

# ── Clients (initialised once) ────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_pinecone_index():
    """Return a cached Pinecone index connection."""
    pc = Pinecone(api_key=PINECONE_API_KEY)
    return pc.Index(PINECONE_INDEX_NAME)


@lru_cache(maxsize=1)
def get_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)


# ── Core functions ────────────────────────────────────────────────────────────

def embed_query(query: str) -> list[float]:
    """Embed a single user query string."""
    client = get_openai_client()
    response = client.embeddings.create(
        input=[query],
        model=EMBEDDING_MODEL,
    )
    return response.data[0].embedding


def _combine_filters(base_filter: dict, extra_filter: dict | None) -> dict:
    if not extra_filter:
        return base_filter
    return {"$and": [base_filter, extra_filter]}


def _search_by_doc_type(
    query: str,
    doc_type: str,
    top_k: int = TOP_K_RESULTS,
    filters: dict | None = None,
) -> list[dict]:
    query_embedding = embed_query(query)
    index = get_pinecone_index()

    query_kwargs = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True,
        "filter": _combine_filters(
            {"doc_type": {"$eq": doc_type}},
            filters,
        ),
    }

    results = index.query(**query_kwargs)

    records = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        meta["score"] = round(match.get("score", 0), 4)
        records.append(meta)

    return records


def search_products(query: str, top_k: int = TOP_K_RESULTS, filters: dict = None) -> list[dict]:
    """
    Embed the query and retrieve the top_k most similar products from Pinecone.

    Args:
        query:   Natural language search query from the user.
        top_k:   Number of results to return.
        filters: Optional Pinecone metadata filter dict, e.g.
                 {"brand": {"$eq": "Haier"}} or {"category": {"$eq": "Air Conditioners"}}

    Returns:
        List of product metadata dicts, ordered by relevance.
    """
    return _search_by_doc_type(
        query=query,
        doc_type="product",
        top_k=top_k,
        filters=filters,
    )


def search_site_info(query: str, top_k: int = TOP_K_RESULTS, filters: dict = None) -> list[dict]:
    """Retrieve non-product site information chunks (locations, policies, FAQs, etc.)."""
    return _search_by_doc_type(
        query=query,
        doc_type="site_info",
        top_k=top_k,
        filters=filters,
    )


def format_products_for_context(products: list[dict]) -> str:
    """
    Convert a list of product metadata dicts into a clean readable
    context block to inject into the LLM prompt.
    """
    if not products:
        return "No relevant products found."

    lines = []
    for i, p in enumerate(products, 1):
        lines.append(f"--- Product {i} ---")
        lines.append(f"Name:         {p.get('name', 'N/A')}")
        lines.append(f"Brand:        {p.get('brand', 'N/A')}")
        lines.append(f"Category:     {p.get('category', 'N/A')}")
        lines.append(f"Price:        {p.get('price', 'N/A')}")

        if p.get("compare_price"):
            lines.append(f"Was:          {p['compare_price']}")
        if p.get("discount"):
            lines.append(f"Discount:     {p['discount']}")

        lines.append(f"Availability: {p.get('availability', 'N/A')}")

        if p.get("sku"):
            lines.append(f"SKU:          {p['sku']}")
        if p.get("model"):
            lines.append(f"Model:        {p['model']}")
        if p.get("warranty"):
            lines.append(f"Warranty:     {p['warranty']}")
        if p.get("specs_summary"):
            lines.append(f"Key Specs:    {p['specs_summary']}")

        lines.append(f"URL:          {p.get('url', '')}")
        lines.append("")   # blank line between products

    return "\n".join(lines).strip()


def format_site_info_for_context(records: list[dict]) -> str:
    """
    Convert site-information metadata records into a readable context block.
    URLs are intentionally omitted here so the assistant doesn't over-link.
    """
    if not records:
        return "No relevant store information found."

    lines = []
    for i, r in enumerate(records, 1):
        lines.append(f"--- Info {i} ---")
        lines.append(f"Type:  {(r.get('type') or 'general').replace('_', ' ').title()}")
        lines.append(f"Title: {r.get('title', 'N/A')}")
        if r.get("content_chunk"):
            lines.append(f"Details: {r['content_chunk']}")
        if r.get("published_at"):
            lines.append(f"Published: {r['published_at'][:10]}")
        if r.get("author"):
            lines.append(f"Author: {r['author']}")
        lines.append("")

    return "\n".join(lines).strip()
