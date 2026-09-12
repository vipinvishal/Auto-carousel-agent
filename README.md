# vipinislearning — automatic AI Threads carousel

This repository sends a ready-to-post technical AI package to
`vipinislearning@gmail.com` automatically. It creates a three-line Threads
post plus exactly five portrait PNG slides in the approved hand-drawn style:
cream paper, black marker typography, yellow/pink brush highlights, simple
technical diagrams, and the blue bird mascot.

The job runs in GitHub Actions, so it does not depend on a Mac being powered
on and it never pauses for per-post approval.

## Delivery schedule

All times are India Standard Time (`Asia/Kolkata`):

- 09:00 IST
- 12:00 IST (noon)
- 17:00 IST

GitHub Actions cron uses UTC, so the workflow stores these as `03:30`, `06:30`,
and `11:30` UTC. Scheduled runs can be delayed by GitHub during periods of
high load. They run from the repository's default branch.

## What each email contains

- `post.txt`: exactly three synchronized Threads lines; the third line includes
  hashtags.
- `slide-01.png` through `slide-05.png`: 1080×1350 PNGs in posting order.
- `package.json`: date, slot, topic, source URL, generation mode, and validation
  metadata.
- `email.html`: a readable summary of the post and source.

The content engine first researches recent technical AI discussion from public
Hacker News and Reddit feeds, prefers source-specific and official-provider
material, and then asks Groq for a strict five-slide JSON package. The package
is rejected back to the approved evergreen lesson if the response is malformed,
the evidence is missing, or the API is unavailable. Current LLM/provider claims
are written as dated task-fit comparisons rather than permanent winner claims.

## Secrets

The repository needs these GitHub Actions secrets (already configured for this
repository):

- `GMAIL_APP_PASSWORD`: Gmail app password for `vipinislearning@gmail.com`.
- `GROQ_API_KEY`: content-generation key. Without it, the approved fallback
  lesson is used and email delivery still works.

## Local test

From the repository root:

```bash
python -m pip install -r requirements.txt
python src/automation.py --date 2099-01-01 --slot 0900 --topic rag --force-fallback
```

The output is written below `out/` and is ignored by Git. To send a local test,
set `GMAIL_APP_PASSWORD` in the environment and add `--send`.

Run the test suite with:

```bash
python -m unittest discover -s tests
```

## GitHub test email

Use the Actions tab and run **vipinislearning approved AI Threads carousel**
manually. Choose a slot, set `topic` to `llm` to preview the approved LLM
comparison template, and enable `test_fallback` for a deterministic test that
does not call the content API. The workflow still renders, validates, and sends
the real five-slide email.

## Editorial promise

Every post is English-only and technical-AI-only: LLM behavior, prompting,
RAG, embeddings, retrieval, agents, evaluation, latency, cost, privacy, or
deployment. It is designed to be simple enough to understand quickly and
useful enough to save or share.
