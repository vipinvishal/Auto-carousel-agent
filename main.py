"""
main.py — FastAPI server + YouTube WebSub (PubSubHubbub) listener.

Endpoints:
  GET  /webhook  → verify subscription challenge (echo hub.challenge)
  POST /webhook  → receive new-video ping, run pipeline in background thread

Startup:
  - Subscribe to YouTube's PubSubHubbub hub for Vaibhav Sisinty's channel
  - APScheduler renews the subscription every 5 days (hub leases 10 days)

Deploy: uvicorn main:app --host 0.0.0.0 --port $PORT
"""

import logging
import threading
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse

import agent
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── WebSub subscription helpers ──────────────────────────────────────────────

def _subscribe() -> None:
    """POST a subscribe request to the PubSubHubbub hub."""
    callback_url = f"{config.CALLBACK_BASE_URL.rstrip('/')}/webhook"
    payload = {
        "hub.callback":      callback_url,
        "hub.mode":          "subscribe",
        "hub.topic":         config.YOUTUBE_FEED_URL,
        "hub.lease_seconds": config.WEBSUB_LEASE_SECONDS,
        "hub.verify":        "async",
    }
    try:
        resp = requests.post(config.PUBSUB_HUB, data=payload, timeout=15)
        if resp.status_code in (202, 204):
            logger.info(
                "WebSub subscription requested — callback: %s  topic: %s",
                callback_url, config.YOUTUBE_FEED_URL,
            )
        else:
            logger.warning(
                "WebSub subscription returned HTTP %d: %s",
                resp.status_code, resp.text[:200],
            )
    except requests.RequestException as exc:
        logger.error("WebSub subscription request failed: %s", exc)


# ── App lifespan (startup / shutdown) ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting YouTube Carousel Agent …")

    # Subscribe to WebSub on first boot
    _subscribe()

    # Renew every 5 days so the 10-day hub lease never expires
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(_subscribe, "interval", days=5, id="websub_renew")
    scheduler.start()
    logger.info("APScheduler started — WebSub renewal every 5 days.")

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("YouTube Carousel Agent stopped.")


# ── FastAPI app ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="YouTube → Instagram Carousel Agent",
    version="1.0.0",
    lifespan=lifespan,
)


# ── WebSub endpoints ──────────────────────────────────────────────────────────

@app.get("/webhook")
async def websub_verify(request: Request) -> PlainTextResponse:
    """
    YouTube hub sends a GET with hub.challenge when verifying the subscription.
    Echo the challenge back to confirm.
    """
    params = request.query_params
    challenge = params.get("hub.challenge", "")
    mode      = params.get("hub.mode", "")
    topic     = params.get("hub.topic", "")

    logger.info("WebSub verify — mode=%s  topic=%s", mode, topic)

    if not challenge:
        return PlainTextResponse("Missing hub.challenge", status_code=400)

    return PlainTextResponse(challenge, status_code=200)


@app.post("/webhook")
async def websub_receive(request: Request) -> Response:
    """
    YouTube hub POSTs an Atom feed entry when a new video is published.
    Parse the video ID and title, then run the pipeline in a background thread.
    """
    body = await request.body()
    logger.info("WebSub POST received — %d bytes", len(body))

    video_id, video_title = _parse_atom(body)
    if not video_id:
        logger.warning("Could not extract video ID from WebSub payload.")
        return Response(status_code=200)  # Always 200 to avoid hub retries

    logger.info("New video detected — id=%s  title=%s", video_id, video_title)

    # Run the pipeline in a daemon thread so the HTTP response returns immediately
    thread = threading.Thread(
        target=_run_pipeline_safe,
        args=(video_id, video_title),
        daemon=True,
    )
    thread.start()

    return Response(status_code=200)


@app.get("/health")
async def health() -> dict:
    """Simple health-check endpoint for Render.com uptime monitoring."""
    return {"status": "ok", "channel_id": config.CHANNEL_ID}


# ── Internal helpers ──────────────────────────────────────────────────────────

_ATOM_NS = {
    "atom":    "http://www.w3.org/2005/Atom",
    "yt":      "http://www.youtube.com/xml/schemas/2015",
    "media":   "http://search.yahoo.com/mrss/",
}


def _parse_atom(xml_bytes: bytes) -> tuple[str, str]:
    """
    Parse a YouTube Atom feed entry and return (video_id, title).
    Returns ("", "") if parsing fails or entry is absent.
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        logger.error("Failed to parse WebSub XML: %s", exc)
        return "", ""

    # The ping body is a full <feed> with one <entry>
    entry = root.find("atom:entry", _ATOM_NS)
    if entry is None:
        # Some hubs send the entry directly as the root element
        entry = root if root.tag.endswith("}entry") or root.tag == "entry" else None

    if entry is None:
        logger.warning("No <entry> found in WebSub payload.")
        return "", ""

    video_id_el = entry.find("yt:videoId", _ATOM_NS)
    title_el    = entry.find("atom:title", _ATOM_NS)

    video_id    = video_id_el.text.strip() if video_id_el is not None else ""
    video_title = title_el.text.strip()    if title_el    is not None else ""

    return video_id, video_title


def _run_pipeline_safe(video_id: str, video_title: str) -> None:
    """Wrapper that catches all exceptions so the background thread never crashes silently."""
    try:
        result = agent.run_pipeline(video_id, video_title)
        if result["success"]:
            logger.info(
                "Pipeline finished for '%s' — email_sent=%s",
                result["title"], result["email_sent"],
            )
        else:
            logger.error(
                "Pipeline failed for '%s' — error: %s",
                result["title"], result["error"],
            )
    except Exception as exc:
        logger.exception("Unhandled exception in pipeline thread for %s: %s", video_id, exc)
