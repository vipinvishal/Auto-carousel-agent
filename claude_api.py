"""
claude_api.py — AI content generation using Groq (free tier).
Fixed: better prompt with examples, larger transcript window, lower temperature.
"""

import json
import logging
from groq import Groq
import config

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a brutal, no-fluff social media content strategist.
You extract SPECIFIC, SURPRISING, CONCRETE insights from transcripts.
You NEVER write generic filler like "AI is changing things" or "Learn new skills".
Every point must make the reader think "wow I didn't know that" or "that's exactly my problem".
You always respond with valid JSON only — no markdown fences, no explanation."""

_USER_TEMPLATE = """YouTube video titled: "{title}"

FULL TRANSCRIPT:
{transcript}

---

TASK: Create an 8-slide Instagram carousel from this transcript for @VipinAIHub (AI education audience).

CRITICAL RULES FOR CONTENT QUALITY:
- Extract SPECIFIC facts, numbers, names, tools from the transcript — not vague summaries
- Slide 1 title MUST be a scroll-stopping hook with a specific claim or surprising fact from the video
- Every bullet point must be SPECIFIC — mention actual tool names, actual numbers, actual outcomes
- Write like you're texting a smart friend — no corporate speak, no filler

BAD examples (never write like this):
- "AI is changing things fast"
- "Robots learn new skills"  
- "The future is here"
- "Learn and grow"

GOOD examples (write like this):
- "Claude built a full app in 3 hrs — took humans 6 months"
- "GPT-4o now sees, hears and responds in real-time"
- "This one prompt saves 4 hours of manual work daily"
- "Vaibhav's agency went from 0 to ₹1Cr using just 3 AI tools"

Return a single JSON object with EXACTLY this shape:
{{
  "summary": "2-3 sentence summary with SPECIFIC details from the video — mention actual tools, numbers, or outcomes",
  "bullets": [
    "Specific insight 1 from transcript — max 15 words, must include a concrete detail",
    "Specific insight 2 from transcript — max 15 words, must include a concrete detail",
    "Specific insight 3 from transcript — max 15 words, must include a concrete detail",
    "Specific insight 4 from transcript — max 15 words, must include a concrete detail",
    "Specific insight 5 from transcript — max 15 words, must include a concrete detail",
    "Specific insight 6 from transcript — max 15 words, must include a concrete detail"
  ],
  "slide_titles": [
    "SLIDE 1: Scroll-stopping hook — specific surprising claim from the video (max 8 words)",
    "SLIDE 2: Specific topic from video (max 6 words)",
    "SLIDE 3: Specific topic from video (max 6 words)",
    "SLIDE 4: Specific topic from video (max 6 words)",
    "SLIDE 5: Specific topic from video (max 6 words)",
    "SLIDE 6: Specific topic from video (max 6 words)",
    "SLIDE 7: The biggest takeaway (max 8 words)",
    "SLIDE 8: Follow for more AI insights"
  ],
  "slide_emojis": ["🔥", "🤖", "⚡", "🛠️", "📈", "💡", "🎯", "🚀"],
  "slide_points": [
    ["Specific point from video — max 12 words", "Specific point from video — max 12 words", "Specific point from video — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Specific point — max 12 words", "Specific point — max 12 words", "Specific point — max 12 words"],
    ["Biggest lesson from the video — max 12 words", "Second key takeaway — max 12 words", "What to do next — max 12 words"],
    ["Daily AI tips on @VipinAIHub", "Follow to stay ahead of AI curve", "Save this post — share with your team"]
  ],
  "caption": "Instagram caption — start with a hook line, then 3 key insights from the video as numbered points, end with a question to drive comments, then hashtags. Tag @VipinAIHub. Include: #AITools #ArtificialIntelligence #IndiaAI #AIForBusiness #VipinAIHub"
}}

REMEMBER: Pull REAL content from the transcript. If the video mentions a specific tool, number, person, or outcome — USE IT. Do not invent or generalize."""


def get_content(transcript: str, video_title: str = "") -> dict:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not set. Get a free key at https://console.groq.com")

    client = Groq(api_key=config.GROQ_API_KEY)

    # Groq free tier limit is 12K tokens/min. Prompt template uses ~4K tokens,
    # leaving ~7K for transcript (~5,500 chars) + ~500 buffer.
    max_chars = 5_500
    truncated = transcript[:max_chars]
    if len(transcript) > max_chars:
        logger.info("Transcript truncated from %d to %d chars.", len(transcript), max_chars)

    prompt = _USER_TEMPLATE.format(
        title=video_title or "Unknown",
        transcript=truncated,
    )

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=8_192,
            temperature=0.3,  # Lower = more faithful to transcript, less hallucination
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        logger.debug("Groq raw response: %s", raw[:300])
    except Exception as exc:
        raise RuntimeError(f"Groq API error: {exc}") from exc

    cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Groq returned non-JSON response: {raw[:200]}") from exc

    # Validate and pad all lists
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

    logger.info("Groq content generated — summary: %d chars", len(data.get("summary", "")))
    return data