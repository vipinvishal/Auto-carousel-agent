"""
transcript.py — Fetch YouTube transcript and video metadata.

Uses yt-dlp as the primary method (works from cloud IPs like GitHub Actions).
youtube-transcript-api is kept as a local fallback only.

Why yt-dlp: youtube-transcript-api makes direct HTTP requests to YouTube's
transcript endpoint, which is blocked from cloud provider IPs (AWS, GCP, Azure).
yt-dlp uses YouTube's InnerTube API which is not subject to the same block.
"""

import logging
import os
import requests
import yt_dlp

logger = logging.getLogger(__name__)

_LANG_PREFERENCE = ["en", "en-US", "en-GB", "en-IN", "hi"]


# ── Primary: yt-dlp (cloud-safe) ─────────────────────────────────────────────

def _cookie_opt() -> dict:
    """Return cookiefile option if YOUTUBE_COOKIE_FILE env var is set."""
    cookie_file = os.environ.get("YOUTUBE_COOKIE_FILE", "")
    if cookie_file and os.path.exists(cookie_file):
        logger.info("Using YouTube cookies from %s", cookie_file)
        return {"cookiefile": cookie_file}
    return {}


def get_transcript(video_id: str) -> str:
    """
    Fetch the full transcript text using yt-dlp.
    Works from GitHub Actions (with cookies) and local machines.

    Set YOUTUBE_COOKIE_FILE env var to a Netscape-format cookie file
    to bypass YouTube's cloud IP bot detection.

    Raises:
        RuntimeError: if no transcript can be fetched.
    """
    ydl_opts = {
        "quiet":         True,
        "no_warnings":   True,
        "skip_download": True,
        **_cookie_opt(),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=False,
            )
    except Exception as exc:
        raise RuntimeError(f"yt-dlp failed to fetch video info for {video_id}: {exc}") from exc

    # Try manual subtitles first, then auto-generated captions
    for caps_key in ("subtitles", "automatic_captions"):
        caps = info.get(caps_key) or {}
        for lang in _LANG_PREFERENCE:
            if lang not in caps:
                continue
            for fmt in caps[lang]:
                if fmt.get("ext") == "json3":
                    text = _fetch_and_parse_json3(fmt["url"])
                    if text:
                        logger.info(
                            "Transcript fetched via yt-dlp (%s, %s): %d chars",
                            caps_key, lang, len(text),
                        )
                        return text

    raise RuntimeError(
        f"No transcript found for {video_id}. "
        "The video may not have captions enabled."
    )


def _fetch_and_parse_json3(url: str) -> str:
    """Download a json3-format subtitle file and return plain text."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Failed to download subtitle file: %s", exc)
        return ""

    texts = []
    for event in data.get("events", []):
        for seg in event.get("segs", []):
            t = seg.get("utf8", "").strip()
            if t and t != "\n":
                texts.append(t)
    return " ".join(texts)


# ── Video title ───────────────────────────────────────────────────────────────

def get_video_title(video_id: str) -> str:
    """
    Return the video title via oEmbed (no API key needed).
    Falls back to a generic title on failure.
    """
    try:
        url = (
            "https://www.youtube.com/oembed"
            f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        title = resp.json().get("title", "")
        if title:
            logger.info("Video title: %s", title)
            return title
    except Exception as exc:
        logger.warning("Could not fetch video title for %s: %s", video_id, exc)
    return f"Video {video_id}"
