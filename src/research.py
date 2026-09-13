"""Small, server-friendly research layer for the daily carousel job.

It gathers recent technical AI stories from public feeds, prefers primary
sources when available, and returns source text to the content engine. The
research step is deliberately separate from writing so every claim can be
traced back to the selected URL.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HN_BASE = "https://hacker-news.firebaseio.com/v0"
_EXA_SEARCH_URL = "https://api.exa.ai/search"
_HEADERS = {
    "User-Agent": "vipinislearning-ai-carousel/1.0 (+https://github.com/vipinvishal/Auto-carousel-agent)",
    "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
}
_SUBREDDITS = ("artificial", "MachineLearning", "AITools", "LocalLLaMA")
_GOOGLE_NEWS_QUERIES = (
    '"AI agent" OR "LLM" developer',
    '"large language model" release',
    'RAG OR embeddings OR "context window"',
)
_CUTOFF_SECONDS = 72 * 60 * 60
_MAX_CONTEXT = 7_000
_EXA_QUERIES = (
    "latest technical AI model release LLM agents RAG evaluation developer",
    "latest AI engineering LLM reliability retrieval prompt tool calling",
    "latest generative AI research model provider benchmark deployment",
)

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
    if any(term in lowered for term in _DISTINCTIVE_TERMS):
        return True
    # A bare mention of "AI" creates false positives such as general news
    # headlines saying something is "without AI". Require a second technical
    # signal or an explicit AI-system phrase before selecting the story.
    whole_word_hits = _WHOLE_WORD_TERMS.findall(title)
    explicit_phrases = ("ai model", "ai tool", "ai agent", "ai system", "generative ai", "ai research")
    return len(whole_word_hits) >= 2 or any(phrase in lowered for phrase in explicit_phrases)


def _get_json(url: str, timeout: int = 12) -> object | None:
    try:
        response = requests.get(url, headers=_HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.debug("Research request failed for %s: %s", url, exc)
        return None


def _get_text(url: str, params: dict[str, str] | None = None, timeout: int = 15) -> str:
    try:
        response = requests.get(url, params=params, headers={**_HEADERS, "Accept": "application/rss+xml,application/xml,text/html"}, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as exc:
        logger.debug("Research request failed for %s: %s", url, exc)
        return ""


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
        "comments": len(item.get("kids", []) or []),
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
        for listing in (f"top.json?t=day&limit=40", f"hot.json?limit=40"):
            payload = _get_json(f"https://www.reddit.com/r/{subreddit}/{listing}", timeout=12)
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
                    "comments": int(post.get("num_comments", 0) or 0),
                    "created": created,
                    "selftext": str(post.get("selftext", "")),
                })
    return stories


def _fetch_google_news() -> list[dict]:
    """Use Google News RSS for fresh coverage and cross-source recurrence."""
    cutoff = time.time() - _CUTOFF_SECONDS
    stories: list[dict] = []
    for query in _GOOGLE_NEWS_QUERIES:
        xml = _get_text(
            "https://news.google.com/rss/search",
            params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
            timeout=15,
        )
        if not xml:
            continue
        try:
            root = ElementTree.fromstring(xml)
        except ElementTree.ParseError:
            continue
        for item in root.findall("./channel/item")[:30]:
            title = str(item.findtext("title") or "").strip()
            link = str(item.findtext("link") or "").strip()
            published = str(item.findtext("pubDate") or "").strip()
            if not title or not link or not _is_technical_ai(title):
                continue
            try:
                created = parsedate_to_datetime(published).astimezone(timezone.utc).timestamp()
            except (TypeError, ValueError, OverflowError):
                continue
            if created < cutoff:
                continue
            stable_key = f"{title}\n{link}"
            stories.append({
                # Stable across Python processes so evidence can be compared
                # reliably in logs and package metadata.
                "id": f"news:{hashlib.sha1(stable_key.encode('utf-8')).hexdigest()[:16]}",
                "title": title,
                "url": link,
                "source": "Google News",
                "score": 8,
                "comments": 0,
                "created": created,
                "selftext": "",
            })
    return stories


def _fetch_exa() -> list[dict]:
    """Fetch current, source-grounded technical AI evidence from Exa.

    Exa is the canonical research layer for scheduled jobs. Social/news feeds
    are retained below only to add public-engagement and recurrence signals.
    """
    api_key = os.getenv("EXA_API_KEY", "")
    if not api_key:
        logger.warning("EXA_API_KEY is not configured; Exa research is unavailable")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    stories: list[dict] = []
    for query in _EXA_QUERIES:
        try:
            response = requests.post(
                _EXA_SEARCH_URL,
                headers={"x-api-key": api_key, "Content-Type": "application/json"},
                json={
                    "query": query,
                    "type": "auto",
                    "category": "news",
                    "numResults": 8,
                    "startPublishedDate": cutoff.isoformat().replace("+00:00", "Z"),
                },
                timeout=30,
            )
            if not response.ok:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
            payload = response.json()
        except Exception as exc:
            logger.warning("Exa search failed for %r: %s", query, exc)
            continue

        for item in payload.get("results", []):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            if not title or not url or not _is_technical_ai(title):
                continue
            published = str(item.get("publishedDate") or "")
            try:
                created = datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
            except ValueError:
                created = time.time()
            if created < cutoff.timestamp():
                continue
            highlights = item.get("highlights") or []
            text = " ".join(str(value) for value in highlights if value).strip()
            if not text:
                text = str(item.get("text") or "").strip()
            stable_key = f"{title}\n{url}"
            stories.append({
                "id": f"exa:{hashlib.sha1(stable_key.encode('utf-8')).hexdigest()[:16]}",
                "title": title,
                "url": url,
                "source": "Exa",
                "score": 30,
                "comments": 0,
                "created": created,
                "selftext": text[:_MAX_CONTEXT],
                "exa_context": text[:_MAX_CONTEXT],
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
    """Return a high-signal candidate for each daily slot when possible.

    The rank combines freshness, public engagement, source quality, technical
    specificity, and recurrence across HN/Reddit/Google News. It is a public
    trend proxy, not a claim about private platform view counts.
    """
    exa_stories = _fetch_exa()
    if os.getenv("REQUIRE_EXA", "").lower() == "true" and not exa_stories:
        raise RuntimeError("Exa returned no current technical-AI research; stopping before content generation")
    stories = exa_stories + _fetch_hn() + _fetch_reddit() + _fetch_google_news()
    deduped: dict[str, dict] = {}
    for story in stories:
        key = re.sub(r"[^a-z0-9]+", " ", story["title"].lower()).strip()
        existing = deduped.get(key)
        if not existing:
            story = dict(story)
            story["signal_count"] = 1
            story["signals"] = [story["source"]]
            deduped[key] = story
            continue
        signals = existing.setdefault("signals", [])
        if story["source"] not in signals:
            signals.append(story["source"])
        existing["signal_count"] = len(signals)
        existing["score"] = max(int(existing.get("score", 0)), int(story.get("score", 0)))
        existing["comments"] = max(int(existing.get("comments", 0)), int(story.get("comments", 0)))
        existing["created"] = max(float(existing.get("created", 0)), float(story.get("created", 0)))
    # When Exa is available, it is the source-of-truth pool. Other feeds help
    # with trend signals but do not replace Exa-grounded evidence.
    primary_pool = [story for story in deduped.values() if "Exa" in story.get("signals", [])]
    ranked = sorted(
        primary_pool or deduped.values(),
        key=lambda story: (
            _story_score(story["title"], story["score"] + min(120, story.get("comments", 0) * 2), story["url"], story["created"])
            + min(18.0, (story.get("signal_count", 1) - 1) * 6.0)
        ),
        reverse=True,
    )
    if not ranked:
        logger.warning("No recent technical AI stories found")
        return None
    slot_index = ("0900", "1200", "1700").index(slot)
    # Use the top three distinct high-signal stories across the three slots;
    # do not rotate into arbitrary lower-ranked content just to force variety.
    candidate = ranked[slot_index % min(len(ranked), 8)]
    candidate = dict(candidate)
    candidate["context"] = _scrape_context(candidate)
    candidate["topic_key"] = classify_topic(candidate["title"])
    candidate["trend_score"] = round(
        _story_score(candidate["title"], candidate["score"] + min(120, candidate.get("comments", 0) * 2), candidate["url"], candidate["created"])
        + min(18.0, (candidate.get("signal_count", 1) - 1) * 6.0),
        2,
    )
    candidate["evidence"] = [
        {"title": candidate["title"], "source": candidate["source"], "url": candidate["url"]}
    ]
    for related in ranked:
        if related.get("id") == candidate.get("id"):
            continue
        candidate["evidence"].append({"title": related["title"], "source": related["source"], "url": related["url"]})
        if len(candidate["evidence"]) >= 4:
            break
    candidate.pop("hn_kids", None)
    logger.info(
        "Selected %s: %s (trend_score=%s; signals=%s)",
        candidate["source"],
        candidate["title"],
        candidate["trend_score"],
        ", ".join(candidate.get("signals", [])),
    )
    return candidate
