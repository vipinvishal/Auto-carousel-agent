"""
carousel.py — Instagram carousel generator optimised for virality.

Design principles (Instagram / Threads engagement):
  • Space Grotesk body — modern, creator-economy feel
  • Barlow Condensed display — bold, commanding, scroll-stopping
  • Curiosity-gap slide labels that create a "need to swipe" pull
  • Progress bar on every slide (proven swipe-through driver)
  • BREAKING badge on cover — signals recency and urgency
  • Numbered fact rows (not confusing pills) on slide 2
  • Emoji impact rows on slide 5 ("What changes for YOU")
  • Minimum 16 px body text — readable on a 6" phone screen
"""

import html as _html
import logging
import os

logger = logging.getLogger(__name__)

# ── Design tokens ─────────────────────────────────────────────────────────────
_RUST       = "#C4441A"
_PURPLE     = "#6C3BFF"
_PURPLE_L   = "#A78BFF"
_CREAM      = "#EDEADE"
_CREAM_DARK = "#D9D4C7"
_DARK       = "#151210"
_DARK2      = "#1E1A16"
_WHITE      = "#FFFFFF"
_BLACK      = "#111111"
_GREEN      = "#4ADE80"

# Space Grotesk: modern / creator-economy body font (replaces plain Barlow)
# Barlow Condensed: keeps the bold editorial display look
_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Space+Grotesk:wght@300;400;500;600;700"
    "&family=Barlow+Condensed:wght@700;800;900"
    "&family=DM+Mono:wght@400;500"
    "&display=swap"
)

# Curiosity-gap labels — each creates a "pull" to swipe to the next
_LABELS = [
    "BREAKING NOW",       # 1 — urgency signal
    "THE REAL STORY",     # 2 — implies hidden knowledge
    "THE NUMBERS",        # 3 — people love concrete stats
    "WHY IT MATTERS",     # 4 — reader-centric framing
    "WHAT CHANGES NOW",   # 5 — forces mental action
    "YOUR MOVE",          # 6 — direct, actionable
    "THE TAKEAWAY",       # 7 — value payoff
    "JOIN THE SIGNAL",    # 8 — community CTA
]

_DEFAULT_EMOJIS = ["🔥", "🤖", "⚡", "🛠️", "📈", "💡", "🎯", "🚀"]


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _e(text: str) -> str:
    return _html.escape(str(text), quote=True)


def _grid(opacity: float = 0.06) -> str:
    return f"""
<svg style="position:absolute;inset:0;width:100%;height:100%;pointer-events:none;"
  xmlns="http://www.w3.org/2000/svg">
  <defs>
    <pattern id="g" width="105" height="131.25" patternUnits="userSpaceOnUse">
      <path d="M 105 0 L 0 0 0 131.25" fill="none"
        stroke="currentColor" stroke-width="0.5" opacity="{opacity}"/>
    </pattern>
  </defs>
  <rect width="100%" height="100%" fill="url(#g)" color="#000"/>
</svg>"""


def _progress_bar(current: int, total: int, color: str) -> str:
    """Thin progress bar at the very bottom — tells viewers how far they've swiped."""
    pct = round((current / total) * 100)
    return f"""
<div style="position:absolute;bottom:0;left:0;right:0;height:3px;
  background:rgba(128,128,128,0.18);">
  <div style="width:{pct}%;height:100%;background:{color};border-radius:0 2px 2px 0;"></div>
</div>"""


def _top_bar(label: str, num: int, total: int,
             label_color: str, counter_color: str) -> str:
    return f"""
<div style="position:absolute;top:0;left:0;right:0;padding:18px 22px 0;
  display:flex;justify-content:space-between;align-items:flex-start;">
  <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;
    font-weight:700;letter-spacing:2.5px;text-transform:uppercase;
    color:{label_color};">{_e(label)}</span>
  <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;
    font-weight:600;letter-spacing:1.5px;color:{counter_color};">
    {num:02d} / {total:02d}</span>
</div>"""


def _bottom_bar(handle: str, show_swipe: bool,
                handle_color: str, swipe_color: str) -> str:
    swipe_html = ""
    if show_swipe:
        swipe_html = f"""
<div style="display:flex;align-items:center;gap:5px;">
  <span style="font-family:'Space Grotesk',sans-serif;font-size:9px;
    font-weight:600;letter-spacing:1.5px;text-transform:uppercase;
    color:{swipe_color};">SWIPE</span>
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
    stroke="{swipe_color}" stroke-width="2" stroke-linecap="round"
    stroke-linejoin="round"
    style="background:rgba(128,128,128,0.18);border-radius:50%;padding:3px;">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
</div>"""
    return f"""
<div style="position:absolute;bottom:6px;left:0;right:0;padding:0 22px 12px;
  display:flex;justify-content:space-between;align-items:flex-end;">
  <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;
    font-weight:600;letter-spacing:2px;text-transform:uppercase;
    color:{handle_color};">@{_e(handle.lstrip('@'))}</span>
  {swipe_html}
</div>"""


def _two_tone_title(line1: str, accent: str, line2: str,
                    base: str, accent_color: str, size: str = "72px") -> str:
    parts = []
    for text, color in [(line1, base), (accent, accent_color), (line2, base)]:
        if text:
            parts.append(
                f'<div style="font-family:\'Barlow Condensed\',sans-serif;'
                f'font-size:{size};font-weight:900;line-height:0.92;'
                f'letter-spacing:-1px;color:{color};text-transform:uppercase;">'
                f'{_e(text)}</div>'
            )
    return "\n".join(parts)


def _accent_bar(color: str) -> str:
    return (
        f'<div style="width:44px;height:4px;background:{color};'
        f'border-radius:2px;margin:14px 0 14px;"></div>'
    )


def _body(text: str, color: str, size: str = "16px", weight: str = "400") -> str:
    return (
        f'<p style="font-family:\'Space Grotesk\',sans-serif;font-size:{size};'
        f'font-weight:{weight};line-height:1.55;color:{color};margin:0;">'
        f'{_e(text)}</p>'
    )


def _breaking_badge(text: str = "LIVE UPDATE", dot_color: str = _RUST,
                    bg: str = "rgba(196,68,26,0.12)",
                    label_color: str = _RUST) -> str:
    """Pulsing 'BREAKING' badge — signals recency and urgency on slide 1."""
    return f"""
<div style="display:inline-flex;align-items:center;gap:7px;
  background:{bg};border:1px solid rgba(196,68,26,0.3);
  border-radius:100px;padding:5px 14px;margin-bottom:14px;">
  <div style="width:7px;height:7px;border-radius:50%;background:{dot_color};"></div>
  <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:700;
    letter-spacing:2.5px;text-transform:uppercase;color:{label_color};">{_e(text)}</span>
</div>"""


def _fact_row(num: str, text: str,
              num_color: str, text_color: str, border_color: str) -> str:
    """Large-numbered fact row — clear, punchy, screenshot-worthy."""
    return f"""
<div style="display:flex;align-items:flex-start;gap:16px;
  padding:12px 0;border-bottom:1px solid {border_color};">
  <div style="font-family:'Barlow Condensed',sans-serif;font-size:40px;
    font-weight:900;color:{num_color};line-height:1;min-width:46px;">{_e(num)}</div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:16px;
    font-weight:500;color:{text_color};line-height:1.4;padding-top:6px;">{_e(text)}</div>
</div>"""


def _numbered_row(num: str, title: str, desc: str,
                  num_color: str, title_color: str,
                  desc_color: str, border_color: str) -> str:
    return f"""
<div style="display:flex;align-items:flex-start;gap:14px;
  padding:12px 0;border-bottom:1px solid {border_color};">
  <span style="font-family:'Barlow Condensed',sans-serif;font-size:32px;
    font-weight:900;color:{num_color};min-width:38px;line-height:1;">{num}</span>
  <div>
    <p style="font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:600;
      color:{title_color};margin:0 0 2px;">{_e(title)}</p>
    <p style="font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:400;
      color:{desc_color};margin:0;line-height:1.45;">{_e(desc)}</p>
  </div>
</div>"""


def _impact_row(emoji: str, text: str, text_color: str, border_color: str) -> str:
    """Emoji + impact statement row for 'What changes now' slide."""
    return f"""
<div style="display:flex;align-items:flex-start;gap:14px;
  padding:12px 0;border-bottom:1px solid {border_color};">
  <div style="font-size:24px;min-width:34px;line-height:1.2;">{emoji}</div>
  <div style="font-family:'Space Grotesk',sans-serif;font-size:16px;
    font-weight:500;color:{text_color};line-height:1.4;padding-top:2px;">{_e(text)}</div>
</div>"""


def _terminal_block(lines: list[str]) -> str:
    rows = []
    for ln in lines:
        if ln.startswith("$"):
            color = "#A78BFF"
        elif ln.startswith("✓") or ln.startswith("*"):
            color = _GREEN
        elif ln.startswith("→"):
            color = "#A0A0A0"
        else:
            color = "#D0D0D0"
        rows.append(
            f'<div style="font-family:\'DM Mono\',monospace;font-size:12px;'
            f'color:{color};line-height:1.75;">{_e(ln)}</div>'
        )
    return f"""
<div style="background:#0D0D0D;border-radius:10px;padding:13px 15px;margin:12px 0;">
  <div style="display:flex;gap:5px;margin-bottom:9px;">
    <div style="width:9px;height:9px;border-radius:50%;background:#FF5F57;"></div>
    <div style="width:9px;height:9px;border-radius:50%;background:#FEBC2E;"></div>
    <div style="width:9px;height:9px;border-radius:50%;background:#28C840;"></div>
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


# ── Slide builders ────────────────────────────────────────────────────────────

def _slide1(title: str, subtitle: str, handle: str) -> str:
    words = title.upper().split()
    mid   = max(1, len(words) // 2)
    l1    = " ".join(words[:mid])
    acc   = words[mid] if len(words) > mid else ""
    l2    = " ".join(words[mid + 1:]) if len(words) > mid + 1 else ""

    inner = f"""
<div style="width:420px;height:525px;background:{_CREAM};position:relative;overflow:hidden;">
  {_grid(0.07)}
  {_top_bar(_LABELS[0], 1, 8, _RUST, "#999")}

  <div style="position:absolute;top:46px;left:22px;right:22px;">
    {_breaking_badge("TRENDING NOW")}
    {_two_tone_title(l1, acc, l2, _BLACK, _RUST, "70px")}
    {_accent_bar(_RUST)}
    {_body(subtitle, "#555", "15px")}
  </div>

  <!-- Corner mark -->
  <div style="position:absolute;bottom:24px;right:22px;
    font-family:'Barlow Condensed',sans-serif;font-size:10px;
    font-weight:700;letter-spacing:3px;color:#BBB;text-transform:uppercase;">
    AI DECODED × VIPINAIHUB
  </div>

  {_bottom_bar(handle, True, "#999", _RUST)}
  {_progress_bar(1, 8, _RUST)}
</div>"""
    return _base(inner, _CREAM)


def _slide2(title: str, pts: list[str], handle: str) -> str:
    words = title.upper().split()
    l1 = " ".join(words[:2]) if len(words) >= 2 else title.upper()
    l2 = " ".join(words[2:]) if len(words) > 2 else ""

    rows = "".join(
        _fact_row(f"{i+1:02d}", pt, _RUST, "rgba(255,255,255,0.88)",
                  "rgba(255,255,255,0.07)")
        for i, pt in enumerate(pts[:3]) if pt
    )

    inner = f"""
<div style="width:420px;height:525px;background:{_DARK};position:relative;overflow:hidden;">
  {_grid(0.09)}
  {_top_bar(_LABELS[1], 2, 8, _RUST, "rgba(255,255,255,0.3)")}

  <div style="position:absolute;top:44px;left:22px;right:22px;">
    {_two_tone_title(l1, "", l2, _WHITE, _RUST, "58px")}
    <div style="margin-top:10px;">{rows}</div>
  </div>

  {_bottom_bar(handle, True, "rgba(255,255,255,0.3)", "rgba(255,255,255,0.45)")}
  {_progress_bar(2, 8, _RUST)}
</div>"""
    return _base(inner, _DARK)


def _slide3(title: str, terminal_lines: list[str], body_text: str, handle: str) -> str:
    words = title.upper().split()
    mid = max(1, len(words) // 3)
    l1 = " ".join(words[:mid])
    l2 = " ".join(words[mid:mid * 2])
    l3 = " ".join(words[mid * 2:])

    inner = f"""
<div style="width:420px;height:525px;background:{_RUST};position:relative;overflow:hidden;">
  {_grid(0.12)}
  {_top_bar(_LABELS[2], 3, 8, "rgba(255,255,255,0.65)", "rgba(255,255,255,0.5)")}

  <div style="position:absolute;top:44px;left:22px;right:22px;">
    <div style="font-family:'Barlow Condensed',sans-serif;font-size:56px;
      font-weight:900;line-height:0.92;letter-spacing:-1px;
      color:{_WHITE};text-transform:uppercase;margin-bottom:12px;">
      {_e(l1)}<br>
      <span style="color:rgba(255,255,255,0.5);">{_e(l2)}</span><br>
      {_e(l3)}
    </div>
    {_terminal_block(terminal_lines)}
    {_body(body_text, "rgba(255,255,255,0.72)", "14px")}
  </div>

  {_bottom_bar(handle, True, "rgba(255,255,255,0.4)", "rgba(255,255,255,0.5)")}
  {_progress_bar(3, 8, "rgba(255,255,255,0.6)")}
</div>"""
    return _base(inner, _RUST)


def _slide4(title: str, acc: str, items: list[tuple[str, str]], handle: str) -> str:
    rows = "".join(
        _numbered_row(f"{i+1:02d}", item[0], item[1],
                      _RUST, _BLACK, "#666", _CREAM_DARK)
        for i, item in enumerate(items[:4])
    )
    inner = f"""
<div style="width:420px;height:525px;background:{_CREAM};position:relative;overflow:hidden;">
  {_grid(0.07)}
  {_top_bar(_LABELS[3], 4, 8, _RUST, "#999")}

  <div style="position:absolute;top:42px;left:22px;right:22px;">
    {_two_tone_title(title, acc, "", _BLACK, _RUST, "56px")}
    <div style="margin-top:10px;">{rows}</div>
  </div>

  {_bottom_bar(handle, True, "#999", "#999")}
  {_progress_bar(4, 8, _RUST)}
</div>"""
    return _base(inner, _CREAM)


def _slide5(title: str, acc: str, pts: list[str],
            emojis: list[str], handle: str) -> str:
    """'What changes now' — emoji + impact rows. Reader-centric framing."""
    default_emojis = ["⚡", "🔥", "🎯"]
    rows = "".join(
        _impact_row(emojis[i] if i < len(emojis) else default_emojis[i % 3],
                    pt, "rgba(255,255,255,0.88)", "rgba(255,255,255,0.07)")
        for i, pt in enumerate(pts[:3]) if pt
    )
    inner = f"""
<div style="width:420px;height:525px;background:{_DARK2};position:relative;overflow:hidden;">
  {_grid(0.09)}
  <!-- Purple glow top-right -->
  <div style="position:absolute;top:-60px;right:-60px;width:220px;height:220px;
    border-radius:50%;background:radial-gradient(circle,rgba(108,59,255,.2) 0%,transparent 65%);"></div>

  {_top_bar(_LABELS[4], 5, 8, _PURPLE_L, "rgba(255,255,255,0.3)")}

  <div style="position:absolute;top:44px;left:22px;right:22px;">
    {_two_tone_title(title, acc, "", _WHITE, _PURPLE_L, "58px")}
    <div style="margin-top:10px;">{rows}</div>
  </div>

  {_bottom_bar(handle, True, "rgba(255,255,255,0.3)", "rgba(255,255,255,0.4)")}
  {_progress_bar(5, 8, _PURPLE)}
</div>"""
    return _base(inner, _DARK2)


def _slide6(title: str, acc: str, steps: list[tuple[str, str]], handle: str) -> str:
    rows = "".join(
        _numbered_row(f"{i+1:02d}", s[0], s[1],
                      _PURPLE, _BLACK, "#555", _CREAM_DARK)
        for i, s in enumerate(steps[:4])
    )
    inner = f"""
<div style="width:420px;height:525px;background:{_CREAM};position:relative;overflow:hidden;">
  {_grid(0.07)}
  {_top_bar(_LABELS[5], 6, 8, _PURPLE, "#999")}

  <div style="position:absolute;top:42px;left:22px;right:22px;">
    {_two_tone_title(title, acc, "", _BLACK, _PURPLE, "56px")}
    <div style="margin-top:10px;">{rows}</div>
  </div>

  {_bottom_bar(handle, True, "#999", "#999")}
  {_progress_bar(6, 8, _PURPLE)}
</div>"""
    return _base(inner, _CREAM)


def _slide7(title: str, body_text: str, handle: str) -> str:
    words = title.upper().split()
    mid   = max(1, len(words) // 2)
    l1    = " ".join(words[:mid])
    l2    = " ".join(words[mid:])

    inner = f"""
<div style="width:420px;height:525px;background:{_RUST};position:relative;overflow:hidden;">
  {_grid(0.12)}
  {_top_bar(_LABELS[6], 7, 8, "rgba(255,255,255,0.65)", "rgba(255,255,255,0.5)")}

  <div style="position:absolute;inset:0;display:flex;flex-direction:column;
    align-items:center;justify-content:center;padding:28px 28px 52px;">

    <div style="width:52px;height:52px;background:rgba(255,255,255,0.15);
      border-radius:14px;display:flex;align-items:center;justify-content:center;
      margin-bottom:16px;">
      <span style="font-family:'Barlow Condensed',sans-serif;font-size:26px;
        font-weight:900;color:{_WHITE};">V</span>
    </div>

    <div style="font-family:'Barlow Condensed',sans-serif;font-size:60px;
      font-weight:900;line-height:0.92;letter-spacing:-1px;
      color:{_WHITE};text-transform:uppercase;text-align:center;margin-bottom:16px;">
      {_e(l1)}<br>{_e(l2)}
    </div>

    {_body(body_text, "rgba(255,255,255,0.78)", "15px")}

    <!-- Save prompt -->
    <div style="margin-top:20px;display:flex;align-items:center;gap:8px;">
      <div style="width:32px;height:1px;background:rgba(255,255,255,0.35);"></div>
      <span style="font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:600;
        letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,0.5);">
        SAVE THIS POST</span>
      <div style="width:32px;height:1px;background:rgba(255,255,255,0.35);"></div>
    </div>
  </div>

  {_bottom_bar(handle, False, "rgba(255,255,255,0.35)", "")}
  {_progress_bar(7, 8, "rgba(255,255,255,0.5)")}
</div>"""
    return _base(inner, _RUST)


def _slide8(handle: str, brand_name: str = "VipinAIHub") -> str:
    inner = f"""
<div style="width:420px;height:525px;background:{_DARK};position:relative;overflow:hidden;">
  {_grid(0.09)}

  <!-- Purple glow -->
  <div style="position:absolute;top:-80px;right:-80px;width:280px;height:280px;
    border-radius:50%;background:radial-gradient(circle,rgba(108,59,255,.28) 0%,transparent 65%);"></div>
  <div style="position:absolute;bottom:-60px;left:-60px;width:200px;height:200px;
    border-radius:50%;background:radial-gradient(circle,rgba(108,59,255,.15) 0%,transparent 65%);"></div>

  {_top_bar(_LABELS[7], 8, 8, _PURPLE_L, "rgba(255,255,255,0.3)")}

  <div style="position:absolute;inset:0;display:flex;flex-direction:column;
    align-items:center;justify-content:center;padding:28px 28px 52px;">

    <!-- Icon -->
    <div style="width:56px;height:56px;
      background:linear-gradient(135deg,{_PURPLE} 0%,#9B72FF 100%);
      border-radius:14px;display:flex;align-items:center;justify-content:center;
      margin-bottom:18px;box-shadow:0 8px 28px rgba(108,59,255,.45);">
      <span style="font-family:'Barlow Condensed',sans-serif;font-size:26px;
        font-weight:900;color:{_WHITE};">V</span>
    </div>

    <div style="font-family:'Barlow Condensed',sans-serif;font-size:52px;
      font-weight:900;line-height:0.92;letter-spacing:-1px;
      color:{_WHITE};text-transform:uppercase;text-align:center;margin-bottom:8px;">
      FOLLOW<br><span style="color:{_PURPLE_L};">THE SIGNAL.</span>
    </div>

    <p style="font-family:'Space Grotesk',sans-serif;font-size:14px;
      color:rgba(255,255,255,0.5);text-align:center;line-height:1.55;margin-bottom:20px;">
      {_e(brand_name)} — AI decoded, every few days.<br>No hype. Just what actually matters.</p>

    <!-- Handle pill -->
    <div style="background:rgba(108,59,255,.25);border:1px solid rgba(108,59,255,.5);
      border-radius:100px;padding:10px 28px;margin-bottom:18px;">
      <span style="font-family:'Barlow Condensed',sans-serif;font-size:22px;
        font-weight:900;color:{_WHITE};">@VipinAIHub</span>
    </div>

    <!-- Social row -->
    <div style="display:flex;gap:8px;width:100%;">
      <div style="flex:1;background:rgba(255,255,255,.05);border-radius:8px;
        padding:9px 11px;display:flex;align-items:center;gap:7px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="{_WHITE}">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231
            -5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.259 5.629 5.905-5.629z
            m-1.161 17.52h1.833L7.084 4.126H5.117z"/>
        </svg>
        <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;
          color:rgba(255,255,255,0.65);">x.com/VipinAIHub</span>
      </div>
      <div style="flex:1;background:rgba(255,255,255,.05);border-radius:8px;
        padding:9px 11px;display:flex;align-items:center;gap:7px;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="#0A66C2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/>
          <rect x="2" y="9" width="4" height="12"/>
          <circle cx="4" cy="4" r="2"/>
        </svg>
        <span style="font-family:'Space Grotesk',sans-serif;font-size:10px;
          color:rgba(255,255,255,0.65);">vipin-vishal-b8b92643</span>
      </div>
    </div>
  </div>

  {_bottom_bar(handle, False, "rgba(255,255,255,0.25)", "")}
  {_progress_bar(8, 8, _PURPLE)}
</div>"""
    return _base(inner, _DARK)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_carousel_html(
    content: dict,
    output_dir: str,
    brand_name: str      = "VipinAIHub",
    brand_handle: str    = "@VipinAIHub",
    brand_x: str         = "x.com/VipinAIHub",
    brand_linkedin: str  = "linkedin.com/in/vipin-vishal-b8b92643",
) -> list[str]:
    os.makedirs(output_dir, exist_ok=True)

    titles   = list(content.get("slide_titles",  []))
    pts_all  = list(content.get("slide_points",  []))
    bullets  = list(content.get("bullets",       []))
    emojis   = list(content.get("slide_emojis",  _DEFAULT_EMOJIS))
    summary  = content.get("summary", "")

    import re as _re
    _slide_prefix = _re.compile(r"^slide\s*\d+\s*[:\-–]\s*", _re.IGNORECASE)
    titles = [_slide_prefix.sub("", t).strip() for t in titles]

    while len(titles)  < 8: titles.append(f"Slide {len(titles)+1}")
    while len(pts_all) < 8: pts_all.append(["", "", ""])
    while len(emojis)  < 8: emojis.append("✨")

    def _pts(i):  return pts_all[i] if i < len(pts_all) else ["", "", ""]
    def _t(i):    return titles[i]  if i < len(titles)  else ""

    def _split(text: str):
        words = text.split()
        if len(words) <= 1:
            return text, ""
        return " ".join(words[:-1]), words[-1]

    def _to_pairs(pts_list):
        """Split each point at em-dash into (title, desc) pairs."""
        pairs = []
        for pt in pts_list[:4]:
            if not pt:
                continue
            parts = pt.split("—", 1)
            pairs.append((parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""))
        return pairs

    slides = []

    # 1 — Cover
    slides.append(_slide1(
        title    = _t(0),
        subtitle = summary[:130] if summary else "Swipe to find out what just changed.",
        handle   = brand_handle,
    ))

    # 2 — The real story (3 numbered facts)
    slides.append(_slide2(
        title  = _t(1),
        pts    = _pts(1),
        handle = brand_handle,
    ))

    # 3 — The numbers (terminal)
    p3 = _pts(2)
    terminal = [
        f"$ {_t(2).lower()[:32]}",
        f"→ {p3[0][:48]}"  if p3[0]           else "→ Fetching data...",
        f"→ {p3[1][:48]}"  if len(p3) > 1 and p3[1] else "→ Processing...",
        f"✓ {p3[2][:48]}"  if len(p3) > 2 and p3[2] else "✓ Done.",
    ]
    slides.append(_slide3(
        title          = _t(2),
        terminal_lines = terminal,
        body_text      = bullets[2] if len(bullets) > 2 else "",
        handle         = brand_handle,
    ))

    # 4 — Why it matters (numbered pairs)
    main4, acc4 = _split(_t(3))
    slides.append(_slide4(
        title  = main4,
        acc    = acc4,
        items  = _to_pairs(_pts(3)) or [("Key insight", "Context here.")],
        handle = brand_handle,
    ))

    # 5 — What changes now (emoji impact rows)
    main5, acc5 = _split(_t(4))
    slides.append(_slide5(
        title  = main5,
        acc    = acc5,
        pts    = _pts(4),
        emojis = emojis[4:7],
        handle = brand_handle,
    ))

    # 6 — Your move (numbered action steps with purple)
    main6, acc6 = _split(_t(5))
    slides.append(_slide6(
        title  = main6,
        acc    = acc6,
        steps  = _to_pairs(_pts(5)) or [("Take action", "Start here.")],
        handle = brand_handle,
    ))

    # 7 — The takeaway (big centred quote)
    slides.append(_slide7(
        title     = _t(6),
        body_text = bullets[5] if len(bullets) > 5 else "Follow @VipinAIHub for daily AI signals.",
        handle    = brand_handle,
    ))

    # 8 — CTA
    slides.append(_slide8(handle=brand_handle, brand_name=brand_name))

    html_paths: list[str] = []
    for idx, html in enumerate(slides):
        path = os.path.join(output_dir, f"slide_{idx+1}.html")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        html_paths.append(os.path.abspath(path))

    logger.info("Generated %d HTML slides in %s", len(html_paths), output_dir)
    return html_paths
