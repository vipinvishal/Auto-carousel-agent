import json
import os
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import automation  # noqa: E402
import content_engine  # noqa: E402
import image_engine  # noqa: E402
import research  # noqa: E402
from renderer import (  # noqa: E402
    APPROVED_REFERENCE_DIR,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HAND,
    FONT_HAND_BOLD,
    FONT_MARKER,
    MASCOT_PATH,
    OUTPUT_SIZE,
    REFERENCE_STYLE_DIR,
    TEMPLATE_SPEC,
    TEMPLATE_SPEC_PATH,
    VISUAL_TEMPLATE,
)


class PipelineTests(unittest.TestCase):
    def test_schedule_is_three_ist_slots(self):
        self.assertEqual(automation.SLOTS, ("0900", "1200", "1700"))

    def test_ref_image_template_is_the_only_dynamic_visual_contract(self):
        self.assertTrue(TEMPLATE_SPEC_PATH.exists())
        self.assertEqual(VISUAL_TEMPLATE, "ref-image-handwritten-v3-image-model")
        self.assertEqual(TEMPLATE_SPEC["name"], VISUAL_TEMPLATE)
        self.assertEqual(TEMPLATE_SPEC["source_of_truth"], "assets/approved/reference-style/")
        self.assertIn("slide 5 only", TEMPLATE_SPEC["invariants"]["cta"])
        self.assertIn("slide counter", TEMPLATE_SPEC["forbidden"])

    def test_research_rejects_bare_ai_mentions(self):
        self.assertFalse(research._is_technical_ai("Show HN: Hacker News, without AI"))
        self.assertTrue(research._is_technical_ai("New AI model adds structured tool calling"))

    @patch.object(research, "_scrape_context", return_value="A technical explanation from the selected source.")
    @patch.object(research, "_fetch_exa", return_value=[])
    @patch.object(research, "_fetch_google_news")
    @patch.object(research, "_fetch_reddit")
    @patch.object(research, "_fetch_hn")
    def test_research_selects_high_signal_story_and_keeps_evidence(self, fetch_hn, fetch_reddit, fetch_news, _fetch_exa, scrape):
        now = research.time.time()
        fetch_hn.return_value = [{
            "id": "hn:1",
            "title": "New AI model adds structured tool calling",
            "url": "https://example.com/model",
            "source": "Hacker News",
            "score": 80,
            "comments": 20,
            "created": now,
        }]
        fetch_reddit.return_value = [{
            "id": "reddit:1",
            "title": "New AI model adds structured tool calling",
            "url": "https://reddit.com/r/artificial/1",
            "source": "Reddit r/artificial",
            "score": 40,
            "comments": 12,
            "created": now,
        }]
        fetch_news.return_value = [{
            "id": "news:1",
            "title": "New AI model adds structured tool calling",
            "url": "https://blog.google/ai/model",
            "source": "Google News",
            "score": 8,
            "comments": 0,
            "created": now,
        }]
        candidate = research.choose_candidate(date(2026, 9, 13), "0900")
        self.assertEqual(candidate["title"], "New AI model adds structured tool calling")
        self.assertEqual(candidate["signal_count"], 3)
        self.assertEqual(len(candidate["signals"]), 3)
        self.assertGreater(candidate["trend_score"], 0)
        self.assertEqual(len(candidate["evidence"]), 1)
        scrape.assert_called_once()

    def test_approved_fallback_builds_five_synchronized_pngs(self):
        folder, package, slides = automation.build_package(
            date(2099, 1, 1),
            "0900",
            "rag",
            force_fallback=True,
            allow_pillow_preview=True,
        )
        errors = automation.validate(folder, package, slides)
        self.assertEqual(errors, [])
        self.assertEqual(len(slides), 5)
        self.assertEqual(len(package["post_lines"]), 3)
        self.assertIn("#", package["post_lines"][2])
        self.assertFalse(package["manual_review_required"])
        self.assertEqual(package["pipeline_steps"][0], "topic_research")
        self.assertEqual(package["pipeline_steps"][-1], "gmail_delivery")
        self.assertEqual(package["visual_template"], VISUAL_TEMPLATE)
        self.assertEqual(package["visual_template_source"], "assets/approved/reference-style/")
        with Image.open(slides[0]) as image:
            self.assertEqual(image.size, OUTPUT_SIZE)
            self.assertEqual(image.format, "PNG")
        metadata = json.loads((folder / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["slides"], [path.name for path in slides])

    @patch.object(automation, "generate_carousel")
    def test_production_uses_reference_conditioned_image_model(self, generate_carousel):
        generated = [APPROVED_REFERENCE_DIR / f"slide-{index:02d}.png" for index in range(1, 6)]
        generate_carousel.return_value = generated
        _, package, slides = automation.build_package(
            date(2099, 1, 4), "0900", "agents", force_fallback=True
        )
        generate_carousel.assert_called_once()
        self.assertEqual(slides, generated)
        self.assertEqual(package["render_mode"], "gemini-reference-conditioned")

    def test_fallback_is_compatible_with_renderer(self):
        topic = content_engine.generate_content(None, "llm", force_fallback=True)
        self.assertEqual(len(topic["post_lines"]), 3)
        self.assertEqual(len(topic["slides"]), 5)
        self.assertIn("#", topic["post_lines"][2])
        self.assertTrue(topic["cta"])

    def test_image_model_prompt_uses_exact_ref_image_language(self):
        topic = content_engine.generate_content(None, "agents", force_fallback=True)
        prompt = image_engine.build_prompt(topic, 1)
        self.assertIn("matching the reference images extremely closely", prompt)
        self.assertIn("Text (verbatim", prompt)
        self.assertIn("large expressive bird", prompt.lower())
        self.assertIn("Avoid: SaaS dashboard", prompt)

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "configured"})
    @patch.object(content_engine.requests, "post")
    def test_openrouter_generates_validated_copy(self, post):
        post.return_value.ok = True
        post.return_value.json.return_value = {
            "model": "openrouter/free",
            "choices": [{"message": {"content": '{"ok": true}'}}],
        }
        data, mode = content_engine._call_content_model("test")
        self.assertEqual(data, {"ok": True})
        self.assertEqual(mode, "openrouter-validated:openrouter/free")
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 8000)
        self.assertEqual(post.call_args.kwargs["json"]["reasoning"], {"exclude": True})

    def test_viral_rulebook_is_loaded_by_content_engine(self):
        self.assertEqual(content_engine.RULEBOOK["story_arc"], ["curiosity", "tension", "insight", "payoff"])
        self.assertIn("one idea", " ".join(content_engine.RULEBOOK["content_rules"]).lower())

    def test_llm_fallback_uses_exact_approved_reference_pngs(self):
        folder, package, slides = automation.build_package(
            date(2099, 1, 2), "1200", "llm", force_fallback=True
        )
        self.assertEqual(automation.validate(folder, package, slides), [])
        self.assertEqual(package["render_mode"], "exact-approved-reference")
        with Image.open(slides[0]) as image:
            with Image.open(APPROVED_REFERENCE_DIR / "slide-01.png") as reference:
                self.assertEqual(image.size, reference.size)
                self.assertEqual(image.tobytes(), reference.tobytes())

    def test_reference_lock_uses_exact_approved_llm_pngs(self):
        folder, package, slides = automation.build_package(
            date(2099, 1, 3), "1700", reference_lock=True
        )
        self.assertEqual(automation.validate(folder, package, slides), [])
        self.assertEqual(package["render_mode"], "exact-ref-image-reference")
        self.assertEqual(package["topic"], "reference")
        for slide, reference in zip(slides, automation.REFERENCE_SLIDES):
            self.assertEqual(slide.read_bytes(), reference.read_bytes())

    def test_approved_assets_and_bundled_fonts_exist(self):
        for font_path in (FONT_HAND, FONT_HAND_BOLD, FONT_MARKER, FONT_BODY, FONT_BODY_BOLD):
            self.assertTrue(Path(font_path).exists(), font_path)
        self.assertTrue(MASCOT_PATH.exists())
        self.assertEqual(len(list(APPROVED_REFERENCE_DIR.glob("slide-*.png"))), 5)
        self.assertEqual(len(list(REFERENCE_STYLE_DIR.glob("*.png"))), 8)


if __name__ == "__main__":
    unittest.main()
