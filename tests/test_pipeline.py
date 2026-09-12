import json
import sys
import unittest
from datetime import date
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import automation  # noqa: E402
import content_engine  # noqa: E402
import research  # noqa: E402
from renderer import (  # noqa: E402
    APPROVED_REFERENCE_DIR,
    FONT_BODY,
    FONT_BODY_BOLD,
    FONT_HAND,
    FONT_HAND_BOLD,
    H,
    MASCOT_PATH,
    VISUAL_TEMPLATE,
    W,
)


class PipelineTests(unittest.TestCase):
    def test_schedule_is_three_ist_slots(self):
        self.assertEqual(automation.SLOTS, ("0900", "1200", "1700"))

    def test_research_rejects_bare_ai_mentions(self):
        self.assertFalse(research._is_technical_ai("Show HN: Hacker News, without AI"))
        self.assertTrue(research._is_technical_ai("New AI model adds structured tool calling"))

    def test_approved_fallback_builds_five_synchronized_pngs(self):
        folder, package, slides = automation.build_package(
            date(2099, 1, 1), "0900", "rag", force_fallback=True
        )
        errors = automation.validate(folder, package, slides)
        self.assertEqual(errors, [])
        self.assertEqual(len(slides), 5)
        self.assertEqual(len(package["post_lines"]), 3)
        self.assertIn("#", package["post_lines"][2])
        self.assertFalse(package["manual_review_required"])
        self.assertEqual(package["visual_template"], VISUAL_TEMPLATE)
        with Image.open(slides[0]) as image:
            self.assertEqual(image.size, (W, H))
            self.assertEqual(image.format, "PNG")
        metadata = json.loads((folder / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["slides"], [path.name for path in slides])

    def test_fallback_is_compatible_with_renderer(self):
        topic = content_engine.generate_content(None, "llm", force_fallback=True)
        self.assertEqual(len(topic["post_lines"]), 3)
        self.assertEqual(len(topic["slides"]), 5)
        self.assertIn("#", topic["post_lines"][2])
        self.assertTrue(topic["cta"])

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

    def test_approved_assets_and_bundled_fonts_exist(self):
        for font_path in (FONT_HAND, FONT_HAND_BOLD, FONT_BODY, FONT_BODY_BOLD):
            self.assertTrue(Path(font_path).exists(), font_path)
        self.assertTrue(MASCOT_PATH.exists())
        self.assertEqual(len(list(APPROVED_REFERENCE_DIR.glob("slide-*.png"))), 5)


if __name__ == "__main__":
    unittest.main()
