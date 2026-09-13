"""Unattended GitHub Actions entry point for vipinislearning."""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
import shutil
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

from content_engine import generate_content
from emailer import send_package
from renderer import (
    APPROVED_REFERENCE_DIR,
    MASCOT_PATH,
    OUTPUT_SIZE,
    REFERENCE_STYLE_DIR,
    TEMPLATE_SPEC,
    VISUAL_TEMPLATE,
    render_slide,
)
from research import choose_candidate

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "out"
IST = ZoneInfo("Asia/Kolkata")
SLOTS = ("0900", "1200", "1700")
LOGGER = logging.getLogger("vipinislearning.carousel")
REFERENCE_SLIDES = tuple(
    APPROVED_REFERENCE_DIR / f"slide-{index:02d}.png"
    for index in range(1, 6)
)
REFERENCE_POST_LINES = [
    "Stop learning AI agents. Build these 5 instead.",
    "Start with one small workflow, then add tools, checks, and a useful payoff.",
    "If this changes how you think about learning AI, save it before your next build. #AIAgents #AIEngineering #LLMs",
]


def automatic_slot(now: datetime | None = None) -> str:
    now = now or datetime.now(IST)
    slot = f"{now.hour:02d}{now.minute:02d}"
    if slot not in SLOTS:
        raise ValueError(f"slot must be one of {', '.join(SLOTS)} IST; got {slot}")
    return slot


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:60] or "technical-ai"


def _email_html(package: dict) -> str:
    lines = "<br>".join(html.escape(line) for line in package["post_lines"])
    return f"""<html><body style='font-family:Arial,sans-serif;color:#141721'>
<h2>vipinislearning — AI Threads package</h2>
<p><b>Package:</b> {html.escape(package['package_id'])}</p>
<p style='font-size:18px;line-height:1.5'>{lines}</p>
<p><b>Source:</b> {html.escape(package['source'])}</p>
<p>Download slides 01–05 and upload them to Threads in order.</p>
</body></html>"""


def build_package(
    day: date,
    slot: str,
    topic_key: str | None = None,
    force_fallback: bool = False,
    reference_lock: bool = False,
):
    candidate = None if reference_lock else choose_candidate(day, slot)
    selected_key = "reference" if reference_lock else (topic_key or (candidate and candidate.get("topic_key")) or "rag")
    if reference_lock:
        topic = {
            "topic_key": "reference",
            "post_lines": REFERENCE_POST_LINES,
            "source": "Source: owner-approved Ref Image reference carousel",
            "research_title": "Approved Ref Image carousel",
            "generation_mode": "exact-reference-assets",
        }
    else:
        topic = generate_content(candidate, selected_key, force_fallback=force_fallback)
    topic_name = selected_key
    folder = OUT_ROOT / day.isoformat() / slot / f"{topic_name}-{_slug(topic.get('research_title', topic_name))}"
    folder.mkdir(parents=True, exist_ok=True)

    slides: list[Path] = []
    render_mode = "pillow-approved-template"
    for slide_no in range(1, 6):
        path = folder / f"slide-{slide_no:02d}.png"
        # Explicit reference-lock delivery copies the five owner-approved LLM
        # PNGs unchanged. This is the only path that promises the exact
        # hand-lettered raster artwork in the email.
        if reference_lock:
            source_path = REFERENCE_SLIDES[slide_no - 1]
            if not source_path.exists():
                raise FileNotFoundError(f"missing approved Ref Image asset: {source_path}")
            shutil.copyfile(source_path, path)
            render_mode = "exact-ref-image-reference"
        # The approved LLM carousel is kept as a golden raster reference. A
        # manual fallback test should email those exact files, not a redraw.
        elif force_fallback and selected_key == "llm":
            shutil.copyfile(APPROVED_REFERENCE_DIR / f"slide-{slide_no:02d}.png", path)
            render_mode = "exact-approved-reference"
        else:
            render_slide(slide_no, 5, topic, path)
        slides.append(path)

    source = topic.get("source") or (candidate and f"Source: {candidate['source']} — {candidate['url']}") or "Source: approved evergreen technical lesson"
    package = {
        "package_id": f"{day.isoformat()}-{slot}-{topic_name}",
        "date": day.isoformat(),
        "slot": slot,
        "timezone": "Asia/Kolkata",
        "topic": topic_name,
        "research_title": topic.get("research_title", ""),
        "language": "English",
        "recipient_email": "vipinislearning@gmail.com",
        "visual_template": VISUAL_TEMPLATE,
        "visual_template_source": TEMPLATE_SPEC["source_of_truth"],
        "render_mode": render_mode,
        "visual_dimensions": f"{OUTPUT_SIZE[0]}x{OUTPUT_SIZE[1]}",
        "post_lines": topic["post_lines"],
        "source": source,
        "source_url": candidate.get("url", "") if candidate else "",
        "generation_mode": topic.get("generation_mode", "approved-local-fallback"),
        "pipeline_steps": [
            "topic_research",
            "information_gathering",
            "skill_rules",
            "content_curation",
            "image_generation",
            "validation",
            "gmail_delivery",
        ],
        "research_signals": topic.get("research_signals", candidate.get("signals", []) if candidate else []),
        "trend_score": topic.get("trend_score", candidate.get("trend_score") if candidate else None),
        "evidence": topic.get("evidence", candidate.get("evidence", []) if candidate else []),
        "viral_rulebook": "config/viral_carousel_rules.json",
        "manual_review_required": False,
        "slides": [path.name for path in slides],
    }
    (folder / "post.txt").write_text("\n".join(package["post_lines"]) + "\n", encoding="utf-8")
    (folder / "package.json").write_text(json.dumps(package, indent=2), encoding="utf-8")
    (folder / "email.html").write_text(_email_html(package), encoding="utf-8")
    return folder, package, slides


def validate(folder: Path, package: dict, slides: list[Path]) -> list[str]:
    errors: list[str] = []
    if not 1 <= len(package.get("post_lines", [])) <= 3:
        errors.append("Threads post must contain no more than three lines")
    if len(package.get("post_lines", [])) != 3:
        errors.append("Threads post must contain exactly three non-empty lines")
    if not package.get("post_lines", ["", "", ""])[2].count("#"):
        errors.append("third post line must include hashtags")
    if len(slides) != 5:
        errors.append("package must contain exactly five PNG slides")
    expected_size = OUTPUT_SIZE
    for path in slides:
        try:
            with Image.open(path) as image:
                if image.size != expected_size:
                    errors.append(f"wrong dimensions for {path.name}: {image.size}; expected {expected_size}")
                if image.format != "PNG":
                    errors.append(f"not a PNG: {path.name}")
        except Exception as exc:
            errors.append(f"unreadable slide {path.name}: {exc}")
    if package.get("manual_review_required") is not False:
        errors.append("manual approval flag must be false")
    if not package.get("source"):
        errors.append("missing source note")
    if not MASCOT_PATH.exists():
        errors.append("approved mascot asset is missing")
    if package.get("visual_template") != TEMPLATE_SPEC["name"]:
        errors.append("package is not using the locked Ref Image template")
    if package.get("visual_template_source") != TEMPLATE_SPEC["source_of_truth"]:
        errors.append("package is not using the permanent Ref Image source")
    if len(list(REFERENCE_STYLE_DIR.glob("*.png"))) != 8:
        errors.append("permanent Ref Image library must contain eight source images")
    if len(list(APPROVED_REFERENCE_DIR.glob("slide-*.png"))) != 5:
        errors.append("approved reference carousel must contain five slides")
    if len(REFERENCE_SLIDES) != 5 or any(not path.exists() for path in REFERENCE_SLIDES):
        errors.append("Ref Image reference set must contain five approved slides")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=SLOTS, default=None)
    parser.add_argument("--topic", choices=("rag", "prompting", "agents", "llm"), default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--force-fallback", action="store_true")
    parser.add_argument("--reference-lock", action="store_true")
    args = parser.parse_args()

    now = datetime.now(IST)
    day = date.fromisoformat(args.date) if args.date else now.date()
    slot = args.slot or os.getenv("CAROUSEL_SLOT")
    if not slot:
        slot = automatic_slot(now)

    folder, package, slides = build_package(day, slot, args.topic, args.force_fallback, args.reference_lock)
    errors = validate(folder, package, slides)
    if errors:
        raise SystemExit("Validation failed: " + "; ".join(errors))
    if args.send:
        send_package(folder, package, slides)
        print(f"Email sent to {package['recipient_email']}")
    print(f"Package ready: {folder}")
    print(f"Validation passed; mode={package['generation_mode']}; manual_review_required=false")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    raise SystemExit(main())
