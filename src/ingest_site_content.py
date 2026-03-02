"""
ingest_site_content.py
======================
Ingests site_content.json (static pages, blogs, policies, FAQs)
into the same Pinecone index alongside the products.

Run AFTER ingest_data.py:
    python -m src.ingest_site_content

Each page/blog post is split into chunks of ~500 words so large
pages don't lose meaning when embedded as one giant vector.
"""

import json
import time
from pathlib import Path

from openai import OpenAI
from pinecone import Pinecone

from src.config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    EMBEDDING_MODEL,
    INGEST_BATCH_SIZE,
)

openai_client = OpenAI(api_key=OPENAI_API_KEY)

CHUNK_SIZE = 500        # words per chunk
CHUNK_OVERLAP = 50      # words of overlap between chunks


# ── Chunking ──────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping word-based chunks.
    Overlap ensures context isn't lost at chunk boundaries.

    e.g. chunk_size=500, overlap=50:
      chunk 1: words 0-499
      chunk 2: words 450-949
      chunk 3: words 900-1399
      ...
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]   # short enough, no splitting needed

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += chunk_size - overlap

    return chunks


# ── Text preparation ──────────────────────────────────────────────────────────

def content_item_to_text(item: dict, chunk: str, chunk_index: int) -> str:
    """Build a rich text string for a single chunk of a content item."""
    parts = []
    parts.append(f"Type: {item.get('type', '').replace('_', ' ').title()}")
    parts.append(f"Title: {item.get('title', '')}")

    if item.get("author"):
        parts.append(f"Author: {item['author']}")
    if item.get("published_at"):
        parts.append(f"Published: {item['published_at'][:10]}")
    if item.get("tags"):
        parts.append(f"Tags: {item['tags']}")
    if item.get("summary"):
        parts.append(f"Summary: {item['summary'][:300]}")

    parts.append(f"URL: {item.get('url', '')}")
    parts.append(f"\nContent:\n{chunk}")

    return "\n".join(parts)


def build_metadata(item: dict, chunk: str, chunk_index: int, total_chunks: int) -> dict:
    return {
        "doc_type":      "site_info",
        "item_id":       item.get("id", ""),
        "type":          item.get("type", ""),
        "title":         item.get("title", "")[:200],
        "url":           item.get("url", ""),
        "chunk_index":   chunk_index,
        "total_chunks":  total_chunks,
        "author":        item.get("author", ""),
        "published_at":  item.get("published_at", ""),
        "tags":          str(item.get("tags", "")),
        # Keep a compact source excerpt so answers are grounded in retrieved text.
        "content_chunk": chunk[:2500],
    }


# ── Embedding ─────────────────────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> list[list[float]]:
    response = openai_client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL,
    )
    return [item.embedding for item in response.data]


# ── Main ingest ───────────────────────────────────────────────────────────────

def ingest_site_content(data_path: str = "data/site_content.json"):
    print(f"\n{'='*55}")
    print("  Japan Electronics — Site Content Ingestion")
    print(f"{'='*55}\n")

    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {data_path}\n"
            "Run site_content_scraper.py first to generate it."
        )

    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    items = raw.get("content", [])
    print(f"Loaded {len(items)} content items from {data_path}")

    # Connect to existing Pinecone index
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(PINECONE_INDEX_NAME)
    print(f"Connected to Pinecone index '{PINECONE_INDEX_NAME}'\n")

    # Build all vectors (with chunking)
    all_vectors = []
    total_chunks = 0

    for item in items:
        content = item.get("content", "").strip()
        if not content:
            logger_print(f"  Skipping empty item: {item.get('title', item.get('id'))}")
            continue

        chunks = chunk_text(content)
        total_chunks += len(chunks)

        for i, chunk in enumerate(chunks):
            text = content_item_to_text(item, chunk, i)
            vector_id = f"{item['id']}_chunk_{i}"
            meta = build_metadata(item, chunk, i, len(chunks))
            all_vectors.append((vector_id, text, meta))

    print(f"Total chunks to embed: {total_chunks} (from {len(items)} items)\n")

    # Embed and upsert in batches
    total_upserted = 0
    for batch_start in range(0, len(all_vectors), INGEST_BATCH_SIZE):
        batch = all_vectors[batch_start: batch_start + INGEST_BATCH_SIZE]
        batch_ids   = [v[0] for v in batch]
        batch_texts = [v[1] for v in batch]
        batch_metas = [v[2] for v in batch]

        batch_num = batch_start // INGEST_BATCH_SIZE + 1
        print(f"Embedding batch {batch_num} ({len(batch)} chunks)...", end=" ", flush=True)

        embeddings = embed_texts(batch_texts)

        vectors = [
            {"id": vid, "values": emb, "metadata": meta}
            for vid, emb, meta in zip(batch_ids, embeddings, batch_metas)
        ]

        index.upsert(vectors=vectors)
        total_upserted += len(vectors)
        print(f"✓ ({total_upserted} total upserted)")
        time.sleep(0.5)

    print(f"\n✅ Done! {total_upserted} chunks ingested into '{PINECONE_INDEX_NAME}'.")
    print(f"   Your chatbot can now answer questions about:")
    print(f"   store locations, policies, blogs, FAQs, and corporate info.")


def logger_print(msg):
    print(msg)


if __name__ == "__main__":
    ingest_site_content()
