"""Deterministic renderer for the approved hand-drawn AI carousel style.

The reference system is intentionally rasterized with Pillow rather than a
browser or a local design app. That keeps the five PNGs stable in GitHub
Actions while preserving the approved cream paper, marker type, brush bands,
pastel doodles, oversized mascot, and final-slide CTA composition.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1350
# Ref Image and the approved raster carousel use this final portrait size.
# The renderer draws on the compact design grid above, then exports once at
# this size so every generated PNG matches the reference dimensions.
OUTPUT_W, OUTPUT_H = 1122, 1402
OUTPUT_SIZE = (OUTPUT_W, OUTPUT_H)
M = 74

FONT_DIR = ROOT / "assets/fonts"
FONT_HAND = str(FONT_DIR / "PatrickHand-Regular.ttf")
# Permanent Marker is an open, bundled brush-marker face used for the large
# irregular lettering seen throughout Ref Image. Patrick Hand remains the
# quieter body voice. Both are bundled so GitHub Actions matches local runs.
FONT_MARKER = str(FONT_DIR / "PermanentMarker-Regular.ttf")
FONT_HAND_BOLD = FONT_MARKER
FONT_BODY = str(FONT_DIR / "NunitoSans-Regular.ttf")
FONT_BODY_BOLD = str(FONT_DIR / "NunitoSans-Bold.ttf")
MASCOT_PATH = ROOT / "assets/approved/blue-bird-mascot.png"
APPROVED_REFERENCE_DIR = ROOT / "assets/approved/reference-carousel"
# Permanent visual source of truth supplied by the owner. These images define
# the approved hand-drawn composition, mascot treatment, marker lettering,
# brush highlights, pastel cards, and CTA style for all future work.
REFERENCE_STYLE_DIR = ROOT / "assets/approved/reference-style"
TEMPLATE_SPEC_PATH = ROOT / "config/ref_image_template.json"
TEMPLATE_SPEC = json.loads(TEMPLATE_SPEC_PATH.read_text(encoding="utf-8"))
VISUAL_TEMPLATE = TEMPLATE_SPEC["name"]

COLORS = {
    "paper": "#FAF8F3",
    "ink": "#11131C",
    "yellow": "#FFD62E",
    "pink": "#F58AA5",
    "purple": "#B898F1",
    "mint": "#94E1BD",
    "blue": "#6FBCEB",
    "orange": "#F7B16F",
    "grey": "#C7CFD9",
    "navy": "#10121D",
    "green": "#2FB773",
    "white": "#FFFFFF",
    "red": "#F45A72",
}


# Evergreen lessons are the safe fallback when research or the content API is
# unavailable. Their wording is also the canonical copy for the approved
# visual examples.
TOPICS = {
    "rag": {
        "series": "RAG, SIMPLY",
        "hook": "Your AI answer can be wrong before it even starts.",
        "post": [
            "Your AI answer can be wrong before it even starts.",
            "Bad context -> bad chunks -> weak search -> wrong answers.",
            "Fix what AI reads first. Save this. #AI #RAG #MachineLearning",
        ],
        "slides": [
            ("THE SIMPLE IDEA", "AI can only answer\nfrom what it sees.", "RAG does two jobs: find useful information, then use it to answer."),
            ("WHERE IT BREAKS", "The model is only as good\nas the chunk it receives.", "One broken paragraph can hide the exact sentence your AI needs."),
            ("CHECK THE CONTEXT", "Your AI answer can be\nwrong before it even starts.", "Most people blame the model. Check the context first."),
            ("SAVE THIS WORKFLOW", "Fix the context\nbefore you fine-tune.", "Clean source -> meaningful chunks -> relevant retrieval -> better answers."),
            ("DO THIS FIRST", "Before you change the model,\ninspect one retrieved chunk.", "It takes 10 seconds and often reveals the real bug."),
        ],
        "source": "Source: RAG quality principles; concept simplified for education",
        "accent": "blue",
        "highlights": ["what it sees", "chunk it receives", "wrong", "context", "retrieved chunk"],
        "banners": ["No useful context. No useful answer.", "Search cannot rescue missing meaning.", "Bad context = bad answers.", "Better context beats a bigger model.", "Weak chunk? Expect a weak answer."],
        "ctas": ["Look at the\nsource first.", "Inspect the\nchunk.", "Fix what AI\nreads first.", "Try it on one\nreal document.", "Test the\nevidence."],
    },
    "prompting": {
        "series": "PROMPTING, SIMPLY",
        "hook": "A vague prompt creates a vague output.",
        "post": [
            "A vague prompt creates a vague output.",
            "Role + context + constraints reduce ambiguity for the model.",
            "What will you add first? #AI #PromptEngineering #LLMs",
        ],
        "slides": [
            ("THE SIMPLE IDEA", "A vague prompt creates\na vague output.", "Start by reducing ambiguity."),
            ("THE MECHANISM", "The model cannot guess\nyour missing constraints.", "Prompting reduces ambiguity before generation."),
            ("THE BUILDING BLOCKS", "Use four controls.", "Task. Context. Constraints. Format."),
            ("THE EXAMPLE", "Give the model\na target.", "Weak: Write a summary. Strong: Summarize these notes in 5 bullets."),
            ("TAKEAWAY", "Specific beats clever.", "A good prompt is an interface between you and the model."),
        ],
        "source": "Source: prompt-engineering principles; concept simplified for education",
        "accent": "orange",
        "highlights": ["vague output", "missing constraints", "four controls", "target", "Specific"],
        "banners": ["Less ambiguity. Better outputs.", "The model cannot read your mind.", "Four controls beat clever wording.", "Give the output a target.", "Specific beats clever."],
        "ctas": ["Make the\ninstruction precise.", "Name the\nconstraint.", "Add the four\ncontrols.", "Show the\ntarget.", "Test one\ninstruction."],
    },
    "llm": {
        "series": "LLM COMPARISON",
        "hook": "There is no single best LLM—only the best fit.",
        "post": [
            "There is no single best LLM—only the best fit.",
            "Compare quality, context, tools, speed, cost, and privacy for your task.",
            "What do you optimize first? #LLM #AIModels #AIEngineering",
        ],
        "slides": [
            ("NO SINGLE BEST MODEL", "There is no single\nbest LLM—only\nthe best fit.", "Different tasks need different strengths."),
            ("START WITH THE TASK", "A benchmark score\nis not a workflow.", "First decide what your task actually needs."),
            ("COMPARE THE SYSTEM", "The model is only\none piece.", "Your result also depends on the provider and the way you use the model."),
            ("NEW MODEL?", "Do not trust the\nlaunch headline.", "Run the same task on every model."),
            ("SAVE THIS CHECKLIST", "Best model = best fit\nfor your task.", "Compare quality, context, tools, speed, cost, and privacy."),
        ],
        "source": "Source: official model documentation and dated task-fit comparison framework",
        "accent": "orange",
        "highlights": ["the best fit", "not a workflow", "one piece", "launch headline", "best fit"],
        "banners": ["A benchmark is not a workflow.", "Match the model to the work.", "The model is not the whole product.", "Measure trade-offs, not marketing.", "Compare quality, context, tools, speed, cost, and privacy."],
        "ctas": ["Compare the\ntask, not the hype.", "Choose the\njob first.", "Check the\nfull stack.", "Date the\nresult.", "What do you\noptimize first?"],
    },
    "agents": {
        "series": "AGENTS, SIMPLY",
        "hook": "An AI agent is a loop—not a single prompt.",
        "post": [
            "An AI agent is a loop—not a single prompt.",
            "Plan, call a tool, inspect the result, then continue or stop.",
            "What guardrail would you add? #AIAgents #AIEngineering #LLMs",
        ],
        "slides": [
            ("THE SIMPLE IDEA", "An AI agent is a loop—\nnot a single prompt.", "Plan. Act. Check."),
            ("THE DIFFERENCE", "A chatbot generates.\nAn agent operates.", "An agent can choose the next step and call tools."),
            ("THE LOOP", "Reliable agents need\nstop conditions.", "Plan -> act -> observe -> continue or stop."),
            ("THE EXAMPLE", "Give it a\nbounded task.", "Define the goal, tools, limits, and handoff."),
            ("TAKEAWAY", "Tools without guardrails\ncreate risk.", "Start with one narrow workflow."),
        ],
        "source": "Source: agent design principles; concept simplified for education",
        "accent": "purple",
        "highlights": ["loop", "operates", "stop conditions", "bounded task", "guardrails"],
        "banners": ["No loop without a boundary.", "Generation is not operation.", "A stop condition is a feature.", "Bound the first workflow.", "Tools without guardrails create risk."],
        "ctas": ["Give the agent\na boundary.", "Separate\nchat from action.", "Define when it\nstops.", "Keep the task\nnarrow.", "Add a human\nhandoff."],
    },
}


VISUAL_LABELS = {
    "rag": {
        1: [("FIND CONTEXT", "context"), ("WRITE ANSWER", "answer"), ("RETRIEVE", "search"), ("CITE SOURCE", "quality")],
        2: [("TOO LONG", "document"), ("CUT MID-SENTENCE", "warning"), ("NO HEADINGS", "context"), ("OUTDATED", "clock")],
        3: [("MESSY DOCS", "document"), ("BAD CHUNKS", "chunks"), ("WEAK SEARCH", "search"), ("WRONG ANSWER", "wrong")],
        4: [("CLEAN SOURCE", "quality"), ("MEANINGFUL CHUNKS", "chunks"), ("RELEVANT RETRIEVAL", "search"), ("BETTER ANSWERS", "answer")],
        5: [("COMPLETE", "quality"), ("CURRENT", "clock"), ("RELEVANT", "target")],
    },
    "prompting": {
        1: [("TASK", "target"), ("CONTEXT", "context"), ("CONSTRAINTS", "rules"), ("FORMAT", "document")],
        2: [("TASK", "target"), ("CONTEXT", "context"), ("CONSTRAINTS", "rules"), ("FORMAT", "document")],
        3: [("ROLE", "person"), ("CONTEXT", "context"), ("RULES", "rules"), ("FORMAT", "document")],
        4: [("WEAK", "warning"), ("TARGET", "target"), ("EXAMPLE", "document"), ("FORMAT", "answer")],
        5: [("TASK", "target"), ("CONTEXT", "context"), ("RULES", "rules"), ("FORMAT", "document"), ("TEST", "quality"), ("OUTPUT", "answer")],
    },
    "llm": {
        1: [("REASONING", "brain"), ("CODING", "code"), ("LONG CONTEXT", "document"), ("LOW COST", "coins")],
        2: [("REASONING", "brain"), ("CODING", "code"), ("LONG CONTEXT", "context"), ("TOOL USE", "tools")],
        3: [("MODEL", "chip"), ("PROVIDER", "provider"), ("CONTEXT", "context"), ("TOOLS", "toolbox")],
        4: [("QUALITY", "target"), ("LATENCY", "clock"), ("COST", "coins"), ("FAILURES", "warning")],
        5: [("QUALITY", "quality"), ("CONTEXT", "context"), ("TOOLS", "tools"), ("SPEED", "speed"), ("COST", "coins"), ("PRIVACY", "privacy")],
    },
    "agents": {
        1: [("PLAN", "target"), ("ACT", "tools"), ("CHECK", "search"), ("STOP", "warning")],
        2: [("GOAL", "target"), ("TOOLS", "tools"), ("STATE", "context"), ("HANDOFF", "person")],
        3: [("PLAN", "target"), ("ACT", "tools"), ("OBSERVE", "search"), ("STOP", "warning")],
        4: [("GOAL", "target"), ("ALLOWED TOOLS", "tools"), ("LIMITS", "rules"), ("HANDOFF", "person")],
        5: [("GOAL", "target"), ("TOOLS", "tools"), ("HANDOFF", "person"), ("LOGS", "document"), ("TEST", "quality"), ("STOP", "warning")],
    },
}

PASTELS = ("purple", "mint", "blue", "orange", "pink", "yellow")


def paper_canvas():
    """Create the warm, softly vignetted paper used by the Ref Image set."""
    base = Image.new("RGBA", (W, H), COLORS["paper"])
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((-180, -120, W + 180, H + 160), fill=(255, 255, 252, 232))
    glow = glow.filter(ImageFilter.GaussianBlur(95))
    base.alpha_composite(glow)
    return base


def f(path: str, size: int, index: int = 0):
    font = ImageFont.truetype(path, size, index=index)
    instance = "Bold" if "Bold" in Path(path).name else "Regular"
    try:
        font.set_variation_by_name(instance)
    except (AttributeError, OSError):
        pass
    return font


def wrap_text(draw, text: str, font_obj, max_width: int):
    lines = []
    for paragraph in str(text).split("\n"):
        if not paragraph.strip():
            lines.append("")
            continue
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = (line + " " + word).strip()
            if draw.textbbox((0, 0), candidate, font=font_obj)[2] <= max_width or not line:
                line = candidate
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def brush_rect(draw, box, fill, radius=30):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius, fill=fill)
    # Layer fixed, irregular marker passes over the smooth base. Keeping the
    # offsets deterministic makes the style stable in GitHub Actions.
    height = max(1, y2 - y1)
    passes = ((0.18, -8, 6), (0.36, 3, -4), (0.54, -5, 8), (0.72, 4, -6), (0.88, -7, 5))
    width = max(8, int(height * 0.22))
    for fraction, left_offset, right_offset in passes:
        yy = y1 + int(height * fraction)
        draw.line((x1 + left_offset, yy, x2 + right_offset, yy + 1), fill=fill, width=width)
    # Short edge strokes make the band feel painted rather than UI-generated.
    draw.line((x1 + 20, y1 + 4, x2 - 22, y1 + 1), fill=fill, width=8)
    draw.line((x1 + 12, y2 - 4, x2 - 12, y2 + 2), fill=fill, width=7)
    draw.line((x1 + 8, y1 + 16, x1 - 4, y1 + 34), fill=fill, width=7)
    draw.line((x2 - 7, y1 + 14, x2 + 5, y1 + 31), fill=fill, width=7)


def draw_centered(draw, text, center_x, y, font_obj, fill, max_width, gap=8):
    stroke_width = 2 if font_obj.size >= 48 else (1 if font_obj.size >= 26 else 0)
    lines = wrap_text(draw, text, font_obj, max_width)
    line_height = font_obj.size + gap
    for index, line in enumerate(lines):
        draw.text(
            (center_x, y + index * line_height),
            line,
            font=font_obj,
            fill=fill,
            anchor="ma",
            stroke_width=stroke_width,
            stroke_fill=fill,
        )
    return y + len(lines) * line_height


def _fit_title(draw, text, max_width, max_lines=3, max_size=92, min_size=54):
    title = str(text).upper()
    for size in range(max_size, min_size - 1, -2):
        font = f(FONT_HAND_BOLD, size)
        lines = wrap_text(draw, title, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = f(FONT_HAND_BOLD, min_size)
    return font, wrap_text(draw, title, font, max_width)[:max_lines]


def draw_title(draw, text, highlight, y=112, max_lines=3):
    """Draw the oversized brush-marker hero used throughout Ref Image."""
    font, lines = _fit_title(draw, text, W - 116, max_lines=max_lines)
    line_height = int(font.size * 1.08)
    highlight_lower = str(highlight or "").lower().strip()
    highlighted = False
    for index, line in enumerate(lines):
        line_y = y + index * line_height
        lower = line.lower()
        start = lower.find(highlight_lower) if highlight_lower else -1
        if start < 0 and index == len(lines) - 1 and not highlighted:
            start = 0
            fragment = line
        elif start >= 0:
            fragment = line[start:start + len(highlight_lower)]
        else:
            fragment = ""
        line_width = draw.textbbox((0, 0), line, font=font)[2]
        left = (W - line_width) // 2
        if fragment:
            prefix_width = draw.textbbox((0, 0), line[:start], font=font)[2]
            fragment_width = draw.textbbox((0, 0), fragment, font=font)[2]
            brush_rect(
                draw,
                (
                    left + prefix_width - 20,
                    line_y + int(font.size * 0.16),
                    left + prefix_width + fragment_width + 20,
                    line_y + int(font.size * 0.94),
                ),
                COLORS["yellow"],
                30,
            )
            highlighted = True
        draw.text(
            (left, line_y),
            line,
            font=font,
            fill=COLORS["ink"],
            stroke_width=2,
            stroke_fill=COLORS["ink"],
        )
    underline_y = y + len(lines) * line_height + 2
    draw.line((W * 0.32, underline_y, W * 0.72, underline_y - 4), fill=COLORS["yellow"], width=8)
    draw.line((W * 0.40, underline_y + 13, W * 0.67, underline_y + 9), fill=COLORS["yellow"], width=5)
    return underline_y + 18


def draw_header(draw, label):
    font = f(FONT_HAND_BOLD, 32)
    width = draw.textbbox((0, 0), label, font=font)[2]
    box = (W // 2 - width // 2 - 24, 30, W // 2 + width // 2 + 24, 94)
    brush_rect(draw, box, COLORS["yellow"], 28)
    draw.text(
        (W // 2, 61),
        label,
        font=font,
        fill=COLORS["ink"],
        anchor="mm",
        stroke_width=1,
        stroke_fill=COLORS["ink"],
    )
    for x, y, dx, dy in ((250, 40, -24, -20), (830, 40, 24, -20), (205, 82, -30, 0), (875, 82, 30, 0)):
        draw.line((x, y, x + dx, y + dy), fill=COLORS["yellow"], width=8)


def draw_rays(draw, cx, cy, color=COLORS["ink"], count=8, radius=105):
    import math
    for i in range(count):
        angle = (math.pi * 2 * i) / count
        x1 = cx + int(math.cos(angle) * radius)
        y1 = cy + int(math.sin(angle) * radius)
        x2 = cx + int(math.cos(angle) * (radius + 32))
        y2 = cy + int(math.sin(angle) * (radius + 32))
        draw.line((x1, y1, x2, y2), fill=color, width=7)


def draw_document(draw, cx, cy, scale=1.0, fill=COLORS["white"], folded=True):
    w, h = int(105 * scale), int(135 * scale)
    x1, y1, x2, y2 = cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2
    draw.rounded_rectangle((x1, y1, x2, y2), int(9 * scale), fill=fill, outline=COLORS["ink"], width=max(3, int(6 * scale)))
    for row, length in enumerate((0.68, 0.82, 0.72, 0.55)):
        yy = y1 + int((34 + row * 22) * scale)
        draw.line((x1 + int(18 * scale), yy, x1 + int(18 * scale + w * length), yy), fill=COLORS["ink"], width=max(3, int(6 * scale)))
    if folded:
        draw.line((x2 - int(30 * scale), y1, x2 - int(30 * scale), y1 + int(30 * scale)), fill=COLORS["ink"], width=max(3, int(5 * scale)))
        draw.line((x2 - int(30 * scale), y1 + int(30 * scale), x2, y1 + int(30 * scale)), fill=COLORS["ink"], width=max(3, int(5 * scale)))


def draw_search(draw, cx, cy, scale=1.0):
    r = int(42 * scale)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=COLORS["blue"], outline=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.line((cx + int(30 * scale), cy + int(30 * scale), cx + int(78 * scale), cy + int(78 * scale)), fill=COLORS["ink"], width=max(6, int(12 * scale)))


def draw_pencil(draw, cx, cy, scale=1.0):
    draw.line((cx - int(40 * scale), cy + int(40 * scale), cx + int(40 * scale), cy - int(40 * scale)), fill=COLORS["yellow"], width=max(10, int(22 * scale)))
    draw.line((cx - int(45 * scale), cy + int(46 * scale), cx - int(34 * scale), cy + int(28 * scale)), fill=COLORS["ink"], width=max(4, int(8 * scale)))
    draw.line((cx + int(32 * scale), cy - int(48 * scale), cx + int(48 * scale), cy - int(32 * scale)), fill=COLORS["red"], width=max(5, int(10 * scale)))
    draw.line((cx - int(50 * scale), cy + int(50 * scale), cx - int(62 * scale), cy + int(62 * scale)), fill=COLORS["ink"], width=max(4, int(7 * scale)))


def draw_brain(draw, cx, cy, scale=1.0):
    r = int(44 * scale)
    draw.ellipse((cx - r - 28, cy - r, cx + 8, cy + r), fill=COLORS["pink"], outline=COLORS["ink"], width=max(4, int(6 * scale)))
    draw.ellipse((cx - 8, cy - r, cx + r + 28, cy + r), fill=COLORS["pink"], outline=COLORS["ink"], width=max(4, int(6 * scale)))
    draw.line((cx, cy - r - 4, cx, cy + r + 8), fill=COLORS["ink"], width=max(3, int(5 * scale)))
    draw.line((cx - 35, cy - 8, cx - 12, cy - 18, cx - 30, cy - 34), fill=COLORS["ink"], width=max(3, int(5 * scale)))
    draw.line((cx + 35, cy + 8, cx + 12, cy + 18, cx + 30, cy + 34), fill=COLORS["ink"], width=max(3, int(5 * scale)))
    draw.ellipse((cx - 18, cy - 90, cx + 18, cy - 54), fill=COLORS["yellow"], outline=COLORS["ink"], width=max(3, int(5 * scale)))
    draw.line((cx - 22, cy - 53, cx + 22, cy - 53), fill=COLORS["ink"], width=max(3, int(5 * scale)))


def draw_code(draw, cx, cy, scale=1.0):
    w, h = int(150 * scale), int(100 * scale)
    draw.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), int(10 * scale), fill="#273443", outline=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.line((cx - int(30 * scale), cy, cx - int(4 * scale), cy - int(24 * scale)), fill=COLORS["white"], width=max(4, int(8 * scale)))
    draw.line((cx - int(30 * scale), cy, cx - int(4 * scale), cy + int(24 * scale)), fill=COLORS["white"], width=max(4, int(8 * scale)))
    draw.line((cx + int(30 * scale), cy, cx + int(4 * scale), cy - int(24 * scale)), fill=COLORS["red"], width=max(4, int(8 * scale)))
    draw.line((cx + int(30 * scale), cy, cx + int(4 * scale), cy + int(24 * scale)), fill=COLORS["red"], width=max(4, int(8 * scale)))
    draw.line((cx - w // 2 - 18, cy + h // 2 + 14, cx + w // 2 + 18, cy + h // 2 + 14), fill=COLORS["ink"], width=max(8, int(18 * scale)))


def draw_coins(draw, cx, cy, scale=1.0):
    for dx, dy in ((-28, 22), (28, -2), (0, -36)):
        w, h = int(68 * scale), int(35 * scale)
        x, y = cx + int(dx * scale), cy + int(dy * scale)
        draw.ellipse((x - w // 2, y - h // 2, x + w // 2, y + h // 2), fill=COLORS["yellow"], outline=COLORS["ink"], width=max(3, int(5 * scale)))
        draw.line((x - w // 2, y, x - w // 2, y + int(20 * scale)), fill=COLORS["ink"], width=max(3, int(5 * scale)))
        draw.line((x + w // 2, y, x + w // 2, y + int(20 * scale)), fill=COLORS["ink"], width=max(3, int(5 * scale)))


def draw_clock(draw, cx, cy, scale=1.0):
    r = int(55 * scale)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=COLORS["white"], outline=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.line((cx, cy, cx, cy - int(30 * scale)), fill=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.line((cx, cy, cx + int(24 * scale), cy + int(16 * scale)), fill=COLORS["ink"], width=max(4, int(7 * scale)))


def draw_target(draw, cx, cy, scale=1.0):
    for r, fill in ((60, COLORS["blue"]), (42, COLORS["white"]), (22, COLORS["red"])):
        rr = int(r * scale)
        draw.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=fill, outline=COLORS["ink"], width=max(3, int(6 * scale)))
    draw.line((cx + int(46 * scale), cy - int(46 * scale), cx + int(88 * scale), cy - int(88 * scale)), fill=COLORS["ink"], width=max(4, int(7 * scale)))


def draw_chip(draw, cx, cy, scale=1.0):
    w = int(104 * scale)
    draw.rounded_rectangle((cx - w, cy - w, cx + w, cy + w), int(22 * scale), fill=COLORS["white"], outline=COLORS["ink"], width=max(5, int(8 * scale)))
    draw.rounded_rectangle((cx - int(62 * scale), cy - int(62 * scale), cx + int(62 * scale), cy + int(62 * scale)), int(14 * scale), fill=COLORS["blue"], outline=COLORS["ink"], width=max(4, int(6 * scale)))
    draw.text(
        (cx, cy),
        "AI",
        font=f(FONT_HAND_BOLD, int(48 * scale)),
        fill=COLORS["ink"],
        anchor="mm",
        stroke_width=max(1, int(2 * scale)),
        stroke_fill=COLORS["ink"],
    )
    for offset in (-58, 0, 58):
        draw.line((cx - w - 28, cy + offset, cx - w, cy + offset), fill=COLORS["ink"], width=max(4, int(8 * scale)))
        draw.line((cx + w, cy + offset, cx + w + 28, cy + offset), fill=COLORS["ink"], width=max(4, int(8 * scale)))


def draw_provider(draw, cx, cy, scale=1.0):
    draw.ellipse((cx - 95, cy - 65, cx + 5, cy + 25), fill=COLORS["white"], outline=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.ellipse((cx - 20, cy - 90, cx + 75, cy + 25), fill=COLORS["white"], outline=COLORS["ink"], width=max(4, int(7 * scale)))
    for row in range(3):
        y = cy + int(25 * scale + row * 34 * scale)
        draw.rounded_rectangle((cx - 75, y, cx + 75, y + int(26 * scale)), int(7 * scale), fill="#D7DEE6", outline=COLORS["ink"], width=max(3, int(5 * scale)))
        draw.ellipse((cx + 48, y + int(6 * scale), cx + 58, y + int(16 * scale)), fill=COLORS["yellow"], outline=COLORS["ink"], width=2)


def draw_toolbox(draw, cx, cy, scale=1.0):
    draw.rounded_rectangle((cx - 80, cy - 30, cx + 80, cy + 70), int(14 * scale), fill=COLORS["red"], outline=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.line((cx - 78, cy - 5, cx + 78, cy - 5), fill=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.rounded_rectangle((cx - 34, cy - 60, cx + 34, cy - 28), int(8 * scale), outline=COLORS["ink"], width=max(4, int(7 * scale)))
    draw.line((cx + 68, cy - 8, cx + 128, cy - 70), fill=COLORS["ink"], width=max(4, int(7 * scale)))
    for dx, dy, fill in ((128, -70, COLORS["blue"]), (156, -8, COLORS["yellow"]), (128, 50, COLORS["mint"])):
        draw.ellipse((cx + dx - 15, cy + dy - 15, cx + dx + 15, cy + dy + 15), fill=fill, outline=COLORS["ink"], width=max(3, int(5 * scale)))


def draw_shield(draw, cx, cy, scale=1.0):
    points = [(cx, cy - 78), (cx + 70, cy - 48), (cx + 52, cy + 48), (cx, cy + 82), (cx - 52, cy + 48), (cx - 70, cy - 48)]
    draw.polygon(points, fill=COLORS["mint"], outline=COLORS["ink"])
    draw.rounded_rectangle((cx - 24, cy - 5, cx + 24, cy + 42), 8, fill=COLORS["white"], outline=COLORS["ink"], width=max(3, int(5 * scale)))
    draw.arc((cx - 20, cy - 30, cx + 20, cy + 15), 180, 360, fill=COLORS["ink"], width=max(3, int(5 * scale)))


def draw_icon(draw, kind, cx, cy, scale=1.0):
    if kind == "document" or kind == "context":
        draw_document(draw, cx, cy, scale)
    elif kind == "search":
        draw_search(draw, cx, cy, scale)
    elif kind == "answer":
        draw_document(draw, cx - 16, cy, scale * 0.9)
        draw_pencil(draw, cx + 38, cy + 20, scale * 0.75)
    elif kind == "brain":
        draw_brain(draw, cx, cy + 10, scale * 0.9)
    elif kind == "code":
        draw_code(draw, cx, cy, scale * 0.75)
    elif kind == "coins":
        draw_coins(draw, cx, cy, scale * 0.85)
    elif kind == "clock" or kind == "speed":
        draw_clock(draw, cx, cy, scale * 0.85)
    elif kind == "target":
        draw_target(draw, cx, cy, scale * 0.8)
    elif kind == "chip":
        draw_chip(draw, cx, cy, scale * 0.72)
    elif kind == "provider":
        draw_provider(draw, cx, cy - 30, scale * 0.65)
    elif kind == "toolbox":
        draw_toolbox(draw, cx - 20, cy, scale * 0.7)
    elif kind == "tools" or kind == "tool":
        draw_toolbox(draw, cx - 20, cy + 8, scale * 0.7)
    elif kind == "privacy":
        draw_shield(draw, cx, cy, scale * 0.85)
    elif kind == "warning" or kind == "wrong":
        triangle = int(70 * scale)
        draw.polygon([(cx, cy - triangle), (cx + triangle, cy + triangle), (cx - triangle, cy + triangle)], fill=COLORS["red"], outline=COLORS["ink"])
        draw.text(
            (cx, cy + int(15 * scale)),
            "!" if kind == "warning" else "×",
            font=f(FONT_HAND_BOLD, max(24, int(58 * scale))),
            fill=COLORS["ink"],
            anchor="mm",
            stroke_width=max(1, int(2 * scale)),
            stroke_fill=COLORS["ink"],
        )
    elif kind == "chunks":
        draw_document(draw, cx - 28, cy + 10, scale * 0.72)
        draw_document(draw, cx + 22, cy - 6, scale * 0.72)
    elif kind == "rules":
        draw_document(draw, cx, cy, scale * 0.9)
        draw.line((cx + 45, cy - 45, cx + 72, cy - 18), fill=COLORS["green"], width=12)
        draw.line((cx + 72, cy - 18, cx + 110, cy - 68), fill=COLORS["green"], width=12)
    elif kind == "person":
        draw.ellipse((cx - 26, cy - 58, cx + 26, cy - 6), fill=COLORS["pink"], outline=COLORS["ink"], width=6)
        draw.arc((cx - 60, cy - 5, cx + 60, cy + 96), 180, 360, fill=COLORS["ink"], width=8)
    else:
        draw_target(draw, cx, cy, scale * 0.8)


def draw_card(draw, x, y, w, h, fill, label, icon_kind, icon_scale=1.0, label_band=False):
    draw.rounded_rectangle((x, y, x + w, y + h), 34, fill=fill)
    draw_rays(draw, x + w // 2, y + int(h * 0.42), COLORS["ink"], count=8, radius=int(min(w, h) * 0.31))
    draw_icon(draw, icon_kind, x + w // 2, y + int(h * 0.40), icon_scale)
    label_font = f(FONT_HAND_BOLD, 30 if len(label) < 12 else 26)
    if label_band:
        # Ref Image places each handwritten label on a second brush pass,
        # instead of putting UI-like text inside the icon card.
        brush_rect(draw, (x + 8, y + h - 8, x + w - 8, y + h + 64), fill, 24)
        draw_centered(draw, label, x + w // 2, y + h + 4, label_font, COLORS["ink"], w - 24, gap=0)
    else:
        draw_centered(draw, label, x + w // 2, y + h - 54, label_font, COLORS["ink"], w - 24, gap=0)


def draw_arrow(draw, x1, y1, x2, y2):
    draw.line((x1, y1, x2, y2), fill=COLORS["ink"], width=7)
    draw.polygon([(x2, y2), (x2 - 20, y2 - 14), (x2 - 14, y2 + 14)], fill=COLORS["ink"])


def draw_banner(draw, text, y, height=94):
    box = (84, y, W - 84, y + height)
    brush_rect(draw, box, COLORS["pink"], 32)
    draw_centered(draw, text, W // 2, y + height // 2, f(FONT_HAND, 37), COLORS["ink"], W - 150, gap=0)


def draw_cta(draw, text, box):
    brush_rect(draw, box, COLORS["navy"], 38)
    font = f(FONT_HAND, 52)
    lines = wrap_text(draw, text, font, box[2] - box[0] - 56)
    line_height = font.size + 5
    text_y = box[1] + max(32, (box[3] - box[1] - len(lines) * line_height) // 2)
    draw_centered(draw, text, (box[0] + box[2]) // 2, text_y, font, COLORS["white"], box[2] - box[0] - 56, gap=5)
    underline_y = min(box[3] - 42, text_y + len(lines) * line_height + 8)
    draw.line((box[0] + 64, underline_y, box[2] - 64, underline_y), fill=COLORS["yellow"], width=10)


def mascot(im, box):
    if not MASCOT_PATH.exists():
        return
    bird = Image.open(MASCOT_PATH).convert("RGBA")
    target_w, target_h = box[2] - box[0], box[3] - box[1]
    bird.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    x = box[0] + (target_w - bird.width) // 2
    y = box[1] + target_h - bird.height
    im.alpha_composite(bird, (x, y))


def draw_bottom(draw, im, topic, slide_no, banner_y, cta_y=None):
    mascot(im, (75, banner_y + 12, 475, 1315))
    cta_y = cta_y or banner_y + 120
    draw_cta(draw, topic.get("ctas", ["Save this."] * 5)[slide_no - 1], (520, cta_y, 1000, min(1305, cta_y + 245)))


def topic_visuals(topic, topic_key, slide_no):
    supplied = topic.get("visuals") or []
    if len(supplied) >= slide_no and len(supplied[slide_no - 1]) >= 4:
        return supplied[slide_no - 1][:4]
    return VISUAL_LABELS.get(topic_key, VISUAL_LABELS["rag"])[slide_no][:4]


def draw_ref_card(draw, x, y, w, h, fill, label, icon_kind, label_below=True, show_label=True):
    draw.rounded_rectangle((x, y, x + w, y + h), 34, fill=fill)
    draw_rays(draw, x + w // 2, y + int(h * 0.43), COLORS["ink"], count=7, radius=int(min(w, h) * 0.29))
    draw_icon(draw, icon_kind, x + w // 2, y + int(h * 0.42), 0.72)
    label_font = f(FONT_HAND_BOLD, 26 if len(str(label)) <= 12 else 22)
    if not show_label:
        return
    if label_below:
        draw_centered(draw, str(label).upper(), x + w // 2, y + h + 10, label_font, COLORS["ink"], w + 20, gap=0)
    else:
        draw_centered(draw, str(label).upper(), x + w // 2, y + h - 46, label_font, COLORS["ink"], w - 18, gap=0)


def draw_ref_row(draw, items, y, card_h=205):
    w, gap, start = 210, 36, 66
    for index, (label, icon) in enumerate(items[:4]):
        x = start + index * (w + gap)
        draw_ref_card(draw, x, y, w, card_h, COLORS[PASTELS[index]], label, icon)
        if index < 3:
            draw_arrow(draw, x + w + 6, y + card_h // 2, x + w + gap - 8, y + card_h // 2)


def draw_ref_grid(draw, items, x=560, y=650):
    w, h, gap_x, gap_y = 205, 174, 34, 48
    for index, (label, icon) in enumerate(items[:4]):
        xx = x + (index % 2) * (w + gap_x)
        yy = y + (index // 2) * (h + gap_y)
        draw_ref_card(
            draw,
            xx,
            yy,
            w,
            h,
            COLORS[PASTELS[index]],
            label,
            icon,
            label_below=False,
            show_label=False,
        )


def draw_speech_bubble(draw, text, box, outline=COLORS["ink"], fill="#FFFDFC"):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, 48, fill=fill, outline=outline, width=5)
    tail = [(x1 + 84, y2 - 4), (x1 + 48, y2 + 50), (x1 + 142, y2 - 14)]
    draw.polygon(tail, fill=fill, outline=outline)
    draw_centered(draw, text, (x1 + x2) // 2, y1 + 46, f(FONT_HAND, 35), COLORS["ink"], x2 - x1 - 70, gap=5)


def draw_swipe(draw, text="SWIPE →", x=760, y=1185):
    font = f(FONT_HAND_BOLD, 42)
    width = draw.textbbox((0, 0), text, font=font)[2]
    brush_rect(draw, (x - 24, y - 18, x + width + 30, y + 58), COLORS["yellow"], 30)
    draw.text((x, y), text, font=font, fill=COLORS["ink"], stroke_width=1, stroke_fill=COLORS["ink"])


def draw_note(draw, text, x, y, w=430, color="pink"):
    font = f(FONT_HAND, 39)
    lines = wrap_text(draw, text, font, w - 56)
    height = max(112, len(lines) * 47 + 42)
    brush_rect(draw, (x, y, x + w, y + height), COLORS[color], 44)
    draw_centered(draw, text, x + w // 2, y + 25, font, COLORS["ink"], w - 56, gap=5)
    draw.line((x + 70, y + height + 18, x + w - 60, y + height + 3), fill=COLORS["yellow"], width=7)


def draw_final_checklist(draw, items, x=720, y=440):
    draw.polygon([(x, y), (x + 286, y + 18), (x + 270, y + 268), (x - 18, y + 246)], fill="#FFFDF8", outline=COLORS["ink"])
    for index, (label, _) in enumerate(items[:4]):
        yy = y + 48 + index * 48
        draw.text((x + 30, yy), str(label).title(), font=f(FONT_HAND, 30), fill=COLORS["ink"])
        draw.ellipse((x + 218, yy - 2, x + 252, yy + 32), fill=COLORS["mint"])
        draw.line((x + 226, yy + 14, x + 235, yy + 24), fill=COLORS["ink"], width=4)
        draw.line((x + 235, yy + 24, x + 246, yy + 7), fill=COLORS["ink"], width=4)


def draw_four_cards(draw, topic_key, slide_no, y, h=265, label_band=False):
    items = VISUAL_LABELS.get(topic_key, VISUAL_LABELS["rag"])[slide_no]
    w, gap, start = 228, 24, 30
    for i, (label, icon) in enumerate(items[:4]):
        x = start + i * (w + gap)
        draw_card(draw, x, y, w, h, COLORS[PASTELS[i]], label, icon, icon_scale=0.86, label_band=label_band)
        if i < 3:
            draw_arrow(draw, x + w + 3, y + h // 2, x + w + gap - 6, y + h // 2)


def draw_two_by_two(draw, topic_key, slide_no, y, card_h=235):
    items = VISUAL_LABELS.get(topic_key, VISUAL_LABELS["rag"])[slide_no]
    w, gap_x, gap_y = 430, 32, 20
    xs, ys = (75, 575), (y, y + card_h + gap_y)
    for i, (label, icon) in enumerate(items[:4]):
        x, yy = xs[i % 2], ys[i // 2]
        draw_card(draw, x, yy, w, card_h, COLORS[PASTELS[i]], label, icon, icon_scale=0.92)


def draw_checklist(draw, topic_key, y):
    items = VISUAL_LABELS.get(topic_key, VISUAL_LABELS["llm"])[4][:4]
    outer = (76, y - 20, 1004, y + 520)
    draw.rounded_rectangle(outer, 32, fill=COLORS["paper"], outline=COLORS["grey"], width=5)
    fills = ("purple", "mint", "blue", "orange")
    for i, (label, icon) in enumerate(items):
        yy = y + i * 122
        draw.rounded_rectangle((100, yy, 980, yy + 104), 24, fill=COLORS[fills[i]])
        draw.ellipse((126, yy + 19, 198, yy + 91), fill=COLORS[fills[i]], outline=COLORS["ink"], width=4)
        draw.text(
            (162, yy + 55),
            str(i + 1),
            font=f(FONT_HAND_BOLD, 44),
            fill=COLORS["ink"],
            anchor="mm",
            stroke_width=2,
            stroke_fill=COLORS["ink"],
        )
        draw_icon(draw, icon, 285, yy + 52, 0.46)
        draw.text(
            (490, yy + 55),
            label,
            font=f(FONT_HAND_BOLD, 39),
            fill=COLORS["ink"],
            anchor="mm",
            stroke_width=2,
            stroke_fill=COLORS["ink"],
        )
        draw.ellipse((875, yy + 16, 951, yy + 92), fill=COLORS["green"])
        draw.line((895, yy + 53, 918, yy + 74), fill=COLORS["white"], width=9)
        draw.line((918, yy + 74, 938, yy + 34), fill=COLORS["white"], width=9)


def render_slide(slide_no, total, topic, out_path):
    topic_key = topic.get("topic_key", "rag")
    fallback = TOPICS.get(topic_key, TOPICS["rag"])
    slides = topic.get("slides") or fallback["slides"]
    slide = slides[slide_no - 1]
    if isinstance(slide, dict):
        label, title, body = slide.get("series", "AI, SIMPLY"), str(slide.get("title", "")), str(slide.get("body", ""))
    else:
        label, title, body = slide
    highlight = (topic.get("highlights") or fallback.get("highlights", [None] * 5))[slide_no - 1]
    banner = (topic.get("banners") or fallback.get("banners", [""] * 5))[slide_no - 1]
    items = topic_visuals(topic, topic_key, slide_no)
    im = paper_canvas()
    draw = ImageDraw.Draw(im)
    draw_header(draw, str(label).upper()[:28])
    title_bottom = draw_title(draw, title, highlight, y=112)
    body_bottom = draw_centered(
        draw,
        body,
        W // 2,
        title_bottom + 16,
        f(FONT_HAND, 36),
        COLORS["ink"],
        W - 120,
        gap=4,
    )

    if slide_no == 1:
        # Ref Image cover: one giant hook, large mascot, 2×2 doodle grid,
        # and a clear swipe cue. No dashboard header or repeated black CTA.
        lower_y = max(625, body_bottom + 30)
        mascot(im, (24, lower_y - 16, 555, 1326))
        draw_ref_grid(draw, items, x=570, y=lower_y)
        draw.line((515, lower_y + 160, 568, lower_y + 104), fill=COLORS["ink"], width=6)
        draw.line((515, lower_y + 160, 560, lower_y + 150), fill=COLORS["ink"], width=6)
        draw_swipe(draw, x=760, y=1230)
    elif slide_no == 2:
        row_y = max(565, body_bottom + 44)
        draw_ref_row(draw, items, row_y)
        draw_note(draw, banner, 62, 1010, w=470, color="pink")
        mascot(im, (555, 880, 1055, 1328))
    elif slide_no == 3:
        row_y = max(560, body_bottom + 42)
        draw_ref_row(draw, items, row_y)
        mascot(im, (42, 880, 520, 1328))
        draw_speech_bubble(draw, banner, (555, 965, 1015, 1165), outline=COLORS["ink"])
    elif slide_no == 4:
        row_y = max(565, body_bottom + 42)
        draw_ref_row(draw, items, row_y)
        draw_note(draw, banner, 62, 1010, w=470, color="pink")
        mascot(im, (565, 875, 1055, 1328))
    else:
        draw_final_checklist(draw, items, x=735, y=max(430, body_bottom + 34))
        final_cta = str(topic.get("cta") or "Save this before your next post.")
        draw_cta(draw, final_cta, (42, 640, 705, 1010))
        draw.line((110, 1030, 520, 1024), fill=COLORS["pink"], width=9)
        mascot(im, (635, 690, 1060, 1330))
        draw_note(draw, banner, 72, 1090, w=520, color="pink")

    # Export at the same dimensions as the supplied Ref Image files. The
    # single final resize keeps the layout deterministic and avoids different
    # line wrapping between local and GitHub Actions environments.
    exported = im.convert("RGB").resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)
    exported.save(out_path, format="PNG", optimize=True)
