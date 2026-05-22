"""
transcript.py — Fetch YouTube transcript and video metadata.
Uses youtube-transcript-api for captions and the public oEmbed endpoint
for the video title (no API key required).

Supports youtube-transcript-api >= 1.0 (instance-based API).
"""

import logging
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    CouldNotRetrieveTranscript,
)

logger = logging.getLogger(__name__)

# Language preference order: English first, then common Indian English variants, then Hindi
_LANG_PREFERENCE = ["en", "en-IN", "en-GB", "en-US", "hi"]


def get_transcript(video_id: str) -> str:
    """
    Return the full transcript text for a YouTube video.
    Tries languages in preference order and falls back to any available
    transcript if preferred languages are missing.

    Raises:
        RuntimeError: if no transcript can be fetched for any reason.
    """
    api = YouTubeTranscriptApi()
    try:
        # fetch() tries languages in order and raises NoTranscriptFound if none match
        fetched = api.fetch(video_id, languages=_LANG_PREFERENCE)
        text = " ".join(entry.text for entry in fetched)
        logger.info("Transcript fetched: %d chars for video %s", len(text), video_id)
        return text
    except NoTranscriptFound:
        # Fall back: list all transcripts and grab the first available one
        try:
            transcript_list = api.list(video_id)
            # find_generated_transcript searches auto-generated captions
            transcript = transcript_list.find_generated_transcript(_LANG_PREFERENCE)
            fetched = transcript.fetch()
            text = " ".join(entry.text for entry in fetched)
            logger.info(
                "Auto-generated transcript fetched: %d chars for video %s",
                len(text),
                video_id,
            )
            return text
        except Exception as inner_exc:
            raise RuntimeError(
                f"No transcript available for video {video_id}: {inner_exc}"
            ) from inner_exc
    except TranscriptsDisabled:
        raise RuntimeError(f"Transcripts are disabled for video {video_id}.")
    except VideoUnavailable:
        raise RuntimeError(f"Video {video_id} is unavailable.")
    except CouldNotRetrieveTranscript as exc:
        raise RuntimeError(
            f"Could not retrieve transcript for {video_id}: {exc}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Unexpected error fetching transcript for {video_id}: {exc}"
        ) from exc


def get_video_title(video_id: str) -> str:
    """
    Return the video title using the public YouTube oEmbed endpoint.
    Falls back to a generic title if the request fails.
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
