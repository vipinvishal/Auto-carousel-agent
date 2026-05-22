"""
check_video.py — Poll Vaibhav Sisinty's YouTube channel for new videos
and run the carousel pipeline when one is found.

Uses yt-dlp (not the YouTube RSS feed) for reliable channel scraping.
Runs as a GitHub Actions cron job every 2 days.
Tracks the last processed video ID in last_video.txt.
"""

import logging
import os
import sys
import tempfile

import yt_dlp

import config
from agent import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

LAST_VIDEO_FILE = "last_video.txt"
CHANNEL_URL     = f"https://www.youtube.com/@vaibhavsisinty/videos"


def _cookie_opt() -> dict:
    cookie_file = os.environ.get("YOUTUBE_COOKIE_FILE", "")
    if cookie_file and os.path.exists(cookie_file):
        return {"cookiefile": cookie_file}
    return {}


def get_latest_video() -> tuple[str, str]:
    """
    Fetch the most recently uploaded video from the channel.
    Returns (video_id, title), or ("", "") on failure.
    """
    ydl_opts = {
        "quiet":        True,
        "no_warnings":  True,
        "extract_flat": True,
        "playlist_end": 1,
        **_cookie_opt(),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(CHANNEL_URL, download=False)

        entries = info.get("entries", [])
        if not entries:
            logger.warning("No videos found for channel.")
            return "", ""

        latest = entries[0]
        video_id = latest.get("id", "")
        title    = latest.get("title", "")
        return video_id, title

    except Exception as exc:
        logger.error("yt-dlp failed to fetch channel: %s", exc)
        return "", ""


def get_last_video_id() -> str:
    if os.path.exists(LAST_VIDEO_FILE):
        return open(LAST_VIDEO_FILE).read().strip()
    return ""


def save_last_video_id(video_id: str) -> None:
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
    logger.info("Latest  : %s — %s", video_id, title)
    logger.info("Last run: %s", last_id or "(none)")

    if video_id == last_id:
        logger.info("No new video since last check. Nothing to do. ✓")
        sys.exit(0)

    logger.info("New video detected — running pipeline...")
    result = run_pipeline(video_id, title)

    if result["success"]:
        save_last_video_id(video_id)
        logger.info("Done! Email sent: %s", result["email_sent"])
        sys.exit(0)
    else:
        logger.error("Pipeline failed: %s", result["error"])
        sys.exit(1)
