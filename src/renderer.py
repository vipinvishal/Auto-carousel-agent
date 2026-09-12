"""Generate and optionally email a five-slide AI explainer package.

The renderer uses the locked, approved hand-drawn explainer system so text
stays sharp while every daily post keeps the same recognizable visual identity.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "out"
W, H = 1080, 1350
M = 74

FONT_DIR = ROOT / "assets/fonts"
FONT_HAND = str(FONT_DIR / "PatrickHand-Regular.ttf")
FONT_HAND_BOLD = str(FONT_DIR / "Fredoka-Bold.ttf")
FONT_BODY = str(FONT_DIR / "NunitoSans-Regular.ttf")
FONT_BODY_BOLD = str(FONT_DIR / "NunitoSans-Bold.ttf")
MASCOT_PATH = ROOT / "assets/approved/blue-bird-mascot.png"
APPROVED_REFERENCE_DIR = ROOT / "assets/approved/reference-carousel"
VISUAL_TEMPLATE = "approved-reference-carousel-v1"

COLORS = {
    "paper": "#F7F4EF",
    "ink": "#141721",
    "yellow": "#FFD928",
    "pink": "#F58CA4",
    "purple": "#B99AEF",
    "mint": "#9FE0BB",
    "blue": "#76BDEB",
    "orange": "#F6B072",
    "grey": "#CBD1D8",
    "navy": "#101322",
}


TOPICS = {
    "rag": {
        "series": "AI, SIMPLY",
        "hook": "Your AI answer can be wrong before it even starts.",
        "post": [
            "Your AI answer can be wrong before it even starts.",
            "Bad context -> bad chunks -> weak search -> wrong answers.",
            "Fix what AI reads first. Save this. #AI #RAG #MachineLearning",
        ],
        "slides": [
            ("SCROLL-STOPPING TRUTH", "Your AI answer can be wrong\nbefore it even starts.", "Check the context first."),
            ("THE SIMPLE IDEA", "AI can only answer\nfrom what it sees.", "RAG does two jobs: find useful information, then use it to answer."),
            ("WHERE IT BREAKS", "The model is only as good\nas the chunk it receives.", "Too long. Cut mid-sentence. No headings. Outdated.\n\nSearch cannot rescue missing meaning."),
            ("DO THIS FIRST", "Before you change the model,\ninspect one retrieved chunk.", "Complete. Current. Relevant.\n\nIt takes 10 seconds and often reveals the real bug."),
            ("SAVE THIS WORKFLOW", "Fix the context\nbefore you fine-tune.", "Clean source -> meaningful chunks -> relevant retrieval -> better answers.\n\nBetter context beats a bigger model."),
        ],
        "source": "Source: RAG quality principles; concept simplified for education",
        "accent": "blue",
    },
    "prompting": {
        "series": "MODEL INPUTS",
        "hook": "A vague prompt creates a vague output.",
        "post": [
            "A vague prompt creates a vague output.",
            "Role + context + constraints reduce ambiguity for the model.",
            "What will you add first? #AI #PromptEngineering #LLMs",
        ],
        "slides": [
            ("MODEL INPUTS", "A vague prompt creates\na vague output.", "Reduce ambiguity first."),
            ("1 / THE MECHANISM", "The model cannot guess\nyour missing constraints.", "Prompting is about reducing ambiguity before generation."),
            ("2 / THE BUILDING BLOCKS", "Use four controls.", "Task. Context. Constraints. Format.\n\nEach one narrows the space of possible answers."),
            ("3 / THE EXAMPLE", "Give the model\na target.", "Weak: Write a summary.\n\nStrong: Summarize these notes in 5 bullets. Keep unknowns visible. Use plain English."),
            ("TAKEAWAY", "Specific beats clever.", "A good prompt is an interface between you and the model.\n\nTest one instruction today."),
        ],
        "source": "Source: prompt-engineering principles; concept simplified for education",
        "accent": "orange",
    },
    "llm": {
        "series": "MODEL COMPARISON",
        "hook": "There is no single best LLM—only the best fit.",
        "post": [
            "There is no single best LLM—only the best fit.",
            "Compare quality, context, tools, speed, cost, and privacy for your task.",
            "What do you optimize first? #LLM #AIModels #AIEngineering",
        ],
        "slides": [
            ("MODEL COMPARISON", "There is no single best LLM—\nonly the best fit.", "Match the model to the job."),
            ("1 / START WITH THE TASK", "A benchmark score is\nnot a workflow.", "Ask what matters: reasoning, coding, long context, tool use, latency, or cost."),
            ("2 / COMPARE THE SYSTEM", "The model is\nonly one piece.", "Model + provider + context window + tools + limits + price + data policy."),
            ("3 / NEW MODEL?", "Do not trust the\nlaunch headline.", "Run the same prompts. Track accuracy, latency, cost, and failure modes. Date the result."),
            ("TAKEAWAY", "Best model = best fit\nfor your task.", "Compare on your workload—not a leaderboard alone.\n\nSave this checklist for the next release."),
        ],
        "source": "Source: model-comparison framework; verify current specs before publishing",
        "accent": "orange",
    },
    "agents": {
        "series": "AGENT MECHANICS",
        "hook": "An AI agent is a loop—not a single prompt.",
        "post": [
            "An AI agent is a loop—not a single prompt.",
            "Plan, call a tool, inspect the result, then continue or stop.",
            "What guardrail would you add? #AIAgents #AIEngineering #LLMs",
        ],
        "slides": [
            ("AGENT MECHANICS", "An AI agent is a loop—\nnot a single prompt.", "Plan. Act. Check."),
            ("1 / THE DIFFERENCE", "A chatbot generates.\nAn agent operates.", "The agent can choose the next step, call tools, and inspect results."),
            ("2 / THE LOOP", "Reliable agents need\nstop conditions.", "Plan -> act -> observe -> continue or stop.\n\nNo boundary means no predictable behavior."),
            ("3 / THE EXAMPLE", "Give it a\nbounded task.", "Goal: classify support tickets\n\nPlan -> group intent\nAct -> call the knowledge base\nCheck -> escalate uncertain cases"),
            ("TAKEAWAY", "Tools without guardrails\ncreate risk.", "Define the goal, allowed tools, limits, and human handoff.\n\nStart with one narrow workflow."),
        ],
        "source": "Source: agent design principles; concept simplified for education",
        "accent": "purple",
    },
}

def f(path, size, index=0):
    font = ImageFont.truetype(path, size, index=index)
    # The bundled Google Fonts files are variable fonts. Select the named
    # instance explicitly so GitHub does not silently render the light master.
    instance = "Bold" if "Bold" in Path(path).name else "Regular"
    try:
        font.set_variation_by_name(instance)
    except (AttributeError, OSError):
        pass
    return font


def wrap_text(draw, text, font_obj, max_width):
    lines = []
    for paragraph in text.split("\n"):
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


def draw_text(draw, xy, text, font_obj, fill, max_width, gap=10):
    x, y = xy
    lines = wrap_text(draw, text, font_obj, max_width)
    for line in lines:
        draw.text((x, y), line, font=font_obj, fill=fill)
        y += font_obj.size + gap
    return y


def marker_highlight(draw, x, y, text, font_obj, color):
    box = draw.textbbox((x, y), text, font=font_obj)
    draw.rounded_rectangle((box[0] - 10, box[1] + 8, box[2] + 10, box[3] - 3), 14, fill=color)
    draw.text((x, y), text, font=font_obj, fill=COLORS["ink"])


def brush_rect(draw, box, fill, radius=28):
    """Approximate the reference's hand-painted rounded highlight."""
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius, fill=fill)
    # Small uneven edge strokes keep the block from reading like a UI card.
    draw.line((x1 + 14, y1 + 5, x2 - 18, y1 + 2), fill=fill, width=8)
    draw.line((x1 + 8, y2 - 4, x2 - 10, y2 + 2), fill=fill, width=7)


def mascot(im, box):
    if not MASCOT_PATH.exists():
        return
    bird = Image.open(MASCOT_PATH).convert("RGBA")
    target_w, target_h = box[2] - box[0], box[3] - box[1]
    bird.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    x = box[0] + (target_w - bird.width) // 2
    y = box[1] + target_h - bird.height
    im.alpha_composite(bird, (x, y))


def sparkles(draw, points, color=COLORS["yellow"]):
    for x, y, size in points:
        draw.line((x - size, y, x + size, y), fill=color, width=8)
        draw.line((x, y - size, x, y + size), fill=color, width=8)


def draw_approved_header(draw, topic, slide_no, total, badge=None):
    label = badge or topic["series"]
    label_font = f(FONT_HAND_BOLD, 30)
    label_box = draw.textbbox((M, 55), label, font=label_font)
    brush_rect(draw, (label_box[0] - 18, label_box[1] - 8, label_box[2] + 18, label_box[3] + 12), COLORS["yellow"], 24)
    draw.text((M, 55), label, font=label_font, fill=COLORS["ink"])
    draw.text((W - M, 63), f"{slide_no:02d}/{total:02d}", font=f(FONT_BODY_BOLD, 24), fill=COLORS["ink"], anchor="ra")


def draw_cta(draw, text, box=(560, 1000, 1000, 1240)):
    brush_rect(draw, box, COLORS["navy"], 34)
    draw_text(draw, (box[0] + 34, box[1] + 40), text, f(FONT_HAND_BOLD, 42), "#FFFFFF", box[2] - box[0] - 68, gap=8)
    draw.line((box[0] + 72, box[3] - 44, box[2] - 72, box[3] - 44), fill=COLORS["yellow"], width=10)


def doodle_arrow(draw, start, end, color=COLORS["ink"], width=5):
    draw.line((*start, *end), fill=color, width=width)
    x, y = end
    draw.polygon([(x, y), (x - 20, y - 12), (x - 12, y + 10)], fill=color)


def draw_process(draw, accent):
    labels = [("LOAD", COLORS["purple"]), ("CLEAN", COLORS["mint"]), ("CHUNK", COLORS["blue"]), ("RETRIEVE", COLORS["orange"])]
    xs = [86, 320, 554, 788]
    for i, (label, fill) in enumerate(labels):
        x = xs[i]
        draw.rounded_rectangle((x, 800, x + 180, 980), 28, fill=fill)
        draw.ellipse((x + 63, 835, x + 117, 889), outline=COLORS["ink"], width=6)
        draw.line((x + 90, 889, x + 90, 930), fill=COLORS["ink"], width=6)
        draw.text((x + 90, 1030), label, font=f(FONT_HAND_BOLD, 26), fill=COLORS["ink"], anchor="ma")
        if i < len(labels) - 1:
            doodle_arrow(draw, (x + 190, 890), (xs[i + 1] - 12, 890), color=accent, width=5)


def draw_rag_flow(draw, accent):
    """Two-step RAG visual matching the approved reference composition."""
    cards = ((92, 700, COLORS["purple"], "FIND CONTEXT"), (598, 700, COLORS["mint"], "WRITE ANSWER"))
    for x, y, fill, label in cards:
        draw.rounded_rectangle((x, y, x + 390, y + 220), 34, fill=fill)
        draw.rounded_rectangle((x + 92, y + 48, x + 226, y + 172), 12, fill="#FFFFFF", outline=COLORS["ink"], width=6)
        for line_y, length in ((y + 84, 92), (y + 116, 112), (y + 148, 76)):
            draw.line((x + 116, line_y, x + 116 + length, line_y), fill=COLORS["ink"], width=6)
        if label == "FIND CONTEXT":
            draw.ellipse((x + 206, y + 86, x + 306, y + 186), fill=COLORS["blue"], outline=COLORS["ink"], width=6)
            draw.line((x + 282, y + 162, x + 340, y + 210), fill=COLORS["ink"], width=12)
        else:
            draw.line((x + 246, y + 70, x + 246, y + 170), fill=COLORS["ink"], width=8)
            draw.line((x + 220, y + 120, x + 272, y + 120), fill=COLORS["ink"], width=8)
        draw.text((x + 195, y + 250), label, font=f(FONT_HAND_BOLD, 28), fill=COLORS["ink"], anchor="ma")
    doodle_arrow(draw, (500, 810), (578, 810), color=accent, width=6)


def draw_loop(draw, accent):
    nodes = [(160, 800, "PLAN"), (430, 700, "ACT"), (700, 800, "CHECK")]
    for x, y, label in nodes:
        draw.ellipse((x, y, x + 190, y + 190), fill=COLORS["paper"], outline=accent, width=7)
        draw.text((x + 95, y + 95), label, font=f(FONT_HAND_BOLD, 30), fill=COLORS["ink"], anchor="mm")
    draw.arc((215, 700, 610, 1080), 205, 340, fill=COLORS["pink"], width=7)
    draw.arc((485, 700, 880, 1080), 200, 335, fill=COLORS["pink"], width=7)


def draw_cards(draw, accent, labels=None, base_y=800):
    labels = labels or ["ROLE", "CONTEXT", "RULES", "FORMAT"]
    for i, label in enumerate(labels):
        x = 120 + (i % 2) * 460
        y = base_y + (i // 2) * 150
        draw.rounded_rectangle((x, y, x + 330, y + 100), 22, fill=COLORS["paper"], outline=accent, width=5)
        draw.ellipse((x + 26, y + 26, x + 74, y + 74), fill=accent)
        draw.text((x + 104, y + 50), label, font=f(FONT_HAND_BOLD, 30), fill=COLORS["ink"], anchor="lm")


def render_slide(slide_no, total, topic, out_path):
    series, title, body = topic["slides"][slide_no - 1]
    accent = COLORS[topic["accent"]]
    im = Image.new("RGBA", (W, H), COLORS["paper"])
    draw = ImageDraw.Draw(im)
    title_font = f(FONT_HAND_BOLD, 72)
    body_font = f(FONT_HAND, 40)
    small = f(FONT_BODY_BOLD, 24)
    draw_approved_header(draw, topic, slide_no, total, badge="AI, SIMPLY" if slide_no == 1 else series)
    sparkles(draw, [(90, 145, 18), (970, 145, 18), (970, 1290, 16)], COLORS["yellow"])
    draw_text(draw, (M, 205), title, title_font, COLORS["ink"], W - 2 * M, gap=4)
    draw.line((M + 40, 475, W - M - 70, 475), fill=COLORS["yellow"], width=10)

    if slide_no == 1:
        draw.text((M, 535), body, font=f(FONT_HAND_BOLD, 36), fill=COLORS["pink"])
        if topic["accent"] == "orange":
            draw_cards(draw, accent, ["REASONING", "CODING", "LONG CONTEXT", "LOW COST"], base_y=700)
        elif topic["accent"] == "blue":
            draw_rag_flow(draw, accent)
        else:
            draw_loop(draw, accent)
        mascot(im, (60, 1040, 510, 1315))
        draw_cta(draw, topic.get("cta", "Match the model\nto the job."), (540, 980, 1000, 1230))
    elif slide_no == 2:
        draw_text(draw, (M, 550), body, body_font, COLORS["ink"], W - 2 * M, gap=14)
        brush_rect(draw, (M, 790, W - M, 970), COLORS["blue"], 30)
        draw_text(draw, (M + 38, 830), "Reasoning · coding · long context\nTool use · latency · cost", f(FONT_HAND_BOLD, 39), COLORS["ink"], W - 2 * M - 76, gap=12)
        mascot(im, (630, 970, 1010, 1315))
    elif slide_no == 3:
        draw_text(draw, (M, 550), body, body_font, COLORS["ink"], W - 2 * M, gap=14)
        draw_cards(draw, accent)
        mascot(im, (40, 1040, 300, 1320))
    elif slide_no == 4:
        brush_rect(draw, (M, 635, W - M, 1000), "#FFFFFF", 30)
        draw_text(draw, (M + 42, 700), body, f(FONT_HAND_BOLD, 39), COLORS["ink"], W - 2 * M - 84, gap=15)
        draw.text((W - M, 1040), "RUN THE SAME TASK ON EVERY MODEL.", font=small, fill=COLORS["pink"], anchor="ra")
        mascot(im, (80, 1030, 410, 1320))
        draw_cta(draw, topic.get("measure_cta", "Measure the\ntrade-offs."), (560, 1080, 1000, 1300))
    else:
        brush_rect(draw, (M, 610, W - M, 905), COLORS["pink"], 34)
        draw_text(draw, (M + 40, 675), body, f(FONT_HAND_BOLD, 40), COLORS["ink"], W - 2 * M - 80, gap=14)
        mascot(im, (70, 875, 500, 1315))
        draw_cta(draw, topic.get("save_cta", "Save this checklist\nfor the next release."), (510, 970, 1000, 1260))
        draw.text((W - M, 1310), topic["source"], font=f(FONT_BODY, 17), fill=COLORS["grey"], anchor="ra")

    im.convert("RGB").save(out_path, format="PNG", optimize=True)
