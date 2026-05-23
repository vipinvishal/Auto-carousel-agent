"""
trends.py — Fetch trending AI/Cloud stories from Hacker News + Reddit.

Sources:
  - Hacker News topstories API (no auth required)
  - Reddit new posts from r/artificial, r/MachineLearning, r/AITools, r/CloudComputing

Returns the highest-scoring AI/Cloud story from the last 48 hours.
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logger = logging.getLogger(__name__)

# Short/ambiguous keywords that must match as whole words (not substrings).
# e.g. "ai" should NOT match "hail", "trail", "email".
_WORD_BOUNDARY_KEYWORDS = [
    r"\bai\b", r"\bml\b", r"\bllm\b", r"\bllms\b", r"\brag\b",
    r"\bgpu\b", r"\bgpus\b", r"\baws\b", r"\bgpt\b", r"\bapi\b",
]

# Multi-word or distinctive keywords — substring match is fine.
_SUBSTRING_KEYWORDS = [
    "openai", "anthropic", "google cloud", "azure", "kubernetes", "docker",
    "mistral", "llama", "hugging face", "machine learning", "deep learning",
    "neural network", "transformer", "diffusion", "chatbot", "agent",
    "fine-tun", "inference", "serverless", "mlops", "nvidia", "generative",
    "vector database", "embedding", "copilot", "langchain", "deepseek",
    "sora", "dall-e", "stable diffusion", "claude", "gemini", "artificial intelligence",
]

_WORD_RE = re.compile("|".join(_WORD_BOUNDARY_KEYWORDS), re.IGNORECASE)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}
_HN_BASE = "https://hacker-news.firebaseio.com/v0"
_REDDIT_SUBS = ["artificial", "MachineLearning", "AITools", "CloudComputing"]
_CUTOFF_SECS = 48 * 3600


def _is_ai_cloud(title: str) -> bool:
    t = title.lower()
    if _WORD_RE.search(title):
        return True
    return any(kw in t for kw in _SUBSTRING_KEYWORDS)


def _fetch_hn_item(story_id: int, cutoff: float) -> dict | None:
    try:
        item = requests.get(
            f"{_HN_BASE}/item/{story_id}.json", timeout=8
        ).json()
        if not item or item.get("type") != "story":
            return None
        if item.get("time", 0) < cutoff:
            return None
        title = item.get("title", "")
        if not _is_ai_cloud(title):
            return None
        return {
            "id": str(story_id),
            "title": title,
            "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            "score": item.get("score", 0),
            "source": "hackernews",
            "selftext": "",
        }
    except Exception:
        return None


def _get_hn_stories(limit: int = 150) -> list[dict]:
    cutoff = time.time() - _CUTOFF_SECS
    try:
        ids = requests.get(f"{_HN_BASE}/topstories.json", timeout=10).json()[:limit]
    except Exception as exc:
        logger.warning("HN topstories fetch failed: %s", exc)
        return []

    stories = []
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(_fetch_hn_item, sid, cutoff): sid for sid in ids}
        for future in as_completed(futures):
            result = future.result()
            if result:
                stories.append(result)

    logger.info("HN: %d AI/Cloud stories in last 48 hrs", len(stories))
    return sorted(stories, key=lambda x: x["score"], reverse=True)


def _get_reddit_stories() -> list[dict]:
    cutoff = time.time() - _CUTOFF_SECS
    stories = []

    for sub in _REDDIT_SUBS:
        try:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            data = requests.get(url, headers=_HEADERS, timeout=10).json()
            for post in data["data"]["children"]:
                p = post["data"]
                if p.get("created_utc", 0) < cutoff:
                    continue
                title = p.get("title", "")
                if not _is_ai_cloud(title):
                    continue
                post_url = p.get("url", "")
                if not post_url or "reddit.com" in post_url:
                    post_url = f"https://www.reddit.com{p.get('permalink', '')}"
                stories.append({
                    "id": p.get("id", ""),
                    "title": title,
                    "url": post_url,
                    "score": p.get("score", 0),
                    "source": f"reddit/r/{sub}",
                    "selftext": p.get("selftext", ""),
                })
        except Exception as exc:
            logger.warning("Reddit r/%s fetch failed: %s", sub, exc)

    logger.info("Reddit: %d AI/Cloud stories in last 48 hrs", len(stories))
    return sorted(stories, key=lambda x: x["score"], reverse=True)


def get_top_story() -> dict | None:
    """
    Return the highest-scoring AI/Cloud story from the last 48 hours.
    Combines Hacker News and Reddit. Returns None if nothing found.
    """
    hn = _get_hn_stories()
    reddit = _get_reddit_stories()

    all_stories = hn + reddit
    all_stories.sort(key=lambda x: x["score"], reverse=True)

    if not all_stories:
        logger.warning("No AI/Cloud stories found in the last 48 hours.")
        return None

    top = all_stories[0]
    logger.info(
        "Top story [%s | score=%d]: %s",
        top["source"], top["score"], top["title"],
    )
    return top
