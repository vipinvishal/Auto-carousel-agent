"""
carousel.py — Editorial Instagram carousel generator.
Design: Giant typography + grid overlay + rust/purple dual accent.
Matches premium magazine aesthetic from reference slides.
"""

import html as _html
import logging
import os

logger = logging.getLogger(__name__)

# ── Design tokens ─────────────────────────────────────────────────────────────
_RUST        = "#C4441A"
_RUST_LIGHT  = "#E8603A"
_PURPLE      = "#6C3BFF"
_PURPLE_L    = "#A78BFF"

_CREAM       = "#EDEADE"   # warm off-white
_CREAM_DARK  = "#D9D4C7"   # dividers on light
_DARK        = "#151210"   # near-black warm
_DARK2       = "#1E1A16"   # slightly lighter dark

_WHITE       = "#FFFFFF"
_BLACK       = "#111111"

_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Barlow+Condensed:wght@400;600;700;800;900"
    "&family=Barlow:wght@400;500;600"
    "&family=DM+Mono:wght@400;500"
    "&display=swap"
)

_DEFAULT_EMOJIS = ["🔥","🤖","⚡","🛠️","📈","💡","🎯","🚀"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _e(text: str) -> str:
    return _html.escape(str(text), quote=True)


def _grid_overlay(opacity: float = 0.06) -> str:
    """Subtle grid lines — the signature look from reference slides."""
    return f"""
<svg style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;"
  xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="grid" width="105" height="131.25" patternUnits="userSpaceOnUse">
      <path d="M 105 0 L 0 0 0 131.25" fill="none"
        stroke="currentColor" stroke-width="0.5" opacity="{opacity}"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#grid)" color="{'#000' }"/>
  <!-- crosshair dots at grid intersections -->
  <circle cx="105" cy="131" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="210" cy="131" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="315" cy="131" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="105" cy="262" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="210" cy="262" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="315" cy="262" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="105" cy="393" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="210" cy="393" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
  <circle cx="315" cy="393" r="2.5" fill="currentColor" opacity="{opacity * 1.8}" color="#888"/>
</svg>"""


def _top_bar(label: str, slide_num: int, total: int,
             label_color: str, counter_color: str) -> str:
    return f"""
<div style="position:absolute;top:0;left:0;right:0;padding:20px 22px 0;
  display:flex;justify-content:space-between;align-items:flex-start;">
  <span style="font-family:'Barlow Condensed',sans-serif;font-size:11px;
    font-weight:700;letter-spacing:2.5px;text-transform:uppercase;
    color:{label_color};">{_e(label)}</span>
  <span style="font-family:'Barlow Condensed',sans-serif;font-size:11px;
    font-weight:600;letter-spacing:1.5px;color:{counter_color};">
    {slide_num:02d} / {total:02d}</span>
</div>"""


def _bottom_bar(handle: str, show_swipe: bool,
                handle_color: str, swipe_color: str) -> str:
    swipe = ""
    if show_swipe:
        swipe = f"""
<div style="display:flex;align-items:center;gap:5px;">
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
    stroke="{swipe_color}" stroke-width="1.5" stroke-linecap="round"
    stroke-linejoin="round"
    style="background:rgba(128,128,128,0.15);border-radius:50%;padding:4px;">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
</div>"""
    return f"""
<div style="position:absolute;bottom:0;left:0;right:0;padding:0 22px 18px;
  display:flex;justify-content:space-between;align-items:flex-end;">
  <span style="font-family:'Barlow Condensed',sans-serif;font-size:10px;
    font-weight:600;letter-spacing:2.5px;text-transform:uppercase;
    color:{handle_color};">@{_e(handle.lstrip('@'))}</span>
  {swipe}
</div>"""


def _two_tone_title(line1: str, accent_word: str, line2: str,
                    base_color: str, accent_color: str,
                    size: str = "72px") -> str:
    """
    Editorial two-tone headline.
    line1 and line2 are in base_color, accent_word is in accent_color.
    Pass accent_word='' to skip.
    """
    parts = []
    if line1:
        parts.append(
            f'<div style="font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:{size};font-weight:900;line-height:0.92;'
            f'letter-spacing:-1px;color:{base_color};text-transform:uppercase;">'
            f'{_e(line1)}</div>'
        )
    if accent_word:
        parts.append(
            f'<div style="font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:{size};font-weight:900;line-height:0.92;'
            f'letter-spacing:-1px;color:{accent_color};text-transform:uppercase;">'
            f'{_e(accent_word)}</div>'
        )
    if line2:
        parts.append(
            f'<div style="font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:{size};font-weight:900;line-height:0.92;'
            f'letter-spacing:-1px;color:{base_color};text-transform:uppercase;">'
            f'{_e(line2)}</div>'
        )
    return "\n".join(parts)


def _accent_bar(color: str) -> str:
    return (
        f'<div style="width:48px;height:4px;background:{color};'
        f'border-radius:2px;margin:14px 0 16px;"></div>'
    )


def _body_text(text: str, color: str, size: str = "15px") -> str:
    return (
        f'<p style="font-family:\'Barlow\',sans-serif;font-size:{size};'
        f'font-weight:400;line-height:1.6;color:{color};margin:0;">'
        f'{_e(text)}</p>'
    )


def _numbered_row(num: str, title: str, desc: str,
                  num_color: str, title_color: str,
                  desc_color: str, divider_color: str) -> str:
    return f"""
<div style="display:flex;align-items:flex-start;gap:16px;
  padding:14px 0;border-bottom:1px solid {divider_color};">
  <span style="font-family:'Barlow Condensed',sans-serif;font-size:28px;
    font-weight:300;color:{num_color};min-width:36px;line-height:1;">{num}</span>
  <div>
    <p style="font-family:'Barlow',sans-serif;font-size:14px;font-weight:700;
      color:{title_color};margin:0 0 3px;">{_e(title)}</p>
    <p style="font-family:'Barlow',sans-serif;font-size:13px;font-weight:400;
      color:{desc_color};margin:0;line-height:1.5;">{_e(desc)}</p>
  </div>
</div>"""


def _strikethrough_pills(items: list[str], border_color: str,
                          text_color: str) -> str:
    pills = []
    rows  = [items[i:i+2] for i in range(0, min(len(items), 6), 2)]
    for row in rows:
        row_html = "".join(
            f'<span style="font-family:\'Barlow\',sans-serif;font-size:12px;'
            f'font-weight:500;padding:6px 14px;border:1px solid {border_color};'
            f'border-radius:100px;color:{text_color};'
            f'text-decoration:line-through;">{_e(p)}</span>'
            for p in row
        )
        pills.append(
            f'<div style="display:flex;gap:8px;margin-bottom:8px;">{row_html}</div>'
        )
    return "\n".join(pills)


def _terminal_block(lines: list[str],
                    accent: str = "#C4441A") -> str:
    """macOS-style terminal window with monospace code."""
    rows = []
    for ln in lines:
        if ln.startswith("$"):
            color = accent
        elif ln.startswith("✓") or ln.startswith("*"):
            color = "#4ADE80"
        elif ln.startswith("→"):
            color = "#A0A0A0"
        else:
            color = "#D0D0D0"
        rows.append(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:12px;'
            f'font-weight:400;color:{color};line-height:1.7;">{_e(ln)}</div>'
        )
    return f"""
<div style="background:#111;border-radius:10px;padding:14px 16px;margin:12px 0;">
  <div style="display:flex;gap:5px;margin-bottom:10px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FF5F57;"></div>
    <div style="width:10px;height:10px;border-radius:50%;background:#FEBC2E;"></div>
    <div style="width:10px;height:10px;border-radius:50%;background:#28C840;"></div>
  </div>
  {"".join(rows)}
</div>"""


def _comparison_block(left_header: str, right_header: str,
                       left_items: list[str], right_items: list[str],
                       left_color: str, right_color: str) -> str:
    max_rows = max(len(left_items), len(right_items))
    rows = []
    for i in range(max_rows):
        l = left_items[i] if i < len(left_items) else ""
        r = right_items[i] if i < len(right_items) else ""
        rows.append(
            f'<div style="display:flex;gap:0;">'
            f'<div style="flex:1;font-family:\'DM Mono\',monospace;font-size:11px;'
            f'color:#888;line-height:1.8;padding-right:8px;">{_e(l)}</div>'
            f'<div style="flex:1;font-family:\'DM Mono\',monospace;font-size:11px;'
            f'color:{right_color};line-height:1.8;">* {_e(r)}</div>'
            f'</div>'
        )
    return f"""
<div style="background:#111;border-radius:10px;padding:14px 16px;margin:12px 0;">
  <div style="display:flex;gap:5px;margin-bottom:10px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FF5F57;"></div>
    <div style="width:10px;height:10px;border-radius:50%;background:#FEBC2E;"></div>
    <div style="width:10px;height:10px;border-radius:50%;background:#28C840;"></div>
  </div>
  <div style="display:flex;border-bottom:1px solid #333;padding-bottom:6px;margin-bottom:6px;">
    <div style="flex:1;font-family:'DM Mono',monospace;font-size:10px;
      letter-spacing:1px;color:{left_color};text-transform:uppercase;">{_e(left_header)}</div>
    <div style="flex:1;font-family:'DM Mono',monospace;font-size:10px;
      letter-spacing:1px;color:{right_color};text-transform:uppercase;">{_e(right_header)}</div>
  </div>
  {"".join(rows)}
</div>"""


def _base(body_inner: str, bg: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=420,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{_FONTS_URL}" rel="stylesheet">
<style>
  *,*::before,*::after{{margin:0;padding:0;box-sizing:border-box;}}
  html,body{{width:420px;height:525px;overflow:hidden;background:{bg};}}
  body{{position:relative;-webkit-font-smoothing:antialiased;}}
</style>
</head>
<body>
{body_inner}
</body>
</html>"""


# ── Slide 1 — Cover (Cream + Rust) ───────────────────────────────────────────

def _slide1_cover(title: str, subtitle: str, brand_handle: str) -> str:
    # Split title for two-tone effect
    words = title.upper().split()
    mid   = max(1, len(words) // 2)
    line1 = " ".join(words[:mid])
    accent_word = words[mid] if len(words) > mid else ""
    line2 = " ".join(words[mid+1:]) if len(words) > mid + 1 else ""

    inner = f"""
<div style="width:420px;height:525px;background:{_CREAM};position:relative;overflow:hidden;">
  {_grid_overlay(0.07)}
  {_top_bar("THE HOOK", 1, 8, _RUST, "#999")}

  <!-- Sub-label -->
  <div style="position:absolute;top:52px;left:22px;">
    <span style="font-family:'Barlow Condensed',sans-serif;font-size:11px;
      font-weight:700;letter-spacing:2px;text-transform:uppercase;
      color:#999;">AI DECODED × VIPINAIHUB</span>
  </div>

  <!-- Accent asterisk -->
  <div style="position:absolute;top:74px;left:22px;">
    <span style="font-family:'Barlow Condensed',sans-serif;font-size:24px;
      font-weight:900;color:{_RUST};">*</span>
  </div>

  <!-- Giant title -->
  <div style="position:absolute;top:100px;left:22px;right:22px;">
    {_two_tone_title(line1, accent_word, line2, _BLACK, _RUST, "72px")}
    {_accent_bar(_RUST)}
    {_body_text(subtitle, "#666", "15px")}
  </div>

  {_bottom_bar(brand_handle, True, "#999", "#999")}
</div>"""
    return _base(inner, _CREAM)


# ── Slide 2 — Dark + Rust (Strikethrough myths / problems) ───────────────────

def _slide2_dark(title: str, accent: str, subtitle: str,
                  pill_items: list[str], body: str,
                  brand_handle: str) -> str:
    words = title.upper().split()
    line1 = words[0] if words else ""
    acc   = " ".join(words[1:2])
    line2 = " ".join(words[2:])

    inner = f"""
<div style="width:420px;height:525px;background:{_DARK};position:relative;overflow:hidden;">
  {_grid_overlay(0.09)}
  {_top_bar("THE MYTHS", 2, 8, _RUST, "rgba(255,255,255,0.3)")}

  <div style="position:absolute;top:52px;left:22px;right:22px;">
    {_two_tone_title(line1, acc, line2, _WHITE, _RUST, "72px")}
    <div style="font-family:'Barlow Condensed',sans-serif;font-size:11px;
      font-weight:700;letter-spacing:2px;text-transform:uppercase;
      color:rgba(255,255,255,0.4);margin:8px 0 12px;">
      {_e(subtitle)}</div>
    {_strikethrough_pills(pill_items, "rgba(255,255,255,0.2)", "rgba(255,255,255,0.45)")}
    <div style="width:100%;height:1px;background:rgba(255,255,255,0.08);margin:14px 0 10px;"></div>
    {_body_text(body, "rgba(255,255,255,0.55)", "13px")}
  </div>

  {_bottom_bar(brand_handle, True, "rgba(255,255,255,0.3)", "rgba(255,255,255,0.4)")}
</div>"""
    return _base(inner, _DARK)


# ── Slide 3 — Rust full bleed (bold statement + terminal) ────────────────────

def _slide3_rust(title: str, terminal_lines: list[str],
                  body: str, brand_handle: str) -> str:
    words = title.upper().split()
    mid   = max(1, len(words) // 3)
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:mid*2])
    line3 = " ".join(words[mid*2:])

    inner = f"""
<div style="width:420px;height:525px;background:{_RUST};position:relative;overflow:hidden;">
  {_grid_overlay(0.12)}
  {_top_bar("THE TRUTH", 3, 8, "rgba(255,255,255,0.6)", "rgba(255,255,255,0.5)")}

  <div style="position:absolute;top:48px;left:22px;right:22px;">
    <div style="font-family:'Barlow Condensed',sans-serif;font-size:62px;
      font-weight:900;line-height:0.9;letter-spacing:-1px;
      color:{_WHITE};text-transform:uppercase;margin-bottom:14px;">
      {_e(line1)}<br>
      <span style="color:rgba(255,255,255,0.55);">{_e(line2)}</span><br>
      {_e(line3)}
    </div>
    {_terminal_block(terminal_lines, "#4ADE80")}
    {_body_text(body, "rgba(255,255,255,0.75)", "13px")}
  </div>

  {_bottom_bar(brand_handle, True, "rgba(255,255,255,0.45)", "rgba(255,255,255,0.5)")}
</div>"""
    return _base(inner, _RUST)


# ── Slide 4 — Cream + Rust (numbered list / facts) ───────────────────────────

def _slide4_cream(title: str, accent_word: str,
                   numbered_items: list[tuple[str, str]],
                   brand_handle: str) -> str:
    rows = "".join(
        _numbered_row(
            f"{i+1:02d}", item[0], item[1],
            _RUST, _BLACK, "#666", _CREAM_DARK
        )
        for i, item in enumerate(numbered_items[:4])
    )
    inner = f"""
<div style="width:420px;height:525px;background:{_CREAM};position:relative;overflow:hidden;">
  {_grid_overlay(0.07)}
  {_top_bar("THE FACTS", 4, 8, _RUST, "#999")}

  <div style="position:absolute;top:46px;left:22px;right:22px;">
    {_two_tone_title(title, accent_word, "", _BLACK, _RUST, "58px")}
    <div style="margin-top:8px;">{rows}</div>
  </div>

  {_bottom_bar(brand_handle, True, "#999", "#999")}
</div>"""
    return _base(inner, _CREAM)


# ── Slide 5 — Dark + Purple (comparison / vs) ────────────────────────────────

def _slide5_dark_purple(title: str, accent_word: str,
                         left_header: str, right_header: str,
                         left_items: list[str], right_items: list[str],
                         body: str, brand_handle: str) -> str:
    inner = f"""
<div style="width:420px;height:525px;background:{_DARK2};position:relative;overflow:hidden;">
  {_grid_overlay(0.09)}
  {_top_bar("THE DEPTH", 5, 8, _RUST, "rgba(255,255,255,0.3)")}

  <div style="position:absolute;top:48px;left:22px;right:22px;">
    {_two_tone_title(title, accent_word, "", _WHITE, _RUST, "62px")}
    {_comparison_block(left_header, right_header,
                        left_items, right_items, "#888", "#4ADE80")}
    {_body_text(body, "rgba(255,255,255,0.45)", "12px")}
  </div>

  {_bottom_bar(brand_handle, True, "rgba(255,255,255,0.3)", "rgba(255,255,255,0.4)")}
</div>"""
    return _base(inner, _DARK2)


# ── Slide 6 — Cream + Purple (how-to / numbered steps) ───────────────────────

def _slide6_cream_purple(title: str, accent_word: str,
                          steps: list[tuple[str, str]],
                          brand_handle: str) -> str:
    rows = "".join(
        _numbered_row(
            f"{i+1:02d}", s[0], s[1],
            _PURPLE, _BLACK, "#555", _CREAM_DARK
        )
        for i, s in enumerate(steps[:4])
    )
    inner = f"""
<div style="width:420px;height:525px;background:{_CREAM};position:relative;overflow:hidden;">
  {_grid_overlay(0.07)}
  {_top_bar("THE METHOD", 6, 8, _PURPLE, "#999")}

  <div style="position:absolute;top:46px;left:22px;right:22px;">
    {_two_tone_title(title, accent_word, "", _BLACK, _PURPLE, "58px")}
    <div style="margin-top:8px;">{rows}</div>
  </div>

  {_bottom_bar(brand_handle, True, "#999", "#999")}
</div>"""
    return _base(inner, _CREAM)


# ── Slide 7 — Rust full bleed (biggest takeaway) ─────────────────────────────

def _slide7_rust(title: str, body: str, brand_handle: str) -> str:
    words = title.upper().split()
    mid   = max(1, len(words) // 2)
    line1 = " ".join(words[:mid])
    line2 = " ".join(words[mid:])

    inner = f"""
<div style="width:420px;height:525px;background:{_RUST};position:relative;overflow:hidden;">
  {_grid_overlay(0.12)}
  {_top_bar("THE SIGNAL", 7, 8, "rgba(255,255,255,0.6)", "rgba(255,255,255,0.5)")}

  <!-- Centered content -->
  <div style="position:absolute;inset:0;display:flex;flex-direction:column;
    align-items:center;justify-content:center;padding:28px 28px 50px;">

    <!-- Brand icon -->
    <div style="width:64px;height:64px;background:rgba(255,255,255,0.15);
      border-radius:16px;display:flex;align-items:center;justify-content:center;
      margin-bottom:18px;">
      <span style="font-family:'Barlow Condensed',sans-serif;font-size:28px;
        font-weight:900;color:{_WHITE};">V</span>
    </div>

    <span style="font-family:'Barlow Condensed',sans-serif;font-size:11px;
      font-weight:700;letter-spacing:3px;text-transform:uppercase;
      color:rgba(255,255,255,0.6);margin-bottom:12px;">VIPINAIHUB</span>

    <div style="font-family:'Barlow Condensed',sans-serif;font-size:62px;
      font-weight:900;line-height:0.92;letter-spacing:-1px;
      color:{_WHITE};text-transform:uppercase;text-align:center;margin-bottom:16px;">
      {_e(line1)}<br>{_e(line2)}
    </div>

    <p style="font-family:'Barlow',sans-serif;font-size:14px;
      color:rgba(255,255,255,0.75);text-align:center;line-height:1.5;margin-bottom:20px;">
      {_e(body)}</p>

    <!-- CTA button -->
    <div style="background:{_CREAM};border-radius:100px;padding:11px 28px;">
      <span style="font-family:'Barlow',sans-serif;font-size:14px;
        font-weight:700;color:{_RUST};">Follow @vipin.vishal ↗</span>
    </div>

    <!-- Social links -->
    <div style="margin-top:16px;text-align:center;">
      <p style="font-family:'Barlow',sans-serif;font-size:11px;
        color:rgba(255,255,255,0.45);line-height:1.7;">
        Stay updated on AI — follow @VipinAIHub on X.com<br>
        Connect on LinkedIn → linkedin.com/in/vipin-vishal-b8b92643
      </p>
    </div>
  </div>

  {_bottom_bar(brand_handle, False, "rgba(255,255,255,0.4)", "")}
</div>"""
    return _base(inner, _RUST)


# ── Slide 8 — Dark CTA (Purple) ───────────────────────────────────────────────

def _slide8_cta(caption: str, brand_handle: str) -> str:
    inner = f"""
<div style="width:420px;height:525px;background:{_DARK};position:relative;overflow:hidden;">
  {_grid_overlay(0.09)}

  <!-- Purple glow -->
  <div style="position:absolute;top:-80px;right:-80px;width:280px;height:280px;
    border-radius:50%;background:radial-gradient(circle,rgba(108,59,255,.25) 0%,transparent 65%);"></div>

  {_top_bar("THE FOLLOW", 8, 8, _PURPLE_L, "rgba(255,255,255,0.3)")}

  <div style="position:absolute;inset:0;display:flex;flex-direction:column;
    align-items:center;justify-content:center;padding:28px 28px 50px;">

    <!-- Icon -->
    <div style="width:56px;height:56px;
      background:linear-gradient(135deg,{_PURPLE} 0%,#9B72FF 100%);
      border-radius:14px;display:flex;align-items:center;justify-content:center;
      margin-bottom:16px;box-shadow:0 8px 24px rgba(108,59,255,.45);">
      <span style="font-family:'Barlow Condensed',sans-serif;font-size:24px;
        font-weight:900;color:{_WHITE};">V</span>
    </div>

    <div style="font-family:'Barlow Condensed',sans-serif;font-size:52px;
      font-weight:900;line-height:0.92;letter-spacing:-1px;
      color:{_WHITE};text-transform:uppercase;text-align:center;margin-bottom:8px;">
      FOLLOW<br><span style="color:{_PURPLE_L};">THE SIGNAL.</span>
    </div>

    <p style="font-family:'Barlow',sans-serif;font-size:13px;
      color:rgba(255,255,255,0.5);text-align:center;line-height:1.5;margin-bottom:20px;">
      AI decoded — weekly.<br>No hype. Just signal.</p>

    <!-- Handle pill -->
    <div style="background:rgba(108,59,255,.25);border:1px solid rgba(108,59,255,.55);
      border-radius:100px;padding:10px 26px;margin-bottom:18px;">
      <span style="font-family:'Barlow Condensed',sans-serif;font-size:20px;
        font-weight:800;color:{_WHITE};">@VipinAIHub</span>
    </div>

    <!-- Social -->
    <div style="display:flex;gap:8px;width:100%;">
      <div style="flex:1;background:rgba(255,255,255,.05);border-radius:8px;
        padding:9px 11px;display:flex;align-items:center;gap:7px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="{_WHITE}">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231
            -5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.259 5.629 5.905-5.629z
            m-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
        <span style="font-family:'Barlow',sans-serif;font-size:10px;
          color:rgba(255,255,255,0.7);">x.com/VipinAIHub</span>
      </div>
      <div style="flex:1;background:rgba(255,255,255,.05);border-radius:8px;
        padding:9px 11px;display:flex;align-items:center;gap:7px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="#0A66C2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/>
          <rect x="2" y="9" width="4" height="12"/>
          <circle cx="4" cy="4" r="2"/>
        </svg>
        <span style="font-family:'Barlow',sans-serif;font-size:10px;
          color:rgba(255,255,255,0.7);">vipin-vishal-b8b92643</span>
      </div>
    </div>
  </div>

  {_bottom_bar(brand_handle, False, "rgba(255,255,255,0.25)", "")}
</div>"""
    return _base(inner, _DARK)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_carousel_html(
    content: dict,
    output_dir: str,
    brand_name: str  = "VipinAIHub",
    brand_handle: str = "@VipinAIHub",
    brand_x: str     = "x.com/VipinAIHub",
    brand_linkedin: str = "linkedin.com/in/vipin-vishal-b8b92643",
) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)

    titles  = list(content.get("slide_titles",  []))
    pts_all = list(content.get("slide_points",   []))
    bullets = list(content.get("bullets",        []))
    summary = content.get("summary", "")
    caption = content.get("caption", "Follow @VipinAIHub for daily AI insights.")

    while len(titles)  < 8: titles.append(f"Slide {len(titles)+1}")
    while len(pts_all) < 8: pts_all.append(["", "", ""])

    def _pts(idx): return pts_all[idx] if idx < len(pts_all) else ["","",""]
    def _title(idx): return titles[idx] if idx < len(titles) else ""

    def _split(text: str):
        """Split a title into (main, accent_word) — last word becomes accent."""
        words = text.split()
        if len(words) <= 1:
            return text, ""
        return " ".join(words[:-1]), words[-1]

    slides_html = []

    # Slide 1 — Cover
    slides_html.append(_slide1_cover(
        title    = _title(0),
        subtitle = summary[:120] if summary else "Swipe to find out.",
        brand_handle = brand_handle,
    ))

    # Slide 2 — Myths / problems (strikethrough pills from bullets 0-5)
    pill_items = [b.split("—")[0].strip() for b in bullets[:6]] or ["Point 1","Point 2","Point 3","Point 4"]
    slides_html.append(_slide2_dark(
        title      = _title(1),
        accent     = _RUST,
        subtitle   = "WHAT PEOPLE GET WRONG",
        pill_items = pill_items,
        body       = _pts(1)[0] if _pts(1) else "",
        brand_handle = brand_handle,
    ))

    # Slide 3 — Truth / built different (terminal block)
    p3 = _pts(2)
    terminal_lines = [
        f"$ {_title(2).lower()[:30]}",
        f"→ {p3[0][:45]}" if p3[0] else "→ Initializing...",
        f"→ {p3[1][:45]}" if len(p3) > 1 and p3[1] else "→ Loading context...",
        f"✓ {p3[2][:45]}" if len(p3) > 2 and p3[2] else "✓ Ready.",
    ]
    slides_html.append(_slide3_rust(
        title          = _title(2),
        terminal_lines = terminal_lines,
        body           = bullets[2] if len(bullets) > 2 else "",
        brand_handle   = brand_handle,
    ))

    # Slide 4 — Facts / numbered list
    p4 = _pts(3)
    numbered4 = []
    for i in range(min(4, len(p4))):
        parts = p4[i].split("—", 1) if p4[i] else ["", ""]
        numbered4.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""))
    while len(numbered4) < 2:
        numbered4.append(("Key point", "More detail here."))
    main4, acc4 = _split(_title(3))
    slides_html.append(_slide4_cream(
        title          = main4,
        accent_word    = acc4,
        numbered_items = numbered4,
        brand_handle   = brand_handle,
    ))

    # Slide 5 — Comparison (vs / depth)
    p5 = _pts(4)
    left_items  = [bullets[0][:35], bullets[1][:35], bullets[2][:35], bullets[3][:35]] if len(bullets) >= 4 else ["Point A","Point B"]
    right_items = [p5[0][:35], p5[1][:35], p5[2][:35], bullets[4][:35] if len(bullets) > 4 else ""] if p5 else ["Better","Smarter"]
    main5, acc5 = _split(_title(4))
    slides_html.append(_slide5_dark_purple(
        title        = main5,
        accent_word  = acc5,
        left_header  = "OTHERS",
        right_header = brand_name.upper(),
        left_items   = left_items,
        right_items  = right_items,
        body         = bullets[4] if len(bullets) > 4 else "",
        brand_handle = brand_handle,
    ))

    # Slide 6 — How-to / method (numbered steps with purple)
    p6 = _pts(5)
    steps6 = []
    for i in range(min(4, len(p6))):
        parts = p6[i].split("—", 1) if p6[i] else ["", ""]
        steps6.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""))
    while len(steps6) < 2:
        steps6.append(("Step", "Description here."))
    main6, acc6 = _split(_title(5))
    slides_html.append(_slide6_cream_purple(
        title        = main6,
        accent_word  = acc6,
        steps        = steps6,
        brand_handle = brand_handle,
    ))

    # Slide 7 — Takeaway (Rust CTA)
    slides_html.append(_slide7_rust(
        title        = _title(6),
        body         = bullets[5] if len(bullets) > 5 else "Follow for more AI insights.",
        brand_handle = brand_handle,
    ))

    # Slide 8 — Final CTA (Dark purple)
    slides_html.append(_slide8_cta(
        caption      = caption,
        brand_handle = brand_handle,
    ))

    html_paths: list[str] = []
    for idx, html in enumerate(slides_html):
        path = os.path.join(output_dir, f"slide_{idx+1}.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        html_paths.append(os.path.abspath(path))
        logger.debug("Wrote slide %d → %s", idx+1, path)

    logger.info("Generated %d HTML slides in %s", len(html_paths), output_dir)
    return html_paths