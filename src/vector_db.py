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
    query_embedding = embed_query(query)
    index = get_pinecone_index()

    query_kwargs = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True,
    }
    if filters:
        query_kwargs["filter"] = filters

    results = index.query(**query_kwargs)

    products = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        meta["score"] = round(match.get("score", 0), 4)
        products.append(meta)

    return products


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

        lines.append(f"URL:          {p.get('url', '')}")
        lines.append("")   # blank line between products

    return "\n".join(lines).strip()