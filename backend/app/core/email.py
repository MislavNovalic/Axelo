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

# ── Notification email templates ────────────────────────────────────────────

_NOTIF_FOOTER = """\
<p style="font-size:12px;color:#555;margin-top:24px;">
  You received this because you have email notifications enabled on Axelo.<br>
  <a href="{frontend_url}/settings" style="color:#5c4fff;">Manage notification preferences</a>
</p>
"""

_ASSIGNED_BODY = """\
<p>Hi {name},</p>
<p><strong>{actor}</strong> assigned you to an issue{project_line}:</p>
<p style="padding:12px 16px;background:#1e1e1e;border-left:3px solid #5c4fff;border-radius:4px;font-size:14px;color:#e0e0e0;">
  {title}
</p>
<p>{body}</p>
<a href="{link}" class="btn">View Issue</a>
""" + _NOTIF_FOOTER

_MENTIONED_BODY = """\
<p>Hi {name},</p>
<p><strong>{actor}</strong> mentioned you{project_line}:</p>
<p style="padding:12px 16px;background:#1e1e1e;border-left:3px solid #bb5cf7;border-radius:4px;font-size:14px;color:#e0e0e0;">
  {body}
</p>
<a href="{link}" class="btn">View Thread</a>
""" + _NOTIF_FOOTER

_COMMENTED_BODY = """\
<p>Hi {name},</p>
<p><strong>{actor}</strong> commented on an issue{project_line}:</p>
<p style="padding:12px 16px;background:#1e1e1e;border-left:3px solid #10b981;border-radius:4px;font-size:14px;color:#e0e0e0;">
  <em>{title}</em>
</p>
<p>{body}</p>
<a href="{link}" class="btn">View Comment</a>
""" + _NOTIF_FOOTER

_SPRINT_STARTED_BODY = """\
<p>Hi {name},</p>
<p>A new sprint has started{project_line}:</p>
<p style="padding:12px 16px;background:#1e1e1e;border-left:3px solid #00d97e;border-radius:4px;font-size:16px;font-weight:700;color:#e0e0e0;">
  🚀 {title}
</p>
<p>{body}</p>
<a href="{link}" class="btn">View Sprint Board</a>
""" + _NOTIF_FOOTER

_SPRINT_COMPLETED_BODY = """\
<p>Hi {name},</p>
<p>A sprint has been completed{project_line}:</p>
<p style="padding:12px 16px;background:#1e1e1e;border-left:3px solid #ffd166;border-radius:4px;font-size:16px;font-weight:700;color:#e0e0e0;">
  ✅ {title}
</p>
<p>{body}</p>
<a href="{link}" class="btn">View Sprint Summary</a>
""" + _NOTIF_FOOTER

_ADDED_TO_PROJECT_BODY = """\
<p>Hi {name},</p>
<p><strong>{actor}</strong> added you to a project:</p>
<p style="padding:12px 16px;background:#1e1e1e;border-left:3px solid #06b6d4;border-radius:4px;font-size:16px;font-weight:700;color:#e0e0e0;">
  📁 {title}
</p>
<p>{body}</p>
<a href="{link}" class="btn">Open Project</a>
""" + _NOTIF_FOOTER

_ROLE_CHANGED_BODY = """\
<p>Hi {name},</p>
<p>Your role has been updated{project_line} by <strong>{actor}</strong>.</p>
<p style="padding:12px 16px;background:#1e1e1e;border-left:3px solid #ff8c42;border-radius:4px;font-size:14px;color:#e0e0e0;">
  {body}
</p>
<a href="{link}" class="btn">View Project</a>
""" + _NOTIF_FOOTER

_GENERIC_NOTIF_BODY = """\
<p>Hi {name},</p>
<p>{body}</p>
<a href="{link}" class="btn">View in Axelo</a>
""" + _NOTIF_FOOTER


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


# ── Shared notification email builder ───────────────────────────────────────

def _build_notif_email(subject: str, body_template: str, **kwargs) -> tuple[str, str]:
    """Render subject + full HTML for a notification email."""
    import html as _html
    safe = {k: _html.escape(str(v)) for k, v in kwargs.items()}
    body_html = body_template.format(**safe, frontend_url=settings.FRONTEND_URL)
    full_html = _BASE_HTML.format(
        subject=subject,
        body=body_html,
        frontend_url=settings.FRONTEND_URL,
    )
    plain = (
        f"{kwargs.get('title', subject)}\n\n"
        f"{kwargs.get('body', '')}\n\n"
        f"View: {kwargs.get('link', settings.FRONTEND_URL)}"
    )
    return full_html, plain


def _project_line(project_name: str) -> str:
    import html as _html
    return f" in <strong>{_html.escape(project_name)}</strong>" if project_name else ""


# ── Notification email senders ───────────────────────────────────────────────

async def send_assigned_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        f"You were assigned: {title}", _ASSIGNED_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, f"Assigned to you: {title}", html, plain)


async def send_mentioned_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        f"{actor_name or 'Someone'} mentioned you", _MENTIONED_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, f"{actor_name or 'Someone'} mentioned you", html, plain)


async def send_commented_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        f"New comment on: {title}", _COMMENTED_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, f"New comment on: {title}", html, plain)


async def send_sprint_started_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        f"Sprint started: {title}", _SPRINT_STARTED_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, f"🚀 Sprint started: {title}", html, plain)


async def send_sprint_completed_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        f"Sprint completed: {title}", _SPRINT_COMPLETED_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, f"✅ Sprint completed: {title}", html, plain)


async def send_added_to_project_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        f"Added to project: {title}", _ADDED_TO_PROJECT_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, f"You've been added to: {title}", html, plain)


async def send_role_changed_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        "Your role has been updated", _ROLE_CHANGED_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, "Your role has been updated", html, plain)


async def send_generic_notification_email(
    *, to_email: str, to_name: str, title: str, body: str,
    link: str = "", actor_name: str = "", project_name: str = "",
) -> None:
    html, plain = _build_notif_email(
        title, _GENERIC_NOTIF_BODY,
        name=to_name.split()[0] if to_name else "there",
        actor=actor_name or "Someone",
        title=title, body=body, link=link or settings.FRONTEND_URL,
        project_line=_project_line(project_name),
    )
    await _send(to_email, title, html, plain)
