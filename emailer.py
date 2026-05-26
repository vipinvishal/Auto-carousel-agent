"""
emailer.py — Send the finished carousel PNGs via Gmail SMTP.

Auth  : Gmail App Password (16-digit, not your account password).
Setup : Enable 2-FA on Google, then create an App Password at
        https://myaccount.google.com/apppasswords

Subject : 🎠 New Carousel Ready — {video_title}
Body    : plain-text with summary, bullet points, and an Instagram caption
          ready to copy.
Attachs : slide_1.png … slide_8.png  (in order)
"""

import logging
import os
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

import config

logger = logging.getLogger(__name__)

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587


def send_carousel_email(
    png_paths: list[str],
    video_title: str,
    content: dict,
) -> bool:
    """
    Send carousel PNGs to the configured recipient.

    Args:
        png_paths   : ordered list of PNG file paths (slide_1.png … slide_8.png)
        video_title : title shown in the subject line
        content     : dict with keys summary, bullets, caption (from claude_api)

    Returns:
        True on success, False on failure (logs the error).
    """
    if not config.GMAIL_APP_PASSWORD:
        logger.error("GMAIL_APP_PASSWORD is not set — cannot send email.")
        return False

    subject = f"🎠 New Carousel Ready — {video_title}"
    body = _build_body(video_title, content, slide_count=len(png_paths))

    msg = MIMEMultipart()
    msg["From"]    = config.GMAIL_USER
    msg["To"]      = config.RECIPIENT_EMAIL
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain", "utf-8"))

    # Attach PNGs in slide order
    for png_path in sorted(png_paths, key=_slide_sort_key):
        _attach_png(msg, png_path)

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
            smtp.sendmail(config.GMAIL_USER, config.RECIPIENT_EMAIL, msg.as_string())
        logger.info("Email sent to %s — subject: %s", config.RECIPIENT_EMAIL, subject)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Gmail SMTP authentication failed. "
            "Check GMAIL_APP_PASSWORD and ensure 2-FA is enabled."
        )
    except smtplib.SMTPException as exc:
        logger.error("SMTP error while sending email: %s", exc)
    except OSError as exc:
        logger.error("Network error while sending email: %s", exc)
    return False


# ── Helpers ─────────────────────────────────────────────────────────────────

def _build_body(video_title: str, content: dict, slide_count: int = 0) -> str:
    summary = content.get("summary", "")
    bullets = content.get("bullets", [])
    caption = content.get("caption", "")

    bullet_text = "\n".join(f"  • {b}" for b in bullets if b)

    return (
        f"New carousel generated for:\n{video_title}\n\n"
        f"{'=' * 60}\n"
        f"SUMMARY\n{'=' * 60}\n{summary}\n\n"
        f"{'=' * 60}\n"
        f"KEY INSIGHTS\n{'=' * 60}\n{bullet_text}\n\n"
        f"{'=' * 60}\n"
        f"INSTAGRAM CAPTION (copy-ready)\n{'=' * 60}\n{caption}\n\n"
        f"{'=' * 60}\n"
        f"Slides attached: {slide_count} PNGs\n"
        f"Brand: {config.BRAND_HANDLE} | {config.BRAND_X}\n"
    )


def _attach_png(msg: MIMEMultipart, png_path: str) -> None:
    """Attach a single PNG file to the email message.

    We intentionally use application/octet-stream (not image/png) so that
    Gmail presents each slide as a downloadable file rather than embedding
    it as an inline preview inside the message body.
    """
    filename = os.path.basename(png_path)

    with open(png_path, "rb") as fh:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(fh.read())

    encoders.encode_base64(part)
    # name= in Content-Type + filename= in Content-Disposition → max compatibility
    part.set_param("name", filename)
    part.add_header("Content-Disposition", "attachment", filename=filename)
    msg.attach(part)


def _slide_sort_key(path: str) -> int:
    """Sort slide_1.png before slide_10.png numerically."""
    basename = os.path.splitext(os.path.basename(path))[0]  # e.g. "slide_3"
    parts = basename.split("_")
    try:
        return int(parts[-1])
    except (ValueError, IndexError):
        return 0
