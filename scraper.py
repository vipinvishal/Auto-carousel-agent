"""
scraper.py — Extract clean article text from URLs for carousel generation.

Priority chain:
  1. Reddit selftext   (self-posts with real content)
  2. Scraped article   (TechCrunch, VentureBeat, ArsTechnica, etc.)
  3. HN comments       (when article is JS-rendered or paywalled — HN top
                        comments are often richer context than the article)
  4. Empty string      (caller falls back to headline-only)
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_CHARS = 5_500

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_CONTENT_SELECTORS = [
    "article",
    "[role='main']",
    "main",
    ".post-content",
    ".article-body",
    ".article-content",
    ".entry-content",
    ".story-body",
    ".post-body",
    "#article-body",
    "#content",
]


def scrape_article(url: str, selftext: str = "") -> str:
    """
    Extract clean article text from the given URL.

    Priority:
      1. Reddit selftext (for Reddit self-posts with substantial content)
      2. Scraped HTML from the URL
      3. Empty string (caller should use the title as fallback)

    Returns at most MAX_CHARS characters.
    """
    # Use Reddit selftext if it's a real post (not just a link)
    if selftext and len(selftext.strip()) > 200:
        logger.info("Using Reddit selftext (%d chars)", len(selftext))
        return selftext.strip()[:MAX_CHARS]

    # Don't try to scrape Reddit comment pages
    if "reddit.com" in url and "/comments/" in url:
        logger.info("Skipping Reddit discussion URL, no article to scrape.")
        return ""

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("HTTP fetch failed for %s: %s", url, exc)
        return ""

    try:
        soup = BeautifulSoup(resp.text, "html.parser")

        # Strip boilerplate tags
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "form", "noscript", "iframe"]):
            tag.decompose()

        # Try article-specific containers first
        for selector in _CONTENT_SELECTORS:
            container = soup.select_one(selector)
            if container:
                text = container.get_text(separator=" ", strip=True)
                if len(text) > 300:
                    logger.info(
                        "Scraped %d chars using selector '%s'",
                        len(text), selector,
                    )
                    return text[:MAX_CHARS]

        # Fallback: collect all paragraphs with meaningful content
        paragraphs = [
            p.get_text(strip=True)
            for p in soup.find_all("p")
            if len(p.get_text(strip=True)) > 60
        ]
        text = " ".join(paragraphs)
        if text:
            logger.info("Scraped %d chars from <p> tags", len(text))
            return text[:MAX_CHARS]

        logger.warning("Could not extract meaningful text from %s", url)
        return ""

    except Exception as exc:
        logger.warning("HTML parsing failed for %s: %s", url, exc)
        return ""


_HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"
_MIN_COMMENT_LEN = 80
_MAX_COMMENTS    = 20


def _fetch_comment(cid: int) -> str:
    try:
        c = requests.get(_HN_ITEM.format(cid), timeout=6).json()
        if not c or c.get("deleted") or c.get("dead") or not c.get("text"):
            return ""
        text = BeautifulSoup(c["text"], "html.parser").get_text(" ", strip=True)
        return text if len(text) >= _MIN_COMMENT_LEN else ""
    except Exception:
        return ""


def scrape_hn_comments(story_id: str) -> str:
    """
    Fetch the top HN comments for a story and return them as plain text.

    Used when the linked article page cannot be scraped (JS-rendered, paywalled).
    HN top comments on AI/tech stories are frequently more insightful than the
    article itself — they add context, benchmarks, rebuttals, and comparisons.

    Returns at most MAX_CHARS characters, or empty string on failure.
    """
    try:
        item = requests.get(_HN_ITEM.format(story_id), timeout=8).json()
    except Exception as exc:
        logger.warning("HN item fetch failed for %s: %s", story_id, exc)
        return ""

    title = item.get("title", "")
    parts = [f"Story title: {title}"]

    # Self-post body (Ask HN / Show HN descriptions)
    if item.get("text"):
        desc = BeautifulSoup(item["text"], "html.parser").get_text(" ", strip=True)
        if desc:
            parts.append(f"Description: {desc}")

    kid_ids = item.get("kids", [])[:_MAX_COMMENTS]
    if not kid_ids:
        logger.info("No HN comments found for story %s", story_id)
        return " ".join(parts)[:MAX_CHARS]

    comments = []
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {pool.submit(_fetch_comment, cid): cid for cid in kid_ids}
        for future in as_completed(futures):
            text = future.result()
            if text:
                comments.append(text)

    if comments:
        parts.append("Community insights:")
        parts.extend(comments)
        logger.info(
            "Fetched %d HN comments for story %s (%d chars)",
            len(comments), story_id, sum(len(c) for c in comments),
        )

    combined = " ".join(parts)
    logger.info("HN context: %d chars total", len(combined))
    return combined[:MAX_CHARS]
