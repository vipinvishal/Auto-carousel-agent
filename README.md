<div align="center">

# vipinislearning AI Carousel Automator

### Technical AI explained simply — delivered to your inbox automatically.

[![Scheduled workflow](https://github.com/vipinvishal/Auto-carousel-agent/actions/workflows/carousel.yml/badge.svg)](https://github.com/vipinvishal/Auto-carousel-agent/actions/workflows/carousel.yml)
[![Five PNG slides](https://img.shields.io/badge/carousel-5%20PNG%20slides-ff8aa5)](assets/approved/reference-carousel/slide-01.png)
[![English only](https://img.shields.io/badge/language-English-6fbceb)](config/brand.json)

</div>

<p align="center">
  <img src="assets/approved/reference-carousel/slide-01.png" alt="Approved AI carousel style" width="430">
</p>

<p align="center"><em>The approved visual direction: bold hook, simple diagram, useful takeaway, blue bird, and a clear CTA.</em></p>

The permanent visual reference library is kept in
[`assets/approved/reference-style/`](assets/approved/reference-style/). It is a
copied, version-controlled backup of the owner's `Ref Image` directory, so
future changes can be checked against the agreed hand-drawn look.

## What this project does

This project creates a complete Threads post for `vipinislearning` and emails
it to:

> `vipinislearning@gmail.com`

You do not need to keep your computer switched on. GitHub Actions runs the
automation in the cloud.

## Delivery schedule

| India time | What happens |
|---|---|
| 9:00 AM IST | Exact approved Ref Image carousel |
| 12:00 PM IST | Exact approved Ref Image carousel |
| 5:00 PM IST | Exact approved Ref Image carousel |

GitHub uses UTC internally, so the workflow uses `03:30`, `06:30`, and `11:30`
UTC for these three India-time deliveries.

> GitHub may occasionally start a scheduled job a little late during heavy
> platform load.

## How one email is made

```mermaid
flowchart LR
    A[Find a useful technical AI topic] --> B[Explain it in plain English]
    B --> C[Create 5 synchronized PNG slides]
    C --> D[Validate text, size, and order]
    D --> E[Email the package]
```

The post and the carousel are created together. The hook, explanation, and
takeaway are never generated as separate stories.

## What arrives in the email

Every email contains:

- `post.txt` — exactly three short Threads lines.
- `slide-01.png` to `slide-05.png` — five portrait PNGs in posting order.
- Hashtags on the third post line.
- A source note and package metadata.

The slides use the approved visual language:

- Cream paper background.
- Thick black handwritten-style type.
- Yellow hook highlights.
- Purple, mint, blue, orange, and pink cards.
- Simple technical diagrams and icons.
- Blue bird mascot.
- Pink takeaway banner and black CTA panel.

## Topics we publish

The content stays technical and beginner-friendly. Examples include:

- LLM behavior and model comparisons.
- New model or provider releases.
- RAG, embeddings, chunking, and retrieval.
- Prompting mechanics and output control.
- AI agents, tools, orchestration, and guardrails.
- Evaluation, latency, cost, privacy, and deployment.

For model releases, the content focuses on task fit and trade-offs—not a
permanent “best model” claim. Current claims are tied to research sources and
dated comparisons.

## Image behavior: exact approved reference delivery

The eight-image Ref Image library is stored in
`assets/approved/reference-style/` and is the permanent visual source of truth.
Scheduled emails copy the first five approved PNGs byte-for-byte, so the email
cannot silently send the old renderer style.

The exact reference delivery is intentionally separate from researched-topic
previews. A static raster set cannot carry a new topic's words without
breaking synchronization. New-topic rendering remains available manually with
`reference_lock=false`, but scheduled delivery is locked to the approved
artwork until a true image-generation/template-editing service is added.

## Run a safe local test

From the repository root:

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests
python3 src/automation.py --date 2099-01-01 --slot 0900 --topic llm --force-fallback
```

The generated package is written to `out/`. It contains the five PNGs, the
three-line post, and metadata. The `out/` directory is ignored by Git.

## Send a real test email

Open the **Actions** tab and run **vipinislearning approved AI Threads
carousel** manually with:

1. Any delivery slot.
2. `reference_lock = true`.

This sends the exact approved five-slide reference carousel to the configured
Gmail address without waiting for live research or the content API. To preview
the renderer with a topic, run it with `reference_lock=false` and choose
`topic=agents`, `rag`, `prompting`, or `llm`.

## Required GitHub secrets

These secrets are configured in the repository and are never committed:

| Secret | Used for |
|---|---|
| `GMAIL_APP_PASSWORD` | Sends the email through Gmail SMTP |
| `GROQ_API_KEY` | Generates researched technical-AI copy |

If the content API is unavailable, the approved evergreen fallback keeps the
email pipeline working.

## Repository map

```text
src/automation.py       Build, validate, and send one package
src/research.py         Find and rank recent technical AI topics
src/content_engine.py   Create synchronized three-line copy and slide copy
src/renderer.py          Render the approved five-slide visual system
src/emailer.py           Attach PNGs and send the Gmail message
assets/approved/         Mascot and approved reference carousel
assets/approved/reference-style/
                         Permanent visual reference library
config/                  Brand, editorial, and LLM comparison rules
tests/                   Renderer, schedule, asset, and validation checks
```

## Design promise

Every delivery should make one technical AI idea easier to understand in under
a minute—and useful enough to save, share, or discuss.
