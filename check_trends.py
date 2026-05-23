"""
check_trends.py — Poll for trending AI/Cloud topics and run the carousel pipeline.

Replaces check_video.py. Sources: Hacker News + Reddit (last 48 hours).
Runs as a GitHub Actions cron job every 2 days.
Tracks the last processed story in last_story.txt.
"""

import logging
import os
import sys

import scraper
import trends
from agent import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

LAST_STORY_FILE = "last_story.txt"


def get_last_story_id() -> str:
    if os.path.exists(LAST_STORY_FILE):
        return open(LAST_STORY_FILE).read().strip()
    return ""


def save_last_story_id(story_id: str) -> None:
    with open(LAST_STORY_FILE, "w") as fh:
        fh.write(story_id)
    logger.info("Saved last story ID: %s", story_id)


if __name__ == "__main__":
    logger.info("=== VipinAIHub Carousel Agent — Trending Topics Check ===")

    story = trends.get_top_story()
    if not story:
        logger.error("No trending AI/Cloud stories found in the last 48 hours. Exiting.")
        sys.exit(1)

    story_id = story["id"]
    title    = story["title"]
    url      = story["url"]

    last_id = get_last_story_id()
    logger.info("Top story  : [%s | score=%d] %s", story["source"], story["score"], title)
    logger.info("Story ID   : %s", story_id)
    logger.info("Last run   : %s", last_id or "(none)")

    if story_id == last_id:
        logger.info("Already processed this story. Nothing to do. ✓")
        sys.exit(0)

    logger.info("New story detected — scraping article text...")
    article_text = scraper.scrape_article(url, story.get("selftext", ""))

    if not article_text and story["source"] == "hackernews":
        logger.info("Article scrape failed — falling back to HN comments...")
        article_text = scraper.scrape_hn_comments(story_id)

    if not article_text:
        logger.warning("No content found. Using headline only.")
        article_text = f"Trending topic: {title}\nSource: {url}"

    logger.info("Article text: %d chars", len(article_text))
    logger.info("Running carousel pipeline...")

    result = run_pipeline(article_text, title)

    if result["success"]:
        save_last_story_id(story_id)
        logger.info("Done! Email sent: %s", result["email_sent"])
        sys.exit(0)
    else:
        logger.error("Pipeline failed: %s", result["error"])
        sys.exit(1)
