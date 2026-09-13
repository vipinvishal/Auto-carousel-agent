"""Reference-conditioned carousel rendering with the OpenAI Images API."""

from __future__ import annotations

import base64
import io
import os
from contextlib import ExitStack
from pathlib import Path

from PIL import Image, ImageOps

from renderer import OUTPUT_SIZE, REFERENCE_STYLE_DIR, topic_visuals


MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2.5-sunburst")
QUALITY = os.getenv("OPENAI_IMAGE_QUALITY", "high")

REFERENCE_MAP = {
    1: ("01-cover.png", "02-how-to-build.png"),
    2: ("02-how-to-build.png", "03-pdf-study-agent.png"),
    3: ("03-pdf-study-agent.png", "05-personal-study-coach.png"),
    4: ("04-smart-task-agent.png", "06-content-repurposing-agent.png"),
    5: ("08-cta-comment-project.png", "01-cover.png"),
}


def _slide_fields(topic: dict, slide_no: int) -> tuple[str, str, str]:
    slide = topic["slides"][slide_no - 1]
    if isinstance(slide, dict):
        return (
            str(slide.get("series", "AI, SIMPLY")),
            str(slide.get("title", "")),
            str(slide.get("body", "")),
        )
    return tuple(str(value) for value in slide[:3])


def build_prompt(topic: dict, slide_no: int) -> str:
    series, title, body = _slide_fields(topic, slide_no)
    highlight = str((topic.get("highlights") or [""] * 5)[slide_no - 1])
    banner = str((topic.get("banners") or [""] * 5)[slide_no - 1])
    items = topic_visuals(topic, topic.get("topic_key", "rag"), slide_no)
    labels = ", ".join(str(label).upper() for label, _ in items)
    cta = str(topic.get("cta") or "Save this before your next post.")

    structures = {
        1: "Huge hook in the upper half; large expressive bird at bottom-left pointing to a compact 2x2 doodle cluster on the right; yellow SWIPE pill at bottom-right.",
        2: "Huge hook at top; one four-step horizontal doodle flow across the middle; one pink handwritten payoff note; large expressive bird in a lower corner.",
        3: "Huge hook at top; one four-step horizontal doodle flow across the middle; large expressive bird beside one outlined handwritten speech bubble.",
        4: "Huge hook at top; one four-step horizontal doodle flow across the middle; one pink handwritten practical note; large expressive bird in a lower corner.",
        5: "Huge payoff hook at top; small handwritten checklist; large black brush CTA panel; large expressive bird; one connected pink save note. This is the only slide with a black CTA panel.",
    }
    exact_lines = [series, title, body]
    if slide_no in (2, 3, 4, 5) and banner:
        exact_lines.append(banner)
    if slide_no == 1:
        exact_lines.append("SWIPE →")
    if slide_no == 5:
        exact_lines.append(cta)
    verbatim = "\n".join(f'- "{line}"' for line in exact_lines if line)

    return f"""Use case: infographic-diagram
Asset type: slide {slide_no} of a five-slide technical AI Threads carousel
Primary request: Create a NEW slide about the supplied technical topic while matching the reference images extremely closely in visual language, illustration finish, hierarchy, density, and mascot quality. The references are style and composition guides, not edit targets.
Style/medium: polished hand-lettered educational infographic; organic thick black marker lettering; rough highlighter strokes; clean black-outline technical doodles; soft high-quality 3D blue bird mascot with oversized black glasses; warm cream paper.
Composition/framing: portrait 4:5. {structures[slide_no]}
Attention hierarchy: one huge hook, then one smaller bold mechanism, then one quiet useful detail. One visual idea only.
Color palette: cream, black, bright yellow, coral pink, pastel blue, mint, purple, orange.
Highlighted phrase: highlight exactly "{highlight}" with a rough yellow marker stroke.
Doodle concepts: {labels}.
Text (verbatim; spell every character exactly and add no other words):
{verbatim}
Constraints: Preserve generous but purposeful spacing and the hand-made finish of the references. The bird must be large, expressive, and integrated into the explanation. Keep all text inside a central safe area so no text is lost if the image is cropped to 4:5. No logos and no watermark.
Avoid: SaaS dashboard, geometric corporate font, slide counter, sparse white card, tiny mascot, repeated UI panels, black CTA on slides 1-4, photoreal human, generic flat vector template, or app-interface gradients.
"""


def _save_result(encoded: str, destination: Path) -> None:
    raw = base64.b64decode(encoded)
    with Image.open(io.BytesIO(raw)) as generated:
        final = ImageOps.fit(
            generated.convert("RGB"),
            OUTPUT_SIZE,
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        final.save(destination, format="PNG", optimize=True)


def generate_slide(topic: dict, slide_no: int, destination: Path) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY is required for approved Ref Image generation; "
            "the rejected Pillow renderer will not be emailed as a fallback"
        )

    from openai import OpenAI

    reference_paths = [REFERENCE_STYLE_DIR / name for name in REFERENCE_MAP[slide_no]]
    missing = [path for path in reference_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing Ref Image input: {missing[0]}")

    client = OpenAI()
    with ExitStack() as stack:
        references = [stack.enter_context(path.open("rb")) for path in reference_paths]
        result = client.images.edit(
            model=MODEL,
            image=references,
            prompt=build_prompt(topic, slide_no),
            background="opaque",
            output_format="png",
            quality=QUALITY,
            size="auto",
        )
    if not result.data or not result.data[0].b64_json:
        raise RuntimeError(f"OpenAI image model returned no image for slide {slide_no}")
    _save_result(result.data[0].b64_json, destination)


def generate_carousel(topic: dict, out_dir: Path) -> list[Path]:
    slides: list[Path] = []
    for slide_no in range(1, 6):
        destination = out_dir / f"slide-{slide_no:02d}.png"
        generate_slide(topic, slide_no, destination)
        slides.append(destination)
    return slides
