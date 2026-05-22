# Skills & Libraries Reference

## youtube-transcript-api
- Fetches transcript by video ID
- Handles auto-generated and manual captions
- Falls back to English if Hindi unavailable
```python
from youtube_transcript_api import YouTubeTranscriptApi
transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'hi'])
text = " ".join([t['text'] for t in transcript])
```

## Anthropic Claude API
- Model: claude-sonnet-4-20250514
- Max tokens: 2000
- Prompt returns JSON with keys: summary, bullets (list of 6)
- Always parse response as JSON

## Playwright (PNG Export)
- viewport: 420x525 (never 1080x1350)
- device_scale_factor: 1080/420 = 2.5714
- wait_for_timeout(3000) for Google Fonts
- Hide .ig-header, .ig-dots, .ig-actions, .ig-caption before screenshot
- clip: {x:0, y:0, width:420, height:525}

## Gmail SMTP
- Host: smtp.gmail.com
- Port: 587
- Auth: your Gmail + 16-digit App Password
- Use MIMEMultipart for attachments
- Attach PNGs as application/octet-stream

## FastAPI WebSub
- GET /webhook → verify subscription (echo hub.challenge)
- POST /webhook → receive ping, extract video ID from XML
- On startup → POST to pubsubhubbub.appspot.com to subscribe
- Renew every 5 days via APScheduler

## Render.com Deploy
- render.yaml defines the web service
- Start command: uvicorn main:app --host 0.0.0.0 --port $PORT
- Environment variables set in Render dashboard
- Use $7/month plan to avoid sleep