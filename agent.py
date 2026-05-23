"""
agent.py — Core pipeline orchestrator.

Pipeline:
  1. Generate content from article text  (claude_api.py)
  2. Build HTML slides                   (carousel.py)
  3. Export PNGs                         (export.py)
  4. Send email                          (emailer.py)

Run directly to test with a sample topic:
  python agent.py                                # uses built-in test text
  python agent.py "article text here" "Title"   # custom article + title
"""

import logging
import os
import re
import sys
from datetime import datetime

import carousel
import claude_api
import config
import emailer
import export

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

_TEST_TEXT = (
    "OpenAI has released GPT-5, claiming it scores 90% on the MMLU benchmark, "
    "surpassing GPT-4's 86%. The model supports 128K context windows and runs "
    "at 3x the speed of GPT-4 Turbo. Enterprises on the Plus plan get access "
    "immediately. OpenAI says the model can handle complex multi-step reasoning "
    "and agentic tasks with fewer errors. Early testers report it writes "
    "production-ready code on the first attempt. The API pricing drops by 50% "
    "compared to GPT-4 Turbo. Google is expected to respond with Gemini Ultra 2 "
    "next quarter. AWS has already announced GPT-5 support via Amazon Bedrock."
)
_TEST_TITLE = "OpenAI launches GPT-5 — 90% MMLU, 3x faster, 50% cheaper"


def _slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_-]+", "_", slug).strip("_")
    return slug[:max_len]


def run_pipeline(article_text: str, topic_title: str) -> dict:
    """
    Run the full article → carousel → email pipeline.

    Args:
        article_text : Scraped article body (plain text, up to 5 500 chars)
        topic_title  : Human-readable headline used in email subject + slide 1

    Returns:
        dict with keys:
          success    (bool)
          title      (str)
          output_dir (str)
          png_paths  (list[str])
          email_sent (bool)
          error      (str | None)
    """
    result: dict = {
        "success": False,
        "title": topic_title,
        "output_dir": "",
        "png_paths": [],
        "email_sent": False,
        "error": None,
    }

    # ── 0. Resolve output directory ─────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug      = _slugify(topic_title) or "carousel"
    out_dir   = os.path.join(config.OUTPUT_DIR, f"{slug}_{timestamp}")
    result["output_dir"] = out_dir
    os.makedirs(out_dir, exist_ok=True)

    # ── 1. Generate content via Groq ─────────────────────────────────────────
    logger.info("[1/4] Generating carousel content via Groq …")
    try:
        content = claude_api.get_content(article_text, topic_title=topic_title)
    except RuntimeError as exc:
        result["error"] = str(exc)
        logger.error("Groq API failed: %s", exc)
        return result

    # ── 2. Build HTML slides ─────────────────────────────────────────────────
    logger.info("[2/4] Building HTML carousel slides …")
    html_dir = os.path.join(out_dir, "html")
    try:
        html_paths = carousel.generate_carousel_html(
            content=content,
            output_dir=html_dir,
            brand_name=config.BRAND_NAME,
            brand_handle=config.BRAND_HANDLE,
            brand_x=config.BRAND_X,
            brand_linkedin=config.BRAND_LINKEDIN,
        )
    except Exception as exc:
        result["error"] = f"Carousel generation failed: {exc}"
        logger.error(result["error"])
        return result

    # ── 3. Export PNGs ───────────────────────────────────────────────────────
    logger.info("[3/4] Exporting PNGs via Playwright …")
    png_dir = os.path.join(out_dir, "png")
    try:
        png_paths = export.export_slides(html_paths, png_dir)
    except Exception as exc:
        result["error"] = f"PNG export failed: {exc}"
        logger.error(result["error"])
        return result

    result["png_paths"] = png_paths

    # ── 4. Send email ────────────────────────────────────────────────────────
    logger.info("[4/4] Sending email with %d PNGs …", len(png_paths))
    email_sent = emailer.send_carousel_email(png_paths, topic_title, content)
    result["email_sent"] = email_sent

    result["success"] = True
    logger.info(
        "Pipeline complete for '%s' — email_sent=%s  output=%s",
        topic_title, email_sent, out_dir,
    )
    return result


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    _text  = sys.argv[1] if len(sys.argv) > 1 else _TEST_TEXT
    _title = sys.argv[2] if len(sys.argv) > 2 else _TEST_TITLE

    logger.info("=== VipinAIHub Carousel Agent — Test Run ===")
    logger.info("Topic: %s", _title)

    _result = run_pipeline(_text, _title)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    for k, v in _result.items():
        if k == "png_paths":
            print(f"  {k}: {len(v)} files")
        else:
            print(f"  {k}: {v}")
    print("=" * 60)

    sys.exit(0 if _result["success"] else 1)
