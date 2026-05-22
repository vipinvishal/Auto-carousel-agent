"""
export.py — Render each HTML slide to a 1080 × 1350 px PNG via Playwright.

Viewport strategy:
  - Viewport : 420 × 525 px  (native CSS pixels)
  - DPR      : 1080 / 420 ≈ 2.5714 (device_scale_factor)
  - Output   : 420 × 2.5714 ≈ 1080 px wide, 525 × 2.5714 ≈ 1350 px tall
  - We wait 3 s for Google Fonts to finish loading before screenshotting.
  - A PIL resize step guarantees the output is exactly 1080 × 1350.
"""

import logging
import os

from PIL import Image
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

_VIEWPORT_W = 420
_VIEWPORT_H = 525
_DPR        = 1080 / 420          # ≈ 2.5714
_TARGET_W   = 1080
_TARGET_H   = 1350
_FONT_WAIT  = 3_000               # ms — wait for Google Fonts CDN


def export_slides(html_paths: list[str], output_dir: str) -> list[str]:
    """
    Screenshot each HTML file and save as a PNG at exactly 1080 × 1350 px.

    Args:
        html_paths : ordered list of absolute paths to slide HTML files
        output_dir : directory where PNGs will be written

    Returns:
        Ordered list of absolute PNG paths [slide_1.png … slide_8.png]

    Raises:
        RuntimeError: if Playwright fails to launch or screenshot a slide
    """
    os.makedirs(output_dir, exist_ok=True)
    png_paths: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            # headless=True is the default; args below disable GPU for server envs
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-gpu", "--disable-dev-shm-usage"],
        )
        try:
            for i, html_path in enumerate(html_paths, start=1):
                page = browser.new_page(
                    viewport={"width": _VIEWPORT_W, "height": _VIEWPORT_H},
                    device_scale_factor=_DPR,
                )
                try:
                    file_url = f"file://{html_path}"
                    page.goto(file_url, wait_until="networkidle")

                    # Wait for Google Fonts to load (max 3 s, then proceed anyway)
                    try:
                        page.wait_for_timeout(_FONT_WAIT)
                    except Exception:
                        pass

                    # Hide any Instagram-carousel chrome classes if present
                    page.evaluate(
                        """() => {
                            ['.ig-header','.ig-dots','.ig-actions','.ig-caption']
                            .forEach(sel => document.querySelectorAll(sel)
                            .forEach(el => { el.style.display = 'none'; }));
                        }"""
                    )

                    png_path = os.path.join(output_dir, f"slide_{i}.png")
                    page.screenshot(
                        path=png_path,
                        clip={
                            "x": 0, "y": 0,
                            "width": _VIEWPORT_W, "height": _VIEWPORT_H,
                        },
                    )

                    # Guarantee exact pixel dimensions with PIL
                    _ensure_size(png_path)

                    png_paths.append(os.path.abspath(png_path))
                    logger.info("Exported slide %d → %s", i, png_path)
                finally:
                    page.close()
        finally:
            browser.close()

    return png_paths


def _ensure_size(png_path: str) -> None:
    """Resize the PNG to exactly 1080 × 1350 if floating-point DPR caused a mismatch."""
    with Image.open(png_path) as img:
        if img.size != (_TARGET_W, _TARGET_H):
            logger.debug(
                "Resizing %s from %s to (%d, %d)",
                png_path, img.size, _TARGET_W, _TARGET_H,
            )
            img = img.resize((_TARGET_W, _TARGET_H), Image.LANCZOS)
            img.save(png_path, "PNG")
