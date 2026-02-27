"""
Japan Electronics - Shopify JSON API Scraper
=============================================
This site runs on Shopify, which exposes public JSON endpoints.
No browser automation needed — just simple HTTP requests.

Endpoints used:
  /collections/{handle}/products.json?limit=250&page=N  → products in a collection
  /products/{handle}.json                               → full product detail (specs etc.)

Run:
    pip install requests
    python scraper.py

Output: data/scraped_data.json
"""

import json
import time
import os
import logging
import requests
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://japanelectronics.com.pk"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# All collection handles visible on the homepage
COLLECTION_HANDLES = [
    "air-conditioners",
    "led-tv",
    "built-in-oven",
    "refrigerator",
    "washing-machines",
    "water-dispenser",
    "room-air-cooler-price-in-pakistan",
    "air-fryer",
    "deep-freezers",
    "kitchen-hoods",
    "kitchen-hob",
    "kitchen-appliances",
    "high-quality-geyser-price-in-pakistan",
    # extras from original script (may overlap, duplicates are de-duped by handle)
    "microwave-ovens",
    "dishwashers",
    "small-appliances",
    "cooking-ranges",
    "ramzan-banao-asaan",
]


def get_json(url: str, params: Optional[dict] = None, retries: int = 3) -> Optional[dict]:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return None
            else:
                logger.warning(f"  HTTP {resp.status_code} for {url} (attempt {attempt})")
        except Exception as e:
            logger.warning(f"  Request error: {e} (attempt {attempt})")
        time.sleep(2 ** attempt)
    return None


def scrape_collection(handle: str) -> list[dict]:
    """Return all raw Shopify product objects for a collection."""
    products = []
    page = 1
    seen_ids = set()

    while True:
        url = f"{BASE_URL}/collections/{handle}/products.json"
        data = get_json(url, params={"limit": 250, "page": page})

        if not data:
            logger.info(f"  Collection '{handle}' not found or empty — skipping.")
            break

        batch = data.get("products", [])
        if not batch:
            break

        new_items = [p for p in batch if p["id"] not in seen_ids]
        seen_ids.update(p["id"] for p in new_items)
        products.extend(new_items)
        logger.info(f"  Page {page}: +{len(new_items)} products (total so far: {len(products)})")

        if len(batch) < 250:
            break
        page += 1
        time.sleep(0.5)  # be polite

    return products


def enrich_product(handle: str) -> Optional[dict]:
    """
    Fetch /products/{handle}.json for full detail including metafields-style body_html.
    Usually the collection endpoint already has everything, but this gets the full body_html.
    """
    url = f"{BASE_URL}/products/{handle}.json"
    data = get_json(url)
    if data:
        return data.get("product")
    return None


def format_product(raw: dict, category: str) -> dict:
    """Flatten a raw Shopify product dict into a clean record."""
    variants = raw.get("variants", [])
    images = raw.get("images", [])

    # Price info from the first (or cheapest) variant
    prices = []
    compare_prices = []
    for v in variants:
        try:
            prices.append(float(v["price"]))
        except (TypeError, ValueError):
            pass
        try:
            if v.get("compare_at_price"):
                compare_prices.append(float(v["compare_at_price"]))
        except (TypeError, ValueError):
            pass

    price = f"Rs.{min(prices):,.2f}" if prices else None
    compare_price = f"Rs.{max(compare_prices):,.2f}" if compare_prices else None
    discount = None
    if prices and compare_prices:
        saving_pct = round((1 - min(prices) / max(compare_prices)) * 100)
        if saving_pct > 0:
            discount = f"{saving_pct}% off"

    # Availability
    in_stock = any(v.get("available", False) for v in variants)

    # Options (colour, size, etc.) as a dict
    options = {}
    for opt in raw.get("options", []):
        options[opt["name"]] = opt["values"]

    # Variant table
    variant_list = []
    for v in variants:
        variant_list.append({
            "id": v["id"],
            "title": v["title"],
            "price": v["price"],
            "compare_at_price": v.get("compare_at_price"),
            "sku": v.get("sku"),
            "available": v.get("available"),
            "weight": v.get("weight"),
            "weight_unit": v.get("weight_unit"),
        })

    return {
        "id": raw["id"],
        "handle": raw["handle"],
        "name": raw["title"],
        "brand": raw.get("vendor"),
        "category": category,
        "product_type": raw.get("product_type", ""),
        "tags": raw.get("tags", []),
        "price": price,
        "compare_price": compare_price,
        "discount": discount,
        "availability": "In Stock" if in_stock else "Out of Stock",
        "description_html": raw.get("body_html", ""),
        "options": options,
        "variants": variant_list,
        "images": [img["src"] for img in images],
        "url": f"{BASE_URL}/products/{raw['handle']}",
        "published_at": raw.get("published_at"),
        "updated_at": raw.get("updated_at"),
    }


def scrape_all(output_path: str = "data/scraped_data.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    all_products: dict[int, dict] = {}  # keyed by Shopify product ID to avoid duplicates

    for handle in COLLECTION_HANDLES:
        logger.info(f"\n{'='*50}")
        logger.info(f"Collection: {handle}")
        logger.info(f"{'='*50}")

        raw_products = scrape_collection(handle)
        category_label = handle.replace("-", " ").title()

        for raw in raw_products:
            pid = raw["id"]
            if pid not in all_products:
                formatted = format_product(raw, category_label)
                all_products[pid] = formatted
            else:
                # Add category tag if product appears in multiple collections
                existing_cat = all_products[pid]["category"]
                if category_label not in existing_cat:
                    all_products[pid]["category"] = f"{existing_cat}, {category_label}"

    products_list = list(all_products.values())

    # Build category summary
    category_counts: dict[str, int] = {}
    for p in products_list:
        for cat in p["category"].split(", "):
            category_counts[cat] = category_counts.get(cat, 0) + 1

    output = {
        "metadata": {
            "source": BASE_URL,
            "total_products": len(products_list),
            "collections_scraped": COLLECTION_HANDLES,
            "category_breakdown": category_counts,
        },
        "products": products_list,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*50}")
    logger.info(f"✅ Done! {len(products_list)} unique products saved to {output_path}")
    logger.info(f"{'='*50}")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        logger.info(f"  {cat}: {count}")


if __name__ == "__main__":
    scrape_all("data/scraped_data.json")