# 🤖 VipinAIHub Auto Carousel Agent

> Automatically monitors the internet for trending AI & Cloud news, generates a branded 8-slide Instagram carousel, and emails the ready-to-post PNG slides — every single day, hands-free.

---

## What It Does

**Twice every day** — at **10:00 AM IST** and **5:00 PM IST** — a GitHub Actions job wakes up and:

1. **Scans** Hacker News + Reddit for the top AI/Cloud story from the last 48 hours
2. **Scrapes** the full article text from the story URL
3. **Generates** carousel content (hook, bullet points, CTA, Instagram caption) using **Groq LLaMA 3.3 70B**
4. **Builds** 8 branded HTML slides (purple `#6C3BFF` theme, Plus Jakarta Sans font)
5. **Screenshots** each slide at exactly **1080 × 1350 px** (4:5 Instagram ratio) using Playwright
6. **Emails** all 8 PNG slides + the Instagram caption to `vipinislearning@gmail.com`

No server. No manual work. Just open your email and post.

---

## Pipeline Diagram

```
GitHub Actions Cron (daily 5 AM UTC)
           │
           ▼
     check_trends.py
           │
    ┌──────┴──────┐
    ▼             ▼
trends.py     (dedup check)
(HN + Reddit)  last_story.txt
    │
    ▼
scraper.py
(article text, up to 5,500 chars)
    │
    ▼
claude_api.py
(Groq LLaMA 3.3 70B → JSON)
    │
    ▼
carousel.py
(8 branded HTML slides)
    │
    ▼
export.py
(Playwright → 8× 1080×1350 PNG)
    │
    ▼
emailer.py
(Gmail SMTP → vipinislearning@gmail.com)
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Scheduler | GitHub Actions cron |
| News sources | Hacker News API + Reddit JSON API |
| Article scraper | `requests` + `BeautifulSoup4` |
| AI / Content | Groq API — `llama-3.3-70b-versatile` (free tier) |
| Carousel HTML | Pure Python string templates (self-contained, no external files) |
| PNG export | Playwright (Chromium headless) + Pillow resize |
| Email | Gmail SMTP with App Password |
| Language | Python 3.11+ |

---

## Carousel Style

- **8 slides**, 4:5 ratio — **1080 × 1350 px** per slide
- Alternating light/dark slides
- Brand color: `#6C3BFF` (purple)
- Fonts: Plus Jakarta Sans (headings) + DM Sans (body)
- Progress bar on every slide
- Swipe arrow on all slides except the last
- **Slide 1:** scroll-stopping hook (most surprising fact from the article)
- **Slides 2–7:** specific insights, numbers, tool names — no filler
- **Slide 8:** CTA + brand follow links

---

## Project Files

```
.
├── check_trends.py      ← Entry point (run by GitHub Actions)
├── trends.py            ← Fetches top AI/Cloud story from HN + Reddit
├── scraper.py           ← Scrapes article text + HN comments fallback
├── claude_api.py        ← Groq API call → carousel JSON content
├── carousel.py          ← Builds 8 branded HTML slides
├── export.py            ← Playwright → 1080×1350 PNG export
├── emailer.py           ← Gmail SMTP sender (PNGs as downloadable attachments)
├── agent.py             ← Pipeline orchestrator (called by check_trends.py)
├── config.py            ← All keys, constants (loaded from env vars)
├── requirements.txt     ← Python dependencies
├── last_story.txt       ← Dedup: stores last processed HN/Reddit story ID
└── .github/
    └── workflows/
        └── carousel.yml ← Daily GitHub Actions cron job
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/vipinvishal/Auto-carousel-agent.git
cd Auto-carousel-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
playwright install --with-deps chromium
```

### 3. Get your API keys

| Key | Where to get it |
|---|---|
| `GROQ_API_KEY` | Free at [console.groq.com](https://console.groq.com) |
| `GMAIL_APP_PASSWORD` | Google Account → Security → 2-FA → [App Passwords](https://myaccount.google.com/apppasswords) |

### 4. Create a `.env` file (local dev only)

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

### 5. Run manually

```bash
# Test the full pipeline immediately
python check_trends.py

# Or test just the pipeline with a custom article
python agent.py "Your article text here" "Article headline"
```

---

## GitHub Actions (Automated Daily Runs)

The workflow is already configured in `.github/workflows/carousel.yml`.

**Add secrets to your GitHub repo:**

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Add:
   - `GROQ_API_KEY`
   - `GMAIL_APP_PASSWORD`

The job runs **twice daily** — 10:00 AM IST (`4:30 AM UTC`) and 5:00 PM IST (`11:30 AM UTC`) — and also has a manual trigger button in the Actions tab.

After each run, `last_story.txt` is automatically committed back to the repo so the next run skips already-processed stories.

---

## News Sources

| Source | How it's used |
|---|---|
| **Hacker News** | Top 150 stories filtered for AI/Cloud keywords, scored by HN points |
| **Reddit** | `r/artificial`, `r/MachineLearning`, `r/AITools`, `r/CloudComputing` — last 25 new posts each |

Stories older than **48 hours** are excluded. The highest-scoring story across both sources wins.

If the article page can't be scraped (JS-rendered / paywalled), it falls back to **HN top comments**, which are often more insightful than the article itself.

---

## Brand

| Field | Value |
|---|---|
| Brand | VipinAIHub |
| Handle | @VipinAIHub |
| X (Twitter) | x.com/VipinAIHub |
| LinkedIn | linkedin.com/in/vipin-vishal-b8b92643 |
| Email | vipinislearning@gmail.com |
| Brand color | `#6C3BFF` |

---

## Email Output

Each run sends an email to `vipinislearning@gmail.com` with:
- **Subject:** `🎠 New Carousel Ready — {article title}`
- **Body:** Summary, 6 key bullet points, ready-to-copy Instagram caption + hashtags
- **Attachments:** `slide_1.png` … `slide_8.png` — all as downloadable files (not inline previews)

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ Yes | Groq API key for LLaMA 3.3 70B |
| `GMAIL_APP_PASSWORD` | ✅ Yes | Gmail 16-digit app password |

---

## License

MIT — free to fork and adapt for your own brand.
