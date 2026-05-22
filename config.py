"""
config.py — All keys, constants, and settings.
Load sensitive values from environment variables; never hardcode secrets.
In local dev, place a .env file in the project root with:
  GEMINI_API_KEY=AIza...
  GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
  CALLBACK_BASE_URL=https://your-service.onrender.com
"""

import os
from pathlib import Path

# Load .env file if present (harmless on Render where env vars are set natively)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent / ".env"
    if _env_path.exists():
        load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed — rely on shell env vars

# ── Groq API (free tier — get key at console.groq.com) ─────────────────────
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.3-70b-versatile"

# ── Gmail SMTP ─────────────────────────────────────────────────────────────
GMAIL_USER: str = "vipinislearning@gmail.com"
GMAIL_APP_PASSWORD: str = os.environ.get("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL: str = "vipinislearning@gmail.com"

# ── Brand ──────────────────────────────────────────────────────────────────
BRAND_NAME: str = "VipinAIHub"
BRAND_HANDLE: str = "@VipinAIHub"
BRAND_COLOR: str = "#6C3BFF"
BRAND_X: str = "x.com/VipinAIHub"
BRAND_LINKEDIN: str = "linkedin.com/in/vipin-vishal-b8b92643"
BRAND_EMAIL: str = "vipinislearning@gmail.com"

# ── YouTube / WebSub ───────────────────────────────────────────────────────
CHANNEL_ID: str = "UClXAalunTPaX1YV185DWUeg"
YOUTUBE_FEED_URL: str = (
    f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
)
PUBSUB_HUB: str = "https://pubsubhubbub.appspot.com/subscribe"
# Set CALLBACK_BASE_URL to your Render.com service URL before deploying.
CALLBACK_BASE_URL: str = os.environ.get("CALLBACK_BASE_URL", "http://localhost:8000")
WEBSUB_LEASE_SECONDS: int = 432_000  # 5 days in seconds

# ── Output ─────────────────────────────────────────────────────────────────
OUTPUT_DIR: str = "output"
