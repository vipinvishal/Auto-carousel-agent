"""Unattended GitHub Actions entry point for vipinislearning."""

from __future__ import annotations

import argparse
import html
import json
import logging
import os
import re
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

from content_engine import generate_content
from emailer import send_package
from renderer import APPROVED_REFERENCE_DIR, MASCOT_PATH, VISUAL_TEMPLATE, W, H, render_slide
from research import choose_candidate, classify_topic

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "out"
IST = ZoneInfo("Asia/Kolkata")
SLOTS = ("0900", "1200", "1700")
LOGGER = logging.getLogger("vipinislearning.carousel")


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


def build_package(day: date, slot: str, topic_key: str | None = None, force_fallback: bool = False):
    candidate = choose_candidate(day, slot)
    selected_key = topic_key or (candidate and candidate.get("topic_key")) or "rag"
    topic = generate_content(candidate, selected_key, force_fallback=force_fallback)
    topic_name = selected_key
    folder = OUT_ROOT / day.isoformat() / slot / f"{topic_name}-{_slug(topic.get('research_title', topic_name))}"
    folder.mkdir(parents=True, exist_ok=True)

    slides: list[Path] = []
    for slide_no in range(1, 6):
        path = folder / f"slide-{slide_no:02d}.png"
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
        "visual_dimensions": f"{W}x{H}",
        "post_lines": topic["post_lines"],
        "source": source,
        "source_url": candidate.get("url", "") if candidate else "",
        "generation_mode": topic.get("generation_mode", "approved-local-fallback"),
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
    for path in slides:
        try:
            with Image.open(path) as image:
                if image.size != (W, H):
                    errors.append(f"wrong dimensions for {path.name}: {image.size}")
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
    if len(list(APPROVED_REFERENCE_DIR.glob("slide-*.png"))) != 5:
        errors.append("approved reference carousel must contain five slides")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=SLOTS, default=None)
    parser.add_argument("--topic", choices=("rag", "prompting", "agents", "llm"), default=None)
    parser.add_argument("--date", default=None)
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--force-fallback", action="store_true")
    args = parser.parse_args()

    now = datetime.now(IST)
    day = date.fromisoformat(args.date) if args.date else now.date()
    slot = args.slot or os.getenv("CAROUSEL_SLOT")
    if not slot:
        slot = automatic_slot(now)

    folder, package, slides = build_package(day, slot, args.topic, args.force_fallback)
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
