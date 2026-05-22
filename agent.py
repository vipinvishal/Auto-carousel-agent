"""
agent.py — Core pipeline orchestrator.

Pipeline:
  1. Fetch transcript  (transcript.py)
  2. Generate content  (claude_api.py)
  3. Build HTML slides (carousel.py)
  4. Export PNGs       (export.py)
  5. Send email        (emailer.py)

Run directly to test the pipeline with a known video ID:
  python agent.py                        # uses built-in test video
  python agent.py <video_id>             # custom video
  python agent.py <video_id> <title>     # custom video + title
"""

import logging
import os
import sys
from datetime import datetime

import config
import carousel
import claude_api
import emailer
import export
import transcript

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_pipeline(video_id: str, video_title: str = "") -> dict:
    """
    Run the full transcript → carousel → email pipeline for one video.

    Args:
        video_id    : YouTube video ID (e.g. "dQw4w9WgXcQ")
        video_title : Human-readable title; fetched automatically if empty.

    Returns:
        dict with keys:
          success    (bool)
          video_id   (str)
          title      (str)
          output_dir (str)
          png_paths  (list[str])
          email_sent (bool)
          error      (str | None)
    """
    result: dict = {
        "success": False,
        "video_id": video_id,
        "title": video_title,
        "output_dir": "",
        "png_paths": [],
        "email_sent": False,
        "error": None,
    }

    # ── 0. Resolve output directory ─────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(config.OUTPUT_DIR, f"{video_id}_{timestamp}")
    result["output_dir"] = out_dir
    os.makedirs(out_dir, exist_ok=True)

    # ── 1. Fetch transcript ──────────────────────────────────────────────────
    logger.info("[1/5] Fetching transcript for video: %s", video_id)
    try:
        text = transcript.get_transcript(video_id)
    except RuntimeError as exc:
        result["error"] = str(exc)
        logger.error("Transcript fetch failed: %s", exc)
        return result

    # ── 1b. Resolve title (if not provided by WebSub ping) ──────────────────
    if not video_title:
        video_title = transcript.get_video_title(video_id)
    result["title"] = video_title
    logger.info("Video title: %s", video_title)

    # ── 2. Generate content via Claude ───────────────────────────────────────
    logger.info("[2/5] Generating carousel content via Claude API …")
    try:
        content = claude_api.get_content(text, video_title=video_title)
    except RuntimeError as exc:
        result["error"] = str(exc)
        logger.error("Claude API failed: %s", exc)
        return result

    # ── 3. Build HTML slides ─────────────────────────────────────────────────
    logger.info("[3/5] Building HTML carousel slides …")
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

    # ── 4. Export PNGs ───────────────────────────────────────────────────────
    logger.info("[4/5] Exporting PNGs via Playwright …")
    png_dir = os.path.join(out_dir, "png")
    try:
        png_paths = export.export_slides(html_paths, png_dir)
    except Exception as exc:
        result["error"] = f"PNG export failed: {exc}"
        logger.error(result["error"])
        return result

    result["png_paths"] = png_paths

    # ── 5. Send email ────────────────────────────────────────────────────────
    logger.info("[5/5] Sending email with %d PNGs …", len(png_paths))
    email_sent = emailer.send_carousel_email(png_paths, video_title, content)
    result["email_sent"] = email_sent

    result["success"] = True
    logger.info(
        "Pipeline complete for '%s' — email_sent=%s  output=%s",
        video_title, email_sent, out_dir,
    )
    return result


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    _video_id = sys.argv[1] if len(sys.argv) > 1 else "-BpzxxKe4YU"
    _title    = sys.argv[2] if len(sys.argv) > 2 else ""

    logger.info("=== YouTube Carousel Agent — Test Run ===")
    logger.info("Video ID : %s", _video_id)

    _result = run_pipeline(_video_id, _title)

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
