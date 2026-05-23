"""
claude_api.py — AI content generation using Groq (free tier).

Converts a trending AI/Cloud news article into Instagram carousel content.
"""

import json
import logging

from groq import Groq

import config

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a brutal, no-fluff AI/Tech content strategist for Instagram.
You convert trending AI and Cloud news articles into high-impact carousel content.
You extract SPECIFIC, SURPRISING, CONCRETE facts — not vague summaries.
You NEVER write generic filler like "AI is changing things" or "The future is here".
Every point must make the reader think "I didn't know that" or "this affects me now".
You always respond with valid JSON only — no markdown fences, no explanation."""

_USER_TEMPLATE = """Trending AI/Cloud headline: "{title}"

ARTICLE TEXT:
{article}

---

TASK: Create an 8-slide Instagram carousel for @VipinAIHub (AI/Cloud education audience).

CRITICAL RULES:
- Pull SPECIFIC facts from the article: tool names, numbers, company names, benchmarks, dates
- Slide 1 title MUST be a scroll-stopping hook with the most surprising fact from the article
- Every bullet point must mention something concrete — no vague claims
- Slide 8 is always the CTA / follow slide
- Write like you're texting a smart friend — no corporate speak, no filler

BAD examples (never write like this):
- "AI is changing things fast"
- "Cloud adoption is growing"
- "The future is here"
- "New tools are available"

GOOD examples (write like this):
- "GPT-5 scores 90% on MMLU — beats humans at bar exam"
- "AWS cuts GPU spot price by 40% — ML training just got cheaper"
- "Google's Gemini Ultra 2 beats GPT-4 on 30/32 benchmarks"
- "Meta releases Llama 3.1 — 70B model runs on a single A100"

Return a single JSON object with EXACTLY this shape:
{{
  "summary": "2-3 sentence summary with SPECIFIC details from the article — mention actual tools, numbers, or company names",
  "bullets": [
    "Specific insight 1 — max 15 words, must include a concrete detail",
    "Specific insight 2 — max 15 words, must include a concrete detail",
    "Specific insight 3 — max 15 words, must include a concrete detail",
    "Specific insight 4 — max 15 words, must include a concrete detail",
    "Specific insight 5 — max 15 words, must include a concrete detail",
    "Specific insight 6 — max 15 words, must include a concrete detail"
  ],
  "slide_titles": [
    "Scroll-stopping hook — the most surprising fact from the article (max 8 words)",
    "Specific subtopic from article (max 6 words)",
    "Specific subtopic from article (max 6 words)",
    "Specific subtopic from article (max 6 words)",
    "Specific subtopic from article (max 6 words)",
    "Specific subtopic from article (max 6 words)",
    "The biggest takeaway or action (max 8 words)",
    "Follow for more AI insights"
  ],
  "slide_emojis": ["🔥", "🤖", "⚡", "🛠️", "📈", "💡", "🎯", "🚀"],
  "slide_points": [
    ["Specific fact from article — max 12 words", "Specific fact from article — max 12 words", "Specific fact from article — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Biggest lesson from this news — max 12 words", "What this means for you — max 12 words", "What to do right now — max 12 words"],
    ["Daily AI/Cloud insights on @VipinAIHub", "Follow to stay ahead of AI curve", "Save this — share with your team"]
  ],
  "caption": "Instagram caption — start with the hook line from slide 1, then 3 key facts as numbered points, end with a question to drive comments, then hashtags. Tag @VipinAIHub. Include: #AINews #CloudComputing #ArtificialIntelligence #AITools #VipinAIHub #MachineLearning"
}}

REMEMBER: Pull REAL content from the article. If it mentions a specific tool, number, company, or benchmark — USE IT. Do not invent or generalize."""


def get_content(article_text: str, topic_title: str = "") -> dict:
    if not config.GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Get a free key at https://console.groq.com"
        )

    client = Groq(api_key=config.GROQ_API_KEY)

    # Groq free tier: ~12K TPM. Prompt template ≈ 4K tokens,
    # leaving ~7K for article (~5,500 chars).
    max_chars = 5_500
    truncated = article_text[:max_chars]
    if len(article_text) > max_chars:
        logger.info(
            "Article truncated from %d to %d chars.", len(article_text), max_chars
        )

    prompt = _USER_TEMPLATE.format(
        title=topic_title or "Trending AI/Cloud news",
        article=truncated,
    )

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=8_192,
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        logger.debug("Groq raw response (first 300 chars): %s", raw[:300])
    except Exception as exc:
        raise RuntimeError(f"Groq API error: {exc}") from exc

    cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Groq returned non-JSON response: {raw[:200]}") from exc

    # Validate and pad all required lists
    for key, expected in (("slide_titles", 8), ("slide_emojis", 8), ("bullets", 6)):
        lst = data.get(key, [])
        while len(lst) < expected:
            lst.append("")
        data[key] = lst[:expected]

    pts = data.get("slide_points", [])
    while len(pts) < 8:
        pts.append(["", "", ""])
    for i, row in enumerate(pts):
        if not isinstance(row, list):
            pts[i] = [str(row), "", ""]
        while len(pts[i]) < 3:
            pts[i].append("")
    data["slide_points"] = pts[:8]

    logger.info(
        "Groq content generated — summary: %d chars", len(data.get("summary", ""))
    )
    return data
