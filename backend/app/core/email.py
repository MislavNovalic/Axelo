"""
Email sending utility — OWASP-aware
  - Uses aiosmtplib for async, non-blocking sends
  - HTML + plain-text fallback in every email
  - No user-supplied content rendered as HTML (XSS prevention)
  - SMTP credentials never logged
"""
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


# ── HTML templates ─────────────────────────────────────────────────────────────

_BASE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>{subject}</title>
  <style>
    body {{ margin:0; padding:0; background:#0d0d0d; font-family:'Segoe UI',Arial,sans-serif; color:#e0e0e0; }}
    .wrapper {{ max-width:560px; margin:40px auto; background:#161616; border:1px solid #2a2a2a; border-radius:14px; overflow:hidden; }}
    .header {{ background:linear-gradient(135deg,#5c4fff 0%,#bb5cf7 100%); padding:32px 36px; }}
    .header h1 {{ margin:0; font-size:22px; font-weight:800; color:#fff; letter-spacing:-0.3px; }}
    .header p {{ margin:6px 0 0; font-size:13px; color:rgba(255,255,255,0.75); }}
    .body {{ padding:32px 36px; }}
    .body p {{ font-size:15px; line-height:1.6; color:#c8c8c8; margin:0 0 16px; }}
    .btn {{ display:inline-block; margin:8px 0 24px; padding:13px 28px; background:linear-gradient(135deg,#5c4fff,#bb5cf7); color:#fff !important; text-decoration:none; border-radius:8px; font-weight:700; font-size:15px; }}
    .footer {{ padding:20px 36px; border-top:1px solid #2a2a2a; font-size:12px; color:#555; }}
    .footer a {{ color:#5c4fff; text-decoration:none; }}
    .mono {{ font-family:monospace; background:#1e1e1e; padding:2px 6px; border-radius:4px; font-size:13px; color:#bb5cf7; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>🗂️ Axelo</h1>
      <p>Open-source project management</p>
    </div>
    <div class="body">
      {body}
    </div>
    <div class="footer">
      You received this email because an account was created at Axelo using this address.
      If you didn&apos;t register, you can safely ignore this email.<br><br>
      <a href="{frontend_url}">{frontend_url}</a>
    </div>
  </div>
</body>
</html>
"""

_VERIFY_BODY = """\
<p>Hi {name},</p>
<p>Thanks for signing up! Please verify your email address to activate your account.</p>
<a href="{verify_url}" class="btn">Verify Email Address</a>
<p style="font-size:13px;color:#666;">
  This link expires in <strong>24 hours</strong>.<br>
  If the button doesn&apos;t work, copy this URL into your browser:<br>
  <span class="mono">{verify_url}</span>
</p>
"""

_VERIFY_PLAIN = """\
Hi {name},

Please verify your email address to activate your Axelo account.

Verify here: {verify_url}

This link expires in 24 hours.

If you didn't register, ignore this email.
"""

_ALREADY_VERIFIED_BODY = """\
<p>Hi there,</p>
<p>Your email address is already verified. You can log in at any time.</p>
<a href="{frontend_url}/login" class="btn">Go to Login</a>
"""


async def _send(to_email: str, subject: str, html: str, plain: str) -> None:
    """Low-level async SMTP send. Raises on failure."""
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — skipping email to %s", to_email)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM}>"
    msg["To"] = to_email

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME or None,
            password=settings.SMTP_PASSWORD or None,
            use_tls=False,
            start_tls=settings.SMTP_TLS,
        )
        logger.info("Email sent: subject=%r to=%s", subject, to_email)
    except Exception:
        # Log the error but never log credentials or the message body
        logger.exception("Failed to send email to %s (subject=%r)", to_email, subject)
        raise


async def send_verification_email(to_email: str, full_name: str, token: str) -> None:
    """
    Send email verification link.
    OWASP A03: full_name is HTML-escaped before embedding.
    """
    import html as _html
    safe_name = _html.escape(full_name.split()[0] if full_name else "there")
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    body_html = _VERIFY_BODY.format(name=safe_name, verify_url=verify_url)
    full_html = _BASE_HTML.format(
        subject="Verify your Axelo email",
        body=body_html,
        frontend_url=settings.FRONTEND_URL,
    )
    plain = _VERIFY_PLAIN.format(name=safe_name, verify_url=verify_url)

    await _send(to_email, "Verify your Axelo email address", full_html, plain)
