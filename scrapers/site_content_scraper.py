"""
site_content_scraper.py
=======================
Scrapes all non-product content from japanelectronics.com.pk:
  - Static pages (About Us, Store Locations, Corporate Sales, FAQ, etc.)
  - All blog posts (paginated)
  - Policy pages (Privacy, Terms, Refund)
  - Contact page

Shopify also exposes blogs via JSON API, so we use that where possible.
For static /pages/ we use requests + BeautifulSoup.

Output: data/site_content.json

Usage:
    pip install requests beautifulsoup4
    python site_content_scraper.py
"""

import json
import time
import re
import os
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://japanelectronics.com.pk"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json",
}

# ── All static pages to scrape ─────────────────────────────────────────────────
STATIC_PAGES = [
    {"url": "/pages/about-us",           "title": "About Us",           "type": "about"},
    {"url": "/pages/stores-location",    "title": "Store Locations",    "type": "store_info"},
    {"url": "/pages/corporate-solutions","title": "Corporate Sales",     "type": "corporate"},
    {"url": "/pages/faq",                "title": "FAQs",               "type": "faq"},
    {"url": "/pages/contact-us",         "title": "Contact Us",         "type": "contact"},
    {"url": "/pages/customer-feedback",  "title": "Customer Feedback",  "type": "feedback"},
    {"url": "/pages/reviews",            "title": "Customer Reviews",   "type": "reviews"},
    {"url": "/policies/privacy-policy",  "title": "Privacy Policy",     "type": "policy"},
    {"url": "/policies/terms-of-service","title": "Terms & Conditions", "type": "policy"},
    {"url": "/policies/refund-policy",   "title": "Return & Refund Policy", "type": "policy"},
]

# ── Blog handles (Shopify supports multiple blogs) ────────────────────────────
BLOG_HANDLES = ["all", "news", "blog", "tips", "guides"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_html(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, "html.parser")
            elif resp.status_code == 404:
                logger.warning(f"  404 Not Found: {url}")
                return None
            else:
                logger.warning(f"  HTTP {resp.status_code} for {url} (attempt {attempt})")
        except Exception as e:
            logger.warning(f"  Request error: {e} (attempt {attempt})")
        time.sleep(2 ** attempt)
    return None


def get_json_api(url: str, retries: int = 3) -> dict | None:
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return None
            else:
                logger.warning(f"  HTTP {resp.status_code} (attempt {attempt})")
        except Exception as e:
            logger.warning(f"  Request error: {e} (attempt {attempt})")
        time.sleep(2 ** attempt)
    return None


def clean_text(soup_element) -> str:
    """Extract and clean text from a BeautifulSoup element."""
    if not soup_element:
        return ""
    text = soup_element.get_text(separator=" ", strip=True)
    # Collapse multiple spaces/newlines
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_html(html: str) -> str:
    """Strip HTML tags from a string."""
    soup = BeautifulSoup(html or "", "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()


def extract_main_content(soup: BeautifulSoup) -> str:
    """
    Try multiple selectors to find the main page content area.
    Shopify pages typically use these containers.
    """
    selectors = [
        "main#MainContent",
        "main",
        ".page-content",
        ".page__content",
        ".shopify-policy__body",
        ".rte",                      # Shopify 'rich text editor' class
        "article",
        "#content",
        ".content",
    ]
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = clean_text(el)
            if len(text) > 100:      # ignore tiny/empty matches
                return text
    # Fallback: entire body minus nav/footer
    for tag in soup.select("nav, footer, header, script, style, .announcement-bar"):
        tag.decompose()
    return clean_text(soup.body) if soup.body else ""


# ── Static page scraper ───────────────────────────────────────────────────────

def scrape_static_pages() -> list[dict]:
    results = []
    logger.info("\n── Scraping static pages ──────────────────────────────")

    for page in STATIC_PAGES:
        url = BASE_URL + page["url"]
        logger.info(f"  {page['title']}: {url}")

        soup = get_html(url)
        if not soup:
            logger.warning(f"  Skipped (no content): {page['title']}")
            continue

        content = extract_main_content(soup)
        if not content:
            logger.warning(f"  Skipped (empty content): {page['title']}")
            continue

        results.append({
            "id":      f"page_{page['type']}_{page['url'].split('/')[-1]}",
            "type":    page["type"],
            "title":   page["title"],
            "url":     url,
            "content": content,
        })
        logger.info(f"  ✓ {page['title']} ({len(content)} chars)")
        time.sleep(0.5)

    return results


# ── Blog scraper (Shopify JSON API) ──────────────────────────────────────────

def scrape_blogs_via_api() -> list[dict]:
    """
    Shopify exposes blogs at /blogs/{handle}/articles.json
    This is much cleaner than parsing HTML.
    """
    results = []
    seen_ids = set()
    logger.info("\n── Scraping blog articles (Shopify JSON API) ──────────")

    for handle in BLOG_HANDLES:
        page = 1
        while True:
            url = f"{BASE_URL}/blogs/{handle}/articles.json?limit=250&page={page}"
            data = get_json_api(url)

            if not data:
                break

            articles = data.get("articles", [])
            if not articles:
                break

            new_articles = [a for a in articles if a["id"] not in seen_ids]
            seen_ids.update(a["id"] for a in new_articles)

            for article in new_articles:
                body_text = strip_html(article.get("body_html", ""))
                summary   = strip_html(article.get("summary_html", ""))

                results.append({
                    "id":           f"blog_{article['id']}",
                    "type":         "blog",
                    "title":        article.get("title", ""),
                    "author":       article.get("author", ""),
                    "tags":         article.get("tags", ""),
                    "published_at": article.get("published_at", ""),
                    "url":          f"{BASE_URL}/blogs/{handle}/{article.get('handle', '')}",
                    "summary":      summary,
                    "content":      body_text,
                })

            logger.info(f"  ✓ Blog '{handle}' page {page}: +{len(new_articles)} articles")

            if len(articles) < 250:
                break
            page += 1
            time.sleep(0.5)

    return results


def scrape_blogs_via_html() -> list[dict]:
    """
    Fallback: scrape blog listing page and then each article page individually.
    Used if the JSON API returns nothing.
    """
    results = []
    seen_urls = set()
    logger.info("\n── Scraping blogs via HTML (fallback) ─────────────────")

    # Get all blog post links from the listing page
    for handle in ["all", "blog", "news"]:
        page = 1
        while True:
            listing_url = f"{BASE_URL}/blogs/{handle}?page={page}"
            soup = get_html(listing_url)
            if not soup:
                break

            # Find all article links
            links = soup.select("a[href*='/blogs/']")
            article_links = list(set(
                BASE_URL + a["href"] for a in links
                if "/blogs/" in a.get("href", "")
                and "/tagged" not in a.get("href", "")
                and a["href"] not in [f"/blogs/{h}" for h in BLOG_HANDLES]
                and "articles" not in a.get("href", "")
            ))

            if not article_links:
                break

            for article_url in article_links:
                if article_url in seen_urls:
                    continue
                seen_urls.add(article_url)

                article_soup = get_html(article_url)
                if not article_soup:
                    continue

                title_el = article_soup.select_one("h1, .article__title, .blog-post__title")
                title = clean_text(title_el) if title_el else "Blog Post"

                content_el = article_soup.select_one(
                    "article, .article__content, .blog-post__content, .rte"
                )
                content = clean_text(content_el) if content_el else extract_main_content(article_soup)

                if content:
                    results.append({
                        "id":      f"blog_html_{abs(hash(article_url))}",
                        "type":    "blog",
                        "title":   title,
                        "url":     article_url,
                        "content": content,
                    })
                    logger.info(f"  ✓ {title[:60]}...")
                time.sleep(0.3)

            # Check for next page
            next_btn = soup.select_one("a[aria-label='Next'], .pagination__next, .pagination a:last-child")
            if not next_btn:
                break
            page += 1

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def scrape_all(output_path: str = "data/site_content.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"\n{'='*55}")
    print("  Japan Electronics — Site Content Scraper")
    print(f"{'='*55}")

    all_content = []

    # 1. Static pages
    static = scrape_static_pages()
    all_content.extend(static)
    logger.info(f"\n  Static pages scraped: {len(static)}")

    # 2. Blog articles — try JSON API first, fall back to HTML
    blogs_api = scrape_blogs_via_api()
    if blogs_api:
        all_content.extend(blogs_api)
        logger.info(f"  Blog articles scraped (API): {len(blogs_api)}")
    else:
        logger.info("  JSON API returned no blogs — trying HTML fallback...")
        blogs_html = scrape_blogs_via_html()
        all_content.extend(blogs_html)
        logger.info(f"  Blog articles scraped (HTML): {len(blogs_html)}")

    # 3. Build output
    type_counts = {}
    for item in all_content:
        t = item["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    output = {
        "metadata": {
            "source":        BASE_URL,
            "total_items":   len(all_content),
            "type_breakdown": type_counts,
        },
        "content": all_content,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*55}")
    print(f"✅ Done! {len(all_content)} items saved to {output_path}")
    print(f"{'='*55}")
    for t, count in type_counts.items():
        print(f"  {t}: {count}")


if __name__ == "__main__":
    scrape_all("data/site_content.json")