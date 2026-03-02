"""
ingest_data.py
==============
Run this ONCE to embed all products and upload them to Pinecone.

Usage:
    python -m src.ingest_data
"""

import json
import re
import time
from pathlib import Path

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from src.config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_CLOUD,
    PINECONE_REGION,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    INGEST_BATCH_SIZE,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)


# ── Helpers ───────────────────────────────────────────────────────────────────

def strip_html(html: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def parse_spec_pairs(product: dict) -> list[tuple[str, str]]:
    """
    Extract product specs as key/value pairs from description HTML and tags.
    """
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()

    description_html = product.get("description_html", "") or ""
    for li_html in re.findall(r"<li[^>]*>(.*?)</li>", description_html, flags=re.I | re.S):
        item_text = strip_html(li_html)
        if not item_text:
            continue
        # Expected format is usually "Key: Value"
        if ":" in item_text:
            key, value = item_text.split(":", 1)
        else:
            key, value = "Detail", item_text
        key = re.sub(r"\s+", " ", key).strip(" -")
        value = re.sub(r"\s+", " ", value).strip(" -")
        if not key or not value:
            continue
        dedupe_key = f"{key.lower()}::{value.lower()}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        pairs.append((key, value))

    # Tags often contain extra spec-like fields, e.g. "Capacity_1.5 Ton"
    for raw_tag in product.get("tags", []) or []:
        tag = str(raw_tag).strip()
        if not tag:
            continue
        if "_" in tag:
            key, value = tag.split("_", 1)
            key = key.strip()
            value = value.strip()
        else:
            key, value = "Tag", tag
        if not key or not value:
            continue
        dedupe_key = f"{key.lower()}::{value.lower()}"
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        pairs.append((key, value))

    return pairs


def build_specs_summary(spec_pairs: list[tuple[str, str]], max_chars: int = 1800) -> str:
    """Build a compact single-line summary for Pinecone metadata/context."""
    if not spec_pairs:
        return ""
    chunks: list[str] = []
    total = 0
    for key, value in spec_pairs:
        part = f"{key}: {value}"
        new_total = total + len(part) + (3 if chunks else 0)
        if new_total > max_chars:
            break
        chunks.append(part)
        total = new_total
    return " | ".join(chunks)


def first_spec_value(spec_pairs: list[tuple[str, str]], key_regex: str) -> str:
    """Return the first spec value whose key matches key_regex."""
    for key, value in spec_pairs:
        if re.search(key_regex, key, flags=re.I):
            return value
    return ""


def product_to_text(product: dict) -> str:
    """
    Convert a product dict into a single descriptive text string.
    This is what gets embedded — richer text = better search results.
    """
    parts = []

    parts.append(f"Product: {product.get('name', '')}")
    parts.append(f"Brand: {product.get('brand', 'N/A')}")
    parts.append(f"Category: {product.get('category', '')}")

    if product.get("product_type"):
        parts.append(f"Type: {product['product_type']}")

    parts.append(f"Price: {product.get('price', 'N/A')}")

    if product.get("compare_price"):
        parts.append(f"Original Price: {product['compare_price']}")

    if product.get("discount"):
        parts.append(f"Discount: {product['discount']}")

    parts.append(f"Availability: {product.get('availability', 'Unknown')}")

    spec_pairs = parse_spec_pairs(product)
    specs_summary = build_specs_summary(spec_pairs, max_chars=2500)
    if specs_summary:
        parts.append(f"Specifications: {specs_summary}")

    # Variants (sizes/colours with prices)
    variants = product.get("variants", [])
    if variants and len(variants) > 1:
        variant_strs = []
        for v in variants:
            vs = f"{v.get('title', '')} at Rs.{v.get('price', '')}"
            if v.get("sku"):
                vs += f" (SKU: {v['sku']})"
            variant_strs.append(vs)
        parts.append(f"Variants: {' | '.join(variant_strs)}")
    elif variants:
        v = variants[0]
        if v.get("sku"):
            parts.append(f"SKU: {v['sku']}")

    # Full description (HTML stripped)
    description = strip_html(product.get("description_html", ""))
    if description:
        # Truncate very long descriptions to avoid token limits
        parts.append(f"Description: {description[:1000]}")

    parts.append(f"URL: {product.get('url', '')}")

    return "\n".join(parts)


def build_metadata(product: dict) -> dict:
    """
    Pinecone metadata — kept small (no large text fields).
    Used to return useful info alongside search results.
    """
    variants = product.get("variants", [])
    first_variant = variants[0] if variants else {}
    spec_pairs = parse_spec_pairs(product)
    specs_summary = build_specs_summary(spec_pairs)
    model = first_spec_value(spec_pairs, r"\bmodel\b")
    warranty = first_spec_value(spec_pairs, r"\bwarranty\b")

    return {
        "doc_type":   "product",
        "product_id": str(product.get("id", "")),
        "handle":     product.get("handle", ""),
        "name":       product.get("name", "")[:200],      # Pinecone has metadata size limits
        "brand":      product.get("brand", ""),
        "category":   product.get("category", ""),
        "price":      product.get("price", ""),
        "compare_price": product.get("compare_price") or "",
        "discount":   product.get("discount") or "",
        "availability": product.get("availability", ""),
        "sku":        first_variant.get("sku") or "",
        "model":      model,
        "warranty":   warranty,
        "specs_summary": specs_summary,
        "url":        product.get("url", ""),
        "image":      (product.get("images") or [""])[0],
    }


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using OpenAI."""
    response = openai_client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
    )
    return [item.embedding for item in response.data]


# ── Pinecone setup ────────────────────────────────────────────────────────────

def get_or_create_index(pc: Pinecone):
    existing = [idx.name for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing:
        print(f"Creating Pinecone index '{PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=PINECONE_REGION),
        )
        # Wait for index to be ready
        while not pc.describe_index(PINECONE_INDEX_NAME).status["ready"]:
            print("  Waiting for index to be ready...")
            time.sleep(3)
        print("  Index created and ready.")
    else:
        print(f"Index '{PINECONE_INDEX_NAME}' already exists.")

    return pc.Index(PINECONE_INDEX_NAME)


# ── Main ingest ───────────────────────────────────────────────────────────────

def ingest(data_path: str = "data/scraped_data.json"):
    print(f"\n{'='*55}")
    print("  Japan Electronics — Data Ingestion")
    print(f"{'='*55}\n")

    # Load data
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    products = raw.get("products", raw)   # handles both {products:[]} and [] formats
    print(f"Loaded {len(products)} products from {data_path}\n")

    # Connect to Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = get_or_create_index(pc)

    # Process in batches
    total_upserted = 0
    batch_texts, batch_ids, batch_metadata = [], [], []

    for i, product in enumerate(products):
        pid = str(product.get("id", i))
        text = product_to_text(product)
        meta = build_metadata(product)

        batch_ids.append(pid)
        batch_texts.append(text)
        batch_metadata.append(meta)

        # Upsert when batch is full or we're at the last product
        if len(batch_texts) == INGEST_BATCH_SIZE or i == len(products) - 1:
            print(f"Embedding batch {i // INGEST_BATCH_SIZE + 1} "
                  f"({len(batch_texts)} products)...", end=" ", flush=True)

            embeddings = embed_texts(batch_texts)

            vectors = [
                {"id": bid, "values": emb, "metadata": meta}
                for bid, emb, meta in zip(batch_ids, embeddings, batch_metadata)
            ]

            index.upsert(vectors=vectors)
            total_upserted += len(vectors)
            print(f"✓ ({total_upserted} total upserted)")

            batch_texts, batch_ids, batch_metadata = [], [], []
            time.sleep(0.5)  # avoid rate limits

    print(f"\n Done! {total_upserted} products ingested into Pinecone index '{PINECONE_INDEX_NAME}'.")


if __name__ == "__main__":
    ingest()
