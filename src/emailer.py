"""Gmail SMTP delivery for the generated Threads package."""

from __future__ import annotations

import html
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


SENDER = os.getenv("GMAIL_USER", "vipinislearning@gmail.com")
RECIPIENT = os.getenv("RECIPIENT_EMAIL", "vipinislearning@gmail.com")


def send_package(folder: Path, package: dict, slides: list[Path]) -> None:
    password = os.getenv("GMAIL_APP_PASSWORD", "")
    if not password:
        raise RuntimeError("GMAIL_APP_PASSWORD is not configured in the GitHub environment")

    post = "\n".join(package["post_lines"])
    safe_post = "<br>".join(html.escape(line) for line in package["post_lines"])
    source = html.escape(package.get("source", ""))
    body_html = f"""<html><body style='font-family:Arial,sans-serif;color:#141721'>
<h2>vipinislearning — AI Threads package</h2>
<p><b>Package:</b> {html.escape(package['package_id'])}</p>
<p style='font-size:18px;line-height:1.5'>{safe_post}</p>
<p><b>Source:</b> {source}</p>
<p>Five PNG slides are attached in upload order. This package passed automatic validation and requires no approval.</p>
</body></html>"""

    message = EmailMessage()
    message["Subject"] = f"AI Threads carousel — {package['date']} {package['slot']} — {package['topic']}"
    message["From"] = SENDER
    message["To"] = RECIPIENT
    message.set_content(post + "\n\nFive PNG slides are attached.")
    message.add_alternative(body_html, subtype="html")
    for path in slides:
        message.add_attachment(path.read_bytes(), maintype="image", subtype="png", filename=path.name)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(SENDER, password)
        smtp.send_message(message)
