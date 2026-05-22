# YouTube → Instagram Carousel Agent

## What This Project Does
Monitors Vaibhav Sisinty's YouTube channel in real-time.
The moment a new video is uploaded, this agent:
1. Fetches the transcript automatically
2. Sends it to Claude API for summary + bullet points
3. Generates a branded Instagram carousel (8 slides, 1080x1080 PNG)
4. Emails all PNG slides to vipinislearning@gmail.com via Gmail SMTP

## Tech Stack
- **Runtime**: Python 3.11+
- **Server**: FastAPI (listens for YouTube WebSub pings)
- **Trigger**: YouTube PubSubHubbub (real-time, event-driven)
- **Transcript**: youtube-transcript-api
- **AI**: Claude API (claude-sonnet-4-20250514)
- **Carousel**: Playwright + Pillow (1080x1080 PNG export)
- **Email**: Gmail SMTP (App Password auth)
- **Deploy**: Render.com (always-on free tier)

## Channel Being Monitored
- Channel: Vaibhav Sisinty (@vaibhavsisinty)
- Channel ID: UClXAalunTPaX1YV185DWUeg
- Topic URL: https://www.youtube.com/feeds/videos.xml?channel_id=UClXAalunTPaX1YV185DWUeg

## Brand Config
- Brand: VipinAIHub
- Handle: @VipinAIHub
- Email: vipinislearning@gmail.com
- Brand Color: #6C3BFF
- X: @VipinAIHub
- LinkedIn: linkedin.com/in/vipin-vishal-b8b92643

## Carousel Style
- 8 slides, 4:5 ratio (1080x1350px)
- Alternating light/dark slides
- Fonts: Plus Jakarta Sans (headings) + DM Sans (body)
- Progress bar on every slide
- Swipe arrow on all slides except last
- Last slide: CTA + brand follow links

## Project Files
- main.py — FastAPI server + WebSub listener + subscription renewal
- agent.py — Core pipeline orchestrator
- transcript.py — YouTube transcript fetcher
- claude_api.py — Claude API call for summary + bullets
- carousel.py — HTML carousel generator (branded)
- export.py — Playwright PNG exporter
- emailer.py — Gmail SMTP sender with PNG attachments
- config.py — All keys, settings, constants
- requirements.txt — Dependencies
- render.yaml — Render.com deploy config

## Key Rules
- Never hardcode API keys — always use config.py
- Always wait 3 seconds for fonts before Playwright screenshot
- Carousel HTML must be self-contained (no external file deps)
- PNG export size: exactly 1080x1350px per slide
- Email subject format: "🎠 New Carousel Ready — {video_title}"
- Email body: summary + bullet points + caption ready to copy
- Attach all PNGs in slide order (slide_1.png → slide_8.png)

## Environment Variables (for Render.com)
CLAUDE_API_KEY=
GMAIL_APP_PASSWORD=
CALLBACK_BASE_URL=