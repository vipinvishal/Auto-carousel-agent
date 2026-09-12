"""Small, server-friendly research layer for the daily carousel job.

It gathers recent technical AI stories from public feeds, prefers primary
sources when available, and returns source text to the content engine. The
research step is deliberately separate from writing so every claim can be
traced back to the selected URL.
"""

from __future__ import annotations

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HN_BASE = "https://hacker-news.firebaseio.com/v0"
_HEADERS = {
    "User-Agent": "vipinislearning-ai-carousel/1.0 (+https://github.com/vipinvishal/Auto-carousel-agent)",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
}
_SUBREDDITS = ("artificial", "MachineLearning", "AITools", "LocalLLaMA")
_CUTOFF_SECONDS = 72 * 60 * 60
_MAX_CONTEXT = 7_000

_WHOLE_WORD_TERMS = re.compile(
    r"\b(ai|ml|llm|llms|rag|gpu|gpus|gpt|api|evals|embedding|inference)\b",
    re.IGNORECASE,
)
_DISTINCTIVE_TERMS = (
    "openai", "anthropic", "claude", "gemini", "llama", "mistral", "deepseek",
    "qwen", "hugging face", "machine learning", "deep learning", "neural network",
    "transformer", "agent", "tool calling", "fine-tun", "vector database",
    "retrieval", "context window", "reasoning", "inference", "benchmark",
)
_OFFICIAL_DOMAINS = (
    "openai.com", "platform.openai.com", "anthropic.com", "docs.anthropic.com",
    "ai.google.dev", "blog.google", "ai.meta.com", "mistral.ai", "huggingface.co",
    "aws.amazon.com", "cloud.google.com", "azure.microsoft.com", "docs.x.ai",
)


def _is_technical_ai(title: str) -> bool:
    lowered = title.lower()
    return bool(_WHOLE_WORD_TERMS.search(title)) or any(term in lowered for term in _DISTINCTIVE_TERMS)


def _get_json(url: str, timeout: int = 12) -> object | None:
    try:
        response = requests.get(url, headers=_HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.debug("Research request failed for %s: %s", url, exc)
        return None


def _story_score(title: str, score: int, url: str, created: float) -> float:
    age_hours = max(0.0, (time.time() - created) / 3600.0)
    freshness = max(0.0, 72.0 - age_hours) / 12.0
    official_bonus = 20.0 if any(domain in url.lower() for domain in _OFFICIAL_DOMAINS) else 0.0
    specificity = min(12.0, sum(1 for term in _DISTINCTIVE_TERMS if term in title.lower()) * 2.0)
    return float(score) + freshness + official_bonus + specificity


def _hn_item(story_id: int, cutoff: float) -> dict | None:
    item = _get_json(f"{_HN_BASE}/item/{story_id}.json", timeout=8)
    if not isinstance(item, dict) or item.get("type") != "story":
        return None
    created = float(item.get("time", 0))
    if created < cutoff:
        return None
    title = str(item.get("title", "")).strip()
    if not title or not _is_technical_ai(title):
        return None
    url = str(item.get("url") or f"https://news.ycombinator.com/item?id={story_id}")
    return {
        "id": f"hn:{story_id}",
        "title": title,
        "url": url,
        "source": "Hacker News",
        "score": int(item.get("score", 0) or 0),
        "created": created,
        "hn_kids": list(item.get("kids", []))[:12],
    }


def _fetch_hn(limit: int = 120) -> list[dict]:
    payload = _get_json(f"{_HN_BASE}/topstories.json", timeout=12)
    if not isinstance(payload, list):
        return []
    cutoff = time.time() - _CUTOFF_SECONDS
    stories: list[dict] = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = [pool.submit(_hn_item, int(story_id), cutoff) for story_id in payload[:limit]]
        for future in as_completed(futures):
            try:
                item = future.result()
            except Exception:
                item = None
            if item:
                stories.append(item)
    return stories


def _fetch_reddit() -> list[dict]:
    cutoff = time.time() - _CUTOFF_SECONDS
    stories: list[dict] = []
    for subreddit in _SUBREDDITS:
        payload = _get_json(f"https://www.reddit.com/r/{subreddit}/new.json?limit=40", timeout=12)
        if not isinstance(payload, dict):
            continue
        for child in payload.get("data", {}).get("children", []):
            post = child.get("data", {})
            created = float(post.get("created_utc", 0) or 0)
            title = str(post.get("title", "")).strip()
            if created < cutoff or not title or not _is_technical_ai(title):
                continue
            url = str(post.get("url") or "")
            if not url or "reddit.com" in url:
                url = f"https://www.reddit.com{post.get('permalink', '')}"
            stories.append({
                "id": f"reddit:{post.get('id', '')}",
                "title": title,
                "url": url,
                "source": f"Reddit r/{subreddit}",
                "score": int(post.get("score", 0) or 0),
                "created": created,
                "selftext": str(post.get("selftext", "")),
            })
    return stories


def _scrape_context(candidate: dict) -> str:
    selftext = str(candidate.get("selftext", "")).strip()
    if len(selftext) > 240:
        return selftext[:_MAX_CONTEXT]
    url = candidate.get("url", "")
    if "reddit.com" in url and "/comments/" in url:
        return ""
    try:
        response = requests.get(url, headers={**_HEADERS, "Accept": "text/html"}, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "iframe"]):
            tag.decompose()
        selectors = ("article", "[role='main']", "main", ".article-body", ".article-content", ".post-content")
        for selector in selectors:
            node = soup.select_one(selector)
            if node:
                text = node.get_text(" ", strip=True)
                if len(text) > 300:
                    return text[:_MAX_CONTEXT]
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        text = " ".join(p for p in paragraphs if len(p) > 60)
        return text[:_MAX_CONTEXT]
    except Exception as exc:
        logger.info("Could not scrape article context for %s: %s", url, exc)
        return ""


def classify_topic(title: str) -> str:
    lowered = title.lower()
    if any(term in lowered for term in ("model", "llm", "gpt", "claude", "gemini", "llama", "mistral", "benchmark", "context window")):
        return "llm"
    if any(term in lowered for term in ("rag", "retrieval", "embedding", "vector", "chunk")):
        return "rag"
    if any(term in lowered for term in ("agent", "tool calling", "workflow", "orchestration")):
        return "agents"
    return "prompting"


def choose_candidate(day, slot: str) -> dict | None:
    """Return a different high-value candidate for each daily slot when possible."""
    stories = _fetch_hn() + _fetch_reddit()
    deduped: dict[str, dict] = {}
    for story in stories:
        key = re.sub(r"[^a-z0-9]+", " ", story["title"].lower()).strip()
        deduped.setdefault(key, story)
    ranked = sorted(
        deduped.values(),
        key=lambda story: _story_score(story["title"], story["score"], story["url"], story["created"]),
        reverse=True,
    )
    if not ranked:
        logger.warning("No recent technical AI stories found")
        return None
    slot_index = ("0900", "1200", "1700").index(slot)
    candidate = ranked[(day.toordinal() + slot_index) % min(len(ranked), 8)]
    candidate = dict(candidate)
    candidate["context"] = _scrape_context(candidate)
    candidate["topic_key"] = classify_topic(candidate["title"])
    candidate.pop("hn_kids", None)
    logger.info("Selected %s: %s", candidate["source"], candidate["title"])
    return candidate
