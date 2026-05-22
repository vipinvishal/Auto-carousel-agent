"""
check_video.py — Poll YouTube RSS feed and run the carousel pipeline
if a new video has been uploaded since the last check.

Designed to run as a GitHub Actions cron job every 2 days.
Tracks the last processed video ID in last_video.txt.
"""

import logging
import os
import sys
import xml.etree.ElementTree as ET

import requests

import config
from agent import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

LAST_VIDEO_FILE = "last_video.txt"

_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt":   "http://www.youtube.com/xml/schemas/2015",
}


def get_latest_video() -> tuple[str, str]:
    """Fetch the YouTube RSS feed and return (video_id, title) of the newest video."""
    try:
        resp = requests.get(config.YOUTUBE_FEED_URL, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Failed to fetch YouTube RSS feed: %s", exc)
        return "", ""

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        logger.error("Failed to parse RSS XML: %s", exc)
        return "", ""

    entry = root.find("atom:entry", _NS)
    if entry is None:
        logger.warning("No entries found in RSS feed.")
        return "", ""

    video_id_el = entry.find("yt:videoId", _NS)
    title_el    = entry.find("atom:title",  _NS)

    video_id = video_id_el.text.strip() if video_id_el is not None else ""
    title    = title_el.text.strip()    if title_el    is not None else ""
    return video_id, title


def get_last_video_id() -> str:
    """Read the last processed video ID from disk."""
    if os.path.exists(LAST_VIDEO_FILE):
        content = open(LAST_VIDEO_FILE).read().strip()
        return content
    return ""


def save_last_video_id(video_id: str) -> None:
    """Persist the latest processed video ID so we don't re-process it."""
    with open(LAST_VIDEO_FILE, "w") as fh:
        fh.write(video_id)
    logger.info("Saved last video ID: %s", video_id)


if __name__ == "__main__":
    logger.info("=== YouTube Carousel Agent — Scheduled Check ===")

    video_id, title = get_latest_video()
    if not video_id:
        logger.error("Could not fetch latest video. Exiting.")
        sys.exit(1)

    last_id = get_last_video_id()
    logger.info("Latest video : %s — %s", video_id, title)
    logger.info("Last processed: %s", last_id or "(none)")

    if video_id == last_id:
        logger.info("No new video since last check. Nothing to do.")
        sys.exit(0)

    logger.info("New video detected — running pipeline...")
    result = run_pipeline(video_id, title)

    if result["success"]:
        save_last_video_id(video_id)
        logger.info(
            "Done! Email sent: %s | Output: %s",
            result["email_sent"], result["output_dir"],
        )
        sys.exit(0)
    else:
        logger.error("Pipeline failed: %s", result["error"])
        sys.exit(1)
